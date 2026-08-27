"""Tests for services/geo.py — Haversine formula correctness."""
import pytest
from app.services.geo import haversine_km, mean_absolute_error_km


class TestHaversine:
    def test_same_point_is_zero(self):
        assert haversine_km(15.0, 68.0, 15.0, 68.0) == 0.0

    def test_known_distance_delhi_mumbai(self):
        # New Delhi: 28.6139°N, 77.2090°E
        # Mumbai:    19.0760°N, 72.8777°E
        # Approximate great-circle distance: ~1150 km
        d = haversine_km(28.6139, 77.2090, 19.0760, 72.8777)
        assert 1100 < d < 1200, f"Expected ~1150 km, got {d:.1f} km"

    def test_known_distance_equator(self):
        # Two points 1 degree apart on the equator ≈ 111.2 km
        d = haversine_km(0.0, 0.0, 0.0, 1.0)
        assert 110 < d < 113, f"Expected ~111 km, got {d:.1f} km"

    def test_symmetry(self):
        d1 = haversine_km(15.0, 68.0, 20.0, 72.0)
        d2 = haversine_km(20.0, 72.0, 15.0, 68.0)
        assert abs(d1 - d2) < 1e-6

    def test_north_pole_to_equator(self):
        # 90°N to 0°N, same longitude = quarter of Earth's circumference ≈ 10007 km
        d = haversine_km(90.0, 0.0, 0.0, 0.0)
        assert 9900 < d < 10100, f"Expected ~10007 km, got {d:.1f} km"

    def test_returns_float(self):
        d = haversine_km(15.0, 68.0, 16.0, 69.0)
        assert isinstance(d, float)

    def test_small_displacement(self):
        # 0.1 degree lat difference near equator ≈ 11.1 km
        d = haversine_km(0.0, 0.0, 0.1, 0.0)
        assert 10 < d < 12


class TestMAE:
    def test_empty_returns_zero(self):
        assert mean_absolute_error_km([]) == 0.0

    def test_single_pair(self):
        pairs = [(15.0, 68.0, 15.0, 68.0)]
        assert mean_absolute_error_km(pairs) == 0.0

    def test_averages_correctly(self):
        # Two pairs with known distances
        d1 = haversine_km(15.0, 68.0, 16.0, 68.0)  # ~111 km
        d2 = haversine_km(15.0, 68.0, 15.0, 69.0)  # ~107 km at lat 15
        pairs = [
            (15.0, 68.0, 16.0, 68.0),
            (15.0, 68.0, 15.0, 69.0),
        ]
        mae = mean_absolute_error_km(pairs)
        expected = (d1 + d2) / 2
        assert abs(mae - expected) < 1e-6
