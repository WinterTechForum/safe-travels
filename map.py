#!/usr/bin/env python3
import json
import os
from typing import Any, List, Tuple

import polyline
import requests

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

def compute_route(origin: Tuple[float, float], destination: Tuple[float, float]) -> dict[str, Any]:
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

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    return response.json()

def pick_equidistant_points(points: List[Tuple[float, float]], n: int = 10) -> List[Tuple[float, float]]:
    """Pick n equidistant points from a list of points."""
    if n <= 0:
        raise ValueError("Number of points must be greater than 0")
    step = max(1, len(points) // n)

    return [points[i] for i in range(0, len(points), step)]

if __name__ == '__main__':
    try:
        cb_coords = get_lat_long('Crested Butte, CO')
        denver_coords = get_lat_long('Denver, CO')

        route = compute_route(cb_coords, denver_coords)

        # decode the encodedPolyline from the response
        encodedPolyline = route['routes'][0]['polyline']['encodedPolyline']

        points = polyline.decode(encodedPolyline)

        print(points)
        print(f'Number of points: {len(points)}')

        equidistant_points = pick_equidistant_points(points)

        print(equidistant_points)
    except Exception as e:
        print(f"An error occurred: {e}")