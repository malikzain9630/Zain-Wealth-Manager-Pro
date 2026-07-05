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
from services.dividend_service import (
    get_all_dividends,
    get_income_summary,
    get_income_summary_by_symbol,
    get_income_summary_by_month,
    get_income_summary_by_year,
)
from services.dividend_chart_service import (
    get_stock_wise_dividend_data,
    get_monthly_dividend_data,
    get_yearly_dividend_data,
    get_tax_vs_net_data,
)
from services.dividend_yield_service import (
    get_dividend_yield_by_stock,
    get_passive_income_forecast,
    get_monthly_income_trend,
    get_yearly_income_trend,
    get_top_dividend_stocks,
)


def create_reports(
    generate_excel=True,
    generate_pdf=True,
    output_folder=None
):
    """
    Create Excel and/or PDF reports.

    Existing report sheets are preserved.
    New database-based sheets are added:
        1. PSX Portfolio
        2. Mutual Funds Portfolio
        3. Overall Wealth Summary
        4. Dividend Income
        5. Dividend Summary
        6. Dividend Charts
        7. Dividend Forecast

    Returns:
        {
            "excel_file": Path or None,
            "pdf_file": Path or None,
            "legacy_pdf_file": Path or None,
        }
    """

    if not generate_excel and not generate_pdf:
        raise ValueError("Please select at least one report type: Excel or PDF.")

    if output_folder:
        output = Path(output_folder)
    else:
        output = Path(__file__).resolve().parent.parent.parent / "output"

    output.mkdir(parents=True, exist_ok=True)

    excel_file = output / "Zain_Wealth_Manager_Pro_v1.xlsx"
    legacy_pdf_file = output / "report.pdf"
    combined_pdf_file = output / "Zain_Wealth_Manager_Combined_Report.pdf"

    initialize_database()

    psx_holdings = get_all_holdings()
    mutual_funds = get_all_mutual_funds()
    dividends = get_all_dividends()

    result = {
        "excel_file": None,
        "pdf_file": None,
        "legacy_pdf_file": None,
    }

    if generate_excel:

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

        create_charts_sheet(
            workbook,
            psx_holdings,
            mutual_funds,
            formats
        )

        create_dividend_income_sheet(
            workbook,
            dividends,
            formats
        )

        create_dividend_summary_sheet(
            workbook,
            formats
        )

        create_dividend_charts_sheet(
            workbook,
            formats
        )

        create_dividend_forecast_sheet(
            workbook,
            formats
        )

        workbook.close()

        result["excel_file"] = excel_file

    if generate_pdf:

        # Keep existing PDF report generation safe.
        try:
            generate_pdf_report(str(legacy_pdf_file))
            result["legacy_pdf_file"] = legacy_pdf_file
        except Exception:
            result["legacy_pdf_file"] = None

        # Create new combined PDF report with PSX + Mutual Funds + Dividends.
        create_combined_pdf_report(
            combined_pdf_file,
            psx_holdings,
            mutual_funds,
            dividends
        )

        result["pdf_file"] = combined_pdf_file

    return result


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



def create_charts_sheet(workbook, holdings, mutual_funds, formats):
    """
    Create Excel charts sheet:
        1. PSX Allocation
        2. Mutual Funds Allocation
        3. Overall Wealth Allocation
        4. Profit / Loss Comparison
    """

    sheet = safe_add_worksheet(workbook, "Charts")

    sheet.merge_range("A1:J1", "Charts & Visual Analytics", formats["title"])
    sheet.write("A2", "Generated On", formats["section"])
    sheet.write("B2", datetime.now().strftime("%d-%m-%Y %I:%M %p"), formats["text"])

    psx_rows = get_psx_allocation_rows(holdings)
    mutual_fund_rows = get_mutual_fund_allocation_rows(mutual_funds)
    overall_rows = get_overall_allocation_rows(holdings, mutual_funds)
    profit_loss_rows = get_profit_loss_rows(holdings, mutual_funds)

    write_chart_source_table(
        sheet,
        "A4",
        "PSX Allocation Data",
        ["Symbol", "Current Value"],
        psx_rows,
        formats
    )

    write_chart_source_table(
        sheet,
        "D4",
        "Mutual Funds Allocation Data",
        ["Fund", "Current Value"],
        mutual_fund_rows,
        formats
    )

    write_chart_source_table(
        sheet,
        "A22",
        "Overall Wealth Data",
        ["Category", "Current Value"],
        overall_rows,
        formats
    )

    write_chart_source_table(
        sheet,
        "D22",
        "Profit / Loss Data",
        ["Category", "Profit / Loss"],
        profit_loss_rows,
        formats
    )

    create_excel_pie_chart(
        workbook,
        sheet,
        "PSX Allocation",
        "A6:A{}".format(5 + len(psx_rows)),
        "B6:B{}".format(5 + len(psx_rows)),
        "G4"
    )

    create_excel_pie_chart(
        workbook,
        sheet,
        "Mutual Funds Allocation",
        "D6:D{}".format(5 + len(mutual_fund_rows)),
        "E6:E{}".format(5 + len(mutual_fund_rows)),
        "G20"
    )

    create_excel_pie_chart(
        workbook,
        sheet,
        "Overall Wealth Allocation",
        "A24:A{}".format(23 + len(overall_rows)),
        "B24:B{}".format(23 + len(overall_rows)),
        "G36"
    )

    create_excel_bar_chart(
        workbook,
        sheet,
        "Profit / Loss Comparison",
        "D24:D{}".format(23 + len(profit_loss_rows)),
        "E24:E{}".format(23 + len(profit_loss_rows)),
        "G52"
    )

    sheet.set_column("A:A", 20)
    sheet.set_column("B:B", 18)
    sheet.set_column("D:D", 28)
    sheet.set_column("E:E", 18)
    sheet.set_column("G:J", 18)


def write_chart_source_table(sheet, start_cell, title, headers, rows, formats):
    """
    Write source data for Excel charts.
    """

    start_row, start_col = cell_to_row_col(start_cell)

    sheet.write(start_row, start_col, title, formats["section"])

    for index, header in enumerate(headers):
        sheet.write(start_row + 1, start_col + index, header, formats["header"])

    if not rows:
        sheet.write(start_row + 2, start_col, "No Data", formats["text"])
        sheet.write_number(start_row + 2, start_col + 1, 0, formats["currency"])
        return

    for row_index, row_data in enumerate(rows, start=start_row + 2):
        sheet.write(row_index, start_col, row_data[0], formats["text"])
        sheet.write_number(row_index, start_col + 1, row_data[1], formats["currency"])


def cell_to_row_col(cell):
    """
    Convert simple Excel cell reference to zero-based row/column.
    Supports cells like A1, D22.
    """

    letters = ""
    numbers = ""

    for character in cell:

        if character.isalpha():
            letters += character.upper()
        elif character.isdigit():
            numbers += character

    column = 0

    for character in letters:
        column = column * 26 + (ord(character) - ord("A") + 1)

    return int(numbers) - 1, column - 1


def create_excel_pie_chart(workbook, sheet, title, categories_range, values_range, insert_cell):
    """
    Add pie chart to Excel sheet.
    """

    sheet_name = get_excel_sheet_name(sheet)
    chart = workbook.add_chart({"type": "pie"})

    chart.add_series({
        "name": title,
        "categories": f"='{sheet_name}'!{categories_range}",
        "values": f"='{sheet_name}'!{values_range}",
        "data_labels": {
            "percentage": True,
            "category": True,
            "leader_lines": True
        },
    })

    chart.set_title({"name": title})
    chart.set_style(10)
    chart.set_size({
        "width": 460,
        "height": 300
    })

    sheet.insert_chart(insert_cell, chart)


def create_excel_bar_chart(
    workbook,
    sheet,
    title,
    categories_range,
    values_range,
    insert_cell,
    y_axis_name="Profit / Loss"
):
    """
    Add bar chart to Excel sheet.
    """

    sheet_name = get_excel_sheet_name(sheet)
    chart = workbook.add_chart({"type": "column"})

    chart.add_series({
        "name": title,
        "categories": f"='{sheet_name}'!{categories_range}",
        "values": f"='{sheet_name}'!{values_range}",
        "data_labels": {
            "value": True
        },
    })

    chart.set_title({"name": title})
    chart.set_x_axis({"name": "Category"})
    chart.set_y_axis({"name": y_axis_name})
    chart.set_style(11)
    chart.set_size({
        "width": 460,
        "height": 300
    })

    sheet.insert_chart(insert_cell, chart)


def get_excel_sheet_name(sheet):
    """
    Return safe worksheet name for formulas.
    """

    try:
        return sheet.get_name().replace("'", "''")

    except Exception:
        return "Charts"


def get_psx_allocation_rows(holdings):
    """
    Return PSX allocation rows for charts.
    """

    rows = []

    for item in holdings:

        symbol = str(item["symbol"]).upper()
        current_value = safe_float(item["shares"]) * safe_float(item["current_price"])

        if current_value > 0:
            rows.append([symbol, current_value])

    return rows


def get_mutual_fund_allocation_rows(mutual_funds):
    """
    Return mutual fund allocation rows for charts.
    """

    rows = []

    for item in mutual_funds:

        fund = str(item["fund"])
        current_value = safe_float(item["current_value"])

        if current_value > 0:
            rows.append([fund, current_value])

    return rows


def get_overall_allocation_rows(holdings, mutual_funds):
    """
    Return overall wealth allocation rows.
    """

    psx_current = calculate_psx_total_current_value(holdings)
    mf_current = calculate_mf_total_current_value(mutual_funds)

    rows = []

    if psx_current > 0:
        rows.append(["PSX Portfolio", psx_current])

    if mf_current > 0:
        rows.append(["Mutual Funds", mf_current])

    return rows


def get_profit_loss_rows(holdings, mutual_funds):
    """
    Return profit/loss rows for charts.
    """

    psx_investment = calculate_psx_total_investment(holdings)
    psx_current = calculate_psx_total_current_value(holdings)
    psx_profit = psx_current - psx_investment

    mf_investment = calculate_mf_total_investment(mutual_funds)
    mf_current = calculate_mf_total_current_value(mutual_funds)
    mf_profit = mf_current - mf_investment

    rows = []

    if psx_investment > 0 or psx_current > 0:
        rows.append(["PSX Portfolio", psx_profit])

    if mf_investment > 0 or mf_current > 0:
        rows.append(["Mutual Funds", mf_profit])

    return rows



def create_dividend_income_sheet(workbook, dividends, formats):
    """
    Create database-based dividend income records sheet.
    """

    sheet = safe_add_worksheet(workbook, "Dividend Income")

    sheet.merge_range("A1:I1", "Dividend Income Records", formats["title"])
    sheet.write("A2", "Generated On", formats["section"])
    sheet.write("B2", datetime.now().strftime("%d-%m-%Y %I:%M %p"), formats["text"])

    headers = [
        "ID",
        "Symbol",
        "Shares",
        "Dividend / Share",
        "Gross Amount",
        "Tax Amount",
        "Net Amount",
        "Payment Date",
        "Remarks",
    ]

    for col, header in enumerate(headers):
        sheet.write(3, col, header, formats["header"])

    row = 4

    total_gross = 0
    total_tax = 0
    total_net = 0

    for item in dividends:

        record_id = safe_get(item, "id", "")
        symbol = str(safe_get(item, "symbol", "")).upper()
        shares = safe_float(safe_get(item, "shares", 0))
        dividend_per_share = safe_float(safe_get(item, "dividend_per_share", 0))
        gross_amount = safe_float(safe_get(item, "gross_amount", 0))
        tax_amount = safe_float(safe_get(item, "tax_amount", 0))
        net_amount = safe_float(safe_get(item, "net_amount", 0))
        payment_date = str(safe_get(item, "payment_date", ""))
        remarks = str(safe_get(item, "remarks", ""))

        total_gross += gross_amount
        total_tax += tax_amount
        total_net += net_amount

        sheet.write(row, 0, record_id, formats["text"])
        sheet.write(row, 1, symbol, formats["text"])
        sheet.write_number(row, 2, shares, formats["number"])
        sheet.write_number(row, 3, dividend_per_share, formats["currency"])
        sheet.write_number(row, 4, gross_amount, formats["currency"])
        sheet.write_number(row, 5, tax_amount, formats["currency"])
        sheet.write_number(row, 6, net_amount, formats["currency"])
        sheet.write(row, 7, payment_date, formats["text"])
        sheet.write(row, 8, remarks, formats["text"])

        row += 1

    total_row = row + 1

    sheet.write(total_row, 3, "Total", formats["total_label"])
    sheet.write_number(total_row, 4, total_gross, formats["total_value"])
    sheet.write_number(total_row, 5, total_tax, formats["total_value"])
    sheet.write_number(total_row, 6, total_net, formats["total_value"])

    sheet.set_column("A:A", 10)
    sheet.set_column("B:B", 14)
    sheet.set_column("C:D", 16)
    sheet.set_column("E:G", 18)
    sheet.set_column("H:H", 16)
    sheet.set_column("I:I", 35)
    sheet.freeze_panes(4, 0)


def create_dividend_summary_sheet(workbook, formats):
    """
    Create dividend summary sheet:
        1. Overall Summary
        2. Stock-wise Summary
        3. Monthly Summary
        4. Yearly Summary
    """

    sheet = safe_add_worksheet(workbook, "Dividend Summary")

    sheet.merge_range("A1:F1", "Dividend Income Summary", formats["title"])
    sheet.write("A2", "Generated On", formats["section"])
    sheet.write("B2", datetime.now().strftime("%d-%m-%Y %I:%M %p"), formats["text"])

    overall = get_income_summary()
    symbol_rows = get_income_summary_by_symbol()
    month_rows = get_income_summary_by_month()
    year_rows = get_income_summary_by_year()

    sheet.write("A4", "Overall Dividend Summary", formats["section"])

    overall_headers = [
        "Gross Amount",
        "Tax Amount",
        "Net Amount",
        "Total Records",
    ]

    for col, header in enumerate(overall_headers):
        sheet.write(5, col, header, formats["header"])

    sheet.write_number(6, 0, safe_float(overall["gross_amount"]), formats["currency"])
    sheet.write_number(6, 1, safe_float(overall["tax_amount"]), formats["currency"])
    sheet.write_number(6, 2, safe_float(overall["net_amount"]), formats["currency"])
    sheet.write_number(6, 3, int(overall["total_records"]), formats["text"])

    write_dividend_summary_table(
        sheet,
        "A10",
        "Stock-wise Dividend Summary",
        "Symbol",
        symbol_rows,
        "symbol",
        formats
    )

    write_dividend_summary_table(
        sheet,
        "A25",
        "Monthly Dividend Summary",
        "Month",
        month_rows,
        "month",
        formats
    )

    write_dividend_summary_table(
        sheet,
        "A40",
        "Yearly Dividend Summary",
        "Year",
        year_rows,
        "year",
        formats
    )

    sheet.set_column("A:A", 18)
    sheet.set_column("B:E", 18)
    sheet.set_column("F:F", 16)


def write_dividend_summary_table(
    sheet,
    start_cell,
    title,
    first_header,
    rows,
    first_key,
    formats
):
    """
    Write a dividend summary section.
    """

    start_row, start_col = cell_to_row_col(start_cell)

    sheet.write(start_row, start_col, title, formats["section"])

    headers = [
        first_header,
        "Records",
        "Gross Amount",
        "Tax Amount",
        "Net Amount",
    ]

    for index, header in enumerate(headers):
        sheet.write(start_row + 1, start_col + index, header, formats["header"])

    if not rows:
        sheet.write(start_row + 2, start_col, "No Data", formats["text"])
        sheet.write_number(start_row + 2, start_col + 1, 0, formats["text"])
        sheet.write_number(start_row + 2, start_col + 2, 0, formats["currency"])
        sheet.write_number(start_row + 2, start_col + 3, 0, formats["currency"])
        sheet.write_number(start_row + 2, start_col + 4, 0, formats["currency"])
        return

    row_number = start_row + 2

    for item in rows:

        first_value = str(safe_get(item, first_key, ""))
        records = int(safe_float(safe_get(item, "records", 0)))
        gross_amount = safe_float(safe_get(item, "gross_amount", 0))
        tax_amount = safe_float(safe_get(item, "tax_amount", 0))
        net_amount = safe_float(safe_get(item, "net_amount", 0))

        sheet.write(row_number, start_col, first_value, formats["text"])
        sheet.write_number(row_number, start_col + 1, records, formats["text"])
        sheet.write_number(row_number, start_col + 2, gross_amount, formats["currency"])
        sheet.write_number(row_number, start_col + 3, tax_amount, formats["currency"])
        sheet.write_number(row_number, start_col + 4, net_amount, formats["currency"])

        row_number += 1



def create_dividend_forecast_sheet(workbook, formats):
    """
    Create dividend yield and passive income forecast sheet.
    """

    sheet = safe_add_worksheet(workbook, "Dividend Forecast")

    sheet.merge_range("A1:K1", "Dividend Yield & Passive Income Forecast", formats["title"])
    sheet.write("A2", "Generated On", formats["section"])
    sheet.write("B2", datetime.now().strftime("%d-%m-%Y %I:%M %p"), formats["text"])

    forecast = get_passive_income_forecast()
    yield_rows = get_dividend_yield_by_stock()
    monthly_rows = get_monthly_income_trend()
    yearly_rows = get_yearly_income_trend()
    top_rows = get_top_dividend_stocks(10)

    sheet.write("A4", "Passive Income Forecast Summary", formats["section"])

    summary_headers = [
        "Current Year",
        "Current Month",
        "Total Net Received",
        "Current Year Net",
        "Monthly Forecast",
        "Yearly Forecast",
        "Total Records",
    ]

    for col, header in enumerate(summary_headers):
        sheet.write(5, col, header, formats["header"])

    sheet.write_number(6, 0, int(forecast["current_year"]), formats["text"])
    sheet.write_number(6, 1, int(forecast["current_month"]), formats["text"])
    sheet.write_number(6, 2, safe_float(forecast["total_net_received"]), formats["currency"])
    sheet.write_number(6, 3, safe_float(forecast["current_year_net"]), formats["currency"])
    sheet.write_number(6, 4, safe_float(forecast["monthly_forecast"]), formats["currency"])
    sheet.write_number(6, 5, safe_float(forecast["yearly_forecast"]), formats["currency"])
    sheet.write_number(6, 6, int(forecast["total_records"]), formats["text"])

    sheet.write("A9", "Stock-wise Dividend Yield", formats["section"])

    yield_headers = [
        "Symbol",
        "Shares",
        "Investment Value",
        "Current Value",
        "Gross Dividend",
        "Tax Amount",
        "Net Dividend",
        "Records",
        "Yield on Cost %",
        "Current Yield %",
    ]

    for col, header in enumerate(yield_headers):
        sheet.write(10, col, header, formats["header"])

    row = 11

    if not yield_rows:
        sheet.write(row, 0, "No Data", formats["text"])
        row += 1
    else:
        for item in yield_rows:
            sheet.write(row, 0, str(item["symbol"]).upper(), formats["text"])
            sheet.write_number(row, 1, safe_float(item["shares"]), formats["number"])
            sheet.write_number(row, 2, safe_float(item["investment_value"]), formats["currency"])
            sheet.write_number(row, 3, safe_float(item["current_value"]), formats["currency"])
            sheet.write_number(row, 4, safe_float(item["gross_dividend"]), formats["currency"])
            sheet.write_number(row, 5, safe_float(item["tax_amount"]), formats["currency"])
            sheet.write_number(row, 6, safe_float(item["net_dividend"]), formats["currency"])
            sheet.write_number(row, 7, int(item["dividend_records"]), formats["text"])
            sheet.write_number(row, 8, safe_float(item["yield_on_cost"]) / 100, formats["percent"])
            sheet.write_number(row, 9, safe_float(item["current_yield"]) / 100, formats["percent"])
            row += 1

    next_section_row = row + 2

    sheet.write(next_section_row, 0, "Top Dividend Stocks", formats["section"])

    top_headers = [
        "Rank",
        "Symbol",
        "Net Dividend",
        "Yield on Cost %",
        "Current Yield %",
        "Records",
    ]

    for col, header in enumerate(top_headers):
        sheet.write(next_section_row + 1, col, header, formats["header"])

    top_start_row = next_section_row + 2

    if not top_rows:
        sheet.write(top_start_row, 0, "No Data", formats["text"])
        top_rows_for_chart = [["No Data", 0]]
    else:
        top_rows_for_chart = []

        for index, item in enumerate(top_rows):
            write_row = top_start_row + index
            rank = index + 1

            sheet.write_number(write_row, 0, rank, formats["text"])
            sheet.write(write_row, 1, str(item["symbol"]).upper(), formats["text"])
            sheet.write_number(write_row, 2, safe_float(item["net_dividend"]), formats["currency"])
            sheet.write_number(write_row, 3, safe_float(item["yield_on_cost"]) / 100, formats["percent"])
            sheet.write_number(write_row, 4, safe_float(item["current_yield"]) / 100, formats["percent"])
            sheet.write_number(write_row, 5, int(item["dividend_records"]), formats["text"])

            top_rows_for_chart.append([
                str(item["symbol"]).upper(),
                safe_float(item["net_dividend"])
            ])

    trend_start_row = top_start_row + max(len(top_rows), 1) + 3

    sheet.write(trend_start_row, 0, "Monthly Income Trend", formats["section"])

    monthly_headers = [
        "Month",
        "Records",
        "Gross Amount",
        "Tax Amount",
        "Net Amount",
    ]

    for col, header in enumerate(monthly_headers):
        sheet.write(trend_start_row + 1, col, header, formats["header"])

    monthly_data_start = trend_start_row + 2

    if not monthly_rows:
        sheet.write(monthly_data_start, 0, "No Data", formats["text"])
        sheet.write_number(monthly_data_start, 4, 0, formats["currency"])
        monthly_rows_for_chart = [["No Data", 0]]
    else:
        monthly_rows_for_chart = []

        for index, item in enumerate(monthly_rows):
            write_row = monthly_data_start + index

            sheet.write(write_row, 0, str(item["month"]), formats["text"])
            sheet.write_number(write_row, 1, int(item["records"]), formats["text"])
            sheet.write_number(write_row, 2, safe_float(item["gross_amount"]), formats["currency"])
            sheet.write_number(write_row, 3, safe_float(item["tax_amount"]), formats["currency"])
            sheet.write_number(write_row, 4, safe_float(item["net_amount"]), formats["currency"])

            monthly_rows_for_chart.append([
                str(item["month"]),
                safe_float(item["net_amount"])
            ])

    yearly_start_col = 6

    sheet.write(trend_start_row, yearly_start_col, "Yearly Income Trend", formats["section"])

    yearly_headers = [
        "Year",
        "Records",
        "Gross Amount",
        "Tax Amount",
        "Net Amount",
    ]

    for col, header in enumerate(yearly_headers):
        sheet.write(trend_start_row + 1, yearly_start_col + col, header, formats["header"])

    yearly_data_start = trend_start_row + 2

    if not yearly_rows:
        sheet.write(yearly_data_start, yearly_start_col, "No Data", formats["text"])
        sheet.write_number(yearly_data_start, yearly_start_col + 4, 0, formats["currency"])
    else:
        for index, item in enumerate(yearly_rows):
            write_row = yearly_data_start + index

            sheet.write(write_row, yearly_start_col, str(item["year"]), formats["text"])
            sheet.write_number(write_row, yearly_start_col + 1, int(item["records"]), formats["text"])
            sheet.write_number(write_row, yearly_start_col + 2, safe_float(item["gross_amount"]), formats["currency"])
            sheet.write_number(write_row, yearly_start_col + 3, safe_float(item["tax_amount"]), formats["currency"])
            sheet.write_number(write_row, yearly_start_col + 4, safe_float(item["net_amount"]), formats["currency"])

    chart_start_row = trend_start_row + max(len(monthly_rows), len(yearly_rows), 1) + 4

    # Chart source tables
    write_chart_source_table(
        sheet,
        f"A{chart_start_row + 1}",
        "Top Dividend Stocks Chart Data",
        ["Symbol", "Net Dividend"],
        top_rows_for_chart,
        formats
    )

    write_chart_source_table(
        sheet,
        f"D{chart_start_row + 1}",
        "Monthly Forecast Chart Data",
        ["Month", "Net Amount"],
        monthly_rows_for_chart,
        formats
    )

    top_chart_rows_count = len(top_rows_for_chart)
    monthly_chart_rows_count = len(monthly_rows_for_chart)

    create_excel_bar_chart(
        workbook,
        sheet,
        "Top Dividend Stocks",
        f"A{chart_start_row + 3}:A{chart_start_row + 2 + top_chart_rows_count}",
        f"B{chart_start_row + 3}:B{chart_start_row + 2 + top_chart_rows_count}",
        f"G{chart_start_row + 1}",
        "Net Dividend"
    )

    create_excel_bar_chart(
        workbook,
        sheet,
        "Monthly Dividend Income Trend",
        f"D{chart_start_row + 3}:D{chart_start_row + 2 + monthly_chart_rows_count}",
        f"E{chart_start_row + 3}:E{chart_start_row + 2 + monthly_chart_rows_count}",
        f"G{chart_start_row + 18}",
        "Net Dividend"
    )

    sheet.set_column("A:A", 18)
    sheet.set_column("B:B", 14)
    sheet.set_column("C:G", 18)
    sheet.set_column("H:J", 18)
    sheet.set_column("K:K", 18)
    sheet.freeze_panes(10, 0)


def create_dividend_charts_sheet(workbook, formats):
    """
    Create dividend charts sheet:
        1. Stock-wise Dividend Income
        2. Monthly Dividend Income
        3. Yearly Dividend Income
        4. Tax vs Net Received
    """

    sheet = safe_add_worksheet(workbook, "Dividend Charts")

    sheet.merge_range("A1:J1", "Dividend Income Charts", formats["title"])
    sheet.write("A2", "Generated On", formats["section"])
    sheet.write("B2", datetime.now().strftime("%d-%m-%Y %I:%M %p"), formats["text"])

    stock_rows = chart_dict_to_rows(get_stock_wise_dividend_data())
    monthly_rows = chart_dict_to_rows(get_monthly_dividend_data())
    yearly_rows = chart_dict_to_rows(get_yearly_dividend_data())
    tax_net_rows = chart_dict_to_rows(get_tax_vs_net_data())

    write_chart_source_table(
        sheet,
        "A4",
        "Stock-wise Dividend Data",
        ["Symbol", "Net Amount"],
        stock_rows,
        formats
    )

    write_chart_source_table(
        sheet,
        "D4",
        "Monthly Dividend Data",
        ["Month", "Net Amount"],
        monthly_rows,
        formats
    )

    write_chart_source_table(
        sheet,
        "A22",
        "Yearly Dividend Data",
        ["Year", "Net Amount"],
        yearly_rows,
        formats
    )

    write_chart_source_table(
        sheet,
        "D22",
        "Tax vs Net Data",
        ["Category", "Amount"],
        tax_net_rows,
        formats
    )

    create_excel_pie_chart(
        workbook,
        sheet,
        "Stock-wise Dividend Income",
        "A6:A{}".format(5 + len(stock_rows)),
        "B6:B{}".format(5 + len(stock_rows)),
        "G4"
    )

    create_excel_bar_chart(
        workbook,
        sheet,
        "Monthly Dividend Income",
        "D6:D{}".format(5 + len(monthly_rows)),
        "E6:E{}".format(5 + len(monthly_rows)),
        "G20",
        "Net Dividend Income"
    )

    create_excel_bar_chart(
        workbook,
        sheet,
        "Yearly Dividend Income",
        "A24:A{}".format(23 + len(yearly_rows)),
        "B24:B{}".format(23 + len(yearly_rows)),
        "G36",
        "Net Dividend Income"
    )

    create_excel_pie_chart(
        workbook,
        sheet,
        "Tax vs Net Received",
        "D24:D{}".format(23 + len(tax_net_rows)),
        "E24:E{}".format(23 + len(tax_net_rows)),
        "G52"
    )

    sheet.set_column("A:A", 20)
    sheet.set_column("B:B", 18)
    sheet.set_column("D:D", 24)
    sheet.set_column("E:E", 18)
    sheet.set_column("G:J", 18)


def chart_dict_to_rows(data):
    """
    Convert chart service dictionary to row list.
    """

    labels = data.get("labels", [])
    values = data.get("values", [])

    rows = []

    for label, value in zip(labels, values):

        value = safe_float(value)

        if value > 0:
            rows.append([str(label), value])

    if not rows:
        rows.append(["No Data", 0])

    return rows


def create_pdf_chart_drawings(holdings, mutual_funds):
    """
    Create simple PDF chart drawings.
    If ReportLab graphics are not available, return an empty list.
    """

    try:
        from reportlab.graphics.shapes import Drawing, String
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.lib import colors

    except Exception:
        return []

    drawings = []

    psx_rows = get_psx_allocation_rows(holdings)
    mutual_fund_rows = get_mutual_fund_allocation_rows(mutual_funds)
    overall_rows = get_overall_allocation_rows(holdings, mutual_funds)
    profit_loss_rows = get_profit_loss_rows(holdings, mutual_funds)

    psx_chart = create_pdf_pie_chart(
        "PSX Allocation",
        psx_rows,
        Drawing,
        String,
        Pie,
        colors
    )

    if psx_chart:
        drawings.append(psx_chart)

    mf_chart = create_pdf_pie_chart(
        "Mutual Funds Allocation",
        mutual_fund_rows,
        Drawing,
        String,
        Pie,
        colors
    )

    if mf_chart:
        drawings.append(mf_chart)

    overall_chart = create_pdf_pie_chart(
        "Overall Wealth Allocation",
        overall_rows,
        Drawing,
        String,
        Pie,
        colors
    )

    if overall_chart:
        drawings.append(overall_chart)

    profit_chart = create_pdf_bar_chart(
        "Profit / Loss Comparison",
        profit_loss_rows,
        Drawing,
        String,
        VerticalBarChart,
        colors
    )

    if profit_chart:
        drawings.append(profit_chart)

    return drawings


def create_pdf_pie_chart(title, rows, Drawing, String, Pie, colors):
    """
    Create PDF pie chart drawing.
    """

    rows = rows[:8]

    if not rows:
        return None

    labels = [str(row[0]) for row in rows]
    values = [safe_float(row[1]) for row in rows]

    if sum(values) <= 0:
        return None

    drawing = Drawing(720, 230)

    drawing.add(String(
        20,
        205,
        title,
        fontName="Helvetica-Bold",
        fontSize=12
    ))

    pie = Pie()
    pie.x = 35
    pie.y = 35
    pie.width = 150
    pie.height = 150
    pie.data = values
    pie.labels = [
        f"{label} ({value / sum(values) * 100:.1f}%)"
        for label, value in zip(labels, values)
    ]

    for index in range(len(values)):
        pie.slices[index].fillColor = get_pdf_color(index, colors)

    drawing.add(pie)

    legend_x = 230
    legend_y = 170

    for index, label in enumerate(labels):

        value = values[index]
        percent = value / sum(values) * 100

        drawing.add(String(
            legend_x,
            legend_y - index * 18,
            f"{label}: {format_money(value)} ({percent:.1f}%)",
            fontSize=8
        ))

    return drawing


def create_pdf_bar_chart(title, rows, Drawing, String, VerticalBarChart, colors, y_axis_name="Profit / Loss"):
    """
    Create PDF bar chart drawing.
    """

    rows = rows[:6]

    if not rows:
        return None

    labels = [str(row[0]) for row in rows]
    values = [safe_float(row[1]) for row in rows]

    if not values:
        return None

    max_value = max(values)
    min_value = min(values)

    if max_value == 0 and min_value == 0:
        return None

    drawing = Drawing(720, 260)

    drawing.add(String(
        20,
        235,
        title,
        fontName="Helvetica-Bold",
        fontSize=12
    ))

    drawing.add(String(
        50,
        215,
        y_axis_name,
        fontSize=8
    ))

    chart = VerticalBarChart()
    chart.x = 50
    chart.y = 55
    chart.height = 150
    chart.width = 560
    chart.data = [values]
    chart.categoryAxis.categoryNames = labels

    value_min = min(0, min_value)
    value_max = max(0, max_value)

    if value_min == value_max:
        value_max = value_min + 1

    chart.valueAxis.valueMin = value_min
    chart.valueAxis.valueMax = value_max
    chart.valueAxis.valueStep = (value_max - value_min) / 4

    chart.bars[0].fillColor = colors.HexColor("#4472C4")
    chart.categoryAxis.labels.angle = 0
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.labels.fontSize = 7

    drawing.add(chart)

    return drawing


def get_pdf_color(index, colors):
    """
    Return PDF chart color.
    """

    palette = [
        colors.HexColor("#4472C4"),
        colors.HexColor("#ED7D31"),
        colors.HexColor("#A5A5A5"),
        colors.HexColor("#FFC000"),
        colors.HexColor("#5B9BD5"),
        colors.HexColor("#70AD47"),
        colors.HexColor("#264478"),
        colors.HexColor("#9E480E"),
    ]

    return palette[index % len(palette)]

def create_combined_pdf_report(pdf_file, holdings, mutual_funds, dividends):
    """
    Create PDF report with PSX, Mutual Funds, Dividends and Overall Wealth Summary.
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

    story.append(Paragraph("Dividend Income Summary", styles["Heading2"]))
    story.append(create_pdf_table(get_dividend_summary_pdf_rows()))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Passive Income Forecast", styles["Heading2"]))
    story.append(create_pdf_table(get_passive_income_forecast_pdf_rows()))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Dividend Yield by Stock", styles["Heading2"]))
    story.append(create_pdf_table(get_dividend_yield_pdf_rows()))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Top Dividend Stocks", styles["Heading2"]))
    story.append(create_pdf_table(get_top_dividend_stocks_pdf_rows()))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Dividend Records", styles["Heading2"]))
    story.append(create_pdf_table(get_dividend_records_pdf_rows(dividends)))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Charts & Visual Analytics", styles["Heading2"]))

    chart_drawings = create_pdf_chart_drawings(holdings, mutual_funds)

    for chart in chart_drawings:
        story.append(chart)
        story.append(Spacer(1, 12))

    story.append(Paragraph("Dividend Charts", styles["Heading2"]))

    dividend_chart_drawings = create_pdf_dividend_chart_drawings()

    for chart in dividend_chart_drawings:
        story.append(chart)
        story.append(Spacer(1, 12))

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



def create_pdf_dividend_chart_drawings():
    """
    Create simple PDF chart drawings for dividend income.
    """

    try:
        from reportlab.graphics.shapes import Drawing, String
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.lib import colors

    except Exception:
        return []

    drawings = []

    stock_rows = chart_dict_to_rows(get_stock_wise_dividend_data())
    monthly_rows = chart_dict_to_rows(get_monthly_dividend_data())
    yearly_rows = chart_dict_to_rows(get_yearly_dividend_data())
    tax_net_rows = chart_dict_to_rows(get_tax_vs_net_data())

    stock_chart = create_pdf_pie_chart(
        "Stock-wise Dividend Income",
        stock_rows,
        Drawing,
        String,
        Pie,
        colors
    )

    if stock_chart:
        drawings.append(stock_chart)

    monthly_chart = create_pdf_bar_chart(
        "Monthly Dividend Income",
        monthly_rows,
        Drawing,
        String,
        VerticalBarChart,
        colors,
        "Net Dividend Income"
    )

    if monthly_chart:
        drawings.append(monthly_chart)

    yearly_chart = create_pdf_bar_chart(
        "Yearly Dividend Income",
        yearly_rows,
        Drawing,
        String,
        VerticalBarChart,
        colors,
        "Net Dividend Income"
    )

    if yearly_chart:
        drawings.append(yearly_chart)

    tax_net_chart = create_pdf_pie_chart(
        "Tax vs Net Received",
        tax_net_rows,
        Drawing,
        String,
        Pie,
        colors
    )

    if tax_net_chart:
        drawings.append(tax_net_chart)

    return drawings



def get_passive_income_forecast_pdf_rows():
    """
    Return PDF rows for passive income forecast.
    """

    forecast = get_passive_income_forecast()

    return [
        [
            "Current Year",
            "Current Year Net",
            "Monthly Forecast",
            "Yearly Forecast",
            "Total Net Received",
            "Records",
        ],
        [
            str(forecast["current_year"]),
            format_money(forecast["current_year_net"]),
            format_money(forecast["monthly_forecast"]),
            format_money(forecast["yearly_forecast"]),
            format_money(forecast["total_net_received"]),
            str(forecast["total_records"]),
        ],
    ]


def get_dividend_yield_pdf_rows():
    """
    Return PDF rows for stock-wise dividend yield.
    """

    rows = [[
        "Symbol",
        "Investment",
        "Current Value",
        "Net Dividend",
        "Yield on Cost",
        "Current Yield",
    ]]

    yield_rows = get_dividend_yield_by_stock()

    if not yield_rows:
        rows.append([
            "No Data",
            format_money(0),
            format_money(0),
            format_money(0),
            "0.00%",
            "0.00%",
        ])
        return rows

    for item in yield_rows[:12]:
        rows.append([
            str(item["symbol"]).upper(),
            format_money(item["investment_value"]),
            format_money(item["current_value"]),
            format_money(item["net_dividend"]),
            format_plain_percent(item["yield_on_cost"]),
            format_plain_percent(item["current_yield"]),
        ])

    return rows


def get_top_dividend_stocks_pdf_rows():
    """
    Return PDF rows for top dividend stocks.
    """

    rows = [[
        "Rank",
        "Symbol",
        "Net Dividend",
        "Yield on Cost",
        "Current Yield",
        "Records",
    ]]

    top_rows = get_top_dividend_stocks(10)

    if not top_rows:
        rows.append([
            "1",
            "No Data",
            format_money(0),
            "0.00%",
            "0.00%",
            "0",
        ])
        return rows

    for index, item in enumerate(top_rows):
        rows.append([
            str(index + 1),
            str(item["symbol"]).upper(),
            format_money(item["net_dividend"]),
            format_plain_percent(item["yield_on_cost"]),
            format_plain_percent(item["current_yield"]),
            str(item["dividend_records"]),
        ])

    return rows


def get_dividend_summary_pdf_rows():
    """
    Return PDF rows for dividend income summary.
    """

    overall = get_income_summary()

    return [
        [
            "Gross Dividend",
            "Tax Deducted",
            "Net Received",
            "Total Records",
        ],
        [
            format_money(overall["gross_amount"]),
            format_money(overall["tax_amount"]),
            format_money(overall["net_amount"]),
            str(overall["total_records"]),
        ],
    ]


def get_dividend_records_pdf_rows(dividends):
    """
    Return PDF rows for dividend records.
    """

    rows = [[
        "Symbol",
        "Shares",
        "DPS",
        "Gross",
        "Tax",
        "Net",
        "Payment Date",
    ]]

    if not dividends:
        rows.append([
            "No Data",
            "0",
            format_money(0),
            format_money(0),
            format_money(0),
            format_money(0),
            "",
        ])
        return rows

    for item in dividends:

        rows.append([
            str(safe_get(item, "symbol", "")).upper(),
            format_quantity(safe_get(item, "shares", 0)),
            format_money(safe_get(item, "dividend_per_share", 0)),
            format_money(safe_get(item, "gross_amount", 0)),
            format_money(safe_get(item, "tax_amount", 0)),
            format_money(safe_get(item, "net_amount", 0)),
            str(safe_get(item, "payment_date", "")),
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



def safe_get(item, key, default=None):
    """
    Safely read a value from dict-like rows, sqlite rows or objects.
    """

    try:
        if hasattr(item, "get"):
            return item.get(key, default)

        return item[key]

    except Exception:
        return default


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



def format_plain_percent(value):
    """
    Format already-calculated percentage value for PDF.
    Example: 4.25 -> 4.25%
    """

    return f"{safe_float(value):,.2f}%"


def format_quantity(value):
    """
    Format quantity for PDF.
    """

    return f"{safe_float(value):,.4f}"
