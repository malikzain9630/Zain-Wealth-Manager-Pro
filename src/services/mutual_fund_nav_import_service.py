"""
Mutual Fund NAV Import Service
Handles CSV based NAV updates for mutual funds.
"""

import csv
from pathlib import Path

from services.mutual_fund_service import update_mutual_fund_nav


def normalize_column_name(name):
    """
    Normalize CSV column names.
    """

    return (
        str(name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def get_value(row, possible_keys):
    """
    Get value from CSV row using flexible column names.
    """

    normalized_row = {}

    for key, value in row.items():
        normalized_row[normalize_column_name(key)] = value

    for key in possible_keys:

        normalized_key = normalize_column_name(key)

        if normalized_key in normalized_row:
            return normalized_row[normalized_key]

    return None


def import_mutual_fund_nav_csv(csv_file_path):
    """
    Import mutual fund current NAV from CSV file.

    Supported columns:
        fund, current_nav

    Also supports:
        fund_name, name, scheme, nav, price, current
    """

    csv_path = Path(csv_file_path)

    if not csv_path.exists():
        raise FileNotFoundError("CSV file not found.")

    if csv_path.suffix.lower() != ".csv":
        raise ValueError("Invalid file type. Please select a CSV file.")

    updated = 0
    skipped = 0
    errors = []

    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:

        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("CSV file is empty or has no headers.")

        for row_number, row in enumerate(reader, start=2):

            try:
                fund = get_value(
                    row,
                    ["fund", "fund_name", "name", "scheme", "scheme_name"]
                )

                current_nav = get_value(
                    row,
                    ["current_nav", "nav", "price", "current", "current_price"]
                )

                if not fund or current_nav is None:
                    skipped += 1
                    errors.append(
                        f"Row {row_number}: Missing fund name or current NAV."
                    )
                    continue

                fund = str(fund).strip()
                current_nav = float(
                    str(current_nav).replace(",", "").strip()
                )

                update_mutual_fund_nav(
                    fund,
                    current_nav
                )

                updated += 1

            except Exception as e:
                skipped += 1
                errors.append(f"Row {row_number}: {str(e)}")

    return {
        "updated": updated,
        "skipped": skipped,
        "errors": errors
    }