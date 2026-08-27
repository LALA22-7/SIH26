"""
GET /api/replay/{event_id} — full historical replay from pre-computed DB data

This endpoint NEVER calls ML at serve time.
All predictions must already be in the DB (via scripts/precompute_replay.py).
"""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.event import Event
from app.models.metric_row import MetricRow
from app.models.prediction import Prediction
from app.models.satellite_frame import SatelliteFrame
from app.schemas.common import CenterPoint, PatternResult
from app.schemas.replay import (
    ReplayActualSlot,
    ReplayErrors,
    ReplayPredictionSlot,
    ReplayResponse,
    ReplayStep,
)
from app.services.geo import haversine_km

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["replay"])


@router.get("/replay/{event_id}", response_model=ReplayResponse)
async def get_replay(
    event_id: str,
    db: AsyncSession = Depends(get_db),
) -> ReplayResponse:
    """
    Return the full historical replay sequence for a cyclone event.

    Each step represents one analysis time:
    - The observation frame used at that time
    - T+12 and T+24 predictions stored from that analysis
    - Actual best-track positions from the metrics table
    - Haversine errors in km

    The replay is sorted strictly by analysis time (ascending).
    This endpoint requires no live internet and makes no ML calls.
    """
    # ── Validate event ─────────────────────────────────────────────────────
    event_result = await db.execute(
        select(Event).where(Event.event_id == event_id)
    )
    if event_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")

    # ── Load all predictions for this event ────────────────────────────────
    preds_result = await db.execute(
        select(Prediction)
        .where(Prediction.event_id == event_id)
        .order_by(Prediction.base_time.asc(), Prediction.valid_time.asc())
    )
    all_predictions: list[Prediction] = list(preds_result.scalars().all())

    # ── Load all metric rows for actuals ───────────────────────────────────
    metrics_result = await db.execute(
        select(MetricRow)
        .where(MetricRow.event_id == event_id)
        .order_by(MetricRow.base_time.asc())
    )
    all_metrics: list[MetricRow] = list(metrics_result.scalars().all())

    # ── Load all frames for observation lookup ─────────────────────────────
    frames_result = await db.execute(
        select(SatelliteFrame)
        .where(SatelliteFrame.event_id == event_id)
        .order_by(SatelliteFrame.timestamp.asc())
    )
    all_frames: list[SatelliteFrame] = list(frames_result.scalars().all())

    # ── Index by base_time ─────────────────────────────────────────────────
    # Group predictions by base_time
    from collections import defaultdict
    preds_by_base: dict[datetime, list[Prediction]] = defaultdict(list)
    for p in all_predictions:
        preds_by_base[p.base_time].append(p)

    # Index metrics by (base_time, horizon_hours)
    metrics_index: dict[tuple[datetime, int], MetricRow] = {}
    for m in all_metrics:
        metrics_index[(m.base_time, m.horizon_hours)] = m

    # Index frames by timestamp for observation lookup
    frame_by_ts: dict[datetime, SatelliteFrame] = {f.timestamp: f for f in all_frames}

    if not preds_by_base:
        # Return an empty replay rather than 404 — event exists, just no predictions yet
        return ReplayResponse(event_id=event_id, total_steps=0, steps=[])

    # ── Build replay steps ─────────────────────────────────────────────────
    steps: list[ReplayStep] = []

    for base_time in sorted(preds_by_base.keys()):
        step_preds = preds_by_base[base_time]

        # Find the closest observation frame at or before base_time
        observation_frame_id: str | None = None
        candidates = [f for f in all_frames if f.timestamp <= base_time]
        if candidates:
            closest = max(candidates, key=lambda f: f.timestamp)
            observation_frame_id = closest.frame_id

        # Build T+12 and T+24 prediction slots
        prediction_dict: dict[str, ReplayPredictionSlot] = {}
        actual_dict: dict[str, ReplayActualSlot] = {}
        errors = ReplayErrors()

        for pred in step_preds:
            # Determine horizon label
            delta_hours = int((pred.valid_time - pred.base_time).total_seconds() / 3600)
            label = f"t{delta_hours}"

            prediction_dict[label] = ReplayPredictionSlot(
                valid_time=pred.valid_time,
                center=CenterPoint(lat=pred.pred_lat, lon=pred.pred_lon),
                pattern=PatternResult(
                    label=pred.pattern_label,
                    confidence=pred.pattern_confidence,
                ),
            )

            # Look up actual position from metrics
            metric = metrics_index.get((base_time, delta_hours))
            if metric:
                actual_dict[label] = ReplayActualSlot(
                    valid_time=pred.valid_time,
                    center=CenterPoint(lat=metric.actual_lat, lon=metric.actual_lon),
                )
                error_km = haversine_km(
                    pred.pred_lat, pred.pred_lon,
                    metric.actual_lat, metric.actual_lon,
                )
                if delta_hours == 12:
                    errors.t12_km = round(error_km, 2)
                elif delta_hours == 24:
                    errors.t24_km = round(error_km, 2)

        steps.append(
            ReplayStep(
                time=base_time,
                observation_frame=observation_frame_id,
                prediction=prediction_dict,
                actual=actual_dict,
                errors=errors,
            )
        )

    logger.info("[REPLAY] event=%s steps=%d", event_id, len(steps))

    return ReplayResponse(
        event_id=event_id,
        total_steps=len(steps),
        steps=steps,
    )
