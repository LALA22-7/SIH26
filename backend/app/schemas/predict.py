"""Schemas for POST /api/ps70/predict."""
from datetime import datetime
from pydantic import BaseModel, field_validator
from app.schemas.common import CenterPoint, PatternResult, ModelMeta, UncertaintyBlock


class PredictRequest(BaseModel):
    event_id: str
    start_timestamp: datetime

    @field_validator("start_timestamp", mode="after")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("start_timestamp must include timezone info (use UTC)")
        return v


class PredictionStep(BaseModel):
    """One forecast horizon step (T+12 or T+24)."""

    valid_time: datetime
    center: CenterPoint
    pattern: PatternResult


class PredictResponse(BaseModel):
    event_id: str
    base_time: datetime
    predictions: list[PredictionStep]
    uncertainty: UncertaintyBlock
    model: ModelMeta
