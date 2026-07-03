"""
SQLite Database Manager
"""

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "wealth_manager.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_database():

    conn = get_connection()
    cur = conn.cursor()

    # ----------------------------
    # Portfolio Table
    # ----------------------------

    cur.execute("""
    CREATE TABLE IF NOT EXISTS portfolio (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        symbol TEXT NOT NULL,

        shares REAL NOT NULL,

        avg_price REAL NOT NULL,

        current_price REAL NOT NULL

    )
    """)

    # ----------------------------
    # Transactions Table
    # ----------------------------

    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        trans_date TEXT,

        symbol TEXT,

        trans_type TEXT,

        quantity REAL,

        price REAL

    )
    """)

    conn.commit()
    conn.close()