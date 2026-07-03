"""
Portfolio Rebalancing Engine
"""

from allocation import get_allocation_analysis
from data.target_allocation import TARGET_ALLOCATION


def get_rebalancing_plan():

    plan = []

    for item in get_allocation_analysis():

        asset = item["asset"]
        current = item["percent"]
        target = TARGET_ALLOCATION.get(asset, 0)

        difference = round(current - target, 2)

        if difference > 5:
            action = "Reduce"

        elif difference < -5:
            action = "Increase"

        else:
            action = "Maintain"

        plan.append({

            "asset": asset,

            "current": current,

            "target": target,

            "difference": difference,

            "action": action

        })

    return plan