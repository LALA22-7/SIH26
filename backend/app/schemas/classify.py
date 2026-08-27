"""Schemas for POST /api/ps70/classify and GET /api/ps70/classifications/{event_id}."""
from datetime import datetime, timezone
from pydantic import BaseModel, field_validator
from app.schemas.common import CenterPoint, PatternResult, ModelMeta, SourceRef


class ClassifyRequest(BaseModel):
    event_id: str
    timestamp: datetime
    frame_id: str

    @field_validator("timestamp", mode="after")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamp must include timezone information (use UTC)")
        return v


class ClassifyResponse(BaseModel):
    event_id: str
    timestamp: datetime
    center: CenterPoint
    pattern: PatternResult
    source: SourceRef
    model: ModelMeta


class ClassificationRecord(BaseModel):
    """Single classification entry returned in the time-series list."""

    classification_id: str
    event_id: str
    frame_id: str | None
    timestamp: datetime
    center: CenterPoint
    pattern: PatternResult
    model: ModelMeta

    model_config = {"from_attributes": True}


class ClassificationListResponse(BaseModel):
    event_id: str
    count: int
    classifications: list[ClassificationRecord]
