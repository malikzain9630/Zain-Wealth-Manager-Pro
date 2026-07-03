"""
Net Worth History Sheet
"""

from styles import ExcelTheme
from utils import get_networth_history


def create_networth_history_sheet(workbook):

    theme = ExcelTheme(workbook)

    ws = workbook.add_worksheet("Net Worth History")

    ws.set_column("A:A", 20)
    ws.set_column("B:B", 22)

    # ----------------------------
    # Header
    # ----------------------------

    ws.merge_range(
        "A1:B2",
        "NET WORTH HISTORY",
        theme.title
    )

    headers = [
        "Month",
        "Net Worth"
    ]

    for col, header in enumerate(headers):
        ws.write(3, col, header, theme.heading)

    history = get_networth_history()

    row = 4

    for item in history:

        ws.write(row, 0, item["month"], theme.normal)
        ws.write(row, 1, item["net_worth"], theme.currency)

        row += 1

    # ----------------------------
    # Total Records
    # ----------------------------

    ws.write(row + 1, 0, "Total Records", theme.heading)
    ws.write(row + 1, 1, len(history), theme.normal)