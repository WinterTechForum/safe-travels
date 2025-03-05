#!/usr/bin/env python3
import os
from typing import Any, List, Tuple

import dateutil
import polyline
import requests
from langchain_core.tools import tool


def get_lat_long(city_name: str) -> Tuple[float, float]:
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'address': city_name,
        'key': os.environ['GOOGLE_MAPS_API_KEY']
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if not data['results']:
        raise ValueError(f"No results found for city: {city_name}")

    lat = data['results'][0]['geometry']['location']['lat']
    lng = data['results'][0]['geometry']['location']['lng']

    return lat, lng


def ensure_rfc3339_format(date_str: str) -> str:
    """
    Ensure the given date string is in RFC3339 format.

    Args:
        date_str (str): The date string to validate.

    Returns:
        str: The date string in RFC3339 format.

    Raises:
        ValueError: If the date string is not in a valid format.
    """
    try:
        # Try to parse the date string to a datetime object
        dt = dateutil.parser.parse(date_str)

        # convert the date to UTC
        dt = dt.astimezone(dateutil.tz.gettz('UTC'))

        # Return the date string in RFC3339 format with a trailing Z to indicate UTC
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        raise ValueError(f"Invalid date string: {date_str}. Ensure it is in RFC3339 format.")


def compute_route(origin: Tuple[float, float], destination: Tuple[float, float],
                  departure_time: str | None = None,
                  arrival_time: str | None = None) -> dict[str, Any]:
    url = 'https://routes.googleapis.com/directions/v2:computeRoutes'

    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': os.environ['GOOGLE_MAPS_API_KEY'],
        'X-Goog-FieldMask': 'routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline'
    }

    data = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": origin[0],
                    "longitude": origin[1]
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": destination[0],
                    "longitude": destination[1]
                }
            }
        },
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE",
        "computeAlternativeRoutes": False,
        "routeModifiers": {
            "avoidTolls": False,
            "avoidHighways": False,
            "avoidFerries": False
        },
        "languageCode": "en-US",
        "units": "IMPERIAL"
    }

    # ensure departure_time is in RFC3339 format

    if departure_time:
        data['departureTime'] = ensure_rfc3339_format(departure_time)
    elif arrival_time:
        data['arrivalTime'] = ensure_rfc3339_format(arrival_time)

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    return response.json()


def pick_equidistant_points(points: List[Tuple[float, float]], n: int = 10) -> List[Tuple[float, float]]:
    """Pick n equidistant points from a list of points."""
    if n <= 0:
        raise ValueError("Number of points must be greater than 0")
    step = max(1, len(points) // n)

    return [points[i] for i in range(0, len(points), step)]


@tool
def derive_route(city0: str, city1: str, departure_time: str | None = None,
                 arrival_time: str | None = None) -> List[Tuple[float, float]]:
    """Derive a route between two cities."""
    city0_coords = get_lat_long(city0)
    city1_coords = get_lat_long(city1)

    route = compute_route(city0_coords, city1_coords, departure_time, arrival_time)

    # decode the encodedPolyline from the response
    encodedPolyline = route['routes'][0]['polyline']['encodedPolyline']

    points = polyline.decode(encodedPolyline)

    return pick_equidistant_points(points)


if __name__ == '__main__':
    points = derive_route.run({'city0': 'Crested Butte, CO', 'city1': 'Denver, CO'})
    print(points)
