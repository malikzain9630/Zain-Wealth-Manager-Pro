"""
Dividend Yield Service
Calculates dividend yield and passive income forecast.
"""

from datetime import datetime

from services.portfolio_service import get_all_holdings
from services.dividend_service import (
    get_income_summary,
    get_income_summary_by_symbol,
    get_income_summary_by_month,
    get_income_summary_by_year,
)


def get_dividend_yield_by_stock():
    """
    Calculate stock-wise dividend yield.

    Yield on cost:
        Net Dividend Received / Investment Value * 100

    Current yield:
        Net Dividend Received / Current Value * 100
    """

    holdings = get_all_holdings()
    symbol_summary = get_income_summary_by_symbol()

    dividend_map = {}

    for item in symbol_summary:
        symbol = str(item["symbol"]).upper()

        dividend_map[symbol] = {
            "records": int(item["records"]),
            "gross_amount": safe_float(item["gross_amount"]),
            "tax_amount": safe_float(item["tax_amount"]),
            "net_amount": safe_float(item["net_amount"]),
        }

    rows = []

    for holding in holdings:
        symbol = str(holding["symbol"]).upper()
        shares = safe_float(holding["shares"])
        avg_price = safe_float(holding["avg_price"])
        current_price = safe_float(holding["current_price"])

        investment_value = shares * avg_price
        current_value = shares * current_price

        dividend_data = dividend_map.get(symbol, {
            "records": 0,
            "gross_amount": 0,
            "tax_amount": 0,
            "net_amount": 0,
        })

        gross_dividend = dividend_data["gross_amount"]
        tax_amount = dividend_data["tax_amount"]
        net_dividend = dividend_data["net_amount"]
        records = dividend_data["records"]

        if investment_value > 0:
            yield_on_cost = (net_dividend / investment_value) * 100
        else:
            yield_on_cost = 0

        if current_value > 0:
            current_yield = (net_dividend / current_value) * 100
        else:
            current_yield = 0

        rows.append({
            "symbol": symbol,
            "shares": round(shares, 4),
            "avg_price": round(avg_price, 4),
            "current_price": round(current_price, 4),
            "investment_value": round(investment_value, 2),
            "current_value": round(current_value, 2),
            "gross_dividend": round(gross_dividend, 2),
            "tax_amount": round(tax_amount, 2),
            "net_dividend": round(net_dividend, 2),
            "dividend_records": records,
            "yield_on_cost": round(yield_on_cost, 2),
            "current_yield": round(current_yield, 2),
        })

    rows.sort(
        key=lambda item: item["net_dividend"],
        reverse=True
    )

    return rows


def get_current_year_dividend_summary():
    """
    Return dividend summary for the current year.
    """

    current_year = str(datetime.now().year)
    yearly_summary = get_income_summary_by_year()

    for item in yearly_summary:
        year = str(item["year"])

        if year == current_year:
            return {
                "year": current_year,
                "records": int(item["records"]),
                "gross_amount": safe_float(item["gross_amount"]),
                "tax_amount": safe_float(item["tax_amount"]),
                "net_amount": safe_float(item["net_amount"]),
            }

    return {
        "year": current_year,
        "records": 0,
        "gross_amount": 0,
        "tax_amount": 0,
        "net_amount": 0,
    }


def get_passive_income_forecast():
    """
    Calculate passive income forecast.

    Method:
    - Uses current year dividend received.
    - Annual forecast = current year net dividend / completed months * 12
    - Monthly forecast = annual forecast / 12

    This gives a simple run-rate estimate.
    """

    today = datetime.now()
    current_month = today.month

    current_year_summary = get_current_year_dividend_summary()
    current_year_net = safe_float(current_year_summary["net_amount"])

    if current_month > 0:
        yearly_forecast = (current_year_net / current_month) * 12
    else:
        yearly_forecast = 0

    monthly_forecast = yearly_forecast / 12
    overall = get_income_summary()

    total_gross = safe_float(overall["gross_amount"])
    total_tax = safe_float(overall["tax_amount"])
    total_net = safe_float(overall["net_amount"])
    total_records = int(overall["total_records"])

    return {
        "current_year": today.year,
        "current_month": current_month,
        "current_year_net": round(current_year_net, 2),
        "monthly_forecast": round(monthly_forecast, 2),
        "yearly_forecast": round(yearly_forecast, 2),
        "total_gross_received": round(total_gross, 2),
        "total_tax_deducted": round(total_tax, 2),
        "total_net_received": round(total_net, 2),
        "total_records": total_records,
    }


def get_monthly_income_trend():
    """
    Return monthly net dividend income trend.
    """

    monthly_summary = get_income_summary_by_month()
    rows = []

    for item in monthly_summary:
        rows.append({
            "month": str(item["month"]),
            "records": int(item["records"]),
            "gross_amount": round(safe_float(item["gross_amount"]), 2),
            "tax_amount": round(safe_float(item["tax_amount"]), 2),
            "net_amount": round(safe_float(item["net_amount"]), 2),
        })

    rows.sort(key=lambda item: item["month"])

    return rows


def get_yearly_income_trend():
    """
    Return yearly net dividend income trend.
    """

    yearly_summary = get_income_summary_by_year()
    rows = []

    for item in yearly_summary:
        rows.append({
            "year": str(item["year"]),
            "records": int(item["records"]),
            "gross_amount": round(safe_float(item["gross_amount"]), 2),
            "tax_amount": round(safe_float(item["tax_amount"]), 2),
            "net_amount": round(safe_float(item["net_amount"]), 2),
        })

    rows.sort(key=lambda item: item["year"])

    return rows


def get_top_dividend_stocks(limit=5):
    """
    Return top dividend stocks by net dividend received.
    """

    rows = get_dividend_yield_by_stock()
    filtered_rows = []

    for item in rows:
        if item["net_dividend"] > 0:
            filtered_rows.append(item)

    return filtered_rows[:limit]


def get_dividend_dashboard_summary():
    """
    Return compact dividend summary for dashboard.
    """

    forecast = get_passive_income_forecast()
    top_stocks = get_top_dividend_stocks(3)
    top_symbol = ""

    if top_stocks:
        top_symbol = top_stocks[0]["symbol"]

    return {
        "total_net_received": forecast["total_net_received"],
        "current_year_net": forecast["current_year_net"],
        "monthly_forecast": forecast["monthly_forecast"],
        "yearly_forecast": forecast["yearly_forecast"],
        "total_records": forecast["total_records"],
        "top_dividend_stock": top_symbol,
    }


def safe_float(value):
    """
    Convert value to float safely.
    """

    try:
        if value is None:
            return 0.0

        return float(value)

    except (ValueError, TypeError):
        return 0.0
