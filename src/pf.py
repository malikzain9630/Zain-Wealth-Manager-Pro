"""
Provident Fund Sheet
Version 3.1
"""

from styles import ExcelTheme
from data.pf import PF_DATA
from utils import pf_projection


def create_pf_sheet(workbook):

    theme = ExcelTheme(workbook)

    ws = workbook.add_worksheet("Provident Fund")

    # -----------------------------
    # Column Width
    # -----------------------------

    ws.set_column("A:A", 28)
    ws.set_column("B:B", 18)
    ws.set_column("D:E", 18)

    # -----------------------------
    # Header
    # -----------------------------

    ws.merge_range(
        "A1:E2",
        "PROVIDENT FUND DASHBOARD",
        theme.title
    )

    current = PF_DATA["current_balance"]
    employee = PF_DATA["employee_monthly"]
    employer = PF_DATA["employer_monthly"]

    monthly = employee + employer
    annual = monthly * 12

    # -----------------------------
    # Summary
    # -----------------------------

    summary = [

        ("Current Balance", current),

        ("Employee Monthly", employee),

        ("Employer Monthly", employer),

        ("Monthly Total", monthly),

        ("Annual Contribution", annual)

    ]

    row = 4

    for title, value in summary:

        ws.write(row, 0, title, theme.heading)
        ws.write(row, 1, value, theme.currency)

        row += 2

    # -----------------------------
    # Monthly Contribution History
    # -----------------------------

    ws.write("D4", "Contribution History", theme.heading)

    headers = [
        "Month",
        "Contribution"
    ]

    for col, head in enumerate(headers, start=3):
        ws.write(4, col, head, theme.heading)

    months = [
        "Jan","Feb","Mar","Apr","May","Jun",
        "Jul","Aug","Sep","Oct","Nov","Dec"
    ]

    r = 5

    for month in months:

        ws.write(r, 3, month, theme.normal)
        ws.write(r, 4, monthly, theme.currency)

        r += 1

    # -----------------------------
    # Projection
    # -----------------------------

    ws.write("A18", "5 Year Projection", theme.heading)

    ws.write("A19", "Year", theme.heading)
    ws.write("B19", "Estimated Balance", theme.heading)

    projection = pf_projection()

    row = 20

    for year, amount in projection:

        ws.write(row, 0, year, theme.normal)
        ws.write(row, 1, amount, theme.currency)

        row += 1