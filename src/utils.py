"""
Utility Functions
"""

from data.portfolio import PORTFOLIO
from portfolio_db import get_portfolio

PORTFOLIO = get_portfolio()
from data.mutual_funds import MUTUAL_FUNDS
from data.pf import PF_DATA
from data.pension import PENSION_DATA

def get_summary():

    psx_investment = 0
    psx_current = 0

    for stock in PORTFOLIO:

        invest = stock["shares"] * stock["avg"]
        current = stock["shares"] * stock["current"]

        psx_investment += invest
        psx_current += current

    psx_profit = psx_current - psx_investment

    mutual_total = sum(f["value"] for f in MUTUAL_FUNDS)

    provident_fund = PF_DATA["current_balance"]

    pension = PENSION_DATA["current_value"]

    net_worth = (
        psx_current
        + mutual_total
        + provident_fund
        + pension
    )
    asset_allocation = {

        "PSX": round(psx_current, 2),

        "Mutual Funds": round(mutual_total, 2),

        "Provident Fund": round(provident_fund, 2),

        "Pension": round(pension, 2)

    }
    return {

        "net_worth": round(net_worth,2),

        "investment": round(psx_investment+mutual_total,2),

        "current": round(psx_current+mutual_total,2),

        "profit": round(psx_profit,2),

        "mutual": round(mutual_total,2),

        "pf": round(provident_fund,2),

        "pension": round(pension,2),

        "allocation": asset_allocation

    }

def pf_projection():

    balance = PF_DATA["current_balance"]
    monthly = (
        PF_DATA["employee_monthly"]
        + PF_DATA["employer_monthly"]
    )

    rate = PF_DATA["annual_profit_rate"] / 100

    projection = []

    current = balance

    for year in range(1, 6):

        current = (current + monthly * 12) * (1 + rate)

        projection.append((
            2026 + year,
            round(current, 2)
        ))

    return projection

def pension_projection():

    current = PENSION_DATA["current_value"]

    monthly = PENSION_DATA["monthly_contribution"]

    rate = PENSION_DATA["annual_return"] / 100

    projection = []

    balance = current

    for year in range(1, 6):

        balance = (balance + monthly * 12) * (1 + rate)

        projection.append((

            2026 + year,

            round(balance, 2)

        ))

    return projection

def get_asset_allocation():

    summary = get_summary()

    return [

        ("PSX", summary["current"] - summary["mutual"]),

        ("Mutual Funds", summary["mutual"]),

        ("Provident Fund", summary["pf"]),

        ("Pension", summary["pension"])

    ]

from data.dividends import DIVIDENDS


def get_dividend_summary():

    total = 0

    for item in DIVIDENDS:
        total += item["shares"] * item["dividend_per_share"]

    return round(total, 2)

def get_health_score():

    summary = get_summary()

    score = 0

    # Net Worth
    if summary["net_worth"] >= 500000:
        score += 30
    elif summary["net_worth"] >= 250000:
        score += 20
    else:
        score += 10

    # Diversification
    allocation = summary["allocation"]

    active_assets = sum(
        1 for value in allocation.values() if value > 0
    )

    score += active_assets * 10

    # Profitability
    if summary["profit"] > 0:
        score += 20

    # Mutual Funds
    if summary["mutual"] > 0:
        score += 10

    # Provident Fund
    if summary["pf"] > 0:
        score += 10

    if score > 100:
        score = 100

    return score

from datetime import datetime
from data.goals import GOALS


def get_goal_progress():

    summary = get_summary()

    current_net_worth = summary["net_worth"]
    target = GOALS["target_net_worth"]

    progress = (current_net_worth / target) * 100

    current_year = datetime.now().year
    years_remaining = max(
        GOALS["target_year"] - current_year,
        0
    )

    return {

        "target": round(target, 2),

        "current": round(current_net_worth, 2),

        "progress": round(progress, 2),

        "years_remaining": years_remaining,

        "monthly_investment": GOALS["current_monthly_investment"]

    }

from data.performance import PERFORMANCE


def get_performance():

    return PERFORMANCE

from data.transactions import TRANSACTIONS


def get_transactions():

    return TRANSACTIONS

from data.networth_history import NET_WORTH_HISTORY


def get_networth_history():

    return NET_WORTH_HISTORY