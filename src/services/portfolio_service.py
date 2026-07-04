"""
Portfolio Service
"""

from portfolio_db import (
    add_holding,
    delete_holding,
    update_holding,
    get_portfolio
)


def get_all_holdings():
    """
    Return all portfolio holdings.
    """
    return get_portfolio()


def add_new_holding(symbol, shares, avg_price, current_price):
    """
    Add a new holding after validation.
    """

    symbol = symbol.strip().upper()

    if not symbol:
        raise ValueError("Symbol cannot be empty.")

    if shares <= 0:
        raise ValueError("Shares must be greater than zero.")

    if avg_price <= 0:
        raise ValueError("Average Price must be greater than zero.")

    if current_price <= 0:
        raise ValueError("Current Price must be greater than zero.")

    add_holding(
        symbol,
        shares,
        avg_price,
        current_price
    )


def update_existing_holding(symbol, shares, avg_price, current_price):
    """
    Update an existing holding.
    """

    symbol = symbol.strip().upper()

    if not symbol:
        raise ValueError("Symbol cannot be empty.")

    if shares <= 0:
        raise ValueError("Shares must be greater than zero.")

    if avg_price <= 0:
        raise ValueError("Average Price must be greater than zero.")

    if current_price <= 0:
        raise ValueError("Current Price must be greater than zero.")

    update_holding(
        symbol,
        shares,
        avg_price,
        current_price
    )


def remove_holding(symbol):
    """
    Delete a holding.
    """

    symbol = symbol.strip().upper()

    if not symbol:
        raise ValueError("Symbol cannot be empty.")

    delete_holding(symbol)