"""
Portfolio Service
"""

from portfolio_db import (
    add_holding,
    delete_holding,
    get_portfolio
)


def get_all_holdings():
    """Return all portfolio holdings."""
    return get_portfolio()


def add_new_holding(symbol, shares, avg_price, current_price):
    """Add a holding."""
    add_holding(
        symbol,
        shares,
        avg_price,
        current_price
    )


def remove_holding(symbol):
    """Delete a holding."""
    delete_holding(symbol)