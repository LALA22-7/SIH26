"""
ML adapter — bridges the backend to the ML package.

Tries to import `ml.inference.predict_frame` and `ml.inference.predict_sequence`.
If either import fails (ML package not yet available) or if ML_FORCE_STUB=true,
falls back to deterministic stub responses based on the Day-1 fixture in the spec.

All callers should use `run_classify` and `run_predict` — never import ML directly
from any other module.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Mode detection ─────────────────────────────────────────────────────────────

def _detect_mode() -> str:
    """Return 'real' if ML package is importable and not force-stubbed, else 'stub'."""
    from app.core.config import get_settings
    settings = get_settings()
    if settings.ml_force_stub:
        return "stub"
    try:
        import ml.inference  # noqa: F401
        return "real"
    except ImportError:
        return "stub"


_MODE: str | None = None  # resolved lazily on first call


def _get_mode() -> str:
    global _MODE
    if _MODE is None:
        _MODE = _detect_mode()
        if _MODE == "stub":
            logger.warning(
                "[ML ADAPTER] Running in STUB MODE — "
                "ml.inference not importable or ML_FORCE_STUB=true. "
                "All predictions are deterministic fixtures."
            )
        else:
            logger.info("[ML ADAPTER] Running in REAL MODE — ml.inference loaded.")
    return _MODE


# ── Stub responses ─────────────────────────────────────────────────────────────

_CLASSIFY_STUB: dict[str, Any] = {
    "center": {"lat": 15.20, "lon": 68.40},
    "pattern": {"label": "banding", "confidence": 0.72},
    "model": {"name": "ps70-classifier-stub", "version": "0.1.0"},
}

_PREDICT_STUB: dict[str, Any] = {
    "predictions": [
        {
            "horizon_hours": 12,
            "center": {"lat": 16.10, "lon": 67.80},
            "pattern": {"label": "eye", "confidence": 0.64},
            # provisional uncertainty — not calibrated
            "sigma_lat": 0.5,
            "sigma_lon": 0.5,
        },
        {
            "horizon_hours": 24,
            "center": {"lat": 17.20, "lon": 67.10},
            "pattern": {"label": "eye", "confidence": 0.59},
            "sigma_lat": 0.8,
            "sigma_lon": 0.8,
        },
    ],
    "model": {"name": "ps70-temporal-stub", "version": "0.1.0"},
}


# ── Public interface ───────────────────────────────────────────────────────────

def run_classify(frame_array: Any | None = None) -> dict[str, Any]:
    """
    Run classification inference on a single satellite frame.

    Parameters
    ----------
    frame_array
        Numpy array of shape [C, H, W] (float32, normalised).
        Ignored in stub mode.

    Returns
    -------
    dict with keys: center, pattern, model
    """
    if _get_mode() == "stub":
        logger.debug("[ML ADAPTER] classify → stub")
        return dict(_CLASSIFY_STUB)

    try:
        from ml.inference import predict_frame  # type: ignore[import]
        result = predict_frame(frame_array)
        logger.debug("[ML ADAPTER] classify → real inference")
        return result
    except Exception as exc:
        logger.error("[ML ADAPTER] Real inference failed (%s), falling back to stub", exc)
        return dict(_CLASSIFY_STUB)


def run_predict(sequence_array: Any | None = None) -> dict[str, Any]:
    """
    Run temporal prediction on a sequence of frames.

    Parameters
    ----------
    sequence_array
        Numpy array of shape [T, C, H, W] (float32, normalised).
        Ignored in stub mode.

    Returns
    -------
    dict with keys: predictions (list), model
    Each prediction item: horizon_hours, center, pattern, sigma_lat, sigma_lon
    """
    if _get_mode() == "stub":
        logger.debug("[ML ADAPTER] predict → stub")
        return dict(_PREDICT_STUB)

    try:
        from ml.inference import predict_sequence  # type: ignore[import]
        result = predict_sequence(sequence_array)
        logger.debug("[ML ADAPTER] predict → real inference")
        return result
    except Exception as exc:
        logger.error("[ML ADAPTER] Real inference failed (%s), falling back to stub", exc)
        return dict(_PREDICT_STUB)


def reset_mode() -> None:
    """Force re-detection of ML mode. Useful in tests."""
    global _MODE
    _MODE = None
