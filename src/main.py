"""
Zain Wealth Manager Pro
Main Entry Point
"""

import sys
from pathlib import Path

import xlsxwriter

# Add Project Root to Python Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

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


def generate_reports():
    """Generate Excel and PDF Reports"""

    output = Path(__file__).parent.parent / "output"
    output.mkdir(exist_ok=True)

    excel_file = output / "Zain_Wealth_Manager_Pro_v1.xlsx"
    pdf_file = output / "report.pdf"

    initialize_database()

    workbook = xlsxwriter.Workbook(excel_file)

    create_dashboard(workbook)
    create_psx_sheet(workbook)
    create_mutual_funds_sheet(workbook)
    create_pf_sheet(workbook)
    create_pension_sheet(workbook)
    create_dividend_sheet(workbook)
    create_transaction_sheet(workbook)
    create_allocation_sheet(workbook)
    create_networth_history_sheet(workbook)

    workbook.close()

    generate_pdf_report(str(pdf_file))

    return excel_file, pdf_file


def main():

    excel_file, pdf_file = generate_reports()

    print("Workbook Created Successfully")
    print(excel_file)

    print("PDF Report Created Successfully")
    print(pdf_file)


if __name__ == "__main__":
    main()