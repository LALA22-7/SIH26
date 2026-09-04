"""
ml/inference.py
───────────────
Public interface between the ML package and the backend.

The backend's ml_adapter.py imports and calls exactly two functions:

    predict_frame(frame: np.ndarray) -> dict
    predict_sequence(sequence: np.ndarray) -> dict

Both functions are defined at the bottom of this file.
The InferenceService class handles model loading and raw forward passes.
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
MODEL_VERSION = "2.0.0-temporal"


class InferenceService:
    def __init__(
        self,
        checkpoint_path: str = DEFAULT_CHECKPOINT,
        num_classes: int = 5,
        predict_pattern: bool = True,
        predict_confidence: bool = True,
        in_channels: int = 2,
    ) -> None:
        from ml.src.model import CycloneTemporalModel

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.predict_pattern = predict_pattern
        self.predict_confidence = predict_confidence

        self.model = CycloneTemporalModel(
            num_classes=num_classes,
            in_channels=in_channels,
        ).to(self.device)

        if not os.path.exists(checkpoint_path):
            logger.warning(f"Checkpoint not found: {checkpoint_path}. Using untrained model.")
        else:
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
        Run a single forward pass. image_tensor is [C, H, W].
        We reshape it to [1, 1, C, H, W] for the temporal model.
        """
        with torch.no_grad():
            x = image_tensor.unsqueeze(0).unsqueeze(0).to(self.device)
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
            response["pattern"] = None

        return response

    def predict_temporal(self, sequence_tensor: torch.Tensor) -> dict[str, Any]:
        """
        Run sequence forward pass. sequence_tensor is [T, C, H, W].
        Reshape to [1, T, C, H, W].
        """
        with torch.no_grad():
            x = sequence_tensor.unsqueeze(0).to(self.device)
            outputs = self.model(x)

        # Get current center
        cur_lat = float(outputs["center"][0][0].cpu())
        cur_lon = float(outputs["center"][0][1].cpu())

        # Estimate motion vector from the sequence
        # Note: Extrapolating from noisy single-frame predictions is highly unstable.
        # Until future targets are supervised, we default to the persistence baseline.
        t12_lat = cur_lat
        t12_lon = cur_lon
        t24_lat = cur_lat
        t24_lon = cur_lon

        # Get current pattern
        pred_id = int(torch.argmax(outputs["pattern"][0]).cpu())
        label = ID_TO_LABEL.get(pred_id, "unknown")
        conf = float(outputs["confidence"][0][0].cpu())

        # Temperature-scaled confidence is now baked in model output
        # Use simple provisional sigma derived from confidence for now
        base_sigma_t12 = 0.5
        base_sigma_t24 = 0.8
        
        # In a fully calibrated system, uncertainty could be learned or function of confidence
        # Here we scale base sigma by inverse confidence (lower conf -> higher uncertainty)
        scale_factor = 1.0 + (1.0 - conf)
        
        return {
            "predictions": [
                {
                    "horizon_hours": 12,
                    "center": {"lat": t12_lat, "lon": t12_lon},
                    "pattern": {"label": label, "confidence": conf},
                    "sigma_lat": base_sigma_t12 * scale_factor,
                    "sigma_lon": base_sigma_t12 * scale_factor,
                },
                {
                    "horizon_hours": 24,
                    "center": {"lat": t24_lat, "lon": t24_lon},
                    "pattern": {"label": label, "confidence": conf},
                    "sigma_lat": base_sigma_t24 * scale_factor,
                    "sigma_lon": base_sigma_t24 * scale_factor,
                },
            ],
            "model": {
                "name": MODEL_NAME,
                "version": MODEL_VERSION,
            },
        }

# ── Singleton ──────────────────────────────────────────────────────────────────
_service: InferenceService | None = None

def _get_service() -> InferenceService:
    global _service
    if _service is None:
        _service = InferenceService(
            checkpoint_path=DEFAULT_CHECKPOINT,
            predict_pattern=True,
            predict_confidence=True,
            in_channels=2,
        )
    return _service

# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC CONTRACT
# ══════════════════════════════════════════════════════════════════════════════

def predict_frame(frame: np.ndarray) -> dict[str, Any]:
    svc = _get_service()

    if not isinstance(frame, np.ndarray):
        raise TypeError(f"frame must be np.ndarray, got {type(frame)}")
    if frame.ndim != 3:
        raise ValueError(f"frame must be [C, H, W], got shape {frame.shape}")

    tensor = torch.tensor(frame, dtype=torch.float32)
    result = svc.predict(tensor)

    if result["pattern"] is None:
        result["pattern"] = {
            "label": "unlabeled",
            "confidence": None,
        }

    return result

def predict_sequence(sequence: np.ndarray) -> dict[str, Any]:
    if not isinstance(sequence, np.ndarray):
        raise TypeError(f"sequence must be np.ndarray, got {type(sequence)}")
    if sequence.ndim != 4:
        raise ValueError(f"sequence must be [T, C, H, W], got shape {sequence.shape}")

    svc = _get_service()
    tensor = torch.tensor(sequence, dtype=torch.float32)
    return svc.predict_temporal(tensor)
