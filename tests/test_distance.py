import pytest
from app.services.distance_service import calculate_haversine_distance


def test_haversine_distance_same_location():
    # Same point should return 0 distance
    dist = calculate_haversine_distance(12.9716, 77.5946, 12.9716, 77.5946)
    assert dist == 0.0


def test_haversine_distance_known_distance():
    # Distance between Bangalore (12.9716, 77.5946) and Chennai (13.0827, 80.2707) is ~290 km
    dist = calculate_haversine_distance(12.9716, 77.5946, 13.0827, 80.2707)
    assert 280.0 <= dist <= 310.0
