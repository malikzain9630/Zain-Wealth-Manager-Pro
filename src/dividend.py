"""
Dividend Tracker
"""

from styles import ExcelTheme
from utils import get_dividend_summary
from data.dividends import DIVIDENDS


def create_dividend_sheet(workbook):

    theme = ExcelTheme(workbook)

    ws = workbook.add_worksheet("Dividend Tracker")

    ws.set_column("A:D", 22)

    # Header
    ws.merge_range(
        "A1:D2",
        "DIVIDEND TRACKER",
        theme.title
    )

    total = get_dividend_summary()

    ws.write("A4", "Estimated Annual Dividend", theme.heading)
    ws.write("B4", total, theme.currency)

    # Table Header
    headers = [
        "Company",
        "Shares",
        "Dividend / Share",
        "Annual Dividend"
    ]

    for col, head in enumerate(headers):
        ws.write(6, col, head, theme.heading)

    row = 7

    for item in DIVIDENDS:

        annual = item["shares"] * item["dividend_per_share"]

        ws.write(row, 0, item["symbol"], theme.normal)
        ws.write(row, 1, item["shares"], theme.normal)
        ws.write(row, 2, item["dividend_per_share"], theme.currency)
        ws.write(row, 3, annual, theme.currency)

        row += 1

    ws.write(row + 1, 2, "TOTAL", theme.heading)
    ws.write(row + 1, 3, total, theme.currency)