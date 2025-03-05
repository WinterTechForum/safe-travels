from typing import Any

from langchain_core.tools import tool


@tool
def assess_danger(point: dict[str, Any] | None = None) -> float:
    """
    Compute the danger score of a point based on the weather information.

    Args:
        point (dict[str, Any]): A point on a route to compute the danger score for.

    Returns:
        float: The danger score of the point.
    """
    print('Compute route danger score...')
    print(point)

    return 0.0