"""
Seed Portfolio Data
"""

from portfolio_db import add_holding, get_portfolio


def seed():

    if get_portfolio():
        print("Database already contains data.")
        return

    holdings = [

        ("MEBL", 100, 320, 378),
        ("FFC", 50, 390, 432),
        ("ENGROH", 25, 170, 186)

    ]

    for item in holdings:
        add_holding(*item)

    print("Portfolio seeded successfully.")


if __name__ == "__main__":
    seed()