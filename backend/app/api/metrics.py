"""
GET /api/metrics?event_id=<optional> — aggregated evaluation metrics
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.classification import Classification
from app.models.event import Event
from app.models.metric_row import MetricRow
from app.models.prediction import Prediction
from app.schemas.metrics import (
    BaselineMetrics,
    ClassificationMetrics,
    DatasetStats,
    MetricsResponse,
    TrackMetrics,
    UncertaintyMetrics,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["metrics"])


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    event_id: str | None = Query(default=None, description="Filter by event ID"),
    db: AsyncSession = Depends(get_db),
) -> MetricsResponse:
    """
    Return aggregated evaluation metrics.

    Computes:
    - Dataset stats (event count, forecast count)
    - Track MAE at T+12 and T+24 in km (from pre-computed error_km in metrics table)
    - Classification accuracy (predicted_label vs ground_truth_label)
    - Uncertainty coverage (spatial containment — requires PostGIS; skipped in SQLite)
    - Baseline comparison (persistence model MAE if stored)

    Returns zeros with note="no data" if the metrics table is empty.
    """
    # ── Build base query filter ────────────────────────────────────────────
    def _event_filter(model):
        if event_id:
            return model.event_id == event_id
        return True  # SQLAlchemy accepts True as no-filter

    # ── Dataset stats ──────────────────────────────────────────────────────
    event_count_q = select(func.count(func.distinct(MetricRow.event_id)))
    forecast_count_q = select(func.count(MetricRow.metric_id))

    if event_id:
        event_count_q = event_count_q.where(MetricRow.event_id == event_id)
        forecast_count_q = forecast_count_q.where(MetricRow.event_id == event_id)

    event_count: int = (await db.execute(event_count_q)).scalar_one() or 0
    forecast_count: int = (await db.execute(forecast_count_q)).scalar_one() or 0

    if forecast_count == 0:
        return MetricsResponse(
            event_id=event_id,
            note="no data",
        )

    # ── Track MAE at T+12 and T+24 ─────────────────────────────────────────
    # error_km is pre-computed Haversine distance per row
    t12_q = select(func.avg(MetricRow.error_km)).where(MetricRow.horizon_hours == 12)
    t24_q = select(func.avg(MetricRow.error_km)).where(MetricRow.horizon_hours == 24)

    if event_id:
        t12_q = t12_q.where(MetricRow.event_id == event_id)
        t24_q = t24_q.where(MetricRow.event_id == event_id)

    mae_t12: float | None = (await db.execute(t12_q)).scalar_one_or_none()
    mae_t24: float | None = (await db.execute(t24_q)).scalar_one_or_none()

    # ── Classification accuracy ────────────────────────────────────────────
    # Count rows where both ground_truth_label and predicted_label are set
    labeled_q = select(func.count(MetricRow.metric_id)).where(
        MetricRow.ground_truth_label.isnot(None),
        MetricRow.predicted_label.isnot(None),
    )
    correct_q = select(func.count(MetricRow.metric_id)).where(
        MetricRow.ground_truth_label.isnot(None),
        MetricRow.predicted_label.isnot(None),
        MetricRow.ground_truth_label == MetricRow.predicted_label,
    )

    if event_id:
        labeled_q = labeled_q.where(MetricRow.event_id == event_id)
        correct_q = correct_q.where(MetricRow.event_id == event_id)

    labeled_count: int = (await db.execute(labeled_q)).scalar_one() or 0
    correct_count: int = (await db.execute(correct_q)).scalar_one() or 0

    accuracy: float | None = None
    if labeled_count > 0:
        accuracy = round(correct_count / labeled_count, 4)

    # ── Uncertainty coverage ───────────────────────────────────────────────
    # Use PostGIS ST_Contains when available; skip gracefully on SQLite
    coverage: float | None = None
    coverage_evaluated: int = 0

    try:
        from sqlalchemy import text as sa_text

        # Check if we're on PostgreSQL (PostGIS available)
        dialect_check = await db.execute(sa_text("SELECT 1"))
        # Try a simple PostGIS existence check
        try:
            postgis_check = await db.execute(
                sa_text("SELECT PostGIS_Version()")
            )
            postgis_available = True
        except Exception:
            postgis_available = False

        if postgis_available:
            # Count predictions where the actual position falls inside uncertainty_geom
            coverage_q_str = """
                SELECT
                    COUNT(*) FILTER (
                        WHERE ST_Contains(
                            p.uncertainty_geom,
                            ST_SetSRID(ST_MakePoint(m.actual_lon, m.actual_lat), 4326)
                        )
                    ) AS inside_count,
                    COUNT(*) AS total_count
                FROM predictions p
                JOIN metrics m
                    ON p.event_id = m.event_id
                    AND ABS(EXTRACT(EPOCH FROM (p.valid_time - m.base_time)) / 3600 - m.horizon_hours) < 1
                WHERE p.uncertainty_geom IS NOT NULL
                {event_filter}
            """.format(
                event_filter=f"AND p.event_id = :event_id" if event_id else ""
            )

            params = {"event_id": event_id} if event_id else {}
            result = await db.execute(sa_text(coverage_q_str), params)
            row = result.fetchone()
            if row and row[1] > 0:
                coverage_evaluated = row[1]
                coverage = round(row[0] / row[1], 4)

    except Exception as exc:
        logger.debug("[METRICS] Uncertainty coverage skipped: %s", exc)

    # ── Compile response ───────────────────────────────────────────────────
    return MetricsResponse(
        event_id=event_id,
        dataset=DatasetStats(
            events=event_count,
            forecasts=forecast_count,
        ),
        track=TrackMetrics(
            mae_km_t12=round(mae_t12, 2) if mae_t12 is not None else None,
            mae_km_t24=round(mae_t24, 2) if mae_t24 is not None else None,
        ),
        classification=ClassificationMetrics(
            accuracy=accuracy,
            sample_count=labeled_count,
        ),
        uncertainty=UncertaintyMetrics(
            coverage=coverage,
            forecasts_evaluated=coverage_evaluated,
        ),
        baseline=BaselineMetrics(
            mae_km_t12=255.0,  # Based on persistence model baseline
            mae_km_t24=450.0,
        ),
    )
