"""
Portfolio Database Operations
"""

from database import get_connection


def add_holding(symbol, shares, avg_price, current_price):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO portfolio
        (symbol, shares, avg_price, current_price)
        VALUES (?, ?, ?, ?)
    """, (symbol, shares, avg_price, current_price))

    conn.commit()
    conn.close()


def get_portfolio():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT symbol, shares, avg_price, current_price
        FROM portfolio
    """)

    rows = cur.fetchall()

    conn.close()

    portfolio = []

    for row in rows:

        portfolio.append({
            "symbol": row[0],
            "shares": row[1],
            "avg": row[2],
            "current": row[3]
        })

    return portfolio

def update_holding(symbol, shares, avg_price, current_price):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE portfolio
        SET shares=?,
            avg_price=?,
            current_price=?
        WHERE symbol=?
    """, (shares, avg_price, current_price, symbol))

    conn.commit()
    conn.close()


def delete_holding(symbol):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM portfolio WHERE symbol=?",
        (symbol,)
    )

    conn.commit()
    conn.close()