"""
Portfolio Allocation Analysis
"""

from utils import get_summary


def get_allocation_analysis():

    summary = get_summary()

    allocation = summary["allocation"]
    total = sum(allocation.values())

    result = []

    for asset, value in allocation.items():

        percent = round((value / total) * 100, 2) if total else 0

        if percent >= 30:
            status = "Good"
        elif percent >= 15:
            status = "Average"
        else:
            status = "Increase"

        result.append({
            "asset": asset,
            "value": value,
            "percent": percent,
            "status": status
        })

    return result