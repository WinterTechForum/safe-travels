#!/usr/bin/env python3

import polyline

with open('polyline.txt') as f:
    polyline_str = f.read().strip()

print(polyline.decode(polyline_str))