"""
scripts/seed_db.py
──────────────────
Populate the database with real frames from normalized_manifest.csv
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import csv
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST_CSV = os.path.join(PROJECT_ROOT, "data", "normalized", "normalized_manifest.csv")

def _get_engine():
    url = os.environ.get(
        "DATABASE_SYNC_URL",
        "sqlite:///cyclonewatch.db", # fallback for dev
    )
    # Using sqlite for testing if postgres is not available
    if "postgresql" not in url:
        # Create a local sqlite db in backend
        url = "sqlite:///" + os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cyclonewatch.db")
    return create_engine(url, echo=False)

def _reset(db: Session) -> None:
    logger.info("Resetting all seed data...")
    for table in ("metrics", "predictions", "classifications", "satellite_frames", "events"):
        try:
            db.execute(text(f"DELETE FROM {table}"))
        except:
            pass
    db.commit()
    logger.info("Reset complete.")

def seed(reset: bool = False) -> None:
    # Need to load the models so tables are created/known if using SQLAlchemy
    try:
        from app.models.event import Event
        from app.models.satellite_frame import SatelliteFrame
        from app.models.base import Base
    except ImportError as e:
        logger.error(f"Could not import models: {e}. Make sure you run from the backend directory.")
        return

    engine = _get_engine()
    # Create tables if sqlite
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        if reset:
            _reset(db)

        # ── 1. Events ───────────────────────────────────────────────────────
        events = {
            "biparjoy_2023": Event(
                event_id="biparjoy_2023",
                name="Biparjoy",
                year=2023,
                basin="NI",
                start_time=datetime(2023, 6, 6, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2023, 6, 16, 0, 0, tzinfo=timezone.utc),
                notes="Primary demo event."
            ),
            "amphan_2020": Event(
                event_id="amphan_2020",
                name="Amphan",
                year=2020,
                basin="NI",
                start_time=datetime(2020, 5, 16, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2020, 5, 21, 0, 0, tzinfo=timezone.utc),
                notes="Secondary demo event."
            ),
            "fani_2019": Event(
                event_id="fani_2019",
                name="Fani",
                year=2019,
                basin="NI",
                start_time=datetime(2019, 4, 25, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2019, 5, 4, 0, 0, tzinfo=timezone.utc),
                notes="Extra historical event."
            ),
            "tauktae_2021": Event(
                event_id="tauktae_2021",
                name="Tauktae",
                year=2021,
                basin="NI",
                start_time=datetime(2021, 5, 13, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2021, 5, 19, 0, 0, tzinfo=timezone.utc),
                notes="Extra historical event."
            ),
            "phailin_2013": Event(
                event_id="phailin_2013",
                name="Phailin",
                year=2013,
                basin="NI",
                start_time=datetime(2013, 10, 7, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2013, 10, 14, 0, 0, tzinfo=timezone.utc),
                notes="Extra historical event."
            ),
            "hudhud_2014": Event(
                event_id="hudhud_2014",
                name="Hudhud",
                year=2014,
                basin="NI",
                start_time=datetime(2014, 10, 6, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2014, 10, 14, 0, 0, tzinfo=timezone.utc),
                notes="Extra historical event."
            ),
            "ockhi_2017": Event(
                event_id="ockhi_2017",
                name="Ockhi",
                year=2017,
                basin="NI",
                start_time=datetime(2017, 11, 28, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2017, 12, 5, 0, 0, tzinfo=timezone.utc),
                notes="Extra historical event."
            )
        }
        
        for eid, ev in events.items():
            if not db.get(Event, eid):
                db.add(ev)
                logger.info("Added Event: %s", eid)
        db.commit()

        # ── 2. Satellite frames ─────────────────────────────────────────────
        if not os.path.exists(MANIFEST_CSV):
            logger.error("Manifest not found: %s", MANIFEST_CSV)
            return

        with open(MANIFEST_CSV, newline="") as f:
            reader = csv.DictReader(f)
            frames_added = 0
            for row in reader:
                if row["status"] not in ("PASS", "REVIEW"):
                    continue
                
                event_id = row["event_id"]
                if event_id not in events:
                    continue
                    
                frame_id = os.path.basename(row["npz_path"])
                ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
                
                # Reconstruct the correct local path for this machine
                correct_npz_path = os.path.join(PROJECT_ROOT, "data", "normalized", event_id, "frames", frame_id)
                
                existing = db.get(SatelliteFrame, frame_id)
                if not existing:
                    frame = SatelliteFrame(
                        frame_id=frame_id,
                        event_id=event_id,
                        timestamp=ts,
                        channels={"ir": True, "water_vapor": True},
                        file_paths={
                            "npz": correct_npz_path,
                        },
                        crs="EPSG:4326",
                        bbox=None, 
                        resolution={"width": 256, "height": 256},
                        source="INSAT-3D",
                        local_path=correct_npz_path,
                    )
                    db.add(frame)
                    frames_added += 1
            
            db.commit()
            logger.info("Added %d SatelliteFrames.", frames_added)

    logger.info("Seed complete.")

def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data into CycloneWatch DB")
    parser.add_argument("--reset", action="store_true", help="Delete existing seed rows before inserting")
    args = parser.parse_args()
    seed(reset=args.reset)

if __name__ == "__main__":
    main()
