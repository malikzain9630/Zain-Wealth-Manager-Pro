"""
Chart Service
Prepares data for portfolio visual analytics.
"""

from services.portfolio_service import get_all_holdings
from services.mutual_fund_service import get_all_mutual_funds


def get_psx_allocation_data():
    """
    Return PSX allocation chart data.

    Format:
    {
        "labels": ["FFC", "MEBL"],
        "values": [12000, 15000]
    }
    """

    holdings = get_all_holdings()

    labels = []
    values = []

    for item in holdings:

        symbol = str(item["symbol"]).upper()
        shares = float(item["shares"])
        current_price = float(item["current_price"])

        current_value = shares * current_price

        if current_value > 0:
            labels.append(symbol)
            values.append(current_value)

    return {
        "labels": labels,
        "values": values
    }


def get_mutual_fund_allocation_data():
    """
    Return mutual fund allocation chart data.

    Format:
    {
        "labels": ["KMIF Growth", "MIF Growth"],
        "values": [19000, 17400]
    }
    """

    funds = get_all_mutual_funds()

    labels = []
    values = []

    for item in funds:

        fund = str(item["fund"])
        current_value = float(item["current_value"])

        if current_value > 0:
            labels.append(fund)
            values.append(current_value)

    return {
        "labels": labels,
        "values": values
    }


def get_overall_wealth_data():
    """
    Return overall wealth data.

    Categories:
        PSX Portfolio
        Mutual Funds
    """

    holdings = get_all_holdings()
    funds = get_all_mutual_funds()

    psx_value = 0
    mutual_fund_value = 0

    for item in holdings:

        shares = float(item["shares"])
        current_price = float(item["current_price"])

        psx_value += shares * current_price

    for item in funds:

        mutual_fund_value += float(item["current_value"])

    labels = []
    values = []

    if psx_value > 0:
        labels.append("PSX Portfolio")
        values.append(psx_value)

    if mutual_fund_value > 0:
        labels.append("Mutual Funds")
        values.append(mutual_fund_value)

    return {
        "labels": labels,
        "values": values
    }


def get_profit_loss_data():
    """
    Return profit/loss comparison data.

    Categories:
        PSX Portfolio
        Mutual Funds
    """

    holdings = get_all_holdings()
    funds = get_all_mutual_funds()

    psx_investment = 0
    psx_current = 0

    for item in holdings:

        shares = float(item["shares"])
        avg_price = float(item["avg_price"])
        current_price = float(item["current_price"])

        psx_investment += shares * avg_price
        psx_current += shares * current_price

    mutual_fund_investment = 0
    mutual_fund_current = 0

    for item in funds:

        mutual_fund_investment += float(item["investment_value"])
        mutual_fund_current += float(item["current_value"])

    psx_profit = psx_current - psx_investment
    mutual_fund_profit = mutual_fund_current - mutual_fund_investment

    labels = []
    values = []

    if psx_investment > 0 or psx_current > 0:
        labels.append("PSX Portfolio")
        values.append(psx_profit)

    if mutual_fund_investment > 0 or mutual_fund_current > 0:
        labels.append("Mutual Funds")
        values.append(mutual_fund_profit)

    return {
        "labels": labels,
        "values": values
    }


def get_chart_summary():
    """
    Return combined summary for charts window.
    """

    holdings = get_all_holdings()
    funds = get_all_mutual_funds()

    psx_investment = 0
    psx_current = 0

    for item in holdings:

        shares = float(item["shares"])
        avg_price = float(item["avg_price"])
        current_price = float(item["current_price"])

        psx_investment += shares * avg_price
        psx_current += shares * current_price

    mutual_fund_investment = 0
    mutual_fund_current = 0

    for item in funds:

        mutual_fund_investment += float(item["investment_value"])
        mutual_fund_current += float(item["current_value"])

    total_investment = psx_investment + mutual_fund_investment
    total_current = psx_current + mutual_fund_current
    total_profit = total_current - total_investment

    if total_investment > 0:
        total_profit_percent = (total_profit / total_investment) * 100
    else:
        total_profit_percent = 0

    return {
        "psx_current": round(psx_current, 2),
        "mutual_fund_current": round(mutual_fund_current, 2),
        "total_investment": round(total_investment, 2),
        "total_current": round(total_current, 2),
        "total_profit": round(total_profit, 2),
        "total_profit_percent": round(total_profit_percent, 2),
    }