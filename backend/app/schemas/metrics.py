"""Schemas for GET /api/metrics."""
from pydantic import BaseModel


class DatasetStats(BaseModel):
    events: int = 0
    forecasts: int = 0


class TrackMetrics(BaseModel):
    mae_km_t12: float | None = None
    mae_km_t24: float | None = None


class ClassificationMetrics(BaseModel):
    accuracy: float | None = None
    sample_count: int = 0


class UncertaintyMetrics(BaseModel):
    coverage: float | None = None
    forecasts_evaluated: int = 0


class BaselineMetrics(BaseModel):
    mae_km_t12: float | None = None
    mae_km_t24: float | None = None


class MetricsResponse(BaseModel):
    event_id: str | None = None
    dataset: DatasetStats = DatasetStats()
    track: TrackMetrics = TrackMetrics()
    classification: ClassificationMetrics = ClassificationMetrics()
    uncertainty: UncertaintyMetrics = UncertaintyMetrics()
    baseline: BaselineMetrics = BaselineMetrics()
    note: str | None = None
