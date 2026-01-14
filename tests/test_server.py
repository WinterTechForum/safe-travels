"""Tests for server.py"""

from datetime import datetime, timezone

import pytest

from server import (
    _compute_danger_score,
    fetch_weather_for_waypoints,
    weather_code_to_condition,
)


class TestWeatherCodeToCondition:
    """Tests for weather_code_to_condition function."""

    def test_clear_sky_codes(self):
        assert weather_code_to_condition(0) == "sunny"
        assert weather_code_to_condition(1) == "sunny"

    def test_cloudy_codes(self):
        assert weather_code_to_condition(2) == "cloudy"
        assert weather_code_to_condition(3) == "cloudy"

    def test_foggy_codes(self):
        assert weather_code_to_condition(45) == "foggy"
        assert weather_code_to_condition(48) == "foggy"

    def test_rainy_codes(self):
        rainy_codes = [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]
        for code in rainy_codes:
            assert weather_code_to_condition(code) == "rainy"

    def test_snowy_codes(self):
        snowy_codes = [71, 73, 75, 77, 85, 86]
        for code in snowy_codes:
            assert weather_code_to_condition(code) == "snowy"

    def test_stormy_code(self):
        assert weather_code_to_condition(95) == "stormy"

    def test_hail_codes(self):
        assert weather_code_to_condition(96) == "hail"
        assert weather_code_to_condition(99) == "hail"

    def test_unknown_code_defaults_to_cloudy(self):
        assert weather_code_to_condition(999) == "cloudy"


class TestComputeDangerScore:
    """Tests for _compute_danger_score function."""

    def test_safe_conditions(self):
        score = _compute_danger_score(
            temp_c=20.0,
            wind_kph=10.0,
            condition="sunny",
            gust_kph=15.0
        )
        # temp: 0 (20C is normal), wind: max(10/16, 15/16) = 0.9375, condition: 0
        assert score == pytest.approx(0.9375)

    def test_cold_and_snowy(self):
        score = _compute_danger_score(
            temp_c=-10.0,
            wind_kph=32.0,
            condition="snowy",
            gust_kph=40.0
        )
        # temp: 1 + 10/10 = 2, wind: max(32/16, 40/16) = 2.5, condition: 3
        assert score == pytest.approx(7.5)

    def test_hot_and_stormy(self):
        score = _compute_danger_score(
            temp_c=40.0,
            wind_kph=80.0,
            condition="stormy",
            gust_kph=100.0
        )
        # temp: 1 + 10/10 = 2, wind: max(80/16, 100/16) = 6.25, condition: 6
        assert score == pytest.approx(14.25)

    def test_gust_takes_precedence_over_wind(self):
        score_high_gust = _compute_danger_score(
            temp_c=20.0,
            wind_kph=10.0,
            condition="sunny",
            gust_kph=50.0
        )
        score_low_gust = _compute_danger_score(
            temp_c=20.0,
            wind_kph=10.0,
            condition="sunny",
            gust_kph=5.0
        )
        # High gust should use gust value, low gust should use wind value
        assert score_high_gust > score_low_gust


class TestFetchWeatherForWaypoints:
    """Tests for fetch_weather_for_waypoints function."""

    def test_fetches_weather_for_single_waypoint(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "hourly": {
                "time": ["2026-01-23T07:00", "2026-01-23T08:00", "2026-01-23T09:00"],
                "temperature_2m": [5.0, 6.0, 7.0],
                "wind_speed_10m": [10.0, 12.0, 14.0],
                "wind_gusts_10m": [15.0, 18.0, 21.0],
                "weather_code": [3, 3, 61]
            }
        }
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch("server.requests.get", return_value=mock_response)

        waypoints = [
            (33.95, -83.98, datetime(2026, 1, 23, 7, 30, tzinfo=timezone.utc))
        ]
        result = fetch_weather_for_waypoints(waypoints)

        assert len(result) == 1
        assert result[0]["lat"] == 33.95
        assert result[0]["lon"] == -83.98
        # Should match closest hour (7:00)
        assert result[0]["temp_c"] == 5.0
        assert result[0]["condition"] == "cloudy"

    def test_fetches_weather_for_multiple_waypoints(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = [
            {
                "hourly": {
                    "time": ["2026-01-23T07:00", "2026-01-23T08:00"],
                    "temperature_2m": [5.0, 6.0],
                    "wind_speed_10m": [10.0, 12.0],
                    "wind_gusts_10m": [15.0, 18.0],
                    "weather_code": [3, 3]
                }
            },
            {
                "hourly": {
                    "time": ["2026-01-23T07:00", "2026-01-23T08:00"],
                    "temperature_2m": [4.0, 5.0],
                    "wind_speed_10m": [8.0, 10.0],
                    "wind_gusts_10m": [12.0, 15.0],
                    "weather_code": [71, 71]
                }
            }
        ]
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch("server.requests.get", return_value=mock_response)

        base_time = datetime(2026, 1, 23, 7, 0, tzinfo=timezone.utc)
        waypoints = [
            (33.95, -83.98, base_time),
            (34.20, -83.90, datetime(2026, 1, 23, 7, 30, tzinfo=timezone.utc))
        ]
        result = fetch_weather_for_waypoints(waypoints)

        assert len(result) == 2
        assert result[0]["condition"] == "cloudy"
        assert result[1]["condition"] == "snowy"

    def test_matches_closest_hour(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "hourly": {
                "time": ["2026-01-23T07:00", "2026-01-23T08:00", "2026-01-23T09:00"],
                "temperature_2m": [5.0, 10.0, 15.0],
                "wind_speed_10m": [10.0, 10.0, 10.0],
                "wind_gusts_10m": [15.0, 15.0, 15.0],
                "weather_code": [0, 0, 0]
            }
        }
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch("server.requests.get", return_value=mock_response)

        # Time is 8:45, should match 9:00 (index 2)
        waypoints = [
            (33.95, -83.98, datetime(2026, 1, 23, 8, 45, tzinfo=timezone.utc))
        ]
        result = fetch_weather_for_waypoints(waypoints)

        assert result[0]["temp_c"] == 15.0  # 9:00 temperature

    def test_includes_arrival_time_in_result(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "hourly": {
                "time": ["2026-01-23T07:00"],
                "temperature_2m": [5.0],
                "wind_speed_10m": [10.0],
                "wind_gusts_10m": [15.0],
                "weather_code": [0]
            }
        }
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch("server.requests.get", return_value=mock_response)

        arrival = datetime(2026, 1, 23, 7, 0, tzinfo=timezone.utc)
        waypoints = [(33.95, -83.98, arrival)]
        result = fetch_weather_for_waypoints(waypoints)

        assert "arrival_time" in result[0]
        assert result[0]["arrival_time"] == arrival.isoformat()


class TestAssessRouteDanger:
    """Integration tests for assess_route_danger MCP tool."""

    def test_assess_route_danger_with_departure_time(self, mocker):
        # Import the FunctionTool and access .fn for the underlying function
        from server import assess_route_danger

        # Mock get_lat_long
        mocker.patch("server.get_lat_long", side_effect=[
            (33.9519, -83.9880),  # origin
            (34.5270, -83.9801)   # destination
        ])

        # Mock compute_route
        mocker.patch("server.compute_route", return_value={
            "routes": [{
                "duration": "3600s",
                "distanceMeters": 50000,
                "polyline": {"encodedPolyline": "test"}
            }]
        })

        # Mock polyline.decode
        mocker.patch("server.polyline.decode", return_value=[
            (33.95, -83.98), (34.00, -83.97), (34.10, -83.96),
            (34.20, -83.95), (34.30, -83.94), (34.40, -83.93),
            (34.50, -83.92), (34.52, -83.98)
        ])

        # Mock fetch_weather_for_waypoints
        mock_weather = [
            {"lat": 33.95, "lon": -83.98, "arrival_time": "2026-01-23T07:00:00+00:00",
             "temp_c": 5.0, "wind_kph": 10.0, "gust_kph": 15.0, "condition": "cloudy"},
            {"lat": 34.10, "lon": -83.96, "arrival_time": "2026-01-23T07:30:00+00:00",
             "temp_c": 4.0, "wind_kph": 12.0, "gust_kph": 18.0, "condition": "cloudy"},
            {"lat": 34.30, "lon": -83.94, "arrival_time": "2026-01-23T08:00:00+00:00",
             "temp_c": 3.0, "wind_kph": 15.0, "gust_kph": 20.0, "condition": "snowy"},
        ]
        mocker.patch("server.fetch_weather_for_waypoints", return_value=mock_weather)

        # Mock pick_equidistant_points to return 3 points
        mocker.patch("server.pick_equidistant_points", return_value=[
            (33.95, -83.98), (34.10, -83.96), (34.30, -83.94)
        ])

        # Use .fn to access the underlying function
        result = assess_route_danger.fn(
            origin="Grayson, GA",
            destination="Dahlonega, GA",
            departure_time="2026-01-23T07:00:00Z"
        )

        assert result["origin"] == "Grayson, GA"
        assert result["destination"] == "Dahlonega, GA"
        assert result["duration_minutes"] == 60
        assert len(result["waypoints"]) == 3
        assert "departure_time" in result
        assert "arrival_time" in result
        assert result["status"] in ["SAFE", "MODERATE", "HAZARDOUS", "EXTREME"]

    def test_assess_route_danger_defaults_to_now(self, mocker):
        from server import assess_route_danger

        mocker.patch("server.get_lat_long", side_effect=[
            (33.9519, -83.9880),
            (34.5270, -83.9801)
        ])

        mocker.patch("server.compute_route", return_value={
            "routes": [{
                "duration": "1800s",
                "distanceMeters": 25000,
                "polyline": {"encodedPolyline": "test"}
            }]
        })

        mocker.patch("server.polyline.decode", return_value=[(33.95, -83.98), (34.52, -83.98)])
        mocker.patch("server.pick_equidistant_points", return_value=[(33.95, -83.98)])
        mocker.patch("server.fetch_weather_for_waypoints", return_value=[
            {"lat": 33.95, "lon": -83.98, "arrival_time": "2026-01-23T12:00:00+00:00",
             "temp_c": 20.0, "wind_kph": 5.0, "gust_kph": 8.0, "condition": "sunny"}
        ])

        # Use .fn to access the underlying function
        result = assess_route_danger.fn(
            origin="Grayson, GA",
            destination="Dahlonega, GA"
            # No departure_time or arrival_time provided
        )

        # Should still work and return valid result
        assert "departure_time" in result
        assert "arrival_time" in result
        assert result["duration_minutes"] == 30

    def test_assess_route_danger_with_arrival_time(self, mocker):
        from server import assess_route_danger

        mocker.patch("server.get_lat_long", side_effect=[
            (33.9519, -83.9880),
            (34.5270, -83.9801)
        ])

        mocker.patch("server.compute_route", return_value={
            "routes": [{
                "duration": "3600s",
                "distanceMeters": 50000,
                "polyline": {"encodedPolyline": "test"}
            }]
        })

        mocker.patch("server.polyline.decode", return_value=[(33.95, -83.98), (34.52, -83.98)])
        mocker.patch("server.pick_equidistant_points", return_value=[(33.95, -83.98)])
        mocker.patch("server.fetch_weather_for_waypoints", return_value=[
            {"lat": 33.95, "lon": -83.98, "arrival_time": "2026-01-23T09:00:00+00:00",
             "temp_c": 20.0, "wind_kph": 5.0, "gust_kph": 8.0, "condition": "sunny"}
        ])

        # Use .fn to access the underlying function
        result = assess_route_danger.fn(
            origin="Grayson, GA",
            destination="Dahlonega, GA",
            arrival_time="2026-01-23T10:00:00Z"
        )

        # Departure should be 1 hour before arrival (duration is 3600s)
        assert "2026-01-23T09:00:00" in result["departure_time"]
        assert "2026-01-23T10:00:00" in result["arrival_time"]


class TestDeriveRoute:
    """Tests for derive_route MCP tool."""

    def test_derive_route_returns_waypoints(self, mocker):
        from server import derive_route

        mocker.patch("server.get_lat_long", side_effect=[
            (33.9519, -83.9880),
            (34.5270, -83.9801)
        ])

        mocker.patch("server.compute_route", return_value={
            "routes": [{
                "duration": "3600s",
                "distanceMeters": 50000,
                "polyline": {"encodedPolyline": "test_polyline"}
            }]
        })

        expected_points = [(33.95, -83.98), (34.10, -83.96), (34.52, -83.98)]
        mocker.patch("server.polyline.decode", return_value=expected_points)
        mocker.patch("server.pick_equidistant_points", return_value=expected_points)

        # Use .fn to access the underlying function
        result = derive_route.fn(
            origin="Grayson, GA",
            destination="Dahlonega, GA"
        )

        assert result == expected_points
