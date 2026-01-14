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


def wind_severity(kph: float) -> float:
    return kph / 16


def precipitation_severity(rain_mm: float, snowfall_cm: float) -> float:
    """Compute severity from precipitation rates.

    Args:
        rain_mm: Rain in the preceding hour (mm)
        snowfall_cm: Snowfall in the preceding hour (cm)

    Returns:
        Severity score from 0-10
    """
    # Rain severity: light <2.5mm/hr, moderate 2.5-7.5mm/hr, heavy >7.5mm/hr
    rain_score = 0.0
    if rain_mm > 0:
        if rain_mm < 2.5:
            rain_score = rain_mm / 2.5  # 0-1 for light rain
        elif rain_mm < 7.5:
            rain_score = 1 + (rain_mm - 2.5) / 5 * 2  # 1-3 for moderate
        else:
            rain_score = 3 + min((rain_mm - 7.5) / 7.5 * 3, 4)  # 3-7 for heavy

    # Snowfall severity: more dangerous than rain
    # Light <1cm/hr, moderate 1-2.5cm/hr, heavy >2.5cm/hr
    snow_score = 0.0
    if snowfall_cm > 0:
        if snowfall_cm < 1:
            snow_score = snowfall_cm * 2  # 0-2 for light snow
        elif snowfall_cm < 2.5:
            snow_score = 2 + (snowfall_cm - 1) / 1.5 * 3  # 2-5 for moderate
        else:
            snow_score = 5 + min((snowfall_cm - 2.5) / 2.5 * 3, 5)  # 5-10 for heavy

    return max(rain_score, snow_score)


def visibility_severity(visibility_m: float) -> float:
    """Compute severity from visibility distance.

    Args:
        visibility_m: Visibility in meters

    Returns:
        Severity score from 0-10
    """
    # Good visibility: >10km (10000m) = 0
    # Moderate: 4-10km = 0-1
    # Poor: 1-4km = 1-3
    # Very poor: 200m-1km = 3-6
    # Dense fog: <200m = 6-10
    if visibility_m >= 10000:
        return 0.0
    elif visibility_m >= 4000:
        return (10000 - visibility_m) / 6000  # 0-1
    elif visibility_m >= 1000:
        return 1 + (4000 - visibility_m) / 3000 * 2  # 1-3
    elif visibility_m >= 200:
        return 3 + (1000 - visibility_m) / 800 * 3  # 3-6
    else:
        return 6 + min((200 - visibility_m) / 200 * 4, 4)  # 6-10


def black_ice_risk(
    temp_c: float, soil_temp_c: float | None, dew_point_c: float | None
) -> float:
    """Compute black ice risk from temperature conditions.

    Black ice forms when:
    - Air temp is near or below freezing (0-4°C most dangerous)
    - Road surface (soil) temp is at or below freezing
    - High humidity (dew point close to air temp)

    Args:
        temp_c: Air temperature in Celsius
        soil_temp_c: Soil/surface temperature in Celsius (proxy for road temp)
        dew_point_c: Dew point temperature in Celsius

    Returns:
        Risk score from 0-5
    """
    # No risk if clearly above freezing
    if temp_c > 4 and (soil_temp_c is None or soil_temp_c > 2):
        return 0.0

    risk = 0.0

    # Temperature risk zone: -5°C to 4°C is the danger zone
    # Peak danger around 0-2°C where water freezes but roads look wet
    if temp_c <= 4:
        if -5 <= temp_c <= 4:
            # Peak risk at 0-2°C
            if 0 <= temp_c <= 2:
                risk = 3.0
            elif temp_c < 0:
                risk = 2.0 + temp_c / 5  # Decreases as it gets colder
            else:
                risk = 3.0 - (temp_c - 2) / 2  # 2-4°C range
        elif temp_c < -5:
            risk = 1.0  # Cold enough that ice is expected/obvious

    # Soil temp below freezing increases risk
    if soil_temp_c is not None and soil_temp_c <= 0:
        soil_factor = min(abs(soil_temp_c) / 5, 1.0)
        risk += soil_factor

    # High humidity (dew point close to temp) increases risk
    if dew_point_c is not None and temp_c <= 4:
        dew_spread = temp_c - dew_point_c
        if dew_spread < 3:
            risk += (3 - dew_spread) / 3  # Up to +1 for saturated air

    return min(risk, 5.0)
