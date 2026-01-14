#!/usr/bin/env python3
"""Safe Travels MCP Server - Exposes route derivation and danger assessment tools."""

from fastmcp import FastMCP

from danger_assessment import (
    temperature_severity,
    weather_conditions_severity,
    wind_severity,
)
from routing import compute_route, get_lat_long, pick_equidistant_points

import polyline
import requests


def weather_code_to_condition(code: int) -> str:
    """Map Open-Meteo weather codes to condition strings."""
    if code in [0, 1]:
        return "sunny"
    if code in [2, 3]:
        return "cloudy"
    if code in [45, 48]:
        return "foggy"
    if code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
        return "rainy"
    if code in [71, 73, 75, 77, 85, 86]:
        return "snowy"
    if code == 95:
        return "stormy"
    if code in [96, 99]:
        return "hail"
    return "cloudy"


def fetch_weather_for_waypoints(
    waypoints: list[tuple[float, float]],
) -> list[dict]:
    """Fetch current weather for multiple waypoints using Open-Meteo API."""
    lats = ",".join(str(wp[0]) for wp in waypoints)
    lons = ",".join(str(wp[1]) for wp in waypoints)

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lats}&longitude={lons}"
        f"&current=temperature_2m,wind_speed_10m,wind_gusts_10m,weather_code"
    )
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    # Handle single vs multiple waypoints (API returns dict vs list)
    if isinstance(data, dict) and "current" in data:
        data = [data]

    results = []
    for i, wp in enumerate(waypoints):
        current = data[i]["current"]
        results.append({
            "lat": wp[0],
            "lon": wp[1],
            "temp_c": current["temperature_2m"],
            "wind_kph": current["wind_speed_10m"],
            "gust_kph": current["wind_gusts_10m"],
            "condition": weather_code_to_condition(current["weather_code"]),
        })

    return results

mcp = FastMCP("safe-travels")


@mcp.tool
def derive_route(
    origin: str,
    destination: str,
    departure_time: str | None = None,
    arrival_time: str | None = None,
) -> list[tuple[float, float]]:
    """
    Derive a route between two cities.

    Args:
        origin: Starting city (e.g. "Denver, CO")
        destination: Destination city (e.g. "Boulder, CO")
        departure_time: Optional departure time in RFC3339 or parseable format
        arrival_time: Optional arrival time in RFC3339 or parseable format

    Returns:
        List of (latitude, longitude) tuples representing equidistant waypoints along the route
    """
    origin_coords = get_lat_long(origin)
    destination_coords = get_lat_long(destination)

    route = compute_route(origin_coords, destination_coords, departure_time, arrival_time)

    encoded_polyline = route["routes"][0]["polyline"]["encodedPolyline"]
    points = polyline.decode(encoded_polyline)

    return pick_equidistant_points(points)


@mcp.tool
def assess_danger(
    temp_c: float,
    wind_kph: float,
    condition: str,
    gust_kph: float = 0.0,
) -> float:
    """
    Compute the danger score for weather conditions at a point.

    Args:
        temp_c: Temperature in Celsius
        wind_kph: Wind speed in kilometers per hour
        condition: Weather condition (e.g. "sunny", "rainy", "snowy", "foggy", "blizzard")
        gust_kph: Wind gust speed in kilometers per hour (optional)

    Returns:
        Danger score as a float. Higher values indicate more dangerous conditions.
        - 0-2: Safe conditions
        - 2-5: Moderate caution advised
        - 5-10: Hazardous conditions
        - 10+: Extremely dangerous
    """
    weather_modifier = weather_conditions_severity.get(condition.lower(), 0.0)
    temp_modifier = temperature_severity(temp_c)
    wind_modifier = wind_severity(wind_kph)
    gust_modifier = wind_severity(gust_kph)

    max_wind_modifier = max(gust_modifier, wind_modifier)

    return weather_modifier + temp_modifier + max_wind_modifier


@mcp.tool
def assess_route_danger(
    origin: str,
    destination: str,
    departure_time: str | None = None,
    arrival_time: str | None = None,
) -> dict:
    """
    Compute the danger assessment for an entire route, including weather conditions.

    This combines route derivation, weather fetching, and danger assessment into
    a single operation.

    Args:
        origin: Starting city (e.g. "Grayson, GA")
        destination: Destination city (e.g. "Dahlonega, GA")
        departure_time: Optional departure time (e.g. "2026-01-23T07:00:00")
        arrival_time: Optional arrival time (e.g. "2026-01-23T10:00:00")

    Returns:
        Dictionary containing:
        - origin: Starting location
        - destination: Ending location
        - waypoints: List of waypoint assessments with lat, lon, weather, and danger score
        - average_danger: Average danger score across all waypoints
        - max_danger: Maximum danger score encountered
        - status: Overall safety status (SAFE, MODERATE, HAZARDOUS, EXTREME)
    """
    # Step 1: Derive the route
    origin_coords = get_lat_long(origin)
    destination_coords = get_lat_long(destination)
    route = compute_route(origin_coords, destination_coords, departure_time, arrival_time)
    encoded_polyline = route["routes"][0]["polyline"]["encodedPolyline"]
    points = polyline.decode(encoded_polyline)
    waypoints = pick_equidistant_points(points)

    # Step 2: Fetch weather for all waypoints
    weather_data = fetch_weather_for_waypoints(waypoints)

    # Step 3: Assess danger at each waypoint
    waypoint_results = []
    danger_scores = []

    for wd in weather_data:
        danger_score = assess_danger(
            temp_c=wd["temp_c"],
            wind_kph=wd["wind_kph"],
            condition=wd["condition"],
            gust_kph=wd["gust_kph"],
        )

        danger_scores.append(danger_score)
        waypoint_results.append({
            "lat": wd["lat"],
            "lon": wd["lon"],
            "temp_c": wd["temp_c"],
            "wind_kph": wd["wind_kph"],
            "gust_kph": wd["gust_kph"],
            "condition": wd["condition"],
            "danger_score": round(danger_score, 2),
        })

    # Step 4: Compute overall assessment
    avg_danger = sum(danger_scores) / len(danger_scores)
    max_danger = max(danger_scores)

    if max_danger < 2:
        status = "SAFE"
    elif max_danger < 5:
        status = "MODERATE"
    elif max_danger < 10:
        status = "HAZARDOUS"
    else:
        status = "EXTREME"

    return {
        "origin": origin,
        "destination": destination,
        "waypoints": waypoint_results,
        "average_danger": round(avg_danger, 2),
        "max_danger": round(max_danger, 2),
        "status": status,
    }


if __name__ == "__main__":
    mcp.run()
