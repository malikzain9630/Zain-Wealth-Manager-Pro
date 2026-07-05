"""
Fund Statement Import Service
Phase 10A - Smart Mutual Fund / MTPF Statement Import

Purpose:
- Read Al Meezan Mutual Fund / MTPF PDF statements.
- Extract balance summary rows:
    Fund Code
    Unit Type
    Units
    NAV
    Investment Value
    FYTD Gain/Loss
    Total Gain/Loss
- Classify rows:
    Mutual Fund
    Pension / MTPF
- Return clean preview rows.
- Do NOT directly update database from this service.

Important:
- This service is separate from Smart Portfolio Import.
- PSX stocks are handled by smart_import_service.py.
- Mutual Funds and MTPF/Pension are handled here.
"""

import re
from pathlib import Path


SUPPORTED_FUND_STATEMENT_EXTENSIONS = [
    ".pdf",
    ".txt",
]


KNOWN_FUND_CODES = {
    "KMIF",
    "MIF",
    "MCF",
    "MIIF",
    "MTPF-DSF",
    "MTPF-ESF",
    "MTPF-MMSF",
    "MTPF-MMF",
    "MTPF-CSF",
}


FUND_NAME_MAP = {
    "KMIF": "KSE Meezan Index Fund",
    "MIF": "Meezan Islamic Fund",
    "MCF": "Meezan Cash Fund",
    "MIIF": "Meezan Islamic Income Fund",
    "MTPF-DSF": "Meezan Tahaffuz Pension Fund - Debt Sub Fund",
    "MTPF-ESF": "Meezan Tahaffuz Pension Fund - Equity Sub Fund",
    "MTPF-MMSF": "Meezan Tahaffuz Pension Fund - Money Market Sub Fund",
    "MTPF-MMF": "Meezan Tahaffuz Pension Fund - Money Market Fund",
    "MTPF-CSF": "Meezan Tahaffuz Pension Fund - Commodity Sub Fund",
}


def read_fund_statement_file(file_path):
    """
    Read Al Meezan Mutual Fund / MTPF statement.

    Returns:
    {
        "success": bool,
        "file_type": str,
        "rows": list[dict],
        "errors": list[str],
        "warnings": list[str],
        "raw_text": str,
        "summary": dict,
    }
    """

    path = Path(file_path)

    result = {
        "success": False,
        "file_type": "",
        "rows": [],
        "errors": [],
        "warnings": [],
        "raw_text": "",
        "summary": {},
    }

    if not path.exists():
        result["errors"].append("Selected file does not exist.")
        return result

    extension = path.suffix.lower()
    result["file_type"] = extension

    if extension not in SUPPORTED_FUND_STATEMENT_EXTENSIONS:
        result["errors"].append(
            "Unsupported fund statement file type. Supported: "
            + ", ".join(SUPPORTED_FUND_STATEMENT_EXTENSIONS)
        )
        return result

    try:

        if extension == ".pdf":
            text = extract_text_from_pdf(path)

        else:
            text = path.read_text(encoding="utf-8", errors="ignore")

        result["raw_text"] = text

        if not looks_like_fund_statement(text):
            result["warnings"].append(
                "This file does not clearly look like an Al Meezan "
                "Mutual Fund/MTPF statement. Extraction will still be attempted."
            )

        rows = extract_fund_statement_rows(text)
        rows = clean_fund_rows(rows)

        result["rows"] = rows
        result["summary"] = get_fund_statement_summary(rows)

        if rows:
            result["success"] = True
        else:
            result["warnings"].append(
                "No valid Mutual Fund/MTPF balance summary rows were detected."
            )

    except Exception as e:
        result["errors"].append(str(e))

    return result


def extract_text_from_pdf(path):
    """
    Extract text from PDF.

    Tries smart_import_service first to reuse installed PDF support.
    Then falls back to pypdf / PyPDF2.
    """

    errors = []

    try:
        from services.smart_import_service import extract_text_from_pdf as psx_extract_text

        text = psx_extract_text(path)

        if text and text.strip():
            return text

    except Exception as e:
        errors.append(f"smart_import_service PDF extractor: {e}")

    try:
        try:
            from pypdf import PdfReader
        except Exception:
            from PyPDF2 import PdfReader

        reader = PdfReader(str(path))

        text_parts = []

        for page in reader.pages:
            text_parts.append(page.extract_text() or "")

        text = "\n".join(text_parts).strip()

        if text:
            return text

    except Exception as e:
        errors.append(f"pypdf/PyPDF2: {e}")

    raise ValueError(
        "Could not extract text from PDF.\n\n"
        "Please install PDF text support:\n"
        "pip install pypdf\n\n"
        "Details:\n"
        + "\n".join(errors)
    )


def looks_like_fund_statement(text):
    """
    Detect whether text looks like Al Meezan fund/MTPF statement.
    """

    lowered = str(text or "").lower()

    keywords = [
        "al meezan investment management",
        "statement of account",
        "balance summary",
        "funds type of units",
        "nav",
        "unit balance",
        "mtpf",
        "meezan islamic fund",
        "kse meezan index fund",
    ]

    score = 0

    for keyword in keywords:
        if keyword in lowered:
            score += 1

    return score >= 3


def extract_fund_statement_rows(text):
    """
    Extract balance summary rows from statement text.

    The parser intentionally reads direct lines only to avoid transaction-detail
    false positives such as 'Value of investment...' lines.
    """

    lines = get_clean_lines(text)

    rows = []

    for line in lines:

        parsed = parse_balance_summary_row(line)

        if parsed:
            rows.append(parsed)

    return rows


def get_clean_lines(text):
    """
    Normalize PDF text lines.
    """

    raw_lines = str(text or "").replace("\r", "\n").splitlines()

    lines = []

    for line in raw_lines:

        line = str(line or "").strip()

        if not line:
            continue

        line = line.replace("\t", " ")
        line = re.sub(r"\s+", " ", line).strip()

        if not line:
            continue

        lines.append(line)

    return lines


def parse_balance_summary_row(line):
    """
    Parse one Al Meezan balance summary row.

    Supports both formats:

    Normal text order:
    KMIF GROWTH-B 104.1872 182.4219 19,006 581 581

    Mixed PDF extraction order:
    104.1872 581 182.4219 19,006KMIF 581GROWTH-B
    """

    line = str(line or "").strip()

    if not line:
        return None

    parsed = parse_normal_balance_summary_row(line)

    if parsed:
        return parsed

    parsed = parse_embedded_code_balance_summary_row(line)

    if parsed:
        return parsed

    return None


def parse_normal_balance_summary_row(line):
    """
    Parse row where fund code is at line start.
    """

    fund_code = find_known_fund_code_at_start(line)

    if not fund_code:
        return None

    remaining = line[len(fund_code):].strip()

    if not remaining:
        return None

    first_number_match = re.search(
        r"[+-]?\d[\d,]*(?:\.\d+)?",
        remaining
    )

    if not first_number_match:
        return None

    unit_type = remaining[:first_number_match.start()].strip()
    number_text = remaining[first_number_match.start():].strip()

    numbers = extract_numbers(number_text)

    if len(numbers) < 3:
        return None

    units = numbers[0]
    nav = numbers[1]
    investment_value = numbers[2]

    fytd_gain_loss = numbers[3] if len(numbers) >= 4 else 0.0
    total_gain_loss = numbers[4] if len(numbers) >= 5 else 0.0

    if not is_reasonable_balance_summary_row(
        units,
        nav,
        investment_value,
        fytd_gain_loss,
        total_gain_loss
    ):
        return None

    return build_fund_row(
        fund_code=fund_code,
        unit_type=unit_type,
        units=units,
        nav=nav,
        investment_value=investment_value,
        fytd_gain_loss=fytd_gain_loss,
        total_gain_loss=total_gain_loss,
    )


def parse_embedded_code_balance_summary_row(line):
    """
    Parse row where PDF extractor places numbers before fund code.

    Observed Al Meezan PDF extraction:
    prefix numbers:
        [units, total_gain_loss, nav, investment_value]
    suffix first number:
        fytd_gain_loss
    suffix remaining text:
        unit_type
    """

    match = find_known_fund_code_anywhere(line)

    if not match:
        return None

    fund_code = match["fund_code"]
    start = match["start"]
    end = match["end"]

    if start == 0:
        return None

    prefix = line[:start]
    suffix = line[end:]

    prefix_numbers = extract_numbers(prefix)
    suffix_numbers = extract_numbers(suffix)

    if len(prefix_numbers) < 4:
        return None

    units = prefix_numbers[0]
    total_gain_loss = prefix_numbers[1]
    nav = prefix_numbers[2]
    investment_value = prefix_numbers[3]

    fytd_gain_loss = suffix_numbers[0] if suffix_numbers else 0.0
    unit_type = extract_unit_type_from_suffix(suffix)

    if not is_reasonable_balance_summary_row(
        units,
        nav,
        investment_value,
        fytd_gain_loss,
        total_gain_loss
    ):
        return None

    return build_fund_row(
        fund_code=fund_code,
        unit_type=unit_type,
        units=units,
        nav=nav,
        investment_value=investment_value,
        fytd_gain_loss=fytd_gain_loss,
        total_gain_loss=total_gain_loss,
    )


def is_reasonable_balance_summary_row(
    units,
    nav,
    investment_value,
    fytd_gain_loss=0.0,
    total_gain_loss=0.0
):
    """
    Avoid false positives from transaction-detail pages.
    """

    units = safe_float(units)
    nav = safe_float(nav)
    investment_value = safe_float(investment_value)

    # NAV should not be negative in balance summary.
    if nav <= 0:
        return False

    # Units and investment value can be zero for inactive funds.
    if units < 0:
        return False

    if investment_value < 0:
        return False

    # Reject date fragments accidentally parsed as investment values.
    if investment_value < 0:
        return False

    return True


def build_fund_row(
    fund_code,
    unit_type,
    units,
    nav,
    investment_value,
    fytd_gain_loss=0.0,
    total_gain_loss=0.0,
):
    """
    Build standardized fund row dict.
    """

    category = classify_fund_category(fund_code)

    if not unit_type:
        unit_type = "N/A"

    unit_type = str(unit_type).strip()

    return {
        "category": category,
        "fund_code": fund_code,
        "fund_name": FUND_NAME_MAP.get(fund_code, fund_code),
        "unit_type": unit_type,
        "units": round(safe_float(units), 4),
        "nav": round(safe_float(nav), 4),
        "investment_value": round(safe_float(investment_value), 2),
        "fytd_gain_loss": round(safe_float(fytd_gain_loss), 2),
        "total_gain_loss": round(safe_float(total_gain_loss), 2),
        "import_suggested": is_import_suggested(units, investment_value),
        "source": "Al Meezan Balance Summary",
        "confidence": calculate_fund_row_confidence(
            fund_code,
            unit_type,
            safe_float(units),
            safe_float(nav),
            safe_float(investment_value)
        ),
        "remarks": build_fund_row_remarks(
            fund_code,
            safe_float(units),
            safe_float(investment_value)
        ),
    }


def find_known_fund_code_anywhere(line):
    """
    Find known fund code anywhere in line.

    Longest code first so MTPF-DSF is matched before shorter codes.
    """

    text = str(line or "").upper()

    codes = sorted(
        KNOWN_FUND_CODES,
        key=lambda item: len(item),
        reverse=True
    )

    for code in codes:

        index = text.find(code)

        if index < 0:
            continue

        return {
            "fund_code": code,
            "start": index,
            "end": index + len(code),
        }

    return None


def extract_unit_type_from_suffix(suffix):
    """
    Extract unit type from suffix text:
    '581GROWTH-B' -> 'GROWTH-B'
    '34HIGH-VOL' -> 'HIGH-VOL'
    """

    text = str(suffix or "").strip()

    if not text:
        return "N/A"

    text = re.sub(r"^[\s\d,.\-+]+", "", text).strip()
    text = re.sub(r"\b[+-]?\d+(?:\.\d+)?\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return "N/A"

    return text


def find_known_fund_code_at_start(line):
    """
    Return fund code if line starts with a known fund code.
    """

    line = str(line or "").strip().upper()

    # Longest first so MTPF-DSF is matched before MTPF.
    codes = sorted(
        KNOWN_FUND_CODES,
        key=lambda item: len(item),
        reverse=True
    )

    for code in codes:

        if line == code:
            return code

        if line.startswith(code + " "):
            return code

    return ""


def classify_fund_category(fund_code):
    """
    Classify fund row as Mutual Fund or Pension/MTPF.
    """

    fund_code = str(fund_code or "").upper()

    if fund_code.startswith("MTPF"):
        return "Pension / MTPF"

    return "Mutual Fund"


def is_import_suggested(units, investment_value):
    """
    Suggest import only for active/current positive holdings.
    """

    units = safe_float(units)
    investment_value = safe_float(investment_value)

    return bool(units > 0 and investment_value > 0)


def calculate_fund_row_confidence(
    fund_code,
    unit_type,
    units,
    nav,
    investment_value
):
    """
    Calculate extraction confidence.
    """

    score = 0

    if fund_code in KNOWN_FUND_CODES:
        score += 35

    if unit_type:
        score += 10

    if units >= 0:
        score += 15

    if nav > 0:
        score += 20

    if investment_value >= 0:
        score += 20

    if score > 100:
        score = 100

    return score


def build_fund_row_remarks(fund_code, units, investment_value):
    """
    Build row remarks.
    """

    if classify_fund_category(fund_code) == "Pension / MTPF":
        base = "MTPF/Pension row extracted from Al Meezan statement."
    else:
        base = "Mutual Fund row extracted from Al Meezan statement."

    if not is_import_suggested(units, investment_value):
        base += " Zero balance row; import usually not required."

    return base


def clean_fund_rows(rows):
    """
    Clean and deduplicate fund rows.
    """

    final_rows = []
    seen = set()

    for row in rows or []:

        fund_code = str(row.get("fund_code", "")).upper().strip()
        unit_type = str(row.get("unit_type", "")).upper().strip()

        key = (
            fund_code,
            unit_type,
            round(safe_float(row.get("units", 0)), 4),
            round(safe_float(row.get("nav", 0)), 4),
            round(safe_float(row.get("investment_value", 0)), 2),
        )

        if key in seen:
            continue

        seen.add(key)

        confidence = int(safe_float(row.get("confidence", 0)))

        if confidence < 0:
            confidence = 0

        if confidence > 100:
            confidence = 100

        final_rows.append({
            "category": row.get("category", ""),
            "fund_code": fund_code,
            "fund_name": row.get("fund_name", FUND_NAME_MAP.get(fund_code, fund_code)),
            "unit_type": row.get("unit_type", ""),
            "units": round(safe_float(row.get("units", 0)), 4),
            "nav": round(safe_float(row.get("nav", 0)), 4),
            "investment_value": round(safe_float(row.get("investment_value", 0)), 2),
            "fytd_gain_loss": round(safe_float(row.get("fytd_gain_loss", 0)), 2),
            "total_gain_loss": round(safe_float(row.get("total_gain_loss", 0)), 2),
            "import_suggested": bool(row.get("import_suggested", False)),
            "source": row.get("source", ""),
            "confidence": confidence,
            "remarks": row.get("remarks", ""),
        })

    final_rows.sort(
        key=lambda item: (
            item["category"],
            item["fund_code"],
            item["unit_type"]
        )
    )

    return final_rows


def get_fund_statement_summary(rows):
    """
    Return summary for extracted rows.
    """

    rows = rows or []

    mutual_fund_rows = [
        row for row in rows
        if row.get("category") == "Mutual Fund"
    ]

    pension_rows = [
        row for row in rows
        if row.get("category") == "Pension / MTPF"
    ]

    suggested_rows = [
        row for row in rows
        if row.get("import_suggested")
    ]

    total_value = sum(
        safe_float(row.get("investment_value", 0))
        for row in rows
    )

    mutual_fund_value = sum(
        safe_float(row.get("investment_value", 0))
        for row in mutual_fund_rows
    )

    pension_value = sum(
        safe_float(row.get("investment_value", 0))
        for row in pension_rows
    )

    total_fytd_gain_loss = sum(
        safe_float(row.get("fytd_gain_loss", 0))
        for row in rows
    )

    total_gain_loss = sum(
        safe_float(row.get("total_gain_loss", 0))
        for row in rows
    )

    return {
        "total_rows": len(rows),
        "suggested_rows": len(suggested_rows),
        "mutual_fund_rows": len(mutual_fund_rows),
        "pension_rows": len(pension_rows),
        "total_value": round(total_value, 2),
        "mutual_fund_value": round(mutual_fund_value, 2),
        "pension_value": round(pension_value, 2),
        "total_fytd_gain_loss": round(total_fytd_gain_loss, 2),
        "total_gain_loss": round(total_gain_loss, 2),
    }


def split_fund_rows_by_category(rows):
    """
    Split rows into mutual fund rows and pension/MTPF rows.
    """

    mutual_funds = []
    pension_mtpf = []

    for row in rows or []:

        if row.get("category") == "Pension / MTPF":
            pension_mtpf.append(row)
        else:
            mutual_funds.append(row)

    return {
        "mutual_funds": mutual_funds,
        "pension_mtpf": pension_mtpf,
    }


def extract_numbers(text):
    """
    Extract numbers from text, supporting commas and negatives.
    """

    text = str(text or "")
    text = text.replace(",", "")

    matches = re.findall(r"[+-]?\d+(?:\.\d+)?", text)

    numbers = []

    for match in matches:
        numbers.append(safe_float(match))

    return numbers


def safe_float(value):
    """
    Convert value to float safely.
    """

    try:
        if value is None:
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        text = text.replace(",", "")

        if not text:
            return 0.0

        return float(text)

    except Exception:
        return 0.0
