"""
Price Service
Handles current price updates for portfolio holdings.
"""

import csv
from pathlib import Path

from services.portfolio_service import (
    get_all_holdings,
    update_existing_holding
)


def get_holding_by_symbol(symbol):
    """
    Find a holding by symbol.
    """

    symbol = str(symbol).strip().upper()

    holdings = get_all_holdings()

    for item in holdings:

        if str(item["symbol"]).strip().upper() == symbol:
            return item

    return None


def update_single_price(symbol, current_price):
    """
    Update current price for a single holding.
    Existing shares and average price remain unchanged.
    """

    symbol = str(symbol).strip().upper()

    if not symbol:
        raise ValueError("Symbol cannot be empty.")

    try:
        current_price = float(current_price)

    except ValueError:
        raise ValueError("Current price must be numeric.")

    if current_price <= 0:
        raise ValueError("Current price must be greater than zero.")

    holding = get_holding_by_symbol(symbol)

    if not holding:
        raise ValueError(f"Holding not found: {symbol}")

    update_existing_holding(
        symbol,
        float(holding["shares"]),
        float(holding["avg_price"]),
        current_price
    )

    return {
        "symbol": symbol,
        "current_price": current_price
    }


def update_multiple_prices(price_updates):
    """
    Update current prices for multiple holdings.

    price_updates format:
    [
        {"symbol": "FFC", "current_price": 420},
        {"symbol": "MEBL", "current_price": 260}
    ]
    """

    updated = 0
    skipped = 0
    errors = []

    for index, item in enumerate(price_updates, start=1):

        try:
            symbol = item.get("symbol")
            current_price = item.get("current_price")

            update_single_price(symbol, current_price)

            updated += 1

        except Exception as e:
            skipped += 1
            errors.append(f"Item {index}: {str(e)}")

    return {
        "updated": updated,
        "skipped": skipped,
        "errors": errors
    }


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


def import_price_csv(csv_file_path):
    """
    Import current prices from CSV file.

    Supported CSV columns:
        symbol, current_price

    Also supports:
        ticker, stock, ltp, price, market_price, current
    """

    csv_path = Path(csv_file_path)

    if not csv_path.exists():
        raise FileNotFoundError("CSV file not found.")

    if csv_path.suffix.lower() != ".csv":
        raise ValueError("Invalid file type. Please select a CSV file.")

    updates = []

    errors = []

    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as file:

        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("CSV file is empty or has no headers.")

        for row_number, row in enumerate(reader, start=2):

            try:
                symbol = get_value(
                    row,
                    ["symbol", "ticker", "stock", "share_symbol"]
                )

                current_price = get_value(
                    row,
                    ["current_price", "price", "ltp", "market_price", "current"]
                )

                if not symbol or current_price is None:
                    errors.append(
                        f"Row {row_number}: Missing symbol or current price."
                    )
                    continue

                symbol = str(symbol).strip().upper()
                current_price = float(str(current_price).replace(",", "").strip())

                updates.append({
                    "symbol": symbol,
                    "current_price": current_price
                })

            except Exception as e:
                errors.append(f"Row {row_number}: {str(e)}")

    result = update_multiple_prices(updates)

    result["errors"] = errors + result["errors"]

    return result