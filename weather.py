from typing import Any

from langchain_core.tools import tool


@tool
def compute_route_danger_score(route: list[dict[str, Any]]) -> float:
    """
    Compute the danger score of a route.

    Args:
        route (dict[str, Any]): The route to compute the danger score for.

    Returns:
        float: The danger score of the route.
    """
    print("Compute route danger score...")

    return 0.0