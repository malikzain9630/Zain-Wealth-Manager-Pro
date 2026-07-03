"""
PDF Report Generator - Zain Wealth Manager Pro
"""

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from analytics import get_portfolio_analytics
from utils import get_summary, get_goal_progress, get_performance
from advisor import generate_advice
from xirr import calculate_xirr


def generate_pdf_report(output_path):

    doc = SimpleDocTemplate(output_path)

    styles = getSampleStyleSheet()
    story = []

    # -----------------------
    # Data
    # -----------------------
    summary = get_summary()
    goal = get_goal_progress()
    performance = get_performance()
    analytics = get_portfolio_analytics()
    advice = generate_advice()
    xirr = calculate_xirr()

    # -----------------------
    # Title
    # -----------------------
    story.append(Paragraph("Zain Wealth Manager Pro - Investment Report", styles["Title"]))
    story.append(Spacer(1, 12))

    # -----------------------
    # Summary Section
    # -----------------------
    story.append(Paragraph("Portfolio Summary", styles["Heading2"]))
    story.append(Paragraph(f"Net Worth: {summary['net_worth']}", styles["Normal"]))
    story.append(Paragraph(f"Current Value: {summary['current']}", styles["Normal"]))
    story.append(Paragraph(f"Profit: {summary['profit']}", styles["Normal"]))
    story.append(Spacer(1, 12))

    # -----------------------
    # Performance Section
    # -----------------------
    story.append(Paragraph("Performance", styles["Heading2"]))
    story.append(Paragraph(f"XIRR: {xirr}%", styles["Normal"]))
    story.append(Paragraph(f"CAGR: {performance['cagr']}%", styles["Normal"]))
    story.append(Paragraph(f"Dividend Yield: {analytics['dividend_yield']}%", styles["Normal"]))
    story.append(Spacer(1, 12))

    # -----------------------
    # Goal Section
    # -----------------------
    story.append(Paragraph("Financial Goal", styles["Heading2"]))
    story.append(Paragraph(f"Target: {goal['target']}", styles["Normal"]))
    story.append(Paragraph(f"Progress: {goal['progress']}%", styles["Normal"]))
    story.append(Spacer(1, 12))

    # -----------------------
    # AI Advice
    # -----------------------
    story.append(Paragraph("AI Investment Advice", styles["Heading2"]))

    for item in advice:
        story.append(Paragraph(f"- {item}", styles["Normal"]))

    # -----------------------
    # Build PDF
    # -----------------------
    doc.build(story)

    return output_path