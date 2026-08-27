"""
scripts/seed_db.py
──────────────────
Populate the database with demo data so every API endpoint returns
meaningful responses without real satellite files or a trained model.

What is inserted
----------------
- 1 event          : biparjoy_2023
- 3 satellite frames: metadata only (no real files required)
- 3 classifications : PostGIS points over the Bay of Bengal
- 2 predictions    : T+12 and T+24 with provisional uncertainty polygon
- 5 metric rows    : pre-computed Haversine errors for /api/metrics

Usage
-----
    # From the backend/ directory:
    python -m scripts.seed_db

    # Against a custom DB URL:
    DATABASE_SYNC_URL=postgresql+psycopg2://... python -m scripts.seed_db

    # Wipe existing seed data first:
    python -m scripts.seed_db --reset
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

# Ensure project root is importable when run as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Demo constants ─────────────────────────────────────────────────────────────
EVENT_ID = "biparjoy_2023"
T0 = datetime(2023, 6, 14, 12, 0, tzinfo=timezone.utc)   # anchor time


def _get_engine():
    url = os.environ.get(
        "DATABASE_SYNC_URL",
        "postgresql+psycopg2://cyclone:cyclone_secret@localhost:5432/cyclonewatch",
    )
    return create_engine(url, echo=False)


def _reset(db: Session) -> None:
    """Delete all seed rows in dependency order."""
    logger.info("Resetting seed data for event '%s'…", EVENT_ID)
    for table in ("metrics", "predictions", "classifications", "satellite_frames", "events"):
        db.execute(
            text(f"DELETE FROM {table} WHERE event_id = :eid"),
            {"eid": EVENT_ID},
        )
    db.commit()
    logger.info("Reset complete.")


def seed(reset: bool = False) -> None:
    from app.models.event import Event
    from app.models.satellite_frame import SatelliteFrame
    from app.models.classification import Classification
    from app.models.prediction import Prediction
    from app.models.metric_row import MetricRow

    engine = _get_engine()

    with Session(engine) as db:
        if reset:
            _reset(db)

        # ── Guard: skip if already seeded ──────────────────────────────────
        existing = db.get(Event, EVENT_ID)
        if existing is not None:
            logger.info("Event '%s' already exists — skipping seed. Use --reset to re-seed.", EVENT_ID)
            return

        logger.info("Seeding demo data for event '%s'…", EVENT_ID)

        # ── 1. Event ───────────────────────────────────────────────────────
        event = Event(
            event_id=EVENT_ID,
            name="Biparjoy",
            year=2023,
            basin="NI",
            start_time=datetime(2023, 6, 6, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2023, 6, 16, 0, 0, tzinfo=timezone.utc),
            notes=(
                "Primary demo event. Very severe cyclonic storm, Arabian Sea. "
                "Made landfall near Jakhau, Gujarat on 15 June 2023."
            ),
        )
        db.add(event)
        logger.info("  + Event: %s", EVENT_ID)

        # ── 2. Satellite frames (metadata only, no real files) ─────────────
        frame_timestamps = [
            T0 - timedelta(hours=12),
            T0 - timedelta(hours=6),
            T0,
        ]
        frames: list[SatelliteFrame] = []

        for i, ts in enumerate(frame_timestamps):
            tag = ts.strftime("%Y-%m-%dT%H%MZ")
            frame = SatelliteFrame(
                frame_id=f"frame_{i + 1:03d}",
                event_id=EVENT_ID,
                timestamp=ts,
                channels={"ir": f"ir_{tag}.tif", "water_vapor": f"wv_{tag}.tif"},
                file_paths={
                    "ir": f"/data/normalized/{EVENT_ID}_{tag}_ir_insat.tif",
                    "water_vapor": f"/data/normalized/{EVENT_ID}_{tag}_wv_insat.tif",
                },
                crs="EPSG:4326",
                bbox=[60.0, 5.0, 80.0, 25.0],
                resolution={"width": 512, "height": 512},
                source="INSAT-3D (demo metadata — file not present)",
                local_path=None,
            )
            db.add(frame)
            frames.append(frame)
            logger.info("  + Frame: %s  ts=%s", frame.frame_id, ts.isoformat())

        # ── 3. Classifications ─────────────────────────────────────────────
        # Cyclone centre tracks northwest as it intensifies
        classification_data = [
            # (timestamp, lat, lon, pattern, confidence)
            (T0 - timedelta(hours=12), 14.80, 68.90, "curved_band",    0.68),
            (T0 - timedelta(hours=6),  15.00, 68.65, "banding",        0.74),
            (T0,                       15.20, 68.40, "banding",        0.72),
        ]

        for i, (ts, lat, lon, pattern, conf) in enumerate(classification_data):
            cls = Classification(
                classification_id=uuid.uuid4(),
                event_id=EVENT_ID,
                frame_id=frames[i].frame_id,
                timestamp=ts,
                lat=lat,
                lon=lon,
                pattern=pattern,
                confidence=conf,
                model_name="ps70-classifier-stub",
                model_version="0.1.0",
                # WKT point — PostGIS stores as geometry; SQLite as TEXT
                geometry=f"SRID=4326;POINT({lon} {lat})",
            )
            db.add(cls)
            logger.info("  + Classification: %s  lat=%.2f lon=%.2f  pattern=%s", ts.isoformat(), lat, lon, pattern)

        # ── 4. Predictions (T+12 and T+24 from T0) ────────────────────────
        from app.services.predict_service import _build_uncertainty_polygon

        predictions_data = [
            # (horizon_hours, pred_lat, pred_lon, pattern, confidence, sigma_lat, sigma_lon)
            (12, 16.10, 67.80, "eye", 0.64, 0.5, 0.5),
            (24, 17.20, 67.10, "eye", 0.59, 0.8, 0.8),
        ]

        for h, p_lat, p_lon, pat, conf, s_lat, s_lon in predictions_data:
            valid_time = T0 + timedelta(hours=h)
            poly = _build_uncertainty_polygon(p_lat, p_lon, s_lat, s_lon)

            from shapely.geometry import shape
            poly_wkt = shape(poly).wkt

            pred = Prediction(
                prediction_id=uuid.uuid4(),
                event_id=EVENT_ID,
                base_time=T0,
                valid_time=valid_time,
                pred_lat=p_lat,
                pred_lon=p_lon,
                pattern_label=pat,
                pattern_confidence=conf,
                model_name="ps70-temporal-stub",
                model_version="0.1.0",
                uncertainty_status="provisional",
                uncertainty_geom=f"SRID=4326;{poly_wkt}",
            )
            db.add(pred)
            logger.info(
                "  + Prediction T+%dh: lat=%.2f lon=%.2f pattern=%s uncertainty=%s",
                h, p_lat, p_lon, pat, pred.uncertainty_status,
            )

        # ── 5. Metric rows (pre-computed Haversine errors) ─────────────────
        # IBTrACS best-track actuals for Biparjoy (approximate demo values)
        # Source: RSMC New Delhi best-track data
        actuals_data = [
            # (base_time, horizon_hours, pred_lat, pred_lon, actual_lat, actual_lon)
            (T0 - timedelta(hours=12), 12, 15.00, 68.65, 15.10, 68.55),
            (T0 - timedelta(hours=12), 24, 15.80, 68.10, 15.90, 68.00),
            (T0,                       12, 16.10, 67.80, 16.20, 67.70),
            (T0,                       24, 17.20, 67.10, 17.30, 67.00),
            (T0 - timedelta(hours=6),  12, 15.50, 68.25, 15.55, 68.20),
        ]

        from app.services.geo import haversine_km

        for bt, h, p_lat, p_lon, a_lat, a_lon in actuals_data:
            error_km = haversine_km(p_lat, p_lon, a_lat, a_lon)
            metric = MetricRow(
                metric_id=uuid.uuid4(),
                event_id=EVENT_ID,
                base_time=bt,
                horizon_hours=h,
                pred_lat=p_lat,
                pred_lon=p_lon,
                actual_lat=a_lat,
                actual_lon=a_lon,
                error_km=round(error_km, 2),
                ground_truth_label="banding",
                predicted_label="banding",
            )
            db.add(metric)
            logger.info(
                "  + Metric T+%dh base=%s  error=%.2f km",
                h, bt.strftime("%Y-%m-%dT%H:%MZ"), error_km,
            )

        db.commit()

    logger.info("Seed complete. Run 'docker compose up' and hit http://localhost:8000/docs to explore.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data into CycloneWatch DB")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing seed rows before inserting (safe to re-run)",
    )
    args = parser.parse_args()
    seed(reset=args.reset)


if __name__ == "__main__":
    main()
