"""
Wealth Asset Service
Business/service layer for Phase 10 wealth assets:
- Provident Fund
- Pension / MTPF
- Bank Cash
- Other manual assets

All values are stored in PKR.
Display conversion is handled separately by currency_service.
"""

from wealth_asset_db import (
    ASSET_TYPES,
    TRANSACTION_TYPES,
    initialize_wealth_asset_tables,
    add_wealth_asset,
    update_wealth_asset,
    delete_wealth_asset,
    get_wealth_assets,
    get_wealth_asset_by_id,
    add_wealth_asset_transaction,
    delete_wealth_asset_transaction,
    get_wealth_asset_transactions,
    get_wealth_asset_transaction_by_id,
    get_wealth_asset_summary,
    get_total_wealth_asset_balance,
)


def initialize_wealth_assets():
    """
    Initialize wealth asset tables.
    """

    initialize_wealth_asset_tables()


def get_asset_types():
    """
    Return allowed asset types.
    """

    return ASSET_TYPES.copy()


def get_transaction_types():
    """
    Return allowed transaction types.
    """

    return TRANSACTION_TYPES.copy()


def get_all_wealth_assets(include_inactive=False):
    """
    Return all wealth assets.
    """

    return get_wealth_assets(include_inactive=include_inactive)


def get_wealth_asset(asset_id):
    """
    Return one wealth asset.
    """

    return get_wealth_asset_by_id(asset_id)


def add_new_wealth_asset(data):
    """
    Add a new wealth asset using dictionary data.
    """

    cleaned = clean_asset_data(data)

    return add_wealth_asset(
        asset_type=cleaned["asset_type"],
        account_name=cleaned["account_name"],
        institution=cleaned["institution"],
        current_balance=cleaned["current_balance"],
        monthly_contribution=cleaned["monthly_contribution"],
        employer_contribution=cleaned["employer_contribution"],
        start_date=cleaned["start_date"],
        last_updated=cleaned["last_updated"],
        remarks=cleaned["remarks"],
    )


def update_existing_wealth_asset(asset_id, data):
    """
    Update an existing wealth asset using dictionary data.
    """

    cleaned = clean_asset_data(data)

    return update_wealth_asset(
        asset_id=asset_id,
        asset_type=cleaned["asset_type"],
        account_name=cleaned["account_name"],
        institution=cleaned["institution"],
        current_balance=cleaned["current_balance"],
        monthly_contribution=cleaned["monthly_contribution"],
        employer_contribution=cleaned["employer_contribution"],
        start_date=cleaned["start_date"],
        last_updated=cleaned["last_updated"],
        remarks=cleaned["remarks"],
        is_active=cleaned["is_active"],
    )


def remove_wealth_asset(asset_id):
    """
    Delete a wealth asset.
    """

    delete_wealth_asset(asset_id)


def add_new_wealth_asset_transaction(data):
    """
    Add a transaction using dictionary data.
    """

    cleaned = clean_transaction_data(data)

    return add_wealth_asset_transaction(
        asset_id=cleaned["asset_id"],
        transaction_type=cleaned["transaction_type"],
        amount=cleaned["amount"],
        transaction_date=cleaned["transaction_date"],
        remarks=cleaned["remarks"],
        update_balance=cleaned["update_balance"],
    )


def remove_wealth_asset_transaction(transaction_id, reverse_balance=False):
    """
    Delete a transaction.
    """

    delete_wealth_asset_transaction(
        transaction_id=transaction_id,
        reverse_balance=reverse_balance
    )


def get_all_wealth_asset_transactions(asset_id=None):
    """
    Return wealth asset transactions.
    """

    return get_wealth_asset_transactions(asset_id=asset_id)


def get_wealth_asset_transaction(transaction_id):
    """
    Return one wealth asset transaction.
    """

    return get_wealth_asset_transaction_by_id(transaction_id)


def get_wealth_assets_summary():
    """
    Return summary by asset type.
    """

    return get_wealth_asset_summary()


def get_wealth_assets_total_balance():
    """
    Return total balance of all wealth assets.
    """

    return get_total_wealth_asset_balance()


def get_summary_by_asset_type():
    """
    Return summary dictionary by asset type.
    """

    rows = get_wealth_asset_summary()

    summary = {}

    for asset_type in ASSET_TYPES:
        summary[asset_type] = {
            "records": 0,
            "total_balance": 0.0,
            "monthly_contribution": 0.0,
            "employer_contribution": 0.0,
        }

    for item in rows:

        asset_type = item["asset_type"]

        summary[asset_type] = {
            "records": int(item["records"]),
            "total_balance": safe_float(item["total_balance"]),
            "monthly_contribution": safe_float(item["monthly_contribution"]),
            "employer_contribution": safe_float(item["employer_contribution"]),
        }

    return summary


def get_phase10_dashboard_summary():
    """
    Return compact summary for dashboard integration.

    Includes:
    - PF balance
    - Pension/MTPF balance
    - Bank cash
    - Other assets
    - Total manual wealth assets
    - Monthly contribution total
    """

    summary = get_summary_by_asset_type()

    provident_fund = summary["Provident Fund"]["total_balance"]
    pension = summary["Pension / MTPF"]["total_balance"]
    bank_cash = summary["Bank Cash"]["total_balance"]
    other_assets = summary["Other"]["total_balance"]

    monthly_contribution = 0.0
    employer_contribution = 0.0
    total_records = 0

    for asset_type in ASSET_TYPES:
        monthly_contribution += summary[asset_type]["monthly_contribution"]
        employer_contribution += summary[asset_type]["employer_contribution"]
        total_records += summary[asset_type]["records"]

    total_balance = (
        provident_fund
        + pension
        + bank_cash
        + other_assets
    )

    return {
        "provident_fund": round(provident_fund, 2),
        "pension_mtpF": round(pension, 2),
        "pension_mtpf": round(pension, 2),
        "bank_cash": round(bank_cash, 2),
        "other_assets": round(other_assets, 2),
        "total_balance": round(total_balance, 2),
        "monthly_contribution": round(monthly_contribution, 2),
        "employer_contribution": round(employer_contribution, 2),
        "total_monthly_saving": round(
            monthly_contribution + employer_contribution,
            2
        ),
        "total_records": total_records,
    }


def get_assets_by_type(asset_type):
    """
    Return assets filtered by asset type.
    """

    asset_type = str(asset_type or "").strip()

    assets = get_all_wealth_assets()

    filtered_assets = []

    for asset in assets:

        if asset["asset_type"] == asset_type:
            filtered_assets.append(asset)

    return filtered_assets


def get_total_balance_by_type(asset_type):
    """
    Return total balance for one asset type.
    """

    assets = get_assets_by_type(asset_type)

    total = 0.0

    for asset in assets:
        total += safe_float(asset["current_balance"])

    return round(total, 2)


def calculate_projected_balance(
    current_balance,
    monthly_contribution,
    employer_contribution=0,
    annual_return_percent=0,
    years=1
):
    """
    Simple projection for PF/Pension/Cash.

    Monthly growth model:
    - monthly contribution added every month
    - annual return converted into monthly return
    """

    current_balance = safe_float(current_balance)
    monthly_contribution = safe_float(monthly_contribution)
    employer_contribution = safe_float(employer_contribution)
    annual_return_percent = safe_float(annual_return_percent)
    years = int(safe_float(years))

    if years < 0:
        years = 0

    months = years * 12

    balance = current_balance
    monthly_addition = monthly_contribution + employer_contribution

    monthly_return = annual_return_percent / 100 / 12

    for _ in range(months):

        balance += monthly_addition

        if monthly_return > 0:
            balance = balance * (1 + monthly_return)

    total_contribution = monthly_addition * months
    estimated_profit = balance - current_balance - total_contribution

    if estimated_profit < 0:
        estimated_profit = 0

    return {
        "years": years,
        "months": months,
        "current_balance": round(current_balance, 2),
        "monthly_addition": round(monthly_addition, 2),
        "total_contribution": round(total_contribution, 2),
        "estimated_profit": round(estimated_profit, 2),
        "projected_balance": round(balance, 2),
    }


def clean_asset_data(data):
    """
    Validate and clean asset data dictionary.
    """

    if not isinstance(data, dict):
        raise ValueError("Invalid asset data.")

    asset_type = str(data.get("asset_type", "")).strip()

    if asset_type not in ASSET_TYPES:
        raise ValueError(
            "Invalid asset type. Allowed: " + ", ".join(ASSET_TYPES)
        )

    account_name = str(data.get("account_name", "")).strip()

    if not account_name:
        raise ValueError("Account name is required.")

    institution = str(data.get("institution", "") or "").strip()
    start_date = str(data.get("start_date", "") or "").strip()
    last_updated = str(data.get("last_updated", "") or "").strip()
    remarks = str(data.get("remarks", "") or "").strip()

    current_balance = safe_float(data.get("current_balance", 0))
    monthly_contribution = safe_float(data.get("monthly_contribution", 0))
    employer_contribution = safe_float(data.get("employer_contribution", 0))

    if current_balance < 0:
        raise ValueError("Current balance cannot be negative.")

    if monthly_contribution < 0:
        raise ValueError("Monthly contribution cannot be negative.")

    if employer_contribution < 0:
        raise ValueError("Employer contribution cannot be negative.")

    is_active = data.get("is_active", 1)

    try:
        is_active = int(is_active)
    except (ValueError, TypeError):
        is_active = 1

    is_active = 1 if is_active == 1 else 0

    return {
        "asset_type": asset_type,
        "account_name": account_name,
        "institution": institution,
        "current_balance": current_balance,
        "monthly_contribution": monthly_contribution,
        "employer_contribution": employer_contribution,
        "start_date": start_date,
        "last_updated": last_updated,
        "remarks": remarks,
        "is_active": is_active,
    }


def clean_transaction_data(data):
    """
    Validate and clean transaction data dictionary.
    """

    if not isinstance(data, dict):
        raise ValueError("Invalid transaction data.")

    asset_id = data.get("asset_id", None)

    if asset_id is None:
        raise ValueError("Asset ID is required.")

    try:
        asset_id = int(asset_id)
    except (ValueError, TypeError):
        raise ValueError("Invalid asset ID.")

    transaction_type = str(
        data.get("transaction_type", "")
    ).strip()

    if transaction_type not in TRANSACTION_TYPES:
        raise ValueError(
            "Invalid transaction type. Allowed: "
            + ", ".join(TRANSACTION_TYPES)
        )

    amount = safe_float(data.get("amount", 0))

    if amount <= 0:
        raise ValueError("Transaction amount must be greater than zero.")

    transaction_date = str(
        data.get("transaction_date", "")
    ).strip()

    remarks = str(data.get("remarks", "") or "").strip()

    update_balance = bool(
        data.get("update_balance", True)
    )

    return {
        "asset_id": asset_id,
        "transaction_type": transaction_type,
        "amount": amount,
        "transaction_date": transaction_date,
        "remarks": remarks,
        "update_balance": update_balance,
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
