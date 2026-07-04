"""
Dividend Service
Handles dividend income business logic.
"""

from datetime import datetime

from dividend_db import (
    add_dividend,
    update_dividend,
    delete_dividend,
    get_dividends,
    get_dividend_by_id,
    get_dividend_summary,
    get_dividend_summary_by_symbol,
    get_dividend_summary_by_year,
    get_dividend_summary_by_month
)


def get_all_dividends():
    """
    Return all dividend records.
    """

    return get_dividends()


def get_dividend(dividend_id):
    """
    Return one dividend record by ID.
    """

    dividend_id = validate_id(dividend_id)

    dividend = get_dividend_by_id(dividend_id)

    if not dividend:
        raise ValueError("Dividend record not found.")

    return dividend


def add_new_dividend(
    symbol,
    shares,
    dividend_per_share,
    tax_amount,
    payment_date,
    remarks=""
):
    """
    Add a new dividend record.

    Gross Amount = Shares x Dividend Per Share
    Net Amount = Gross Amount - Tax Amount
    """

    symbol = validate_symbol(symbol)
    shares = validate_positive_number(shares, "Shares")
    dividend_per_share = validate_positive_number(
        dividend_per_share,
        "Dividend per share"
    )
    tax_amount = validate_non_negative_number(
        tax_amount,
        "Tax amount"
    )
    payment_date = validate_payment_date(payment_date)
    remarks = str(remarks).strip()

    gross_amount = shares * dividend_per_share
    net_amount = gross_amount - tax_amount

    if net_amount < 0:
        raise ValueError("Tax amount cannot be greater than gross amount.")

    add_dividend(
        symbol,
        shares,
        dividend_per_share,
        gross_amount,
        tax_amount,
        net_amount,
        payment_date,
        remarks
    )


def update_existing_dividend(
    dividend_id,
    symbol,
    shares,
    dividend_per_share,
    tax_amount,
    payment_date,
    remarks=""
):
    """
    Update an existing dividend record.
    """

    dividend_id = validate_id(dividend_id)

    existing = get_dividend_by_id(dividend_id)

    if not existing:
        raise ValueError("Dividend record not found.")

    symbol = validate_symbol(symbol)
    shares = validate_positive_number(shares, "Shares")
    dividend_per_share = validate_positive_number(
        dividend_per_share,
        "Dividend per share"
    )
    tax_amount = validate_non_negative_number(
        tax_amount,
        "Tax amount"
    )
    payment_date = validate_payment_date(payment_date)
    remarks = str(remarks).strip()

    gross_amount = shares * dividend_per_share
    net_amount = gross_amount - tax_amount

    if net_amount < 0:
        raise ValueError("Tax amount cannot be greater than gross amount.")

    update_dividend(
        dividend_id,
        symbol,
        shares,
        dividend_per_share,
        gross_amount,
        tax_amount,
        net_amount,
        payment_date,
        remarks
    )


def remove_dividend(dividend_id):
    """
    Delete dividend record.
    """

    dividend_id = validate_id(dividend_id)

    existing = get_dividend_by_id(dividend_id)

    if not existing:
        raise ValueError("Dividend record not found.")

    delete_dividend(dividend_id)


def get_income_summary():
    """
    Return overall dividend income summary.
    """

    return get_dividend_summary()


def get_income_summary_by_symbol():
    """
    Return dividend income summary grouped by symbol.
    """

    return get_dividend_summary_by_symbol()


def get_income_summary_by_year():
    """
    Return dividend income summary grouped by year.
    """

    return get_dividend_summary_by_year()


def get_income_summary_by_month():
    """
    Return dividend income summary grouped by month.
    """

    return get_dividend_summary_by_month()


def calculate_dividend_amount(shares, dividend_per_share, tax_amount):
    """
    Return calculated gross and net dividend amounts.
    """

    shares = validate_positive_number(shares, "Shares")
    dividend_per_share = validate_positive_number(
        dividend_per_share,
        "Dividend per share"
    )
    tax_amount = validate_non_negative_number(
        tax_amount,
        "Tax amount"
    )

    gross_amount = shares * dividend_per_share
    net_amount = gross_amount - tax_amount

    if net_amount < 0:
        raise ValueError("Tax amount cannot be greater than gross amount.")

    return {
        "gross_amount": round(gross_amount, 2),
        "tax_amount": round(tax_amount, 2),
        "net_amount": round(net_amount, 2)
    }


def validate_symbol(symbol):
    """
    Validate stock symbol.
    """

    symbol = str(symbol).strip().upper()

    if not symbol:
        raise ValueError("Symbol cannot be empty.")

    return symbol


def validate_id(value):
    """
    Validate record ID.
    """

    try:
        value = int(value)

    except (ValueError, TypeError):
        raise ValueError("Invalid dividend record ID.")

    if value <= 0:
        raise ValueError("Invalid dividend record ID.")

    return value


def validate_positive_number(value, field_name):
    """
    Validate positive numeric value.
    """

    try:
        value = float(value)

    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be numeric.")

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")

    return value


def validate_non_negative_number(value, field_name):
    """
    Validate zero or positive numeric value.
    """

    if value is None or str(value).strip() == "":
        value = 0

    try:
        value = float(value)

    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be numeric.")

    if value < 0:
        raise ValueError(f"{field_name} cannot be negative.")

    return value


def validate_payment_date(payment_date):
    """
    Validate payment date.

    Required format:
        YYYY-MM-DD
    """

    payment_date = str(payment_date).strip()

    if not payment_date:
        raise ValueError("Payment date cannot be empty.")

    try:
        datetime.strptime(payment_date, "%Y-%m-%d")

    except ValueError:
        raise ValueError("Payment date must be in YYYY-MM-DD format.")

    return payment_date