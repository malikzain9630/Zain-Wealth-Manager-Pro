"""
Portfolio Allocation Sheet
"""

from styles import ExcelTheme
from allocation import get_allocation_analysis


def create_allocation_sheet(workbook):

    theme = ExcelTheme(workbook)

    ws = workbook.add_worksheet("Allocation")

    ws.set_column("A:D", 22)

    # ----------------------------
    # Header
    # ----------------------------

    ws.merge_range(
        "A1:D2",
        "PORTFOLIO ASSET ALLOCATION",
        theme.title
    )

    headers = [
        "Asset",
        "Current Value",
        "Allocation %",
        "Recommendation"
    ]

    for col, header in enumerate(headers):
        ws.write(3, col, header, theme.heading)

    row = 4

    for item in get_allocation_analysis():

        ws.write(row, 0, item["asset"], theme.normal)
        ws.write(row, 1, item["value"], theme.currency)
        ws.write(row, 2, f'{item["percent"]}%', theme.normal)
        ws.write(row, 3, item["status"], theme.normal)

        row += 1