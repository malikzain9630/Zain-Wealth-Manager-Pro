"""
Import Service
Handles CSV portfolio import.
"""

import csv
from pathlib import Path

from services.portfolio_service import (
    get_all_holdings,
    add_new_holding,
    update_existing_holding
)


def normalize_column_name(name):
    """
    Normalize CSV column names for flexible matching.
    """

    return (
        name.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def get_value(row, possible_keys):
    """
    Get value from CSV row using multiple possible column names.
    """

    normalized_row = {}

    for key, value in row.items():
        normalized_row[normalize_column_name(key)] = value

    for key in possible_keys:
        normalized_key = normalize_column_name(key)

        if normalized_key in normalized_row:
            return normalized_row[normalized_key]

    return None


def get_existing_symbols():
    """
    Return existing portfolio symbols as a set.
    """

    holdings = get_all_holdings()

    symbols = set()

    for item in holdings:
        symbols.add(str(item["symbol"]).strip().upper())

    return symbols


def import_portfolio_csv(csv_file_path):
    """
    Import portfolio holdings from a CSV file.

    Required CSV fields:
        symbol
        shares
        avg_price
        current_price

    Returns:
        dict with import summary.
    """

    csv_path = Path(csv_file_path)

    if not csv_path.exists():
        raise FileNotFoundError("CSV file not found.")

    if csv_path.suffix.lower() != ".csv":
        raise ValueError("Invalid file type. Please select a CSV file.")

    added_count = 0
    updated_count = 0
    skipped_count = 0

    errors = []

    existing_symbols = get_existing_symbols()

    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:

        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("CSV file is empty or has no headers.")

        for row_number, row in enumerate(reader, start=2):

            try:
                symbol = get_value(
                    row,
                    ["symbol", "stock", "ticker", "share_symbol"]
                )

                shares = get_value(
                    row,
                    ["shares", "quantity", "qty", "units"]
                )

                avg_price = get_value(
                    row,
                    ["avg_price", "average_price", "avg", "buy_price", "purchase_price"]
                )

                current_price = get_value(
                    row,
                    ["current_price", "market_price", "price", "current", "ltp"]
                )

                if not symbol or shares is None or avg_price is None or current_price is None:
                    skipped_count += 1
                    errors.append(
                        f"Row {row_number}: Missing required data."
                    )
                    continue

                symbol = str(symbol).strip().upper()
                shares = float(str(shares).replace(",", "").strip())
                avg_price = float(str(avg_price).replace(",", "").strip())
                current_price = float(str(current_price).replace(",", "").strip())

                if symbol in existing_symbols:

                    update_existing_holding(
                        symbol,
                        shares,
                        avg_price,
                        current_price
                    )

                    updated_count += 1

                else:

                    add_new_holding(
                        symbol,
                        shares,
                        avg_price,
                        current_price
                    )

                    existing_symbols.add(symbol)
                    added_count += 1

            except Exception as e:

                skipped_count += 1

                errors.append(
                    f"Row {row_number}: {str(e)}"
                )

    return {
        "added": added_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "errors": errors
    }