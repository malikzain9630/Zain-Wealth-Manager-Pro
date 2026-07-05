"""
Smart Import Service
Phase 10A - Smart Portfolio Import Engine

Purpose:
- Read portfolio data from CSV, Excel, PDF text, and image screenshots.
- Extract likely holdings:
    Symbol
    Share Name / Company Name
    Shares
    Average Price
    Current Price
- Return clean preview rows.
- Do NOT directly update portfolio from this service.

Important:
- CSV and Excel are most reliable.
- PDF text extraction requires at least one PDF text library:
    pip install pypdf
  Optional fallbacks:
    pip install PyPDF2 pdfplumber pymupdf
- Image/JPG/PNG OCR requires:
    pillow, pytesseract, Tesseract OCR installed on Windows
"""

import csv
import os
import re
from pathlib import Path


SUPPORTED_EXTENSIONS = [
    ".csv",
    ".xlsx",
    ".xlsm",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff",
]


SYMBOL_HEADERS = [
    "symbol",
    "stock",
    "scrip",
    "ticker",
    "security",
    "security code",
    "company code",
]

NAME_HEADERS = [
    "share name",
    "company name",
    "stock name",
    "security name",
    "name",
    "company",
    "share",
]

SHARES_HEADERS = [
    "shares",
    "share",
    "quantity",
    "qty",
    "holding",
    "holdings",
    "units",
    "volume",
    "balance",
]

AVG_PRICE_HEADERS = [
    "avg price",
    "average price",
    "avg cost",
    "average cost",
    "cost price",
    "purchase price",
    "buy price",
    "rate",
    "avg rate",
]

CURRENT_PRICE_HEADERS = [
    "current price",
    "market price",
    "last price",
    "close price",
    "ltp",
    "price",
    "current rate",
    "market rate",
]

INVESTMENT_HEADERS = [
    "investment",
    "cost value",
    "cost",
    "book value",
    "purchase value",
    "total cost",
]

CURRENT_VALUE_HEADERS = [
    "current value",
    "market value",
    "value",
    "market worth",
    "holding value",
]


COMMON_WORDS_TO_IGNORE = {
    "symbol",
    "stock",
    "shares",
    "quantity",
    "qty",
    "price",
    "current",
    "average",
    "market",
    "value",
    "investment",
    "profit",
    "loss",
    "total",
    "portfolio",
    "statement",
    "client",
    "account",
    "date",
    "name",
    "balance",
    "security",
    "share",
    "company",
}


def read_portfolio_file(file_path):
    """
    Read supported file and return preview rows.

    Returns dictionary:
    {
        "success": bool,
        "file_type": str,
        "rows": list[dict],
        "errors": list[str],
        "warnings": list[str],
        "raw_text": str
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
    }

    if not path.exists():
        result["errors"].append("Selected file does not exist.")
        return result

    extension = path.suffix.lower()
    result["file_type"] = extension

    if extension not in SUPPORTED_EXTENSIONS:
        result["errors"].append(
            "Unsupported file type. Supported: "
            + ", ".join(SUPPORTED_EXTENSIONS)
        )
        return result

    try:

        if extension == ".csv":
            rows = read_csv_file(path)
            result["rows"] = extract_holdings_from_rows(rows)

        elif extension in [".xlsx", ".xlsm"]:
            rows = read_excel_file(path)
            result["rows"] = extract_holdings_from_rows(rows)

        elif extension == ".pdf":
            text = extract_text_from_pdf(path)
            result["raw_text"] = text
            result["rows"] = extract_holdings_from_text(text)

        elif extension in [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]:
            text = extract_text_from_image(path)
            result["raw_text"] = text
            result["rows"] = extract_holdings_from_text(text)

        result["rows"] = clean_preview_rows(result["rows"])

        if result["rows"]:
            result["success"] = True
        else:
            result["warnings"].append(
                "No valid portfolio rows were detected. "
                "For PDF, make sure it is text-based and not scanned. "
                "CSV/Excel is most accurate."
            )

    except Exception as e:
        result["errors"].append(str(e))

    return result


def read_csv_file(path):
    """
    Read CSV file into list of dictionaries.
    """

    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin1"]

    last_error = None

    for encoding in encodings:

        try:
            with open(path, "r", newline="", encoding=encoding) as file:
                sample = file.read(4096)
                file.seek(0)

                dialect = detect_csv_dialect(sample)

                reader = csv.DictReader(file, dialect=dialect)

                rows = []

                for row in reader:
                    rows.append(dict(row))

                if rows:
                    return rows

        except Exception as e:
            last_error = e

    raise ValueError(f"Could not read CSV file. {last_error}")


def detect_csv_dialect(sample):
    """
    Detect CSV delimiter safely.
    """

    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")

    except Exception:
        return csv.excel


def read_excel_file(path):
    """
    Read first useful Excel sheet into list of dictionaries.
    """

    try:
        from openpyxl import load_workbook

    except Exception as e:
        raise ImportError(
            "openpyxl is required to read Excel files. "
            "Install using: pip install openpyxl"
        ) from e

    workbook = load_workbook(str(path), data_only=True, read_only=True)

    best_rows = []

    for sheet in workbook.worksheets:

        rows = list(sheet.iter_rows(values_only=True))

        if not rows:
            continue

        extracted = rows_to_dicts(rows)

        if len(extracted) > len(best_rows):
            best_rows = extracted

    workbook.close()

    return best_rows


def rows_to_dicts(rows):
    """
    Convert Excel rows into dictionaries by detecting header row.
    """

    header_index = detect_header_row(rows)

    if header_index is None:
        return []

    headers = rows[header_index]
    normalized_headers = []

    for value in headers:
        text = normalize_header(value)

        if not text:
            text = f"column_{len(normalized_headers) + 1}"

        normalized_headers.append(text)

    dict_rows = []

    for row in rows[header_index + 1:]:

        if row_is_empty(row):
            continue

        item = {}

        for index, value in enumerate(row):

            if index >= len(normalized_headers):
                continue

            item[normalized_headers[index]] = value

        dict_rows.append(item)

    return dict_rows


def detect_header_row(rows):
    """
    Detect the row that most likely contains portfolio headers.
    """

    best_index = None
    best_score = 0

    for index, row in enumerate(rows[:30]):

        score = 0

        normalized_values = [
            normalize_header(value)
            for value in row
        ]

        for value in normalized_values:

            if value in SYMBOL_HEADERS:
                score += 5

            if value in NAME_HEADERS:
                score += 1

            if value in SHARES_HEADERS:
                score += 5

            if value in AVG_PRICE_HEADERS:
                score += 4

            if value in CURRENT_PRICE_HEADERS:
                score += 4

            if value in INVESTMENT_HEADERS:
                score += 2

            if value in CURRENT_VALUE_HEADERS:
                score += 2

        if score > best_score:
            best_score = score
            best_index = index

    if best_score >= 8:
        return best_index

    return None


def extract_text_from_pdf(path):
    """
    Extract text from text-based PDF.

    Tries:
    1. pypdf
    2. PyPDF2
    3. pdfplumber
    4. pymupdf / fitz

    Install recommended:
        pip install pypdf
    """

    errors = []
    text_parts = []

    # 1) pypdf
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))

        for page in reader.pages:
            text_parts.append(page.extract_text() or "")

        text = "\n".join(text_parts).strip()

        if text:
            return normalize_pdf_text(text)

    except Exception as e:
        errors.append(f"pypdf: {e}")

    # 2) PyPDF2
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(str(path))

        text_parts = []

        for page in reader.pages:
            text_parts.append(page.extract_text() or "")

        text = "\n".join(text_parts).strip()

        if text:
            return normalize_pdf_text(text)

    except Exception as e:
        errors.append(f"PyPDF2: {e}")

    # 3) pdfplumber
    try:
        import pdfplumber

        text_parts = []

        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")

        text = "\n".join(text_parts).strip()

        if text:
            return normalize_pdf_text(text)

    except Exception as e:
        errors.append(f"pdfplumber: {e}")

    # 4) PyMuPDF / fitz
    try:
        import fitz

        text_parts = []

        document = fitz.open(str(path))

        for page in document:
            text_parts.append(page.get_text("text") or "")

        document.close()

        text = "\n".join(text_parts).strip()

        if text:
            return normalize_pdf_text(text)

    except Exception as e:
        errors.append(f"pymupdf: {e}")

    raise ValueError(
        "Could not extract text from PDF.\n\n"
        "Please install PDF text support:\n"
        "pip install pypdf\n\n"
        "If this is a scanned PDF, OCR will be required.\n\n"
        "Details:\n"
        + "\n".join(errors[-4:])
    )


def normalize_pdf_text(text):
    """
    Normalize PDF extracted text.
    """

    text = str(text or "")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s+\n", "\n", text)

    return text.strip()


def extract_text_from_image(path):
    """
    Extract text from JPG/PNG screenshot using OCR.

    Requirements:
    1. pip install pillow pytesseract
    2. Install Tesseract OCR on Windows.
       Common path:
       C:\\Program Files\\Tesseract-OCR\\tesseract.exe
    """

    try:
        from PIL import Image, ImageOps, ImageFilter
        import pytesseract

    except Exception as e:
        raise ImportError(
            "Image import requires OCR Python packages.\n\n"
            "Please run this command:\n"
            "pip install pillow pytesseract\n\n"
            "Then install Tesseract OCR for Windows."
        ) from e

    configure_tesseract_if_available(pytesseract)
    validate_tesseract_language_data()

    try:
        image = Image.open(str(path))

    except Exception as e:
        raise ValueError(f"Could not open selected image file. {e}") from e

    ocr_texts = []

    # Try original image first.
    try:
        ocr_texts.append(
            pytesseract.image_to_string(
                image,
                lang="eng",
                config=get_tesseract_config(6)
            )
        )
    except Exception as e:
        raise RuntimeError(
            "Tesseract OCR is not working.\n\n"
            "Please install Tesseract OCR on Windows and restart the app.\n"
            "Expected path usually:\n"
            "C:\\Program Files\\Tesseract-OCR\\tesseract.exe\n\n"
            f"TESSDATA_PREFIX: {os.environ.get('TESSDATA_PREFIX', '')}\n"
            f"Details: {e}"
        ) from e

    # Try preprocessed image for screenshots.
    try:
        processed = preprocess_image_for_ocr(image)
        ocr_texts.append(
            pytesseract.image_to_string(
                processed,
                lang="eng",
                config=get_tesseract_config(6)
            )
        )
    except Exception:
        pass

    # Try table-like OCR mode.
    try:
        processed = preprocess_image_for_ocr(image)
        ocr_texts.append(
            pytesseract.image_to_string(
                processed,
                lang="eng",
                config=get_tesseract_config(11)
            )
        )
    except Exception:
        pass

    text = "\n".join([t for t in ocr_texts if t and t.strip()]).strip()

    if not text:
        raise ValueError(
            "No readable text detected from image.\n\n"
            "Please use a clearer/high-resolution screenshot, "
            "or use CSV/Excel for best accuracy."
        )

    return normalize_pdf_text(text)


def configure_tesseract_if_available(pytesseract):
    """
    Configure pytesseract with common Windows install paths.

    This version sets:
    - tesseract_cmd
    - TESSDATA_PREFIX without quotes
    - PATH fallback
    """

    possible_paths = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]

    for tesseract_path in possible_paths:

        if not tesseract_path.exists():
            continue

        pytesseract.pytesseract.tesseract_cmd = str(tesseract_path)

        install_folder = tesseract_path.parent
        tessdata_path = install_folder / "tessdata"

        if tessdata_path.exists():
            # No quotes here. Tesseract reads this as an environment variable.
            os.environ["TESSDATA_PREFIX"] = str(tessdata_path)

        # Add install folder to PATH for subprocess dependencies.
        current_path = os.environ.get("PATH", "")

        if str(install_folder) not in current_path:
            os.environ["PATH"] = str(install_folder) + os.pathsep + current_path

        return


def get_tesseract_config(psm=6):
    """
    Return Tesseract OCR config.

    Do not include --tessdata-dir here; TESSDATA_PREFIX handles it.
    """

    return f"--psm {psm}"

def validate_tesseract_language_data():
    """
    Validate English OCR language data exists.
    """

    possible_eng_paths = [
        Path(r"C:\Program Files\Tesseract-OCR\tessdata\eng.traineddata"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tessdata\eng.traineddata"),
    ]

    for eng_path in possible_eng_paths:

        if eng_path.exists():
            return True

    raise RuntimeError(
        "Tesseract English language data is missing.\n\n"
        "Required file:\n"
        "C:\\Program Files\\Tesseract-OCR\\tessdata\\eng.traineddata\n\n"
        "Fix:\n"
        "1. Re-run Tesseract installer\n"
        "2. Select English language data during installation\n"
        "3. Or copy eng.traineddata into the tessdata folder"
    )


def preprocess_image_for_ocr(image):
    """
    Improve screenshot readability for OCR.
    """

    from PIL import ImageOps, ImageFilter

    image = image.convert("L")

    # Enlarge small screenshots.
    width, height = image.size

    if width < 1600:
        scale = 1600 / max(width, 1)
        new_size = (
            int(width * scale),
            int(height * scale),
        )
        image = image.resize(new_size)

    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.SHARPEN)

    # Simple threshold.
    image = image.point(lambda pixel: 255 if pixel > 180 else 0)

    return image


def extract_holdings_from_rows(rows):
    """
    Extract holdings from CSV/Excel dictionary rows.
    """

    if not rows:
        return []

    cleaned_rows = []
    normalized_rows = []

    for row in rows:

        normalized_row = {}

        for key, value in row.items():
            normalized_key = normalize_header(key)
            normalized_row[normalized_key] = value

        normalized_rows.append(normalized_row)

    columns = detect_columns(normalized_rows)

    for row in normalized_rows:

        symbol = get_row_value(row, columns.get("symbol"))
        share_name = get_row_value(row, columns.get("share_name"))
        shares = get_row_value(row, columns.get("shares"))
        avg_price = get_row_value(row, columns.get("avg_price"))
        current_price = get_row_value(row, columns.get("current_price"))

        investment_value = get_row_value(row, columns.get("investment"))
        current_value = get_row_value(row, columns.get("current_value"))

        symbol = normalize_symbol(symbol)
        share_name = clean_share_name(share_name)
        shares = parse_number(shares)
        avg_price = parse_number(avg_price)
        current_price = parse_number(current_price)

        investment_value = parse_number(investment_value)
        current_value = parse_number(current_value)

        if avg_price <= 0 and investment_value > 0 and shares > 0:
            avg_price = investment_value / shares

        if current_price <= 0 and current_value > 0 and shares > 0:
            current_price = current_value / shares

        if not is_valid_symbol(symbol):
            continue

        if shares <= 0:
            continue

        cleaned_rows.append({
            "symbol": symbol,
            "share_name": share_name,
            "shares": round(shares, 4),
            "avg_price": round(avg_price, 4),
            "current_price": round(current_price, 4),
            "investment_value": round(shares * avg_price, 2),
            "current_value": round(shares * current_price, 2),
            "source": "Structured File",
            "confidence": calculate_confidence(symbol, shares, avg_price, current_price),
            "remarks": "",
        })

    return cleaned_rows


def detect_columns(rows):
    """
    Detect portfolio columns from normalized rows.
    """

    all_headers = set()

    for row in rows:
        for key in row.keys():
            all_headers.add(key)

    return {
        "symbol": find_best_header(all_headers, SYMBOL_HEADERS),
        "share_name": find_best_header(all_headers, NAME_HEADERS),
        "shares": find_best_header(all_headers, SHARES_HEADERS),
        "avg_price": find_best_header(all_headers, AVG_PRICE_HEADERS),
        "current_price": find_best_header(all_headers, CURRENT_PRICE_HEADERS),
        "investment": find_best_header(all_headers, INVESTMENT_HEADERS),
        "current_value": find_best_header(all_headers, CURRENT_VALUE_HEADERS),
    }


def find_best_header(headers, candidates):
    """
    Find exact or partial header match.
    """

    for candidate in candidates:
        if candidate in headers:
            return candidate

    for header in headers:
        for candidate in candidates:
            if candidate in header or header in candidate:
                return header

    return None


def extract_holdings_from_text(text):
    """
    Extract holdings from PDF/image raw text using pattern matching.

    Supports lines like:
    ENGROH Engro Holdings Limited 25 170 186
    FFC Fauji Fertilizer Company Limited 50 390 432
    """

    if not text:
        return []

    rows = []
    lines = build_candidate_lines(text)

    for line in lines:

        parsed = parse_holding_line(line)

        if parsed:
            rows.append(parsed)

    return rows


def build_candidate_lines(text):
    """
    Build possible row lines from PDF text.

    Some PDF extractors return a clean line per row.
    Others split table cells line-by-line. This function preserves
    line parsing first and also creates joined chunks as fallback.
    """

    raw_lines = [
        str(line or "").strip()
        for line in str(text or "").splitlines()
        if str(line or "").strip()
    ]

    candidate_lines = list(raw_lines)

    # Fallback: combine nearby lines to catch split PDF rows.
    for i in range(len(raw_lines)):
        chunk = " ".join(raw_lines[i:i + 5])
        if chunk:
            candidate_lines.append(chunk)

    # Another fallback: each symbol onwards until enough numbers.
    symbols = []

    for index, line in enumerate(raw_lines):
        token = line.split()[0] if line.split() else ""
        token = normalize_symbol(token)

        if is_valid_symbol(token):
            symbols.append(index)

    for index in symbols:
        chunk = " ".join(raw_lines[index:index + 6])
        candidate_lines.append(chunk)

    return candidate_lines


def parse_holding_line(line):
    """
    Parse one possible portfolio holding line.
    """

    original_line = str(line or "").strip()

    if not original_line:
        return None

    line = original_line.replace(",", "")

    lowered = line.lower()

    ignore_terms = [
        "symbol share name shares avg price current price",
        "sample psx portfolio",
        "columns include",
        "portfolio import",
    ]

    if any(term in lowered for term in ignore_terms):
        return None

    tokens = line.split()

    if len(tokens) < 4:
        return None

    symbol = ""

    for token in tokens[:5]:
        possible = normalize_symbol(token)

        if is_valid_symbol(possible):
            symbol = possible
            break

    if not symbol:
        return None

    numbers = []

    for token in tokens:

        number = parse_number(token)

        if number > 0:
            numbers.append(number)

    if len(numbers) < 3:
        return None

    # In normal statement row after symbol/name:
    # last three useful numbers are shares, avg price, current price
    shares = numbers[-3]
    avg_price = numbers[-2]
    current_price = numbers[-1]

    if shares <= 0:
        return None

    share_name = extract_share_name_from_line(line, symbol)

    return {
        "symbol": symbol,
        "share_name": share_name,
        "shares": round(shares, 4),
        "avg_price": round(avg_price, 4),
        "current_price": round(current_price, 4),
        "investment_value": round(shares * avg_price, 2),
        "current_value": round(shares * current_price, 2),
        "source": "PDF/Image Text",
        "confidence": calculate_confidence(symbol, shares, avg_price, current_price) - 10,
        "remarks": "Please verify extracted PDF/image row before importing.",
    }


def extract_share_name_from_line(line, symbol):
    """
    Extract share/company name between symbol and numeric columns.
    """

    line = str(line or "").strip()
    symbol = normalize_symbol(symbol)

    if not line or not symbol:
        return ""

    parts = line.split()

    cleaned = []

    found_symbol = False

    for token in parts:

        if not found_symbol:

            if normalize_symbol(token) == symbol:
                found_symbol = True

            continue

        if parse_number(token) > 0:
            break

        cleaned.append(token)

    return clean_share_name(" ".join(cleaned))


def clean_preview_rows(rows):
    """
    Clean duplicate rows and normalize confidence.
    """

    final_rows = []
    seen = set()

    for row in rows or []:

        symbol = normalize_symbol(row.get("symbol", ""))
        share_name = clean_share_name(row.get("share_name", ""))
        shares = parse_number(row.get("shares", 0))
        avg_price = parse_number(row.get("avg_price", 0))
        current_price = parse_number(row.get("current_price", 0))

        if not is_valid_symbol(symbol):
            continue

        if shares <= 0:
            continue

        key = (
            symbol,
            round(shares, 4),
            round(avg_price, 4),
            round(current_price, 4),
        )

        if key in seen:
            continue

        seen.add(key)

        confidence = int(row.get("confidence", 70))

        if confidence < 0:
            confidence = 0

        if confidence > 100:
            confidence = 100

        final_rows.append({
            "symbol": symbol,
            "share_name": share_name,
            "shares": round(shares, 4),
            "avg_price": round(avg_price, 4),
            "current_price": round(current_price, 4),
            "investment_value": round(shares * avg_price, 2),
            "current_value": round(shares * current_price, 2),
            "source": row.get("source", ""),
            "confidence": confidence,
            "remarks": row.get("remarks", ""),
        })

    return final_rows


def calculate_confidence(symbol, shares, avg_price, current_price):
    """
    Return simple confidence score.
    """

    score = 0

    if is_valid_symbol(symbol):
        score += 35

    if shares > 0:
        score += 25

    if avg_price > 0:
        score += 20

    if current_price > 0:
        score += 20

    return score


def get_row_value(row, key):
    """
    Get row value safely.
    """

    if not key:
        return ""

    return row.get(key, "")


def normalize_header(value):
    """
    Normalize column header text.
    """

    text = str(value or "").strip().lower()
    text = text.replace("\n", " ")
    text = text.replace("_", " ")
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


def normalize_symbol(value):
    """
    Normalize PSX stock symbol.
    """

    text = str(value or "").strip().upper()
    text = text.replace(".", "")
    text = text.replace(",", "")
    text = text.replace(":", "")
    text = text.replace(";", "")
    text = text.replace("(", "")
    text = text.replace(")", "")
    text = text.replace("[", "")
    text = text.replace("]", "")

    return text


def clean_share_name(value):
    """
    Clean share/company name.
    """

    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)

    return text


def is_valid_symbol(symbol):
    """
    Basic PSX symbol validation.
    """

    symbol = normalize_symbol(symbol)

    if not symbol:
        return False

    if len(symbol) < 2 or len(symbol) > 12:
        return False

    if not re.match(r"^[A-Z0-9]+$", symbol):
        return False

    if symbol.lower() in COMMON_WORDS_TO_IGNORE:
        return False

    return True


def parse_number(value):
    """
    Parse number from text.
    """

    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if not text:
        return 0.0

    text = text.replace(",", "")
    text = text.replace("PKR", "")
    text = text.replace("Rs.", "")
    text = text.replace("Rs", "")
    text = text.replace("rs.", "")
    text = text.replace("rs", "")
    text = text.replace("%", "")
    text = text.strip()

    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]

    match = re.search(r"-?\d+(\.\d+)?", text)

    if not match:
        return 0.0

    try:
        return float(match.group(0))

    except Exception:
        return 0.0


def row_is_empty(row):
    """
    Check whether Excel row is empty.
    """

    for value in row:

        if value is not None and str(value).strip():
            return False

    return True


def get_import_summary(rows):
    """
    Return import preview summary.
    """

    total_rows = len(rows or [])
    total_investment = 0
    total_current = 0
    low_confidence = 0

    for row in rows or []:
        total_investment += parse_number(row.get("investment_value", 0))
        total_current += parse_number(row.get("current_value", 0))

        if int(row.get("confidence", 0)) < 70:
            low_confidence += 1

    return {
        "total_rows": total_rows,
        "total_investment": round(total_investment, 2),
        "total_current": round(total_current, 2),
        "estimated_profit": round(total_current - total_investment, 2),
        "low_confidence_rows": low_confidence,
    }
