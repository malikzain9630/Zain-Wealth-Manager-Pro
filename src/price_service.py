"""
Price Service
"""

from data.price_cache import PRICE_CACHE


def get_price(symbol):

    return PRICE_CACHE.get(symbol, 0)


def update_price(symbol, price):

    PRICE_CACHE[symbol] = price