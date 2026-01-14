"""Tests for routing.py"""

import pytest

from routing import (
    compute_route,
    ensure_rfc3339_format,
    get_lat_long,
    get_route_duration_seconds,
    pick_equidistant_points,
)


class TestEnsureRfc3339Format:
    """Tests for ensure_rfc3339_format function."""

    def test_iso_format_converted(self):
        result = ensure_rfc3339_format('2026-01-23T07:00:00')
        assert result == '2026-01-23T12:00:00Z'  # Assumes local is EST (-5)

    def test_already_rfc3339_with_z(self):
        result = ensure_rfc3339_format('2026-01-23T12:00:00Z')
        assert result == '2026-01-23T12:00:00Z'

    def test_human_readable_format(self):
        result = ensure_rfc3339_format('January 23, 2026 12:00 PM UTC')
        assert result == '2026-01-23T12:00:00Z'

    def test_invalid_date_raises_error(self):
        with pytest.raises(ValueError):
            ensure_rfc3339_format('not a date')


class TestGetLatLong:
    """Tests for get_lat_long function."""

    def test_valid_city_returns_coordinates(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            'results': [{'geometry': {'location': {'lat': 33.9519, 'lng': -83.9880}}}]
        }
        mock_response.raise_for_status = mocker.Mock()

        mocker.patch('routing.requests.get', return_value=mock_response)
        mocker.patch.dict('os.environ', {'GOOGLE_MAPS_API_KEY': 'test_key'})

        lat, lng = get_lat_long('Grayson, GA')
        assert lat == 33.9519
        assert lng == -83.9880

    def test_invalid_city_raises_error(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {'results': []}
        mock_response.raise_for_status = mocker.Mock()

        mocker.patch('routing.requests.get', return_value=mock_response)
        mocker.patch.dict('os.environ', {'GOOGLE_MAPS_API_KEY': 'test_key'})

        with pytest.raises(ValueError, match='No results found'):
            get_lat_long('NonexistentCity12345')


class TestComputeRoute:
    """Tests for compute_route function."""

    def test_compute_route_with_departure_time(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            'routes': [
                {
                    'duration': '3600s',
                    'distanceMeters': 50000,
                    'polyline': {'encodedPolyline': 'abc123'},
                }
            ]
        }
        mock_response.raise_for_status = mocker.Mock()

        mocker.patch('routing.requests.post', return_value=mock_response)
        mocker.patch.dict('os.environ', {'GOOGLE_MAPS_API_KEY': 'test_key'})

        result = compute_route(
            origin=(33.9519, -83.9880),
            destination=(34.5270, -83.9801),
            departure_time='2026-01-23T07:00:00Z',
        )

        assert result['routes'][0]['duration'] == '3600s'
        assert result['routes'][0]['polyline']['encodedPolyline'] == 'abc123'

    def test_compute_route_with_arrival_time(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            'routes': [
                {
                    'duration': '3600s',
                    'distanceMeters': 50000,
                    'polyline': {'encodedPolyline': 'abc123'},
                }
            ]
        }
        mock_response.raise_for_status = mocker.Mock()

        mock_post = mocker.patch('routing.requests.post', return_value=mock_response)
        mocker.patch.dict('os.environ', {'GOOGLE_MAPS_API_KEY': 'test_key'})

        compute_route(
            origin=(33.9519, -83.9880),
            destination=(34.5270, -83.9801),
            arrival_time='2026-01-23T10:00:00Z',
        )

        # Verify arrivalTime was passed in the request
        call_args = mock_post.call_args
        assert 'arrivalTime' in call_args.kwargs['json']


class TestGetRouteDurationSeconds:
    """Tests for get_route_duration_seconds function."""

    def test_parses_duration_string(self):
        route_response = {'routes': [{'duration': '3600s'}]}
        assert get_route_duration_seconds(route_response) == 3600

    def test_parses_large_duration(self):
        route_response = {'routes': [{'duration': '7200s'}]}
        assert get_route_duration_seconds(route_response) == 7200

    def test_parses_small_duration(self):
        route_response = {'routes': [{'duration': '60s'}]}
        assert get_route_duration_seconds(route_response) == 60


class TestPickEquidistantPoints:
    """Tests for pick_equidistant_points function."""

    def test_picks_correct_number_of_points(self):
        points = [(i, i) for i in range(100)]
        result = pick_equidistant_points(points, n=10)
        assert len(result) == 10

    def test_includes_first_point(self):
        points = [(i, i) for i in range(100)]
        result = pick_equidistant_points(points, n=10)
        assert result[0] == (0, 0)

    def test_points_are_evenly_spaced(self):
        points = [(i, i) for i in range(100)]
        result = pick_equidistant_points(points, n=10)
        # Step should be 10, so points should be at indices 0, 10, 20, ...
        expected = [(i * 10, i * 10) for i in range(10)]
        assert result == expected

    def test_handles_small_list(self):
        points = [(0, 0), (1, 1), (2, 2)]
        result = pick_equidistant_points(points, n=10)
        # When n > len(points), should return all points
        assert len(result) == 3

    def test_raises_on_zero_n(self):
        points = [(0, 0), (1, 1)]
        with pytest.raises(ValueError):
            pick_equidistant_points(points, n=0)

    def test_raises_on_negative_n(self):
        points = [(0, 0), (1, 1)]
        with pytest.raises(ValueError):
            pick_equidistant_points(points, n=-1)
