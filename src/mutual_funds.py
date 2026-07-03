"""
Zain Wealth Manager Pro
Mutual Funds Module
"""

from styles import ExcelTheme


def create_mutual_funds_sheet(workbook):

    theme = ExcelTheme(workbook)

    ws = workbook.add_worksheet("Mutual Funds")

    ws.set_column("A:E", 22)

    # ===== Header =====
    ws.merge_range(
        "A1:E2",
        "Meezan Mutual Funds Portfolio",
        theme.title
    )

    headers = [
        "Fund",
        "Units",
        "Current Value",
        "Allocation %",
        "Status"
    ]

    for col, head in enumerate(headers):
        ws.write(3, col, head, theme.heading)

    funds = [

        ["KMIF Growth",104.1872,19006],
        ["MIF Growth",103.2935,17416],

    ]

    total = sum(fund[2] for fund in funds)

    row = 4

    for fund in funds:

        name = fund[0]
        units = fund[1]
        value = fund[2]

        allocation = value / total

        ws.write(row,0,name,theme.normal)
        ws.write(row,1,units,theme.normal)
        ws.write(row,2,value,theme.currency)
        ws.write(row,3,allocation)

        if allocation >= 0.50:
            ws.write(row,4,"Core Holding",theme.green)
        else:
            ws.write(row,4,"Growth",theme.normal)

        row += 1

    ws.write(row+1,1,"TOTAL",theme.heading)
    ws.write(row+1,2,total,theme.currency)