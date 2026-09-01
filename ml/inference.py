"""
ml/inference.py
───────────────
Public interface between the ML package and the backend.

The backend's ml_adapter.py imports and calls exactly two functions:

    predict_frame(frame: np.ndarray) -> dict
    predict_sequence(sequence: np.ndarray) -> dict

Both functions are defined at the bottom of this file.
The InferenceService class handles model loading and raw forward passes.

Current model state (update this comment when the model is retrained):
    - Checkpoint: ml/checkpoints/model.pt
    - Trained on: centre position regression only (PREDICT_PATTERN=False)
    - Pattern head: NOT trained — pattern label returns None, confidence returns None
    - Channels: IR (ch0) + water vapour (ch1) — shape [2, H, W]
    - Temporal model: NOT yet implemented — predict_sequence falls back to
      repeated single-frame inference and returns provisional sigma values

When the temporal model and pattern labels are ready, update:
    1. InferenceService.__init__ — set predict_pattern=True, predict_confidence=True
    2. predict_sequence — replace with real temporal model forward pass
    3. Update this docstring
"""

from __future__ import annotations

import logging
import os
from typing import Any

import numpy as np
import torch

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CHECKPOINT = os.path.join(_HERE, "checkpoints", "model.pt")

# ── Label map (locked — matches backend DB and Research taxonomy) ───────────────
ID_TO_LABEL: dict[int, str] = {
    0: "eye",
    1: "banding",
    2: "curved_band",
    3: "shear_affected",
    4: "disorganized",
}

# ── Model version ──────────────────────────────────────────────────────────────
MODEL_NAME = "ps70-classifier"
MODEL_VERSION = "1.0.0"


class InferenceService:
    """
    Loads the CNN checkpoint and runs forward passes.

    Parameters
    ----------
    checkpoint_path : str
        Path to the .pt state-dict file.
    num_classes : int
        Must match the number of classes the checkpoint was trained with.
    predict_pattern : bool
        Set True only when the model was actually trained with a pattern head.
        If False, pattern label is returned as None.
    predict_confidence : bool
        Set True only when the confidence head was trained.
        If False, confidence is returned as None.
    in_channels : int
        Number of input channels.  Current data has 2 (IR + water vapour).
    """

    def __init__(
        self,
        checkpoint_path: str = DEFAULT_CHECKPOINT,
        num_classes: int = 5,
        predict_pattern: bool = False,
        predict_confidence: bool = False,
        in_channels: int = 2,
    ) -> None:
        from ml.src.model import CycloneCNN

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.predict_pattern = predict_pattern
        self.predict_confidence = predict_confidence

        self.model = CycloneCNN(
            num_classes=num_classes,
            in_channels=in_channels,
            predict_pattern=predict_pattern,
            predict_confidence=predict_confidence,
        ).to(self.device)

        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(
                f"Checkpoint not found: {checkpoint_path}\n"
                f"Train the model first: python -m ml.src.train"
            )

        state = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(state)
        self.model.eval()
        logger.info(
            "[ML] Loaded checkpoint %s  device=%s  predict_pattern=%s",
            checkpoint_path,
            self.device,
            predict_pattern,
        )

    def predict(self, image_tensor: torch.Tensor) -> dict[str, Any]:
        """
        Run a single forward pass.

        Parameters
        ----------
        image_tensor : torch.Tensor
            Shape [C, H, W], float32, already normalised to [0, 1].

        Returns
        -------
        dict with keys: center, pattern (may be None), model
        """
        with torch.no_grad():
            # Add batch dimension: [C, H, W] → [1, C, H, W]
            x = image_tensor.unsqueeze(0).to(self.device)
            outputs = self.model(x)

        lat = float(outputs["center"][0][0].cpu())
        lon = float(outputs["center"][0][1].cpu())

        response: dict[str, Any] = {
            "center": {"lat": lat, "lon": lon},
            "model": {"name": MODEL_NAME, "version": MODEL_VERSION},
        }

        if self.predict_pattern:
            pred_id = int(torch.argmax(outputs["pattern"][0]).cpu())
            label = ID_TO_LABEL.get(pred_id, "unknown")
            conf = None
            if self.predict_confidence:
                conf = float(outputs["confidence"][0][0].cpu())
            response["pattern"] = {"label": label, "confidence": conf}
        else:
            # Pattern head not trained yet — return None explicitly so the
            # backend can fall back to stub values rather than crashing.
            response["pattern"] = None

        return response


# ── Singleton ──────────────────────────────────────────────────────────────────
# Loaded once on first call, reused for every subsequent request.
_service: InferenceService | None = None


def _get_service() -> InferenceService:
    global _service
    if _service is None:
        _service = InferenceService(
            checkpoint_path=DEFAULT_CHECKPOINT,
            predict_pattern=False,      # flip to True once pattern labels are trained
            predict_confidence=False,   # flip to True after Day-6 calibration
            in_channels=2,
        )
    return _service


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC CONTRACT — these two functions are the ONLY things the backend calls.
# Do not rename them. Do not change their signatures.
# ══════════════════════════════════════════════════════════════════════════════

def predict_frame(frame: np.ndarray) -> dict[str, Any]:
    """
    Classify a single satellite frame.

    Parameters
    ----------
    frame : np.ndarray
        Shape [C, H, W], dtype float32, normalised to [0, 1].
        Current model expects C=2 (channel 0 = IR, channel 1 = water vapour).

    Returns
    -------
    dict ::
        {
            "center":  {"lat": float, "lon": float},
            "pattern": {"label": str, "confidence": float | None}
                        — label is None when pattern head is not trained,
                          confidence is None before Day-6 calibration,
            "model":   {"name": str, "version": str}
        }

    Notes
    -----
    - Pattern label will be None until PREDICT_PATTERN=True is set in train.py
      and the model is retrained with real pattern labels from the Research team.
    - When pattern is None the backend ml_adapter falls back to its stub label.
    """
    svc = _get_service()

    if not isinstance(frame, np.ndarray):
        raise TypeError(f"frame must be np.ndarray, got {type(frame)}")
    if frame.ndim != 3:
        raise ValueError(f"frame must be [C, H, W], got shape {frame.shape}")

    tensor = torch.tensor(frame, dtype=torch.float32)
    result = svc.predict(tensor)

    # If pattern head is not trained, fill in a clearly-labeled placeholder
    # so the backend response is always schema-complete.
    if result["pattern"] is None:
        result["pattern"] = {
            "label": "unlabeled",
            "confidence": None,
        }

    return result


def predict_sequence(sequence: np.ndarray) -> dict[str, Any]:
    """
    Predict future cyclone positions from a temporal sequence of frames.

    Parameters
    ----------
    sequence : np.ndarray
        Shape [T, C, H, W], dtype float32, normalised to [0, 1].
        T = number of frames (all frames up to the analysis time).

    Returns
    -------
    dict ::
        {
            "predictions": [
                {
                    "horizon_hours": 12,
                    "center":  {"lat": float, "lon": float},
                    "pattern": {"label": str, "confidence": float | None},
                    "sigma_lat": float,   # uncertainty std-dev in degrees
                    "sigma_lon": float,
                },
                {
                    "horizon_hours": 24,
                    ...
                }
            ],
            "model": {"name": str, "version": str}
        }

    Notes
    -----
    CURRENT STATE: A dedicated temporal model does not exist yet.
    This function uses the last frame in the sequence for a single-frame
    classification, then extrapolates centre position using a simple
    persistence + recent-motion estimate from the last two frames.

    This is an explicitly provisional approach — it will be replaced when
    the temporal ConvLSTM/GRU model is trained (ML Day-3 deliverable).

    sigma_lat / sigma_lon are fixed provisional values (0.5 degrees ≈ 55 km)
    until Day-6 calibration provides real uncertainty estimates.
    """
    if not isinstance(sequence, np.ndarray):
        raise TypeError(f"sequence must be np.ndarray, got {type(sequence)}")
    if sequence.ndim != 4:
        raise ValueError(f"sequence must be [T, C, H, W], got shape {sequence.shape}")

    svc = _get_service()
    T = sequence.shape[0]

    # ── Classify the most recent frame ────────────────────────────────────
    last_frame = sequence[-1]   # [C, H, W]
    last_tensor = torch.tensor(last_frame, dtype=torch.float32)
    current = svc.predict(last_tensor)

    cur_lat = current["center"]["lat"]
    cur_lon = current["center"]["lon"]

    # ── Estimate motion vector from the last two frames (if available) ────
    # For T=1 there is no prior frame, so motion defaults to zero.
    delta_lat = 0.0
    delta_lon = 0.0

    if T >= 2:
        prev_frame = sequence[-2]
        prev_tensor = torch.tensor(prev_frame, dtype=torch.float32)
        prev_result = svc.predict(prev_tensor)
        delta_lat = cur_lat - prev_result["center"]["lat"]
        delta_lon = cur_lon - prev_result["center"]["lon"]
        # Each frame is ~3h apart in the current dataset → per-frame delta
        # corresponds roughly to a 3h motion vector.
        # T+12 ≈ 4 steps ahead,  T+24 ≈ 8 steps ahead.

    # ── Provisional uncertainty (fixed until Day-6 calibration) ───────────
    SIGMA_T12 = 0.5   # degrees (~55 km)
    SIGMA_T24 = 0.8   # degrees (~89 km) — grows with horizon

    pattern_label = "unlabeled"
    pattern_conf: float | None = None
    if current["pattern"] is not None:
        pattern_label = current["pattern"].get("label", "unlabeled")
        pattern_conf = current["pattern"].get("confidence")

    predictions = [
        {
            "horizon_hours": 12,
            "center": {
                "lat": cur_lat + delta_lat * 4,
                "lon": cur_lon + delta_lon * 4,
            },
            "pattern": {"label": pattern_label, "confidence": pattern_conf},
            "sigma_lat": SIGMA_T12,
            "sigma_lon": SIGMA_T12,
        },
        {
            "horizon_hours": 24,
            "center": {
                "lat": cur_lat + delta_lat * 8,
                "lon": cur_lon + delta_lon * 8,
            },
            "pattern": {"label": pattern_label, "confidence": pattern_conf},
            "sigma_lat": SIGMA_T24,
            "sigma_lon": SIGMA_T24,
        },
    ]

    return {
        "predictions": predictions,
        "model": {
            "name": MODEL_NAME,
            "version": MODEL_VERSION + "-temporal-provisional",
        },
    }
