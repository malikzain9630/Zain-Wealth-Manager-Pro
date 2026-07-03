"""
AI Investment Advisor
"""

from utils import (
    get_summary,
    get_goal_progress,
    get_health_score,
    get_performance
)


def generate_advice():

    summary = get_summary()
    goal = get_goal_progress()
    health = get_health_score()
    performance = get_performance()

    advice = []

    # Health Score
    if health >= 80:
        advice.append("Excellent portfolio health.")
    elif health >= 60:
        advice.append("Portfolio is healthy but can be improved.")
    else:
        advice.append("Improve diversification and increase investments.")

    # Goal Progress
    if goal["progress"] >= 75:
        advice.append("You are close to achieving your financial goal.")
    else:
        advice.append(
            f'Goal progress is {goal["progress"]}%. Continue regular investing.'
        )

    # Dividend Yield
    if performance["dividend_yield"] >= 5:
        advice.append("Dividend income is strong.")
    else:
        advice.append("Consider increasing dividend-paying investments.")

    # Profit
    if summary["profit"] > 0:
        advice.append("Portfolio is currently in profit.")
    else:
        advice.append("Portfolio is currently below cost. Stay invested.")

    return advice