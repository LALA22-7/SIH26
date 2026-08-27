"""
POST /api/ps70/classify        — run classification on a satellite frame
GET  /api/ps70/classifications/{event_id} — time-series of all classifications for an event
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.classification import Classification
from app.models.event import Event
from app.models.satellite_frame import SatelliteFrame
from app.schemas.classify import (
    ClassificationListResponse,
    ClassificationRecord,
    ClassifyRequest,
    ClassifyResponse,
)
from app.schemas.common import CenterPoint, ModelMeta, PatternResult, SourceRef
from app.services.classify_service import run_classification

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ps70", tags=["classify"])


@router.post("/classify", response_model=ClassifyResponse)
async def classify_frame(
    body: ClassifyRequest,
    db: AsyncSession = Depends(get_db),
) -> ClassifyResponse:
    """
    Run classification inference on a satellite frame and persist the result.

    - Looks up the event and frame in the DB.
    - Calls the ML adapter (stub or real).
    - Writes a Classification row to PostGIS.
    - Returns the structured ClassifyResponse.
    """
    # ── Validate event exists ──────────────────────────────────────────────
    event_result = await db.execute(
        select(Event).where(Event.event_id == body.event_id)
    )
    event = event_result.scalar_one_or_none()
    if event is None:
        raise HTTPException(
            status_code=422,
            detail=f"event_id '{body.event_id}' not found. Register the event first.",
        )

    # ── Validate frame exists ──────────────────────────────────────────────
    frame_result = await db.execute(
        select(SatelliteFrame).where(SatelliteFrame.frame_id == body.frame_id)
    )
    frame: SatelliteFrame | None = frame_result.scalar_one_or_none()
    if frame is None:
        raise HTTPException(
            status_code=422,
            detail=f"frame_id '{body.frame_id}' not found. Register the frame first.",
        )

    # ── Run classification ─────────────────────────────────────────────────
    svc_result = run_classification(
        frame_id=body.frame_id,
        event_id=body.event_id,
        timestamp=body.timestamp,
        file_paths=frame.file_paths,
        channels=frame.channels,
    )

    center = svc_result["center"]
    pattern = svc_result["pattern"]
    model = svc_result["model"]

    # ── Persist to DB ──────────────────────────────────────────────────────
    classification = Classification(
        classification_id=uuid.uuid4(),
        event_id=body.event_id,
        frame_id=body.frame_id,
        timestamp=body.timestamp,
        lat=center["lat"],
        lon=center["lon"],
        pattern=pattern["label"],
        confidence=pattern["confidence"],
        model_name=model["name"],
        model_version=model["version"],
        # geometry is set via raw SQL for PostGIS; plain TEXT for SQLite (tests)
        geometry=_build_geometry_value(center["lon"], center["lat"]),
    )
    db.add(classification)
    await db.flush()

    logger.info(
        "[CLASSIFY] Saved classification_id=%s event=%s pattern=%s confidence=%.2f",
        classification.classification_id,
        body.event_id,
        pattern["label"],
        pattern["confidence"],
    )

    return ClassifyResponse(
        event_id=body.event_id,
        timestamp=body.timestamp,
        center=CenterPoint(lat=center["lat"], lon=center["lon"]),
        pattern=PatternResult(label=pattern["label"], confidence=pattern["confidence"]),
        source=SourceRef(frame_id=body.frame_id),
        model=ModelMeta(name=model["name"], version=model["version"]),
    )


def _build_geometry_value(lon: float, lat: float):
    """
    Return a geometry value suitable for the current DB backend.

    PostgreSQL: WKT string that PostGIS can interpret via ST_GeomFromText.
                (In production, GeoAlchemy2 handles the conversion transparently.)
    SQLite (tests): plain WKT string stored as TEXT.
    """
    return f"SRID=4326;POINT({lon} {lat})"


@router.get("/classifications/{event_id}", response_model=ClassificationListResponse)
async def list_classifications(
    event_id: str,
    db: AsyncSession = Depends(get_db),
) -> ClassificationListResponse:
    """
    Return all stored classifications for an event, sorted by timestamp ascending.
    Used by the frontend for the classification time-series view.
    """
    # Validate event
    event_result = await db.execute(
        select(Event).where(Event.event_id == event_id)
    )
    if event_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")

    rows_result = await db.execute(
        select(Classification)
        .where(Classification.event_id == event_id)
        .order_by(Classification.timestamp.asc())
    )
    rows: list[Classification] = list(rows_result.scalars().all())

    records = [
        ClassificationRecord(
            classification_id=str(row.classification_id),
            event_id=row.event_id,
            frame_id=row.frame_id,
            timestamp=row.timestamp,
            center=CenterPoint(lat=row.lat, lon=row.lon),
            pattern=PatternResult(label=row.pattern, confidence=row.confidence),
            model=ModelMeta(name=row.model_name, version=row.model_version),
        )
        for row in rows
    ]

    return ClassificationListResponse(
        event_id=event_id,
        count=len(records),
        classifications=records,
    )
