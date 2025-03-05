#!/usr/bin/env python3
import json
import os
from typing import Any

import polyline
import requests

def get_lat_long(city_name):
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'address': city_name,
        'key': os.environ['GOOGLE_MAPS_API_KEY']
    }
    response = requests.get(url, params=params)
    data = response.json()

    lat = data['results'][0]['geometry']['location']['lat']
    lng = data['results'][0]['geometry']['location']['lng']

    return (lat, lng)

def compute_route(origin: tuple[int, int], destination: tuple[int, int]) -> dict[str, Any]:
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

    return response.json()


def pick_equidistant_points(n: int = 10) -> list[tuple[int, int]]:
    step = len(points) // n

    return [points[i] for i in range(0, len(points), step)]


if __name__ == '__main__':
    cb_coords = get_lat_long('Crested Butte, CO')
    denver_coords = get_lat_long('Denver, CO')

    route = compute_route(cb_coords, denver_coords)

    # decode the encodedPolyline from the response
    encodedPolyline = route['routes'][0]['polyline']['encodedPolyline']

    points = polyline.decode(encodedPolyline)

    print(points)
    print(f'Number of points: {len(points)}')

    points = pick_equidistant_points()

    print(points)
