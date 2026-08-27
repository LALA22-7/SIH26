"""
Classification service.

Orchestrates:
1. Load frame metadata from DB
2. Load satellite array from disk (rasterio) if available, else use mock array
3. Call ML adapter
4. Return structured classification result

The geometry insert (PostGIS point) is handled in the API layer, not here,
so this service stays independent of SQLAlchemy.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np

from app.services.ml_adapter import run_classify

logger = logging.getLogger(__name__)


def _load_frame_array(file_paths: dict[str, str] | None, channels: dict[str, str] | None) -> np.ndarray:
    """
    Load satellite channels from GeoTIFF files and stack into [C, H, W].

    Falls back to a zero-filled mock array if files are not available.
    Convention: [C, H, W] — never [H, W, C] or [C, T, H, W].
    """
    if not file_paths:
        logger.warning("[CLASSIFY SERVICE] No file_paths on frame — using mock array")
        return np.zeros((3, 256, 256), dtype=np.float32)

    bands: list[np.ndarray] = []
    try:
        import rasterio  # type: ignore[import]

        channel_order = ["ir", "water_vapor", "visible"]
        for ch in channel_order:
            path = file_paths.get(ch)
            if path is None:
                continue
            try:
                with rasterio.open(path) as src:
                    arr = src.read(1).astype(np.float32)  # shape: [H, W]
                    bands.append(arr)
                    logger.debug("[CLASSIFY SERVICE] Loaded channel %s from %s shape=%s", ch, path, arr.shape)
            except Exception as e:
                logger.warning("[CLASSIFY SERVICE] Could not read %s: %s — skipping channel", path, e)

    except ImportError:
        logger.warning("[CLASSIFY SERVICE] rasterio not available — using mock array")

    if not bands:
        logger.warning("[CLASSIFY SERVICE] No channels loaded — using mock array")
        return np.zeros((3, 256, 256), dtype=np.float32)

    # Stack to [C, H, W]
    stacked = np.stack(bands, axis=0)
    assert stacked.ndim == 3, f"Expected [C, H, W], got shape {stacked.shape}"
    return stacked


def run_classification(
    frame_id: str,
    event_id: str,
    timestamp: datetime,
    file_paths: dict[str, str] | None,
    channels: dict[str, str] | None,
) -> dict[str, Any]:
    """
    Execute classification for a single satellite frame.

    Returns
    -------
    dict with keys matching ClassifyResponse:
        event_id, timestamp, center (lat/lon), pattern (label/confidence), source, model
    """
    logger.info("[CLASSIFY SERVICE] event=%s frame=%s ts=%s", event_id, frame_id, timestamp)

    frame_array = _load_frame_array(file_paths, channels)
    result = run_classify(frame_array)

    return {
        "event_id": event_id,
        "timestamp": timestamp,
        "center": result["center"],
        "pattern": result["pattern"],
        "source": {"frame_id": frame_id},
        "model": result["model"],
    }
