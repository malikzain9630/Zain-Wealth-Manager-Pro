"""
Portfolio Analytics
"""

from utils import (
    get_summary,
    get_performance,
    get_dividend_summary
)
from xirr import calculate_xirr


def get_portfolio_analytics():

    summary = get_summary()
    performance = get_performance()
    dividend = get_dividend_summary()
    xirr = calculate_xirr()

    current_value = summary["current"]

    dividend_yield = 0

    if current_value > 0:
        dividend_yield = round((dividend / current_value) * 100, 2)

    return {

        "net_worth": summary["net_worth"],

        "investment": summary["investment"],

        "current_value": current_value,

        "profit": summary["profit"],

        "xirr": xirr,

        "cagr": performance["cagr"],

        "annual_dividend": dividend,

        "dividend_yield": dividend_yield,

        "rating": performance["rating"]

    }