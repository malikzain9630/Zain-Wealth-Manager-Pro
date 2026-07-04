"""
Dividend Database Operations
Handles dividend income records.
"""

from database import get_connection


def initialize_dividend_table():
    """
    Create dividends table if it does not already exist.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS dividends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            shares REAL NOT NULL,
            dividend_per_share REAL NOT NULL,
            gross_amount REAL NOT NULL,
            tax_amount REAL NOT NULL,
            net_amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            remarks TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_dividend(
    symbol,
    shares,
    dividend_per_share,
    gross_amount,
    tax_amount,
    net_amount,
    payment_date,
    remarks=""
):
    """
    Add a dividend income record.
    """

    initialize_dividend_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO dividends (
            symbol,
            shares,
            dividend_per_share,
            gross_amount,
            tax_amount,
            net_amount,
            payment_date,
            remarks
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        symbol,
        shares,
        dividend_per_share,
        gross_amount,
        tax_amount,
        net_amount,
        payment_date,
        remarks
    ))

    conn.commit()
    conn.close()


def get_dividends():
    """
    Return all dividend records.
    """

    initialize_dividend_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            symbol,
            shares,
            dividend_per_share,
            gross_amount,
            tax_amount,
            net_amount,
            payment_date,
            remarks
        FROM dividends
        ORDER BY payment_date DESC, id DESC
    """)

    rows = cur.fetchall()
    conn.close()

    dividends = []

    for row in rows:

        dividends.append({
            "id": row[0],
            "symbol": row[1],
            "shares": float(row[2]),
            "dividend_per_share": float(row[3]),
            "gross_amount": float(row[4]),
            "tax_amount": float(row[5]),
            "net_amount": float(row[6]),
            "payment_date": row[7],
            "remarks": row[8] if row[8] else ""
        })

    return dividends


def get_dividend_by_id(dividend_id):
    """
    Return one dividend record by ID.
    """

    initialize_dividend_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            symbol,
            shares,
            dividend_per_share,
            gross_amount,
            tax_amount,
            net_amount,
            payment_date,
            remarks
        FROM dividends
        WHERE id = ?
    """, (dividend_id,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "symbol": row[1],
        "shares": float(row[2]),
        "dividend_per_share": float(row[3]),
        "gross_amount": float(row[4]),
        "tax_amount": float(row[5]),
        "net_amount": float(row[6]),
        "payment_date": row[7],
        "remarks": row[8] if row[8] else ""
    }


def update_dividend(
    dividend_id,
    symbol,
    shares,
    dividend_per_share,
    gross_amount,
    tax_amount,
    net_amount,
    payment_date,
    remarks=""
):
    """
    Update an existing dividend record.
    """

    initialize_dividend_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE dividends
        SET
            symbol = ?,
            shares = ?,
            dividend_per_share = ?,
            gross_amount = ?,
            tax_amount = ?,
            net_amount = ?,
            payment_date = ?,
            remarks = ?
        WHERE id = ?
    """, (
        symbol,
        shares,
        dividend_per_share,
        gross_amount,
        tax_amount,
        net_amount,
        payment_date,
        remarks,
        dividend_id
    ))

    conn.commit()
    conn.close()


def delete_dividend(dividend_id):
    """
    Delete a dividend record.
    """

    initialize_dividend_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM dividends
        WHERE id = ?
    """, (dividend_id,))

    conn.commit()
    conn.close()


def get_dividend_summary():
    """
    Return dividend income summary.
    """

    initialize_dividend_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(gross_amount), 0),
            COALESCE(SUM(tax_amount), 0),
            COALESCE(SUM(net_amount), 0)
        FROM dividends
    """)

    row = cur.fetchone()
    conn.close()

    return {
        "total_records": int(row[0]),
        "gross_amount": float(row[1]),
        "tax_amount": float(row[2]),
        "net_amount": float(row[3])
    }


def get_dividend_summary_by_symbol():
    """
    Return dividend summary grouped by stock symbol.
    """

    initialize_dividend_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            symbol,
            COUNT(*),
            COALESCE(SUM(gross_amount), 0),
            COALESCE(SUM(tax_amount), 0),
            COALESCE(SUM(net_amount), 0)
        FROM dividends
        GROUP BY symbol
        ORDER BY net_amount DESC
    """)

    rows = cur.fetchall()
    conn.close()

    summary = []

    for row in rows:

        summary.append({
            "symbol": row[0],
            "records": int(row[1]),
            "gross_amount": float(row[2]),
            "tax_amount": float(row[3]),
            "net_amount": float(row[4])
        })

    return summary


def get_dividend_summary_by_year():
    """
    Return dividend summary grouped by year.
    """

    initialize_dividend_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            substr(payment_date, 1, 4) AS year,
            COUNT(*),
            COALESCE(SUM(gross_amount), 0),
            COALESCE(SUM(tax_amount), 0),
            COALESCE(SUM(net_amount), 0)
        FROM dividends
        GROUP BY year
        ORDER BY year DESC
    """)

    rows = cur.fetchall()
    conn.close()

    summary = []

    for row in rows:

        summary.append({
            "year": row[0],
            "records": int(row[1]),
            "gross_amount": float(row[2]),
            "tax_amount": float(row[3]),
            "net_amount": float(row[4])
        })

    return summary


def get_dividend_summary_by_month():
    """
    Return dividend summary grouped by month.
    """

    initialize_dividend_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            substr(payment_date, 1, 7) AS month,
            COUNT(*),
            COALESCE(SUM(gross_amount), 0),
            COALESCE(SUM(tax_amount), 0),
            COALESCE(SUM(net_amount), 0)
        FROM dividends
        GROUP BY month
        ORDER BY month DESC
    """)

    rows = cur.fetchall()
    conn.close()

    summary = []

    for row in rows:

        summary.append({
            "month": row[0],
            "records": int(row[1]),
            "gross_amount": float(row[2]),
            "tax_amount": float(row[3]),
            "net_amount": float(row[4])
        })

    return summary