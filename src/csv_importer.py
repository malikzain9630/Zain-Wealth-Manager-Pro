"""
CSV Portfolio Importer
"""

import csv

from backup import create_backup
from logger import info, error

from portfolio_db import (
    add_holding,
    delete_holding,
    get_portfolio
)

REQUIRED_COLUMNS = [
    "Symbol",
    "Shares",
    "Average Price",
    "Current Price"
]


def import_portfolio(csv_file):

    try:

        with open(csv_file, newline="", encoding="utf-8-sig") as file:

            reader = csv.DictReader(file)

            # ----------------------------
            # Validate Columns
            # ----------------------------

            if reader.fieldnames is None:
                raise Exception("CSV file is empty.")

            missing = []

            for col in REQUIRED_COLUMNS:
                if col not in reader.fieldnames:
                    missing.append(col)

            if missing:
                raise Exception(
                    f"Missing Columns: {', '.join(missing)}"
                )

            # ----------------------------
            # Backup Database
            # ----------------------------

            create_backup()

            # ----------------------------
            # Clear Existing Portfolio
            # ----------------------------

            for item in get_portfolio():
                delete_holding(item["symbol"])

            # ----------------------------
            # Import Data
            # ----------------------------

            count = 0

            for row in reader:

                add_holding(
                    row["Symbol"],
                    float(row["Shares"]),
                    float(row["Average Price"]),
                    float(row["Current Price"])
                )

                count += 1

            message = f"Successfully Imported {count} Holdings."

            print(message)
            info(message)

    except FileNotFoundError:

        message = "CSV file not found."

        print("ERROR:", message)

        error(message)

    except ValueError:

        message = "Invalid numeric value inside CSV."

        print("ERROR:", message)

        error(message)

    except Exception as e:

        message = str(e)

        print("ERROR:", message)

        error(message)