"""
Transaction History Sheet
"""

from styles import ExcelTheme
from utils import get_transactions


def create_transaction_sheet(workbook):

    theme = ExcelTheme(workbook)

    ws = workbook.add_worksheet("Transactions")

    ws.set_column("A:G", 18)

    # ----------------------------
    # Header
    # ----------------------------

    ws.merge_range(
        "A1:G2",
        "TRANSACTION HISTORY",
        theme.title
    )

    headers = [
        "Date",
        "Asset",
        "Symbol",
        "Type",
        "Quantity",
        "Price",
        "Amount"
    ]

    for col, header in enumerate(headers):
        ws.write(3, col, header, theme.heading)

    transactions = get_transactions()

    row = 4

    for t in transactions:

        amount = t["quantity"] * t["price"]

        ws.write(row, 0, t["date"], theme.normal)
        ws.write(row, 1, t["asset"], theme.normal)
        ws.write(row, 2, t["symbol"], theme.normal)
        ws.write(row, 3, t["type"], theme.normal)
        ws.write(row, 4, t["quantity"], theme.normal)
        ws.write(row, 5, t["price"], theme.currency)
        ws.write(row, 6, amount, theme.currency)

        row += 1

    # Total Investment
    ws.write(row + 1, 5, "TOTAL", theme.heading)
    ws.write_formula(
        row + 1,
        6,
        f"=SUM(G5:G{row})",
        theme.currency
    )