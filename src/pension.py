"""
Meezan Pension Sheet
Version 1.0
"""

from styles import ExcelTheme
from data.pension import PENSION_DATA
from utils import pension_projection


def create_pension_sheet(workbook):

    theme = ExcelTheme(workbook)

    ws = workbook.add_worksheet("Meezan Pension")

    # -----------------------------
    # Column Width
    # -----------------------------
    ws.set_column("A:A", 30)
    ws.set_column("B:B", 18)

    # -----------------------------
    # Title
    # -----------------------------
    ws.merge_range(
        "A1:B2",
        "MEEZAN PENSION FUND",
        theme.title
    )

    current = PENSION_DATA["current_value"]
    monthly = PENSION_DATA["monthly_contribution"]
    annual = monthly * 12

    summary = [

        ("Current Value", current),

        ("Monthly Contribution", monthly),

        ("Annual Contribution", annual),

        ("Expected Return", f'{PENSION_DATA["annual_return"]}%'),

        ("Retirement Age", PENSION_DATA["retirement_age"])

    ]

    row = 4

    for title, value in summary:

        ws.write(row, 0, title, theme.heading)

        if isinstance(value, (int, float)):
            ws.write(row, 1, value, theme.currency)
        else:
            ws.write(row, 1, value, theme.normal)

        row += 2

    # -----------------------------
    # Projection
    # -----------------------------

    ws.write("D4", "5 Year Projection", theme.heading)

    ws.write("D5", "Year", theme.heading)
    ws.write("E5", "Estimated Value", theme.heading)

    projection = pension_projection()

    r = 5

    for year, amount in projection:

        ws.write(r, 3, year, theme.normal)
        ws.write(r, 4, amount, theme.currency)

        r += 1