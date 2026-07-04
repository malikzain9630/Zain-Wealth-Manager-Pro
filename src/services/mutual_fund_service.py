"""
Mutual Fund Service
Handles mutual fund business logic.
"""

from mutual_fund_db import (
    add_mutual_fund,
    update_mutual_fund,
    delete_mutual_fund,
    get_mutual_funds,
    get_mutual_fund_by_name,
    seed_mutual_funds_if_empty
)


def get_all_mutual_funds():
    """
    Return all mutual funds.
    """

    seed_mutual_funds_if_empty()

    return get_mutual_funds()


def get_mutual_fund(fund):
    """
    Return one mutual fund by name.
    """

    fund = str(fund).strip()

    if not fund:
        raise ValueError("Fund name cannot be empty.")

    seed_mutual_funds_if_empty()

    return get_mutual_fund_by_name(fund)


def add_new_mutual_fund(fund, units, avg_nav, current_nav):
    """
    Add a new mutual fund after validation.
    """

    fund = str(fund).strip()

    if not fund:
        raise ValueError("Fund name cannot be empty.")

    units = validate_positive_number(units, "Units")
    avg_nav = validate_positive_number(avg_nav, "Average NAV")
    current_nav = validate_positive_number(current_nav, "Current NAV")

    existing = get_mutual_fund_by_name(fund)

    if existing:
        raise ValueError(f"Mutual fund already exists: {fund}")

    add_mutual_fund(
        fund,
        units,
        avg_nav,
        current_nav
    )


def update_existing_mutual_fund(fund, units, avg_nav, current_nav):
    """
    Update an existing mutual fund after validation.
    """

    fund = str(fund).strip()

    if not fund:
        raise ValueError("Fund name cannot be empty.")

    units = validate_positive_number(units, "Units")
    avg_nav = validate_positive_number(avg_nav, "Average NAV")
    current_nav = validate_positive_number(current_nav, "Current NAV")

    existing = get_mutual_fund_by_name(fund)

    if not existing:
        raise ValueError(f"Mutual fund not found: {fund}")

    update_mutual_fund(
        fund,
        units,
        avg_nav,
        current_nav
    )


def remove_mutual_fund(fund):
    """
    Delete a mutual fund.
    """

    fund = str(fund).strip()

    if not fund:
        raise ValueError("Fund name cannot be empty.")

    existing = get_mutual_fund_by_name(fund)

    if not existing:
        raise ValueError(f"Mutual fund not found: {fund}")

    delete_mutual_fund(fund)


def update_mutual_fund_nav(fund, current_nav):
    """
    Update only current NAV of a mutual fund.
    Units and average NAV remain unchanged.
    """

    fund = str(fund).strip()

    if not fund:
        raise ValueError("Fund name cannot be empty.")

    current_nav = validate_positive_number(current_nav, "Current NAV")

    existing = get_mutual_fund_by_name(fund)

    if not existing:
        raise ValueError(f"Mutual fund not found: {fund}")

    update_mutual_fund(
        fund,
        existing["units"],
        existing["avg_nav"],
        current_nav
    )


def get_mutual_fund_summary():
    """
    Return mutual fund portfolio summary.
    """

    funds = get_all_mutual_funds()

    total_investment = 0
    total_current = 0

    for fund in funds:

        total_investment += float(fund["investment_value"])
        total_current += float(fund["current_value"])

    profit_loss = total_current - total_investment

    if total_investment > 0:
        profit_percent = (profit_loss / total_investment) * 100
    else:
        profit_percent = 0

    return {
        "total_investment": round(total_investment, 2),
        "total_current": round(total_current, 2),
        "profit_loss": round(profit_loss, 2),
        "profit_percent": round(profit_percent, 2),
        "total_funds": len(funds)
    }


def validate_positive_number(value, field_name):
    """
    Validate positive numeric value.
    """

    try:
        value = float(value)

    except ValueError:
        raise ValueError(f"{field_name} must be numeric.")

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")

    return value