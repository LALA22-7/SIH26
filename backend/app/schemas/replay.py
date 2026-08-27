"""Schemas for GET /api/replay/{event_id}."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel
from app.schemas.common import CenterPoint, PatternResult


class ReplayPredictionSlot(BaseModel):
    """Prediction at one horizon (T+12 or T+24) within a replay step."""

    valid_time: datetime | None = None
    center: CenterPoint | None = None
    pattern: PatternResult | None = None


class ReplayActualSlot(BaseModel):
    """Observed best-track position at a horizon within a replay step."""

    valid_time: datetime | None = None
    center: CenterPoint | None = None


class ReplayErrors(BaseModel):
    """Haversine errors for T+12 and T+24 in km."""

    t12_km: float | None = None
    t24_km: float | None = None


class ReplayStep(BaseModel):
    """One time-step in the historical replay sequence."""

    time: datetime
    observation_frame: str | None = None
    prediction: dict[str, ReplayPredictionSlot] = {}
    actual: dict[str, ReplayActualSlot] = {}
    errors: ReplayErrors = ReplayErrors()


class ReplayResponse(BaseModel):
    event_id: str
    total_steps: int
    steps: list[ReplayStep]
