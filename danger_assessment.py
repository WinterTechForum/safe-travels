from typing import Any

from langchain_core.tools import tool

weather_conditions_severity: dict[str, int] = {
    'sunny': 0,
    'cloudy': 0,
    'overcast': 0,
    'partly cloudy': 0,
    'partly sunny': 0,
    'rainy': 2,
    'snowy': 3,
    'foggy': 4,
    'windy': 5,
    'stormy': 6,
    'hail': 7,
    'tornado': 10,
    'hurricane': 10,
    'blizzard': 10,
}


# write a function to take a temperature in C and return a severity score
# with higher temperatures having lower severity scores
def temperature_severity(temp: float) -> float:
    if temp < 0:
        return abs(temp) / 10 + 1
    elif temp < 30:
        return 0
    else:
        return (temp - 30) / 10 + 1


def wind_severity(kph: int) -> float:
    return kph / 16


@tool
def assess_danger(point: dict[str, Any] | None = None) -> float:
    """
    Compute the danger score of a point based on the weather information.

    Args:
        point (dict[str, Any]): A point on a route to compute the danger score for.

    Returns:
        float: The danger score of the point.
    """
    if point is None:
        return 0.0

    weather_condition_modifier = weather_conditions_severity.get(point['condition'].lower(), 0.0)
    temperature_modifier = temperature_severity(point.get('temp_c', 0))
    wind_modifier = wind_severity(point.get('wind_mph', 0))
    gust_modifier = wind_severity(point.get('gust_mph', 0))

    max_wind_modifier = max(gust_modifier, wind_modifier)

    return weather_condition_modifier + temperature_modifier + max_wind_modifier
