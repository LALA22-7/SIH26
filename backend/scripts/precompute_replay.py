"""
scripts/precompute_replay.py
────────────────────────────
Pre-compute classification and prediction for every frame in an event
and store all results in the database.

This populates the DB so that GET /api/replay/{event_id} works fully
offline with no ML calls at serve time.

Usage
-----
    # From the backend/ directory:
    python -m scripts.precompute_replay --event_id biparjoy_2023

    # With explicit DB URL:
    DATABASE_SYNC_URL=postgresql+psycopg2://... python -m scripts.precompute_replay --event_id biparjoy_2023

What it does
------------
1. Loads all SatelliteFrame rows for the event (sorted by timestamp).
2. For each frame, runs classify → stores Classification row.
3. For each frame, assembles the sequence up to that frame, runs predict
   → stores Prediction rows (T+12, T+24) with provisional uncertainty polygon.
4. Loads IBTrACS / best-track actuals from data/ground_truth/ if available,
   computes Haversine error, stores MetricRow.
5. Prints a summary.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import uuid
from datetime import datetime, timezone

# Ensure backend and project root are on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _get_sync_engine():
    url = os.environ.get(
        "DATABASE_SYNC_URL",
        "sqlite:///cyclonewatch.db",
    )
    if "postgresql" not in url:
        url = "sqlite:///" + os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cyclonewatch.db")
    return create_engine(url, echo=False)


def _load_best_track(event_id: str) -> dict:
    """
    Load IBTrACS best-track CSV from data/ground_truth/<event_id>_best_track.csv.
    Returns a dict keyed by timestamp (UTC datetime) → (lat, lon).
    """
    import csv
    from pathlib import Path
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_root = os.environ.get("DATA_ROOT", os.path.join(project_root, "data"))
    path = Path(data_root) / "ground_truth" / f"{event_id}_best_track.csv"

    if not path.exists():
        logger.warning("Best-track file not found: %s — actuals will be empty", path)
        return {}

    track = {}
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
                lat = float(row["lat"])
                lon = float(row["lon"])
                track[ts] = (lat, lon)
            except (KeyError, ValueError) as e:
                logger.warning("Skipping bad row: %s", e)
    logger.info("Loaded %d best-track points for %s", len(track), event_id)
    return track


def _find_closest_actual(
    valid_time: datetime,
    best_track: dict,
    tolerance_hours: int = 3,
) -> tuple[float, float] | None:
    """Find the best-track point closest to valid_time within tolerance."""
    from datetime import timedelta

    best = None
    best_delta = None
    if valid_time.tzinfo is None:
        valid_time = valid_time.replace(tzinfo=timezone.utc)
    for ts, pos in best_track.items():
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        delta = abs((ts - valid_time).total_seconds())
        if delta <= tolerance_hours * 3600:
            if best_delta is None or delta < best_delta:
                best = pos
                best_delta = delta
    return best


def precompute(event_id: str) -> None:
    from app.models.event import Event
    from app.models.satellite_frame import SatelliteFrame
    from app.models.classification import Classification
    from app.models.prediction import Prediction
    from app.models.metric_row import MetricRow
    from app.services.classify_service import run_classification
    from app.services.predict_service import run_prediction
    from app.services.geo import haversine_km

    engine = _get_sync_engine()

    with Session(engine) as db:
        # ── Validate event ─────────────────────────────────────────────────
        event = db.execute(select(Event).where(Event.event_id == event_id)).scalar_one_or_none()
        if event is None:
            logger.error("Event '%s' not found in DB. Run seed_db.py first.", event_id)
            sys.exit(1)

        # ── Load frames ────────────────────────────────────────────────────
        frames = list(
            db.execute(
                select(SatelliteFrame)
                .where(SatelliteFrame.event_id == event_id)
                .order_by(SatelliteFrame.timestamp.asc())
            ).scalars()
        )
        logger.info("Found %d frames for event '%s'", len(frames), event_id)

        if not frames:
            logger.warning("No frames found. Register satellite frames first.")
            return

        # ── Load best-track actuals ────────────────────────────────────────
        best_track = _load_best_track(event_id)

        classify_count = 0
        predict_count = 0
        metric_count = 0

        for i, frame in enumerate(frames):
            logger.info("[%d/%d] Processing frame %s ts=%s", i + 1, len(frames), frame.frame_id, frame.timestamp)

            # ── Classification ─────────────────────────────────────────────
            svc = run_classification(
                frame_id=frame.frame_id,
                event_id=event_id,
                timestamp=frame.timestamp,
                file_paths=frame.file_paths,
                channels=frame.channels,
            )
            center = svc["center"]
            pattern = svc["pattern"]
            model = svc["model"]

            classification = Classification(
                classification_id=uuid.uuid4(),
                event_id=event_id,
                frame_id=frame.frame_id,
                timestamp=frame.timestamp,
                lat=center["lat"],
                lon=center["lon"],
                pattern=pattern["label"],
                confidence=pattern.get("confidence") or 0.0,
                model_name=model["name"],
                model_version=model["version"],
                geometry=f"SRID=4326;POINT({center['lon']} {center['lat']})",
            )
            db.add(classification)
            classify_count += 1

            # ── Prediction ─────────────────────────────────────────────────
            sequence_frames = [
                {
                    "frame_id": f.frame_id,
                    "timestamp": f.timestamp,
                    "file_paths": f.file_paths,
                    "channels": f.channels,
                }
                for f in frames[: i + 1]
            ]

            pred_result = run_prediction(
                event_id=event_id,
                base_time=frame.timestamp,
                frames=sequence_frames,
            )
            pred_model = pred_result["model"]

            for pred in pred_result["predictions"]:
                poly_wkt = pred.get("uncertainty_wkt")
                db_pred = Prediction(
                    prediction_id=uuid.uuid4(),
                    event_id=event_id,
                    base_time=frame.timestamp,
                    valid_time=pred["valid_time"],
                    pred_lat=pred["center"]["lat"],
                    pred_lon=pred["center"]["lon"],
                    pattern_label=pred["pattern"]["label"],
                    pattern_confidence=pred["pattern"].get("confidence") or 0.0,
                    model_name=pred_model["name"],
                    model_version=pred_model["version"],
                    uncertainty_status=pred["uncertainty_status"],
                    uncertainty_geom=f"SRID=4326;{poly_wkt}" if poly_wkt else None,
                )
                db.add(db_pred)
                predict_count += 1

                # ── Metric row ─────────────────────────────────────────────
                actual = _find_closest_actual(pred["valid_time"], best_track)
                if actual:
                    a_lat, a_lon = actual
                    error_km = haversine_km(
                        pred["center"]["lat"], pred["center"]["lon"], a_lat, a_lon
                    )
                    metric = MetricRow(
                        metric_id=uuid.uuid4(),
                        event_id=event_id,
                        base_time=frame.timestamp,
                        horizon_hours=pred["horizon_hours"],
                        pred_lat=pred["center"]["lat"],
                        pred_lon=pred["center"]["lon"],
                        actual_lat=a_lat,
                        actual_lon=a_lon,
                        error_km=error_km,
                        ground_truth_label=None,   # requires label file — extend if available
                        predicted_label=pred["pattern"]["label"],
                    )
                    db.add(metric)
                    metric_count += 1

        db.commit()

    logger.info(
        "Done. classifications=%d predictions=%d metrics=%d",
        classify_count,
        predict_count,
        metric_count,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-compute replay data for an event")
    parser.add_argument("--event_id", required=True, help="Event ID to precompute (e.g. biparjoy_2023)")
    args = parser.parse_args()
    precompute(args.event_id)


if __name__ == "__main__":
    main()
