#!/usr/bin/env python3
"""Safe Travels MCP Server - Exposes route derivation and danger assessment tools."""

from datetime import datetime, timedelta, timezone

from fastmcp import FastMCP

from danger_assessment import (
    temperature_severity,
    weather_conditions_severity,
    wind_severity,
)
from routing import (
    compute_route,
    get_lat_long,
    get_route_duration_seconds,
    pick_equidistant_points,
)

import dateutil.parser
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
    waypoints: list[tuple[float, float, datetime]],
) -> list[dict]:
    """Fetch forecast weather for waypoints at their expected arrival times.

    Args:
        waypoints: List of (lat, lon, arrival_time) tuples
    """
    lats = ",".join(str(wp[0]) for wp in waypoints)
    lons = ",".join(str(wp[1]) for wp in waypoints)

    # Determine time range needed for forecast
    timestamps = [wp[2] for wp in waypoints]
    min_time = min(timestamps)
    max_time = max(timestamps)

    # Format for Open-Meteo API (ISO8601)
    start_hour = min_time.strftime("%Y-%m-%dT%H:00")
    end_hour = (max_time + timedelta(hours=1)).strftime("%Y-%m-%dT%H:00")

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lats}&longitude={lons}"
        f"&hourly=temperature_2m,wind_speed_10m,wind_gusts_10m,weather_code"
        f"&start_hour={start_hour}&end_hour={end_hour}"
    )
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    # Handle single vs multiple waypoints (API returns dict vs list)
    if isinstance(data, dict) and "hourly" in data:
        data = [data]

    results = []
    for i, (lat, lon, arrival_time) in enumerate(waypoints):
        hourly = data[i]["hourly"]
        # Find the closest hour in the forecast
        times = [datetime.fromisoformat(t) for t in hourly["time"]]
        closest_idx = min(
            range(len(times)),
            key=lambda j: abs((times[j] - arrival_time.replace(tzinfo=None)).total_seconds())
        )

        results.append({
            "lat": lat,
            "lon": lon,
            "arrival_time": arrival_time.isoformat(),
            "temp_c": hourly["temperature_2m"][closest_idx],
            "wind_kph": hourly["wind_speed_10m"][closest_idx],
            "gust_kph": hourly["wind_gusts_10m"][closest_idx],
            "condition": weather_code_to_condition(hourly["weather_code"][closest_idx]),
        })

    return results

def _compute_danger_score(
    temp_c: float,
    wind_kph: float,
    condition: str,
    gust_kph: float = 0.0,
) -> float:
    """Compute danger score from weather conditions."""
    weather_modifier = weather_conditions_severity.get(condition.lower(), 0.0)
    temp_modifier = temperature_severity(temp_c)
    wind_modifier = wind_severity(wind_kph)
    gust_modifier = wind_severity(gust_kph)

    max_wind_modifier = max(gust_modifier, wind_modifier)

    return weather_modifier + temp_modifier + max_wind_modifier


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
def assess_route_danger(
    origin: str,
    destination: str,
    departure_time: str | None = None,
    arrival_time: str | None = None,
) -> dict:
    """
    Compute the danger assessment for an entire route, including weather conditions.

    This combines route derivation, weather fetching, and danger assessment into
    a single operation. Weather forecasts are fetched for each waypoint's expected
    arrival time based on departure time and route duration.

    Args:
        origin: Starting city (e.g. "Grayson, GA")
        destination: Destination city (e.g. "Dahlonega, GA")
        departure_time: Optional departure time (e.g. "2026-01-23T07:00:00")
        arrival_time: Optional arrival time (e.g. "2026-01-23T10:00:00")

    Returns:
        Dictionary containing:
        - origin: Starting location
        - destination: Ending location
        - departure_time: When the trip starts
        - arrival_time: When the trip ends
        - waypoints: List of waypoint assessments with lat, lon, arrival_time, weather, and danger score
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
    waypoint_coords = pick_equidistant_points(points)

    # Step 2: Calculate departure time and waypoint arrival times
    duration_seconds = get_route_duration_seconds(route)

    if departure_time:
        start_time = dateutil.parser.parse(departure_time)
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
    elif arrival_time:
        end_time = dateutil.parser.parse(arrival_time)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        start_time = end_time - timedelta(seconds=duration_seconds)
    else:
        start_time = datetime.now(timezone.utc)

    end_time = start_time + timedelta(seconds=duration_seconds)

    # Calculate arrival time for each waypoint (linear interpolation)
    num_waypoints = len(waypoint_coords)
    waypoints_with_times = []
    for i, (lat, lon) in enumerate(waypoint_coords):
        # Fraction of trip completed at this waypoint
        fraction = i / (num_waypoints - 1) if num_waypoints > 1 else 0
        waypoint_time = start_time + timedelta(seconds=duration_seconds * fraction)
        waypoints_with_times.append((lat, lon, waypoint_time))

    # Step 3: Fetch weather for all waypoints at their arrival times
    weather_data = fetch_weather_for_waypoints(waypoints_with_times)

    # Step 4: Assess danger at each waypoint
    waypoint_results = []
    danger_scores = []

    for wd in weather_data:
        danger_score = _compute_danger_score(
            temp_c=wd["temp_c"],
            wind_kph=wd["wind_kph"],
            condition=wd["condition"],
            gust_kph=wd["gust_kph"],
        )

        danger_scores.append(danger_score)
        waypoint_results.append({
            "lat": wd["lat"],
            "lon": wd["lon"],
            "arrival_time": wd["arrival_time"],
            "temp_c": wd["temp_c"],
            "wind_kph": wd["wind_kph"],
            "gust_kph": wd["gust_kph"],
            "condition": wd["condition"],
            "danger_score": round(danger_score, 2),
        })

    # Step 5: Compute overall assessment
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
        "departure_time": start_time.isoformat(),
        "arrival_time": end_time.isoformat(),
        "duration_minutes": round(duration_seconds / 60),
        "waypoints": waypoint_results,
        "average_danger": round(avg_danger, 2),
        "max_danger": round(max_danger, 2),
        "status": status,
    }


if __name__ == "__main__":
    mcp.run()
