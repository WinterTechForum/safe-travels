"""Tests for danger_assessment.py"""

from danger_assessment import (
    temperature_severity,
    weather_conditions_severity,
    wind_severity,
)


class TestWeatherConditionsSeverity:
    """Tests for the weather_conditions_severity mapping."""

    def test_safe_conditions_have_zero_severity(self):
        safe_conditions = [
            'sunny',
            'cloudy',
            'overcast',
            'partly cloudy',
            'partly sunny',
        ]
        for condition in safe_conditions:
            assert weather_conditions_severity[condition] == 0

    def test_rainy_has_moderate_severity(self):
        assert weather_conditions_severity['rainy'] == 2

    def test_snowy_has_higher_severity(self):
        assert weather_conditions_severity['snowy'] == 3

    def test_foggy_severity(self):
        assert weather_conditions_severity['foggy'] == 4

    def test_severe_conditions_have_max_severity(self):
        severe_conditions = ['tornado', 'hurricane', 'blizzard']
        for condition in severe_conditions:
            assert weather_conditions_severity[condition] == 10


class TestTemperatureSeverity:
    """Tests for temperature_severity function."""

    def test_freezing_temperature_has_severity(self):
        # At -10C, severity should be 1 + 10/10 = 2
        assert temperature_severity(-10) == 2.0

    def test_very_cold_temperature(self):
        # At -20C, severity should be 1 + 20/10 = 3
        assert temperature_severity(-20) == 3.0

    def test_normal_temperature_has_zero_severity(self):
        # Temperatures between 0 and 30 should have 0 severity
        assert temperature_severity(0) == 0
        assert temperature_severity(15) == 0
        assert temperature_severity(25) == 0
        assert temperature_severity(29) == 0

    def test_hot_temperature_has_severity(self):
        # At 40C, severity should be 1 + (40-30)/10 = 2
        assert temperature_severity(40) == 2.0

    def test_very_hot_temperature(self):
        # At 50C, severity should be 1 + (50-30)/10 = 3
        assert temperature_severity(50) == 3.0

    def test_boundary_at_30_degrees(self):
        # At exactly 30C, severity starts
        assert temperature_severity(30) == 1.0


class TestWindSeverity:
    """Tests for wind_severity function."""

    def test_calm_wind_low_severity(self):
        assert wind_severity(0) == 0

    def test_moderate_wind(self):
        # 16 kph should give severity of 1
        assert wind_severity(16) == 1.0

    def test_strong_wind(self):
        # 32 kph should give severity of 2
        assert wind_severity(32) == 2.0

    def test_hurricane_force_wind(self):
        # 160 kph should give severity of 10
        assert wind_severity(160) == 10.0
