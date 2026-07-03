"""
Zain Wealth Manager Pro
PSX Portfolio Module
"""

from styles import ExcelTheme
from data.portfolio import PORTFOLIO


def create_psx_sheet(workbook):

    theme = ExcelTheme(workbook)

    ws = workbook.add_worksheet("PSX Portfolio")

    ws.set_column("A:G", 18)

    # ===== Header =====
    ws.merge_range(
        "A1:G2",
        "Pakistan Stock Exchange Portfolio",
        theme.title
    )

    headers = [
        "Company",
        "Shares",
        "Avg Price",
        "Investment",
        "Current Value",
        "Profit/Loss",
        "Return %"
    ]

    for col, head in enumerate(headers):
        ws.write(3, col, head, theme.heading)

    row = 4

    total_investment = 0
    total_current = 0

    for stock in PORTFOLIO:

        company = stock["symbol"]
        shares = stock["shares"]
        avg = stock["avg"]

        invest = shares * avg
        current = shares * stock["current"]

        profit = current - invest
        percent = (profit / invest) * 100

        ws.write(row, 0, company, theme.normal)
        ws.write(row, 1, shares, theme.normal)
        ws.write(row, 2, avg, theme.currency)
        ws.write(row, 3, invest, theme.currency)
        ws.write(row, 4, current, theme.currency)

        if profit >= 0:
            ws.write(row, 5, profit, theme.green)
        else:
            ws.write(row, 5, profit, theme.red)

        ws.write_number(row, 6, percent / 100)

        total_investment += invest
        total_current += current

        row += 1

    total_profit = total_current - total_investment

    ws.write(row + 1, 2, "TOTAL", theme.heading)
    ws.write(row + 1, 3, total_investment, theme.currency)
    ws.write(row + 1, 4, total_current, theme.currency)

    if total_profit >= 0:
        ws.write(row + 1, 5, total_profit, theme.green)
    else:
        ws.write(row + 1, 5, total_profit, theme.red)