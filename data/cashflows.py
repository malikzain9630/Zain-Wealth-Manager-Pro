"""
Investment Cash Flows
Negative = Investment
Positive = Withdrawal / Current Value
"""

from datetime import date

CASHFLOWS = [

    # PSX Investments
    (date(2024, 1, 10), -50000),
    (date(2024, 6, 15), -25000),
    (date(2025, 2, 5), -30000),

    # Mutual Funds
    (date(2024, 3, 1), -20000),
    (date(2025, 1, 1), -12000),

    # Current Portfolio Value
    (date.today(), 165000)

]