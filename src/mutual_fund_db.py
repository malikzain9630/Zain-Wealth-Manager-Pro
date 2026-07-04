"""
Mutual Fund Database Operations
"""

from database import get_connection


def initialize_mutual_fund_table():
    """
    Create mutual_funds table if it does not already exist.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS mutual_funds (
            fund TEXT PRIMARY KEY,
            units REAL NOT NULL,
            avg_nav REAL NOT NULL,
            current_nav REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def add_mutual_fund(fund, units, avg_nav, current_nav):
    """
    Add a new mutual fund.
    """

    initialize_mutual_fund_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO mutual_funds
        (fund, units, avg_nav, current_nav)
        VALUES (?, ?, ?, ?)
    """, (fund, units, avg_nav, current_nav))

    conn.commit()
    conn.close()


def get_mutual_funds():
    """
    Return all mutual funds.
    """

    initialize_mutual_fund_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT fund, units, avg_nav, current_nav
        FROM mutual_funds
        ORDER BY fund
    """)

    rows = cur.fetchall()
    conn.close()

    funds = []

    for row in rows:

        units = float(row[1])
        avg_nav = float(row[2])
        current_nav = float(row[3])

        investment_value = units * avg_nav
        current_value = units * current_nav
        profit_loss = current_value - investment_value

        if investment_value > 0:
            profit_percent = (profit_loss / investment_value) * 100
        else:
            profit_percent = 0

        funds.append({
            "fund": row[0],
            "units": units,
            "avg_nav": avg_nav,
            "current_nav": current_nav,
            "investment_value": investment_value,
            "current_value": current_value,
            "profit_loss": profit_loss,
            "profit_percent": profit_percent
        })

    return funds


def update_mutual_fund(fund, units, avg_nav, current_nav):
    """
    Update an existing mutual fund.
    """

    initialize_mutual_fund_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE mutual_funds
        SET units = ?,
            avg_nav = ?,
            current_nav = ?
        WHERE fund = ?
    """, (units, avg_nav, current_nav, fund))

    conn.commit()
    conn.close()


def delete_mutual_fund(fund):
    """
    Delete a mutual fund.
    """

    initialize_mutual_fund_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM mutual_funds
        WHERE fund = ?
    """, (fund,))

    conn.commit()
    conn.close()


def get_mutual_fund_by_name(fund):
    """
    Return one mutual fund by name.
    """

    initialize_mutual_fund_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT fund, units, avg_nav, current_nav
        FROM mutual_funds
        WHERE fund = ?
    """, (fund,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    units = float(row[1])
    avg_nav = float(row[2])
    current_nav = float(row[3])

    investment_value = units * avg_nav
    current_value = units * current_nav
    profit_loss = current_value - investment_value

    if investment_value > 0:
        profit_percent = (profit_loss / investment_value) * 100
    else:
        profit_percent = 0

    return {
        "fund": row[0],
        "units": units,
        "avg_nav": avg_nav,
        "current_nav": current_nav,
        "investment_value": investment_value,
        "current_value": current_value,
        "profit_loss": profit_loss,
        "profit_percent": profit_percent
    }


def seed_mutual_funds_if_empty():
    """
    Seed mutual funds from old static data if database table is empty.

    Old data has:
        fund
        units
        value

    We calculate:
        current_nav = value / units
        avg_nav = current_nav

    This keeps old data compatible.
    """

    initialize_mutual_fund_table()

    existing = get_mutual_funds()

    if existing:
        return

    try:
        from data.mutual_funds import MUTUAL_FUNDS

        for item in MUTUAL_FUNDS:

            fund = str(item["fund"]).strip()
            units = float(item["units"])
            value = float(item["value"])

            if units <= 0:
                continue

            current_nav = value / units
            avg_nav = current_nav

            add_mutual_fund(
                fund,
                units,
                avg_nav,
                current_nav
            )

    except Exception:
        pass