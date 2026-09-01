"""
Classification service.

Orchestrates:
1. Load satellite frame array from disk (npz preferred, tif fallback)
2. Call ML adapter (stub or real)
3. Return structured classification result

The geometry insert (PostGIS point) is handled in the API layer, not here,
so this service stays independent of SQLAlchemy.

Channel conventions (matches ml/configs/model_config.json):
    Channel 0 = IR   (irwin_cdr)
    Channel 1 = WV   (water vapour / irwvp)
    Channel 2 = VIS  (visible — optional, only if present in file_paths)

The real data is [2, H, W] (IR + WV only, no visible yet).
Mock arrays fall back to [2, 256, 256] to match the trained model.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import numpy as np

from app.services.ml_adapter import run_classify

logger = logging.getLogger(__name__)

# Ordered channel list — only channels present in file_paths are loaded.
# The model currently expects C=2 (IR + WV). If visible data is added later
# the model must be retrained with in_channels=3 before enabling it here.
_CHANNEL_ORDER = ["ir", "water_vapor", "visible"]

# Fallback mock shape: [C, H, W] matching the current trained model (C=2).
_MOCK_CHANNELS = 2
_MOCK_H = 256
_MOCK_W = 256


def _load_frame_array(
    file_paths: dict[str, str] | None,
    channels: dict[str, str] | None,
) -> np.ndarray:
    """
    Load satellite channels and stack into [C, H, W] float32.

    Load strategy (in priority order):
      1. NPZ file — preferred. standardize_data.py writes a pre-normalised
         [C, H, W] array under key "image". Load directly, no re-normalisation.
      2. GeoTIFF files — via rasterio. Load each channel separately, stack.
      3. Mock array — zeros [2, 256, 256] when nothing is available.

    Shape contract: always [C, H, W]. Never [H, W, C] or [C, T, H, W].
    Variable H/W is fine — CycloneCNN uses AdaptiveAvgPool2d internally.
    """
    # ── Strategy 1: NPZ (standardize_data.py output) ──────────────────────
    if file_paths:
        npz_path = file_paths.get("npz")
        if npz_path is None:
            # Infer npz path from ir path convention:
            # e.g.  /data/normalized/biparjoy_2023/frames/biparjoy_2023_20230614T120000Z.npz
            ir_path = file_paths.get("ir", "")
            if ir_path.endswith(".tif") or ir_path.endswith(".tiff"):
                candidate = ir_path.rsplit("_ir_", 1)
                if len(candidate) == 2:
                    # Try the npz sibling in the frames/ directory
                    import os
                    npz_candidate = os.path.join(
                        os.path.dirname(ir_path),
                        os.path.basename(ir_path).replace("_ir_insat.tif", ".npz"),
                    )
                    if os.path.exists(npz_candidate):
                        npz_path = npz_candidate

        if npz_path:
            try:
                data = np.load(npz_path)
                arr = data["image"].astype(np.float32)   # already [C, H, W], already 0-1
                assert arr.ndim == 3, f"NPZ image must be [C,H,W], got {arr.shape}"
                logger.debug("[CLASSIFY SERVICE] Loaded NPZ %s  shape=%s", npz_path, arr.shape)
                return arr
            except Exception as exc:
                logger.warning("[CLASSIFY SERVICE] NPZ load failed (%s) — trying rasterio", exc)

    # ── Strategy 2: GeoTIFF via rasterio ──────────────────────────────────
    if file_paths:
        bands: list[np.ndarray] = []
        try:
            import rasterio  # type: ignore[import]

            for ch in _CHANNEL_ORDER:
                path = file_paths.get(ch)
                if path is None:
                    continue
                try:
                    with rasterio.open(path) as src:
                        band = src.read(1).astype(np.float32)   # [H, W]
                        # Normalise to [0, 1] using the observed range
                        b_min, b_max = band.min(), band.max()
                        if b_max > b_min:
                            band = (band - b_min) / (b_max - b_min)
                        bands.append(band)
                        logger.debug(
                            "[CLASSIFY SERVICE] rasterio loaded %s  shape=%s", ch, band.shape
                        )
                except Exception as exc:
                    logger.warning("[CLASSIFY SERVICE] rasterio skip %s: %s", ch, exc)

        except ImportError:
            logger.warning("[CLASSIFY SERVICE] rasterio not available")

        if bands:
            stacked = np.stack(bands, axis=0)   # [C, H, W]
            assert stacked.ndim == 3
            return stacked

    # ── Strategy 3: mock ──────────────────────────────────────────────────
    logger.warning(
        "[CLASSIFY SERVICE] No frame data available — using mock [%d,%d,%d]",
        _MOCK_CHANNELS, _MOCK_H, _MOCK_W,
    )
    return np.zeros((_MOCK_CHANNELS, _MOCK_H, _MOCK_W), dtype=np.float32)


def _normalise_pattern(pattern: dict | None) -> dict[str, Any]:
    """
    Ensure pattern is always a schema-complete dict.

    inference.py returns None for the pattern key when the pattern head
    has not been trained. The API schema requires a PatternResult with
    label and confidence — fill in safe defaults so the response never
    crashes, and label it clearly as unlabeled.
    """
    if pattern is None:
        return {"label": "unlabeled", "confidence": None}
    label = pattern.get("label") or "unlabeled"
    conf = pattern.get("confidence")          # may be None — schema allows it
    return {"label": label, "confidence": conf}


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
        event_id, timestamp, center (lat/lon), pattern (label/confidence),
        source (frame_id), model (name/version)
    """
    logger.info("[CLASSIFY SERVICE] event=%s frame=%s ts=%s", event_id, frame_id, timestamp)

    frame_array = _load_frame_array(file_paths, channels)
    result = run_classify(frame_array)

    return {
        "event_id": event_id,
        "timestamp": timestamp,
        "center": result["center"],
        "pattern": _normalise_pattern(result.get("pattern")),
        "source": {"frame_id": frame_id},
        "model": result["model"],
    }
