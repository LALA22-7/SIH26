"""
Geospatial utility functions.

All distance calculations use the Haversine formula (great-circle distance).
Never use raw degree differences as a proxy for km — latitude degrees and
longitude degrees have different km equivalents depending on position.
"""
from math import asin, cos, radians, sin, sqrt


EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute the great-circle distance in kilometres between two points.

    Parameters
    ----------
    lat1, lon1 : float
        Latitude and longitude of point 1 (degrees).
    lat2, lon2 : float
        Latitude and longitude of point 2 (degrees).

    Returns
    -------
    float
        Distance in kilometres.

    Notes
    -----
    Coordinate order follows the project convention: (lat, lon).
    GeoJSON uses [lon, lat] — callers must pass in the correct order.
    """
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)

    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    )

    return 2.0 * EARTH_RADIUS_KM * asin(sqrt(a))


def mean_absolute_error_km(
    pairs: list[tuple[float, float, float, float]],
) -> float:
    """
    Compute MAE in km over a list of (pred_lat, pred_lon, actual_lat, actual_lon) tuples.

    Returns 0.0 for an empty list rather than raising ZeroDivisionError.
    """
    if not pairs:
        return 0.0
    errors = [haversine_km(p_lat, p_lon, a_lat, a_lon) for p_lat, p_lon, a_lat, a_lon in pairs]
    return sum(errors) / len(errors)
