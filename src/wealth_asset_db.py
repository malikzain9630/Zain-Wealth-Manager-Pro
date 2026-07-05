"""
Wealth Asset Database
Database layer for Phase 10:
- Provident Fund
- Pension / MTPF
- Bank Cash
- Other manual wealth assets

Important rule:
- All balances and transactions are stored in PKR.
- Display currency conversion happens in GUI/reports through currency_service.
"""

import sqlite3
from pathlib import Path
from datetime import datetime


DATABASE_NAME = "wealth_manager.db"

ASSET_TYPES = [
    "Provident Fund",
    "Pension / MTPF",
    "Bank Cash",
    "Other",
]

TRANSACTION_TYPES = [
    "Contribution",
    "Employer Contribution",
    "Profit",
    "Withdrawal",
    "Adjustment",
]


def get_database_path():
    """
    Return database path.

    The app usually runs from project root.
    This fallback keeps DB path stable even if run from src folder.
    """

    src_folder = Path(__file__).resolve().parent
    project_root = src_folder.parent

    root_db = project_root / DATABASE_NAME
    src_db = src_folder / DATABASE_NAME

    if root_db.exists():
        return root_db

    if src_db.exists():
        return src_db

    return root_db


def get_connection():
    """
    Return SQLite connection.
    """

    return sqlite3.connect(get_database_path())


def initialize_wealth_asset_tables():
    """
    Create wealth asset tables if they do not exist.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wealth_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_type TEXT NOT NULL,
            account_name TEXT NOT NULL,
            institution TEXT,
            current_balance REAL NOT NULL DEFAULT 0,
            monthly_contribution REAL NOT NULL DEFAULT 0,
            employer_contribution REAL NOT NULL DEFAULT 0,
            start_date TEXT,
            last_updated TEXT,
            remarks TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wealth_asset_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL DEFAULT 0,
            transaction_date TEXT NOT NULL,
            remarks TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (asset_id) REFERENCES wealth_assets(id)
                ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def add_wealth_asset(
    asset_type,
    account_name,
    institution="",
    current_balance=0,
    monthly_contribution=0,
    employer_contribution=0,
    start_date="",
    last_updated="",
    remarks="",
):
    """
    Add a new wealth asset.
    """

    initialize_wealth_asset_tables()

    asset_type = validate_asset_type(asset_type)
    account_name = str(account_name).strip()
    institution = str(institution or "").strip()
    start_date = str(start_date or "").strip()
    last_updated = str(last_updated or "").strip()
    remarks = str(remarks or "").strip()

    if not account_name:
        raise ValueError("Account name is required.")

    current_balance = safe_float(current_balance)
    monthly_contribution = safe_float(monthly_contribution)
    employer_contribution = safe_float(employer_contribution)

    if current_balance < 0:
        raise ValueError("Current balance cannot be negative.")

    if monthly_contribution < 0:
        raise ValueError("Monthly contribution cannot be negative.")

    if employer_contribution < 0:
        raise ValueError("Employer contribution cannot be negative.")

    now = get_now_text()

    if not last_updated:
        last_updated = now[:10]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO wealth_assets (
            asset_type,
            account_name,
            institution,
            current_balance,
            monthly_contribution,
            employer_contribution,
            start_date,
            last_updated,
            remarks,
            is_active,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
    """, (
        asset_type,
        account_name,
        institution,
        current_balance,
        monthly_contribution,
        employer_contribution,
        start_date,
        last_updated,
        remarks,
        now,
        now,
    ))

    conn.commit()
    asset_id = cursor.lastrowid
    conn.close()

    return asset_id


def update_wealth_asset(
    asset_id,
    asset_type,
    account_name,
    institution="",
    current_balance=0,
    monthly_contribution=0,
    employer_contribution=0,
    start_date="",
    last_updated="",
    remarks="",
    is_active=1,
):
    """
    Update an existing wealth asset.
    """

    initialize_wealth_asset_tables()

    asset_id = int(asset_id)
    asset_type = validate_asset_type(asset_type)
    account_name = str(account_name).strip()
    institution = str(institution or "").strip()
    start_date = str(start_date or "").strip()
    last_updated = str(last_updated or "").strip()
    remarks = str(remarks or "").strip()

    if not account_name:
        raise ValueError("Account name is required.")

    current_balance = safe_float(current_balance)
    monthly_contribution = safe_float(monthly_contribution)
    employer_contribution = safe_float(employer_contribution)

    if current_balance < 0:
        raise ValueError("Current balance cannot be negative.")

    if monthly_contribution < 0:
        raise ValueError("Monthly contribution cannot be negative.")

    if employer_contribution < 0:
        raise ValueError("Employer contribution cannot be negative.")

    is_active = 1 if int(is_active) == 1 else 0

    now = get_now_text()

    if not last_updated:
        last_updated = now[:10]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE wealth_assets
        SET
            asset_type = ?,
            account_name = ?,
            institution = ?,
            current_balance = ?,
            monthly_contribution = ?,
            employer_contribution = ?,
            start_date = ?,
            last_updated = ?,
            remarks = ?,
            is_active = ?,
            updated_at = ?
        WHERE id = ?
    """, (
        asset_type,
        account_name,
        institution,
        current_balance,
        monthly_contribution,
        employer_contribution,
        start_date,
        last_updated,
        remarks,
        is_active,
        now,
        asset_id,
    ))

    conn.commit()
    conn.close()


def delete_wealth_asset(asset_id):
    """
    Delete a wealth asset and its transactions.
    """

    initialize_wealth_asset_tables()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM wealth_assets WHERE id = ?",
        (int(asset_id),)
    )

    conn.commit()
    conn.close()


def get_wealth_assets(include_inactive=False):
    """
    Return all wealth assets.
    """

    initialize_wealth_asset_tables()

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if include_inactive:
        cursor.execute("""
            SELECT *
            FROM wealth_assets
            ORDER BY asset_type, account_name
        """)
    else:
        cursor.execute("""
            SELECT *
            FROM wealth_assets
            WHERE is_active = 1
            ORDER BY asset_type, account_name
        """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_wealth_asset_by_id(asset_id):
    """
    Return one wealth asset by ID.
    """

    initialize_wealth_asset_tables()

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM wealth_assets WHERE id = ?",
        (int(asset_id),)
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)

    return None


def add_wealth_asset_transaction(
    asset_id,
    transaction_type,
    amount,
    transaction_date,
    remarks="",
    update_balance=True,
):
    """
    Add transaction for a wealth asset.

    If update_balance=True:
        Contribution / Employer Contribution / Profit / Adjustment increase balance.
        Withdrawal decreases balance.
    """

    initialize_wealth_asset_tables()

    asset_id = int(asset_id)
    transaction_type = validate_transaction_type(transaction_type)
    amount = safe_float(amount)
    transaction_date = str(transaction_date or "").strip()
    remarks = str(remarks or "").strip()

    if amount <= 0:
        raise ValueError("Transaction amount must be greater than zero.")

    if not transaction_date:
        transaction_date = datetime.now().strftime("%Y-%m-%d")

    asset = get_wealth_asset_by_id(asset_id)

    if not asset:
        raise ValueError("Selected asset was not found.")

    now = get_now_text()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO wealth_asset_transactions (
            asset_id,
            transaction_type,
            amount,
            transaction_date,
            remarks,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        asset_id,
        transaction_type,
        amount,
        transaction_date,
        remarks,
        now,
    ))

    if update_balance:

        current_balance = safe_float(asset["current_balance"])

        if transaction_type == "Withdrawal":
            current_balance -= amount
        else:
            current_balance += amount

        if current_balance < 0:
            current_balance = 0

        cursor.execute("""
            UPDATE wealth_assets
            SET
                current_balance = ?,
                last_updated = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            current_balance,
            transaction_date,
            now,
            asset_id,
        ))

    conn.commit()
    transaction_id = cursor.lastrowid
    conn.close()

    return transaction_id


def delete_wealth_asset_transaction(transaction_id, reverse_balance=False):
    """
    Delete a wealth asset transaction.

    reverse_balance=False by default for safety.
    """

    initialize_wealth_asset_tables()

    transaction = get_wealth_asset_transaction_by_id(transaction_id)

    if not transaction:
        return

    conn = get_connection()
    cursor = conn.cursor()

    if reverse_balance:

        asset = get_wealth_asset_by_id(transaction["asset_id"])

        if asset:
            current_balance = safe_float(asset["current_balance"])
            amount = safe_float(transaction["amount"])

            if transaction["transaction_type"] == "Withdrawal":
                current_balance += amount
            else:
                current_balance -= amount

            if current_balance < 0:
                current_balance = 0

            cursor.execute("""
                UPDATE wealth_assets
                SET current_balance = ?, updated_at = ?
                WHERE id = ?
            """, (
                current_balance,
                get_now_text(),
                transaction["asset_id"],
            ))

    cursor.execute(
        "DELETE FROM wealth_asset_transactions WHERE id = ?",
        (int(transaction_id),)
    )

    conn.commit()
    conn.close()


def get_wealth_asset_transactions(asset_id=None):
    """
    Return wealth asset transactions.
    """

    initialize_wealth_asset_tables()

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if asset_id is None:
        cursor.execute("""
            SELECT
                t.*,
                a.asset_type,
                a.account_name,
                a.institution
            FROM wealth_asset_transactions t
            LEFT JOIN wealth_assets a ON a.id = t.asset_id
            ORDER BY t.transaction_date DESC, t.id DESC
        """)
    else:
        cursor.execute("""
            SELECT
                t.*,
                a.asset_type,
                a.account_name,
                a.institution
            FROM wealth_asset_transactions t
            LEFT JOIN wealth_assets a ON a.id = t.asset_id
            WHERE t.asset_id = ?
            ORDER BY t.transaction_date DESC, t.id DESC
        """, (int(asset_id),))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_wealth_asset_transaction_by_id(transaction_id):
    """
    Return one transaction by ID.
    """

    initialize_wealth_asset_tables()

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM wealth_asset_transactions
        WHERE id = ?
    """, (int(transaction_id),))

    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)

    return None


def get_wealth_asset_summary():
    """
    Return total balance summary by asset type.
    """

    initialize_wealth_asset_tables()

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            asset_type,
            COUNT(*) AS records,
            SUM(current_balance) AS total_balance,
            SUM(monthly_contribution) AS monthly_contribution,
            SUM(employer_contribution) AS employer_contribution
        FROM wealth_assets
        WHERE is_active = 1
        GROUP BY asset_type
        ORDER BY asset_type
    """)

    rows = cursor.fetchall()
    conn.close()

    summary_rows = []

    for row in rows:

        summary_rows.append({
            "asset_type": row["asset_type"],
            "records": int(row["records"] or 0),
            "total_balance": safe_float(row["total_balance"]),
            "monthly_contribution": safe_float(row["monthly_contribution"]),
            "employer_contribution": safe_float(row["employer_contribution"]),
        })

    return summary_rows


def get_total_wealth_asset_balance():
    """
    Return total current balance of all active wealth assets.
    """

    summary_rows = get_wealth_asset_summary()
    total = 0

    for item in summary_rows:
        total += safe_float(item["total_balance"])

    return round(total, 2)


def validate_asset_type(asset_type):
    """
    Validate asset type.
    """

    asset_type = str(asset_type or "").strip()

    if asset_type not in ASSET_TYPES:
        raise ValueError(
            "Invalid asset type. Allowed: " + ", ".join(ASSET_TYPES)
        )

    return asset_type


def validate_transaction_type(transaction_type):
    """
    Validate transaction type.
    """

    transaction_type = str(transaction_type or "").strip()

    if transaction_type not in TRANSACTION_TYPES:
        raise ValueError(
            "Invalid transaction type. Allowed: " + ", ".join(TRANSACTION_TYPES)
        )

    return transaction_type


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


def get_now_text():
    """
    Return current datetime text.
    """

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
