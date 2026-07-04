"""
Report Service
Handles Excel & PDF generation.
"""

from main import generate_reports


def create_reports():
    """
    Generate all reports.
    Returns:
        tuple(excel_file, pdf_file)
    """
    return generate_reports()