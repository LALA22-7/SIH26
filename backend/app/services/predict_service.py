"""
Prediction service.

Orchestrates:
1. Accept a list of (frame_metadata, file_paths) representing the input sequence
2. Load arrays and stack into [T, C, H, W]
3. Call ML adapter for temporal prediction
4. Build uncertainty ellipse polygons (Shapely) — provisional until Day-6 calibration
5. Return structured prediction result

Uncertainty polygon convention:
  - Built from sigma_lat and sigma_lon (coordinate-wise std dev in degrees)
  - Approximated as a scaled ellipse around the predicted centre
  - Labeled "provisional" — NOT a calibrated confidence interval
  - GeoJSON coordinate order: [lon, lat]
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
from shapely.geometry import mapping, Point
from shapely.affinity import scale

from app.services.classify_service import _load_frame_array
from app.services.ml_adapter import run_predict

logger = logging.getLogger(__name__)

# Provisional sigma values used until Day-6 ML calibration
_DEFAULT_SIGMA_LAT = 0.5  # degrees
_DEFAULT_SIGMA_LON = 0.5  # degrees


def _build_uncertainty_polygon(
    center_lat: float,
    center_lon: float,
    sigma_lat: float,
    sigma_lon: float,
) -> dict[str, Any]:
    """
    Build a provisional uncertainty ellipse as a GeoJSON Polygon.

    Method:
      1. Create a unit circle around the predicted centre
      2. Scale x-axis by sigma_lon, y-axis by sigma_lat (degrees)
      3. Serialize to GeoJSON [lon, lat] coordinate order

    This is an approximation — NOT a calibrated confidence region.
    Do not label this with a percentage until uncertainty coverage
    has been measured and validated.
    """
    # Unit circle in lat/lon space, then scale by sigma values
    circle = Point(center_lon, center_lat).buffer(1.0)  # unit circle
    ellipse = scale(circle, xfact=sigma_lon, yfact=sigma_lat, origin=(center_lon, center_lat))

    geo = mapping(ellipse)
    # Ensure coordinate order is [lon, lat] (Shapely uses (x=lon, y=lat) natively)
    return {
        "type": geo["type"],
        "coordinates": geo["coordinates"],
    }


def _build_sequence(
    frames: list[dict[str, Any]],
) -> np.ndarray:
    """
    Stack a list of frame metadata dicts into a [T, C, H, W] numpy array.

    Parameters
    ----------
    frames
        List of dicts, each with 'file_paths' and 'channels' keys.
        Must be sorted by timestamp ascending before calling.

    Returns
    -------
    np.ndarray of shape [T, C, H, W], dtype float32
    """
    arrays: list[np.ndarray] = []
    for f in frames:
        arr = _load_frame_array(f.get("file_paths"), f.get("channels"))
        arrays.append(arr)

    if not arrays:
        logger.warning("[PREDICT SERVICE] Empty sequence — using mock [1, 3, 256, 256]")
        return np.zeros((1, 3, 256, 256), dtype=np.float32)

    # Stack on new axis 0 → [T, C, H, W]
    sequence = np.stack(arrays, axis=0)
    assert sequence.ndim == 4, f"Expected [T, C, H, W], got shape {sequence.shape}"
    logger.debug("[PREDICT SERVICE] Sequence shape: %s", sequence.shape)
    return sequence


def run_prediction(
    event_id: str,
    base_time: datetime,
    frames: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Execute temporal prediction from an input sequence.

    Parameters
    ----------
    event_id : str
    base_time : datetime
        The analysis time (last observation time, UTC).
    frames : list[dict]
        Each dict must have: timestamp, file_paths, channels.
        Sorted ascending by timestamp.

    Returns
    -------
    dict with keys:
        event_id, base_time,
        predictions (list of dicts with valid_time, center, pattern, uncertainty_geom_wkt),
        model
    """
    logger.info("[PREDICT SERVICE] event=%s base_time=%s frames=%d", event_id, base_time, len(frames))

    sequence = _build_sequence(frames)
    result = run_predict(sequence)

    predictions_out: list[dict[str, Any]] = []
    for pred in result.get("predictions", []):
        horizon_hours: int = pred.get("horizon_hours", 12)
        valid_time = base_time + timedelta(hours=horizon_hours)

        center_lat: float = pred["center"]["lat"]
        center_lon: float = pred["center"]["lon"]
        sigma_lat: float = pred.get("sigma_lat", _DEFAULT_SIGMA_LAT)
        sigma_lon: float = pred.get("sigma_lon", _DEFAULT_SIGMA_LON)

        uncertainty_polygon = _build_uncertainty_polygon(center_lat, center_lon, sigma_lat, sigma_lon)

        # Convert Shapely polygon to WKT for PostGIS storage
        try:
            from shapely.geometry import shape
            from shapely import wkt as shapely_wkt
            poly = shape(uncertainty_polygon)
            uncertainty_wkt = poly.wkt
        except Exception:
            uncertainty_wkt = None

        predictions_out.append({
            "valid_time": valid_time,
            "horizon_hours": horizon_hours,
            "center": pred["center"],
            "pattern": pred["pattern"],
            "sigma_lat": sigma_lat,
            "sigma_lon": sigma_lon,
            "uncertainty_polygon": uncertainty_polygon,
            "uncertainty_wkt": uncertainty_wkt,
            "uncertainty_status": "provisional",
        })

    return {
        "event_id": event_id,
        "base_time": base_time,
        "predictions": predictions_out,
        "model": result.get("model", {"name": "ps70-temporal-stub", "version": "0.1.0"}),
    }
