import sys
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parent.parent))
import xlsxwriter
from pathlib import Path

from dashboard import create_dashboard
from psx import create_psx_sheet
from mutual_funds import create_mutual_funds_sheet
from pf import create_pf_sheet
from pension import create_pension_sheet
from dividend import create_dividend_sheet
from transactions import create_transaction_sheet
from report_generator import generate_pdf_report
from allocation_sheet import create_allocation_sheet
from networth_history import create_networth_history_sheet
from database import initialize_database

# Output Folder
output = Path(__file__).parent.parent / "output"
output.mkdir(exist_ok=True)

file_name = output / "Zain_Wealth_Manager_Pro_v1.xlsx"
initialize_database()
workbook = xlsxwriter.Workbook(file_name)

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
pdf_path = Path(__file__).parent.parent / "output" / "report.pdf"

generate_pdf_report(str(pdf_path))

print("PDF Report Created Successfully")
print(pdf_path)
print("Workbook Created Successfully")
print(file_name)

from report_generator import generate_pdf_report
from pathlib import Path