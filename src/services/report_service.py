"""
Report Service
Handles Excel & PDF generation.
"""

from datetime import datetime
from pathlib import Path

import xlsxwriter

from allocation_sheet import create_allocation_sheet
from dashboard import create_dashboard
from database import initialize_database
from dividend import create_dividend_sheet
from mutual_funds import create_mutual_funds_sheet
from networth_history import create_networth_history_sheet
from pension import create_pension_sheet
from pf import create_pf_sheet
from psx import create_psx_sheet
from report_generator import generate_pdf_report
from transactions import create_transaction_sheet

from services.portfolio_service import get_all_holdings
from services.mutual_fund_service import get_all_mutual_funds


def create_reports():
    """
    Create Excel and PDF reports.

    Existing report sheets are preserved.
    New database-based sheets are added:
        1. PSX Portfolio
        2. Mutual Funds Portfolio
        3. Overall Wealth Summary
    """

    output = Path(__file__).resolve().parent.parent.parent / "output"
    output.mkdir(exist_ok=True)

    excel_file = output / "Zain_Wealth_Manager_Pro_v1.xlsx"
    legacy_pdf_file = output / "report.pdf"
    combined_pdf_file = output / "Zain_Wealth_Manager_Combined_Report.pdf"

    initialize_database()

    psx_holdings = get_all_holdings()
    mutual_funds = get_all_mutual_funds()

    workbook = xlsxwriter.Workbook(str(excel_file))

    # Existing report sheets
    create_dashboard(workbook)
    create_psx_sheet(workbook)
    create_mutual_funds_sheet(workbook)
    create_pf_sheet(workbook)
    create_pension_sheet(workbook)
    create_dividend_sheet(workbook)
    create_transaction_sheet(workbook)
    create_allocation_sheet(workbook)
    create_networth_history_sheet(workbook)

    # New database-based report sheets
    formats = create_formats(workbook)

    create_psx_portfolio_sheet(
        workbook,
        psx_holdings,
        formats
    )

    create_mutual_funds_portfolio_sheet(
        workbook,
        mutual_funds,
        formats
    )

    create_overall_wealth_sheet(
        workbook,
        psx_holdings,
        mutual_funds,
        formats
    )

    workbook.close()

    # Keep existing PDF report generation safe.
    try:
        generate_pdf_report(str(legacy_pdf_file))
    except Exception:
        pass

    # Create new combined PDF report with PSX + Mutual Funds + Overall Summary.
    create_combined_pdf_report(
        combined_pdf_file,
        psx_holdings,
        mutual_funds
    )

    return excel_file, combined_pdf_file


def create_formats(workbook):
    """
    Create Excel cell formats.
    """

    return {
        "title": workbook.add_format({
            "bold": True,
            "font_size": 16,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#1F4E78",
            "font_color": "#FFFFFF",
            "border": 1
        }),
        "section": workbook.add_format({
            "bold": True,
            "font_size": 13,
            "align": "left",
            "bg_color": "#D9EAF7",
            "border": 1
        }),
        "header": workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#4472C4",
            "font_color": "#FFFFFF",
            "border": 1
        }),
        "text": workbook.add_format({
            "align": "center",
            "border": 1
        }),
        "number": workbook.add_format({
            "align": "center",
            "border": 1,
            "num_format": "#,##0.0000"
        }),
        "currency": workbook.add_format({
            "align": "center",
            "border": 1,
            "num_format": '#,##0.00'
        }),
        "percent": workbook.add_format({
            "align": "center",
            "border": 1,
            "num_format": "0.00%"
        }),
        "profit": workbook.add_format({
            "align": "center",
            "border": 1,
            "font_color": "green",
            "num_format": '#,##0.00'
        }),
        "loss": workbook.add_format({
            "align": "center",
            "border": 1,
            "font_color": "red",
            "num_format": '#,##0.00'
        }),
        "profit_percent": workbook.add_format({
            "align": "center",
            "border": 1,
            "font_color": "green",
            "num_format": "0.00%"
        }),
        "loss_percent": workbook.add_format({
            "align": "center",
            "border": 1,
            "font_color": "red",
            "num_format": "0.00%"
        }),
        "total_label": workbook.add_format({
            "bold": True,
            "align": "right",
            "bg_color": "#E2F0D9",
            "border": 1
        }),
        "total_value": workbook.add_format({
            "bold": True,
            "align": "center",
            "bg_color": "#E2F0D9",
            "border": 1,
            "num_format": '#,##0.00'
        }),
    }


def safe_add_worksheet(workbook, preferred_name):
    """
    Add worksheet safely without duplicate sheet name error.
    Excel sheet name limit is 31 characters.
    """

    existing_names = []

    try:
        for sheet in workbook.worksheets():
            existing_names.append(sheet.get_name().lower())
    except Exception:
        existing_names = []

    base_name = preferred_name[:31]
    candidate = base_name
    counter = 2

    while candidate.lower() in existing_names:
        suffix = f" {counter}"
        candidate = f"{base_name[:31 - len(suffix)]}{suffix}"
        counter += 1

    return workbook.add_worksheet(candidate)


def create_psx_portfolio_sheet(workbook, holdings, formats):
    """
    Create database-based PSX portfolio sheet.
    """

    sheet = safe_add_worksheet(workbook, "PSX Portfolio")

    sheet.merge_range("A1:I1", "PSX Portfolio", formats["title"])
    sheet.write("A2", "Generated On", formats["section"])
    sheet.write("B2", datetime.now().strftime("%d-%m-%Y %I:%M %p"), formats["text"])

    headers = [
        "Symbol",
        "Shares",
        "Average Price",
        "Current Price",
        "Investment Value",
        "Current Value",
        "Profit / Loss",
        "Profit %",
        "Allocation %",
    ]

    for col, header in enumerate(headers):
        sheet.write(3, col, header, formats["header"])

    total_current_value = calculate_psx_total_current_value(holdings)

    row = 4

    for item in holdings:

        symbol = str(item["symbol"]).upper()
        shares = safe_float(item["shares"])
        avg_price = safe_float(item["avg_price"])
        current_price = safe_float(item["current_price"])

        investment_value = shares * avg_price
        current_value = shares * current_price
        profit_loss = current_value - investment_value

        if investment_value > 0:
            profit_percent = profit_loss / investment_value
        else:
            profit_percent = 0

        if total_current_value > 0:
            allocation_percent = current_value / total_current_value
        else:
            allocation_percent = 0

        profit_format = formats["profit"] if profit_loss >= 0 else formats["loss"]
        percent_format = (
            formats["profit_percent"]
            if profit_percent >= 0
            else formats["loss_percent"]
        )

        sheet.write(row, 0, symbol, formats["text"])
        sheet.write_number(row, 1, shares, formats["number"])
        sheet.write_number(row, 2, avg_price, formats["currency"])
        sheet.write_number(row, 3, current_price, formats["currency"])
        sheet.write_number(row, 4, investment_value, formats["currency"])
        sheet.write_number(row, 5, current_value, formats["currency"])
        sheet.write_number(row, 6, profit_loss, profit_format)
        sheet.write_number(row, 7, profit_percent, percent_format)
        sheet.write_number(row, 8, allocation_percent, formats["percent"])

        row += 1

    total_row = row + 1

    total_investment = calculate_psx_total_investment(holdings)
    total_profit = total_current_value - total_investment

    if total_investment > 0:
        total_profit_percent = total_profit / total_investment
    else:
        total_profit_percent = 0

    total_profit_format = formats["profit"] if total_profit >= 0 else formats["loss"]
    total_percent_format = (
        formats["profit_percent"]
        if total_profit_percent >= 0
        else formats["loss_percent"]
    )

    sheet.write(total_row, 3, "Total", formats["total_label"])
    sheet.write_number(total_row, 4, total_investment, formats["total_value"])
    sheet.write_number(total_row, 5, total_current_value, formats["total_value"])
    sheet.write_number(total_row, 6, total_profit, total_profit_format)
    sheet.write_number(total_row, 7, total_profit_percent, total_percent_format)

    sheet.set_column("A:A", 18)
    sheet.set_column("B:D", 15)
    sheet.set_column("E:G", 20)
    sheet.set_column("H:I", 15)
    sheet.freeze_panes(4, 0)


def create_mutual_funds_portfolio_sheet(workbook, mutual_funds, formats):
    """
    Create database-based mutual funds portfolio sheet.
    """

    sheet = safe_add_worksheet(workbook, "Mutual Funds Portfolio")

    sheet.merge_range("A1:H1", "Mutual Funds Portfolio", formats["title"])
    sheet.write("A2", "Generated On", formats["section"])
    sheet.write("B2", datetime.now().strftime("%d-%m-%Y %I:%M %p"), formats["text"])

    headers = [
        "Fund",
        "Units",
        "Average NAV",
        "Current NAV",
        "Investment Value",
        "Current Value",
        "Profit / Loss",
        "Profit %",
    ]

    for col, header in enumerate(headers):
        sheet.write(3, col, header, formats["header"])

    row = 4

    for item in mutual_funds:

        fund = str(item["fund"])
        units = safe_float(item["units"])
        avg_nav = safe_float(item["avg_nav"])
        current_nav = safe_float(item["current_nav"])
        investment_value = safe_float(item["investment_value"])
        current_value = safe_float(item["current_value"])
        profit_loss = safe_float(item["profit_loss"])

        if investment_value > 0:
            profit_percent = profit_loss / investment_value
        else:
            profit_percent = 0

        profit_format = formats["profit"] if profit_loss >= 0 else formats["loss"]
        percent_format = (
            formats["profit_percent"]
            if profit_percent >= 0
            else formats["loss_percent"]
        )

        sheet.write(row, 0, fund, formats["text"])
        sheet.write_number(row, 1, units, formats["number"])
        sheet.write_number(row, 2, avg_nav, formats["currency"])
        sheet.write_number(row, 3, current_nav, formats["currency"])
        sheet.write_number(row, 4, investment_value, formats["currency"])
        sheet.write_number(row, 5, current_value, formats["currency"])
        sheet.write_number(row, 6, profit_loss, profit_format)
        sheet.write_number(row, 7, profit_percent, percent_format)

        row += 1

    total_row = row + 1

    total_investment = calculate_mf_total_investment(mutual_funds)
    total_current = calculate_mf_total_current_value(mutual_funds)
    total_profit = total_current - total_investment

    if total_investment > 0:
        total_profit_percent = total_profit / total_investment
    else:
        total_profit_percent = 0

    total_profit_format = formats["profit"] if total_profit >= 0 else formats["loss"]
    total_percent_format = (
        formats["profit_percent"]
        if total_profit_percent >= 0
        else formats["loss_percent"]
    )

    sheet.write(total_row, 3, "Total", formats["total_label"])
    sheet.write_number(total_row, 4, total_investment, formats["total_value"])
    sheet.write_number(total_row, 5, total_current, formats["total_value"])
    sheet.write_number(total_row, 6, total_profit, total_profit_format)
    sheet.write_number(total_row, 7, total_profit_percent, total_percent_format)

    sheet.set_column("A:A", 28)
    sheet.set_column("B:D", 16)
    sheet.set_column("E:G", 20)
    sheet.set_column("H:H", 15)
    sheet.freeze_panes(4, 0)


def create_overall_wealth_sheet(workbook, holdings, mutual_funds, formats):
    """
    Create overall wealth summary sheet.
    """

    sheet = safe_add_worksheet(workbook, "Overall Wealth Summary")

    sheet.merge_range("A1:F1", "Overall Wealth Summary", formats["title"])
    sheet.write("A2", "Generated On", formats["section"])
    sheet.write("B2", datetime.now().strftime("%d-%m-%Y %I:%M %p"), formats["text"])

    headers = [
        "Category",
        "Investment Value",
        "Current Value",
        "Profit / Loss",
        "Profit %",
        "Records",
    ]

    for col, header in enumerate(headers):
        sheet.write(4, col, header, formats["header"])

    psx_investment = calculate_psx_total_investment(holdings)
    psx_current = calculate_psx_total_current_value(holdings)
    psx_profit = psx_current - psx_investment
    psx_profit_percent = calculate_profit_percent(psx_investment, psx_profit)

    mf_investment = calculate_mf_total_investment(mutual_funds)
    mf_current = calculate_mf_total_current_value(mutual_funds)
    mf_profit = mf_current - mf_investment
    mf_profit_percent = calculate_profit_percent(mf_investment, mf_profit)

    total_investment = psx_investment + mf_investment
    total_current = psx_current + mf_current
    total_profit = total_current - total_investment
    total_profit_percent = calculate_profit_percent(total_investment, total_profit)

    rows = [
        [
            "PSX Portfolio",
            psx_investment,
            psx_current,
            psx_profit,
            psx_profit_percent,
            len(holdings),
        ],
        [
            "Mutual Funds",
            mf_investment,
            mf_current,
            mf_profit,
            mf_profit_percent,
            len(mutual_funds),
        ],
        [
            "Combined Total",
            total_investment,
            total_current,
            total_profit,
            total_profit_percent,
            len(holdings) + len(mutual_funds),
        ],
    ]

    row_number = 5

    for row_data in rows:

        category = row_data[0]
        investment = row_data[1]
        current = row_data[2]
        profit = row_data[3]
        profit_percent = row_data[4]
        records = row_data[5]

        profit_format = formats["profit"] if profit >= 0 else formats["loss"]
        percent_format = (
            formats["profit_percent"]
            if profit_percent >= 0
            else formats["loss_percent"]
        )

        sheet.write(row_number, 0, category, formats["text"])
        sheet.write_number(row_number, 1, investment, formats["currency"])
        sheet.write_number(row_number, 2, current, formats["currency"])
        sheet.write_number(row_number, 3, profit, profit_format)
        sheet.write_number(row_number, 4, profit_percent, percent_format)
        sheet.write_number(row_number, 5, records, formats["text"])

        row_number += 1

    sheet.set_column("A:A", 22)
    sheet.set_column("B:D", 20)
    sheet.set_column("E:E", 15)
    sheet.set_column("F:F", 12)


def create_combined_pdf_report(pdf_file, holdings, mutual_funds):
    """
    Create PDF report with PSX, Mutual Funds and Overall Wealth Summary.
    """

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
        )

    except Exception:
        return

    doc = SimpleDocTemplate(
        str(pdf_file),
        pagesize=landscape(A4),
        rightMargin=24,
        leftMargin=24,
        topMargin=24,
        bottomMargin=24,
    )

    styles = getSampleStyleSheet()
    story = []

    title = Paragraph("Zain Wealth Manager Pro - Combined Report", styles["Title"])
    generated_on = Paragraph(
        f"Generated On: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}",
        styles["Normal"]
    )

    story.append(title)
    story.append(generated_on)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Overall Wealth Summary", styles["Heading2"]))
    story.append(create_pdf_table(get_overall_summary_rows(holdings, mutual_funds)))
    story.append(Spacer(1, 16))

    story.append(Paragraph("PSX Portfolio", styles["Heading2"]))
    story.append(create_pdf_table(get_psx_pdf_rows(holdings)))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Mutual Funds Portfolio", styles["Heading2"]))
    story.append(create_pdf_table(get_mutual_fund_pdf_rows(mutual_funds)))

    doc.build(story)


def create_pdf_table(data):
    """
    Create styled PDF table.
    """

    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white,
            colors.HexColor("#F2F2F2")
        ]),
    ]))

    return table


def get_overall_summary_rows(holdings, mutual_funds):
    """
    Return PDF rows for overall summary.
    """

    psx_investment = calculate_psx_total_investment(holdings)
    psx_current = calculate_psx_total_current_value(holdings)
    psx_profit = psx_current - psx_investment
    psx_profit_percent = calculate_profit_percent(psx_investment, psx_profit)

    mf_investment = calculate_mf_total_investment(mutual_funds)
    mf_current = calculate_mf_total_current_value(mutual_funds)
    mf_profit = mf_current - mf_investment
    mf_profit_percent = calculate_profit_percent(mf_investment, mf_profit)

    total_investment = psx_investment + mf_investment
    total_current = psx_current + mf_current
    total_profit = total_current - total_investment
    total_profit_percent = calculate_profit_percent(total_investment, total_profit)

    return [
        [
            "Category",
            "Investment",
            "Current Value",
            "Profit / Loss",
            "Profit %",
            "Records",
        ],
        [
            "PSX Portfolio",
            format_money(psx_investment),
            format_money(psx_current),
            format_money(psx_profit),
            format_percent(psx_profit_percent),
            str(len(holdings)),
        ],
        [
            "Mutual Funds",
            format_money(mf_investment),
            format_money(mf_current),
            format_money(mf_profit),
            format_percent(mf_profit_percent),
            str(len(mutual_funds)),
        ],
        [
            "Combined Total",
            format_money(total_investment),
            format_money(total_current),
            format_money(total_profit),
            format_percent(total_profit_percent),
            str(len(holdings) + len(mutual_funds)),
        ],
    ]


def get_psx_pdf_rows(holdings):
    """
    Return PDF rows for PSX portfolio.
    """

    rows = [[
        "Symbol",
        "Shares",
        "Avg Price",
        "Current Price",
        "Investment",
        "Current Value",
        "P/L",
        "P/L %",
    ]]

    for item in holdings:

        shares = safe_float(item["shares"])
        avg_price = safe_float(item["avg_price"])
        current_price = safe_float(item["current_price"])

        investment_value = shares * avg_price
        current_value = shares * current_price
        profit_loss = current_value - investment_value
        profit_percent = calculate_profit_percent(
            investment_value,
            profit_loss
        )

        rows.append([
            str(item["symbol"]).upper(),
            format_quantity(shares),
            format_money(avg_price),
            format_money(current_price),
            format_money(investment_value),
            format_money(current_value),
            format_money(profit_loss),
            format_percent(profit_percent),
        ])

    return rows


def get_mutual_fund_pdf_rows(mutual_funds):
    """
    Return PDF rows for mutual fund portfolio.
    """

    rows = [[
        "Fund",
        "Units",
        "Avg NAV",
        "Current NAV",
        "Investment",
        "Current Value",
        "P/L",
        "P/L %",
    ]]

    for item in mutual_funds:

        investment_value = safe_float(item["investment_value"])
        current_value = safe_float(item["current_value"])
        profit_loss = safe_float(item["profit_loss"])
        profit_percent = calculate_profit_percent(
            investment_value,
            profit_loss
        )

        rows.append([
            str(item["fund"]),
            format_quantity(item["units"]),
            format_money(item["avg_nav"]),
            format_money(item["current_nav"]),
            format_money(investment_value),
            format_money(current_value),
            format_money(profit_loss),
            format_percent(profit_percent),
        ])

    return rows


def calculate_psx_total_investment(holdings):
    """
    Calculate PSX total investment.
    """

    total = 0

    for item in holdings:
        total += safe_float(item["shares"]) * safe_float(item["avg_price"])

    return total


def calculate_psx_total_current_value(holdings):
    """
    Calculate PSX total current value.
    """

    total = 0

    for item in holdings:
        total += safe_float(item["shares"]) * safe_float(item["current_price"])

    return total


def calculate_mf_total_investment(mutual_funds):
    """
    Calculate mutual funds total investment.
    """

    total = 0

    for item in mutual_funds:
        total += safe_float(item["investment_value"])

    return total


def calculate_mf_total_current_value(mutual_funds):
    """
    Calculate mutual funds total current value.
    """

    total = 0

    for item in mutual_funds:
        total += safe_float(item["current_value"])

    return total


def calculate_profit_percent(investment_value, profit_loss):
    """
    Calculate profit percentage.
    """

    investment_value = safe_float(investment_value)
    profit_loss = safe_float(profit_loss)

    if investment_value <= 0:
        return 0

    return profit_loss / investment_value


def safe_float(value):
    """
    Convert value to float safely.
    """

    try:
        return float(value)

    except (ValueError, TypeError):
        return 0


def format_money(value):
    """
    Format money for PDF.
    """

    return f"PKR {safe_float(value):,.2f}"


def format_percent(value):
    """
    Format percentage for PDF.
    """

    return f"{safe_float(value) * 100:.2f}%"


def format_quantity(value):
    """
    Format quantity for PDF.
    """

    return f"{safe_float(value):,.4f}"
