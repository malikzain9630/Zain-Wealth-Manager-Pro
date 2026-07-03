"""
Zain Wealth Manager Pro
Executive Dashboard (CLEAN v1.0)
"""

from styles import ExcelTheme

from utils import (
    get_summary,
    get_goal_progress,
    get_health_score,
    get_performance
)

from analytics import get_portfolio_analytics
from advisor import generate_advice

from charts import create_asset_chart, create_networth_chart
from data.settings import SETTINGS
from xirr import calculate_xirr


def create_dashboard(workbook):

    theme = ExcelTheme(workbook)
    ws = workbook.add_worksheet("Dashboard")

    # ----------------------------
    # Layout Setup
    # ----------------------------
    ws.set_column("A:A", 4)
    ws.set_column("B:C", 22)
    ws.set_column("D:E", 22)
    ws.set_column("F:G", 22)
    ws.set_column("H:I", 22)

    # ----------------------------
    # Header
    # ----------------------------
    ws.merge_range(
        "B2:I3",
        "ZAIN WEALTH MANAGER PRO",
        theme.title
    )

    ws.write("B4", "Investor", theme.heading)
    ws.write("C4", SETTINGS["investor"], theme.normal)

    ws.write("F4", "Broker", theme.heading)
    ws.write("G4", SETTINGS["broker"], theme.normal)

    # ----------------------------
    # CORE DATA (Single Source)
    # ----------------------------
    summary = get_summary()
    goal = get_goal_progress()
    health = get_health_score()
    performance = get_performance()
    analytics = get_portfolio_analytics()
    advice = generate_advice()
    xirr = calculate_xirr()

    # ----------------------------
    # KPI CARDS
    # ----------------------------
    cards = [
        ("Net Worth", summary["net_worth"]),
        ("Investment", summary["investment"]),
        ("Current Value", summary["current"]),
        ("Profit / Loss", summary["profit"]),
        ("XIRR", f"{xirr}%"),
        ("Health Score", f"{health}/100"),
        ("Dividend Yield", f"{analytics['dividend_yield']}%"),
    ]

    row = 7

    for title, value in cards:
        ws.merge_range(row, 1, row, 2, title, theme.card_title)
        ws.merge_range(row + 1, 1, row + 1, 2, value, theme.card_value)
        row += 3

    # ----------------------------
    # Monthly Plan
    # ----------------------------
    ws.write("F8", "Monthly Investment Plan", theme.heading)

    plan = [
        ("PSX", SETTINGS["monthly_psx"]),
        ("KMIF", SETTINGS["monthly_kmif"]),
        ("MIF", SETTINGS["monthly_mif"]),
        ("Pension", SETTINGS["monthly_pension"]),
        ("Provident Fund", SETTINGS["monthly_pf"]),
    ]

    r = 8
    for item, amount in plan:
        ws.write(r, 5, item, theme.normal)
        ws.write(r, 6, amount, theme.currency)
        r += 1

    # ----------------------------
    # CHARTS
    # ----------------------------
    create_asset_chart(workbook, ws, summary["allocation"])
    create_networth_chart(workbook, ws)

    # ----------------------------
    # GOALS
    # ----------------------------
    ws.write("F18", "Financial Goals", theme.heading)

    ws.write("F19", "Target Net Worth", theme.normal)
    ws.write("G19", goal["target"], theme.currency)

    ws.write("F20", "Current Net Worth", theme.normal)
    ws.write("G20", goal["current"], theme.currency)

    ws.write("F21", "Progress", theme.normal)
    ws.write("G21", f'{goal["progress"]}%', theme.normal)

    ws.write("F22", "Years Remaining", theme.normal)
    ws.write("G22", goal["years_remaining"], theme.normal)

    ws.write("F23", "Monthly Investment", theme.normal)
    ws.write("G23", goal["monthly_investment"], theme.currency)

    # ----------------------------
    # PERFORMANCE
    # ----------------------------
    ws.write("F25", "Portfolio Performance", theme.heading)

    ws.write("F26", "CAGR", theme.normal)
    ws.write("G26", f'{performance["cagr"]}%')

    ws.write("F27", "XIRR", theme.normal)
    ws.write("G27", f"{xirr}%")

    ws.write("F28", "Dividend Yield", theme.normal)
    ws.write("G28", f'{analytics["dividend_yield"]}%')

    ws.write("F29", "Rating", theme.normal)
    ws.write("G29", analytics["rating"], theme.heading)

    # ----------------------------
    # AI ADVISOR
    # ----------------------------
    ws.write("B34", "AI Investment Advisor", theme.heading)

    row = 35
    for item in advice:
        ws.write(row, 1, "• " + item, theme.normal)
        row += 1

    # ----------------------------
    # FOOTER (SAFE POSITION)
    # ----------------------------
    ws.merge_range(
        "B45:I45",
        "Prepared by Zain Wealth Manager Pro",
        theme.heading
    )