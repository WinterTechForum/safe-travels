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
