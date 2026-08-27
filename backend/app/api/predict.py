"""
POST /api/ps70/predict — run temporal prediction from a base time
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.event import Event
from app.models.prediction import Prediction
from app.models.satellite_frame import SatelliteFrame
from app.schemas.common import (
    CenterPoint,
    GeoJSONPolygon,
    ModelMeta,
    PatternResult,
    UncertaintyBlock,
)
from app.schemas.predict import PredictRequest, PredictResponse, PredictionStep
from app.services.predict_service import run_prediction

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ps70", tags=["predict"])


@router.post("/predict", response_model=PredictResponse)
async def predict(
    body: PredictRequest,
    db: AsyncSession = Depends(get_db),
) -> PredictResponse:
    """
    Run temporal prediction from a base timestamp.

    - Loads all frames for the event up to and including start_timestamp.
    - Calls the ML adapter to produce T+12 and T+24 forecasts.
    - Writes Prediction rows (with provisional uncertainty polygon) to DB.
    - Returns PredictResponse.
    """
    # ── Validate event ─────────────────────────────────────────────────────
    event_result = await db.execute(
        select(Event).where(Event.event_id == body.event_id)
    )
    if event_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=422,
            detail=f"event_id '{body.event_id}' not found.",
        )

    # ── Load frames up to start_timestamp, sorted ascending ───────────────
    frames_result = await db.execute(
        select(SatelliteFrame)
        .where(
            SatelliteFrame.event_id == body.event_id,
            SatelliteFrame.timestamp <= body.start_timestamp,
        )
        .order_by(SatelliteFrame.timestamp.asc())
    )
    frames = list(frames_result.scalars().all())

    # Build frame dicts for the prediction service
    frame_dicts = [
        {
            "frame_id": f.frame_id,
            "timestamp": f.timestamp,
            "file_paths": f.file_paths,
            "channels": f.channels,
        }
        for f in frames
    ]

    # ── Run prediction ─────────────────────────────────────────────────────
    svc_result = run_prediction(
        event_id=body.event_id,
        base_time=body.start_timestamp,
        frames=frame_dicts,
    )

    model_meta = svc_result["model"]

    # ── Persist predictions to DB ──────────────────────────────────────────
    prediction_steps: list[PredictionStep] = []

    for pred in svc_result["predictions"]:
        poly_wkt = pred.get("uncertainty_wkt")

        db_prediction = Prediction(
            prediction_id=uuid.uuid4(),
            event_id=body.event_id,
            base_time=body.start_timestamp,
            valid_time=pred["valid_time"],
            pred_lat=pred["center"]["lat"],
            pred_lon=pred["center"]["lon"],
            pattern_label=pred["pattern"]["label"],
            pattern_confidence=pred["pattern"]["confidence"],
            model_name=model_meta["name"],
            model_version=model_meta["version"],
            uncertainty_status=pred["uncertainty_status"],
            # Store WKT string — PostGIS interprets it; SQLite stores as TEXT
            uncertainty_geom=f"SRID=4326;{poly_wkt}" if poly_wkt else None,
        )
        db.add(db_prediction)

        prediction_steps.append(
            PredictionStep(
                valid_time=pred["valid_time"],
                center=CenterPoint(
                    lat=pred["center"]["lat"],
                    lon=pred["center"]["lon"],
                ),
                pattern=PatternResult(
                    label=pred["pattern"]["label"],
                    confidence=pred["pattern"]["confidence"],
                ),
            )
        )

    await db.flush()

    logger.info(
        "[PREDICT] event=%s base=%s steps=%d model=%s",
        body.event_id,
        body.start_timestamp,
        len(prediction_steps),
        model_meta["name"],
    )

    # Build uncertainty block from the first prediction's polygon
    # (the full corridor geometry can be added once calibration is done)
    uncertainty = _build_uncertainty_block(svc_result["predictions"])

    return PredictResponse(
        event_id=body.event_id,
        base_time=body.start_timestamp,
        predictions=prediction_steps,
        uncertainty=uncertainty,
        model=ModelMeta(name=model_meta["name"], version=model_meta["version"]),
    )


def _build_uncertainty_block(predictions: list[dict]) -> UncertaintyBlock:
    """
    Build the uncertainty block for the response.

    Uses the T+24 polygon as the outer envelope — it encompasses the full
    forecast corridor. Labeled "provisional" until Day-6 calibration.
    """
    # Prefer T+24 (larger ellipse), fall back to T+12
    outer = None
    for pred in sorted(predictions, key=lambda p: p["horizon_hours"], reverse=True):
        poly = pred.get("uncertainty_polygon")
        if poly:
            outer = poly
            break

    if outer is None:
        return UncertaintyBlock(status="provisional")

    return UncertaintyBlock(
        status="provisional",
        geometry=GeoJSONPolygon(
            type=outer["type"],
            coordinates=outer["coordinates"],
        ),
        coverage_target=None,  # not set until calibration
    )
