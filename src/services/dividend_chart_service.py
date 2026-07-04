"""
Dividend Chart Service
Prepares dividend income data for charts.
"""

from services.dividend_service import (
    get_income_summary,
    get_income_summary_by_symbol,
    get_income_summary_by_month,
    get_income_summary_by_year,
)


def get_stock_wise_dividend_data():
    """
    Return stock-wise dividend data for pie/bar charts.

    Format:
    {
        "labels": ["FFC", "MEBL"],
        "values": [5000, 3000]
    }
    """

    summary = get_income_summary_by_symbol()

    labels = []
    values = []

    for item in summary:

        symbol = str(item["symbol"]).upper()
        net_amount = float(item["net_amount"])

        if net_amount > 0:
            labels.append(symbol)
            values.append(net_amount)

    return {
        "labels": labels,
        "values": values
    }


def get_monthly_dividend_data():
    """
    Return monthly dividend income data.

    Format:
    {
        "labels": ["2026-06", "2026-07"],
        "values": [5000, 3000]
    }
    """

    summary = get_income_summary_by_month()

    rows = []

    for item in summary:

        month = str(item["month"])
        net_amount = float(item["net_amount"])

        rows.append({
            "month": month,
            "net_amount": net_amount
        })

    rows.sort(key=lambda item: item["month"])

    labels = []
    values = []

    for item in rows:

        labels.append(item["month"])
        values.append(item["net_amount"])

    return {
        "labels": labels,
        "values": values
    }


def get_yearly_dividend_data():
    """
    Return yearly dividend income data.

    Format:
    {
        "labels": ["2025", "2026"],
        "values": [15000, 25000]
    }
    """

    summary = get_income_summary_by_year()

    rows = []

    for item in summary:

        year = str(item["year"])
        net_amount = float(item["net_amount"])

        rows.append({
            "year": year,
            "net_amount": net_amount
        })

    rows.sort(key=lambda item: item["year"])

    labels = []
    values = []

    for item in rows:

        labels.append(item["year"])
        values.append(item["net_amount"])

    return {
        "labels": labels,
        "values": values
    }


def get_tax_vs_net_data():
    """
    Return tax vs net received data.

    Format:
    {
        "labels": ["Tax Deducted", "Net Received"],
        "values": [2000, 15000]
    }
    """

    summary = get_income_summary()

    tax_amount = float(summary["tax_amount"])
    net_amount = float(summary["net_amount"])

    labels = []
    values = []

    if tax_amount > 0:
        labels.append("Tax Deducted")
        values.append(tax_amount)

    if net_amount > 0:
        labels.append("Net Received")
        values.append(net_amount)

    return {
        "labels": labels,
        "values": values
    }


def get_dividend_chart_summary():
    """
    Return overall dividend summary for chart window.
    """

    summary = get_income_summary()

    gross_amount = float(summary["gross_amount"])
    tax_amount = float(summary["tax_amount"])
    net_amount = float(summary["net_amount"])
    total_records = int(summary["total_records"])

    if gross_amount > 0:
        tax_percent = (tax_amount / gross_amount) * 100
        net_percent = (net_amount / gross_amount) * 100
    else:
        tax_percent = 0
        net_percent = 0

    return {
        "gross_amount": round(gross_amount, 2),
        "tax_amount": round(tax_amount, 2),
        "net_amount": round(net_amount, 2),
        "total_records": total_records,
        "tax_percent": round(tax_percent, 2),
        "net_percent": round(net_percent, 2),
    }
