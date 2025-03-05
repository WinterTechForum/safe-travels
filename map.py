#!/usr/bin/env python3
import json
import os

import polyline
import requests

# write a function to take a city name, and make a call to the google maps API to get the latitude and longitude
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

cb_coords = get_lat_long('Crested Butte, CO')
denver_coords = get_lat_long('Denver, CO')

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
                "latitude": cb_coords[0],
                "longitude": cb_coords[1]
            }
        }
    },
    "destination": {
        "location": {
            "latLng": {
                "latitude": denver_coords[0],
                "longitude": denver_coords[1]
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
print(response.json())

# decode the encodedPolyline from the response
encodedPolyline = response.json()['routes'][0]['polyline']['encodedPolyline']

points = polyline.decode(encodedPolyline)

print(points)
print(f'Number of points: {len(points)}')

# extract 10 equidistant points from the list of points
n = 10
step = len(points) // n
equidistant_points = [points[i] for i in range(0, len(points), step)]

print(equidistant_points)
