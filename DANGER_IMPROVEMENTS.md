# Danger Computation Improvements

## Time-aware weather forecasting
- [x] Fetch forecast data for departure_time instead of current weather
- [x] Use Open-Meteo hourly forecast API endpoint

## Segment-specific timing
- [x] Calculate expected arrival time at each waypoint based on route duration
- [x] Interpolate timestamps along the route
- [x] Fetch forecast for each segment's expected arrival time

## Road-relevant conditions
- [x] Precipitation accumulation (total snowfall, rainfall amounts)
- [x] Visibility distance (fog density, heavy rain visibility impact)
- [x] Road surface temperature vs air temp (black ice risk detection)
- [ ] Recent precipitation history (wet/icy roads from previous storms)

## Terrain awareness
- [ ] Fetch elevation data for waypoints
- [ ] Adjust danger scores for mountain passes / high elevation
- [ ] Incorporate grade/slope data (steep grades + ice multiplier)
- [ ] Account for exposure (ridgelines vs sheltered valleys for wind)

## Temporal factors
- [ ] Day vs night detection (visibility, fatigue, wildlife activity risks)
- [ ] Rush hour detection for urban segments
- [ ] School zone timing awareness

## Historical context
- [ ] Integrate accident frequency data for route segments
- [ ] Identify known trouble spots (bridges, flood-prone areas)
- [ ] Flag areas where bridges freeze before roads

## Actionable output
- [ ] Suggest alternative departure times with better conditions
- [ ] Propose alternate routes when primary route is hazardous
- [ ] Identify specific segments to watch
- [ ] Provide wait recommendations ("wait 2 hours for fog to clear")
