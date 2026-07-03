"""
XIRR Calculator
"""

from datetime import date
from data.cashflows import CASHFLOWS


def xnpv(rate, cashflows):

    total = 0

    first_date = cashflows[0][0]

    for dt, amount in cashflows:

        days = (dt - first_date).days

        total += amount / ((1 + rate) ** (days / 365))

    return total


def calculate_xirr(cashflows=CASHFLOWS):

    rate = 0.10

    for _ in range(100):

        value = xnpv(rate, cashflows)

        derivative = (
            xnpv(rate + 0.0001, cashflows) - value
        ) / 0.0001

        if abs(derivative) < 1e-10:
            break

        new_rate = rate - value / derivative

        if abs(new_rate - rate) < 1e-8:
            rate = new_rate
            break

        rate = new_rate

    return round(rate * 100, 2)