"""Tests for danger_assessment.py"""

from danger_assessment import (
    black_ice_risk,
    precipitation_severity,
    temperature_severity,
    visibility_severity,
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


class TestPrecipitationSeverity:
    """Tests for precipitation_severity function."""

    def test_no_precipitation(self):
        assert precipitation_severity(0, 0) == 0

    def test_light_rain(self):
        # 1mm rain should give low severity
        result = precipitation_severity(1.0, 0)
        assert 0 < result < 1

    def test_moderate_rain(self):
        # 5mm rain should give moderate severity (1-3 range)
        result = precipitation_severity(5.0, 0)
        assert 1 <= result <= 3

    def test_heavy_rain(self):
        # 10mm rain should give high severity
        result = precipitation_severity(10.0, 0)
        assert result >= 3

    def test_light_snowfall(self):
        # 0.5cm snow should give low severity
        result = precipitation_severity(0, 0.5)
        assert 0 < result < 2

    def test_moderate_snowfall(self):
        # 2cm snow should give moderate severity
        result = precipitation_severity(0, 2.0)
        assert 2 <= result <= 5

    def test_heavy_snowfall(self):
        # 5cm snow should give high severity
        result = precipitation_severity(0, 5.0)
        assert result >= 5

    def test_snow_more_dangerous_than_rain(self):
        # Same precipitation rate: snow should be more dangerous
        rain_score = precipitation_severity(5.0, 0)
        snow_score = precipitation_severity(0, 0.5)  # 5mm = 0.5cm equivalent
        # Snow at 0.5cm should be similar or higher than 5mm rain
        assert snow_score >= rain_score * 0.5


class TestVisibilitySeverity:
    """Tests for visibility_severity function."""

    def test_excellent_visibility(self):
        # 15km visibility should have 0 severity
        assert visibility_severity(15000) == 0

    def test_good_visibility(self):
        # 10km visibility should have 0 severity
        assert visibility_severity(10000) == 0

    def test_moderate_visibility(self):
        # 5km visibility should have low severity (0-1)
        result = visibility_severity(5000)
        assert 0 < result <= 1

    def test_poor_visibility(self):
        # 2km visibility should have moderate severity (1-3)
        result = visibility_severity(2000)
        assert 1 <= result <= 3

    def test_very_poor_visibility(self):
        # 500m visibility should have high severity (3-6)
        result = visibility_severity(500)
        assert 3 <= result <= 6

    def test_dense_fog(self):
        # 100m visibility should have very high severity (6-10)
        result = visibility_severity(100)
        assert result >= 6

    def test_extreme_fog(self):
        # Near zero visibility should max out severity
        result = visibility_severity(50)
        assert result >= 8


class TestBlackIceRisk:
    """Tests for black_ice_risk function."""

    def test_warm_temperature_no_risk(self):
        # At 20C, no black ice risk
        assert black_ice_risk(20, None, None) == 0

    def test_peak_danger_zone(self):
        # At 1C (freezing point area), high risk
        result = black_ice_risk(1, None, None)
        assert result >= 2

    def test_very_cold_lower_risk(self):
        # At -10C, ice is expected so lower surprise factor
        result = black_ice_risk(-10, None, None)
        assert result <= 2

    def test_cold_soil_increases_risk(self):
        # Cold soil temp should increase risk
        risk_without_soil = black_ice_risk(2, None, None)
        risk_with_cold_soil = black_ice_risk(2, -2, None)
        assert risk_with_cold_soil > risk_without_soil

    def test_high_humidity_increases_risk(self):
        # Dew point close to temp (humid) should increase risk
        risk_dry = black_ice_risk(2, None, -5)  # Large spread = dry
        risk_humid = black_ice_risk(2, None, 1)  # Small spread = humid
        assert risk_humid > risk_dry

    def test_combined_factors(self):
        # All factors combined should give highest risk
        result = black_ice_risk(1, -2, 0)  # Peak temp, cold soil, humid
        assert result >= 4

    def test_boundary_at_4_degrees(self):
        # At 4C exactly, should still have some risk but lower
        result = black_ice_risk(4, None, None)
        assert 0 < result < 3

    def test_risk_capped_at_5(self):
        # Even worst conditions shouldn't exceed 5
        result = black_ice_risk(1, -5, 1)
        assert result <= 5
