"""
split_ibtracs.py — Split the raw IBTrACS North Indian Ocean file into the
per-event best-track CSVs the rest of the pipeline expects.

The raw NOAA export (ibtracs.NI.list.v04r00.csv) contains every North Indian
Ocean storm since 1842, plus a units row directly under the header. This
script:
  - skips the units row (row 2) when loading
  - filters to NAME + SEASON for each locked event (Biparjoy/2023, Amphan/2020)
  - normalizes timestamps to UTC
  - writes data/ground_truth/<event>_best_track.csv with the minimal schema
    the join script (validate_and_join.py) expects: event_id, timestamp, lat, lon
    (plus the original WMO/USA wind+pressure fields kept for reference)

Run this once whenever the raw IBTrACS export is updated.
"""

import os
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUND_TRUTH_DIR = os.path.join(PROJECT_ROOT, "data", "ground_truth")
os.makedirs(GROUND_TRUTH_DIR, exist_ok=True)

# Path to the raw IBTrACS NI export — adjust if you keep it somewhere else.
RAW_IBTRACS_PATH = os.path.join(PROJECT_ROOT, "data", "ground_truth", "ibtracs.NI.list.v04r00.csv")

# Locked events per the taxonomy/event manifest (section 5A of the execution manual)
EVENTS = [
    {"event_id": "biparjoy_2023", "ibtracs_name": "BIPARJOY",    "season": 2023},
    {"event_id": "amphan_2020",   "ibtracs_name": "AMPHAN",      "season": 2020},
    {"event_id": "fani_2019",     "ibtracs_name": "FANI",        "season": 2019},
    {"event_id": "tauktae_2021",  "ibtracs_name": "TAUKTAE",     "season": 2021},
    {"event_id": "phailin_2013",  "ibtracs_name": "PHAILIN",     "season": 2013},
    {"event_id": "hudhud_2014",   "ibtracs_name": "HUDHUD",      "season": 2014},
    {"event_id": "ockhi_2017",    "ibtracs_name": "OCKHI",       "season": 2017},
]


def split_ibtracs():
    if not os.path.exists(RAW_IBTRACS_PATH):
        print(f"Error: raw IBTrACS file not found at {RAW_IBTRACS_PATH}")
        return

    # Row index 1 (the second physical row, right after the header) is the
    # units row — skip it so pandas doesn't corrupt numeric dtypes.
    df = pd.read_csv(RAW_IBTRACS_PATH, skiprows=[1], low_memory=False)

    # Prefer RSMC New Delhi's own reported position for an apples-to-apples
    # "model vs IMD" comparison, per the cyclone dossier's guidance. Fall back
    # to the blended LAT/LON columns if the New Delhi fields aren't present
    # or are empty for a given row.
    has_newdelhi = "NEWDELHI_LAT" in df.columns and "NEWDELHI_LON" in df.columns

    for event in EVENTS:
        subset = df[(df["NAME"] == event["ibtracs_name"]) & (df["SEASON"] == event["season"])].copy()

        if subset.empty:
            print(f"WARNING: no rows found for {event['ibtracs_name']} / {event['season']} — "
                  f"check the NAME/SEASON values match the raw file exactly.")
            continue

        subset["timestamp"] = pd.to_datetime(subset["ISO_TIME"], utc=True, errors="coerce")
        subset = subset.dropna(subset=["timestamp"]).sort_values("timestamp")

        if has_newdelhi:
            lat = pd.to_numeric(subset["NEWDELHI_LAT"], errors="coerce")
            lon = pd.to_numeric(subset["NEWDELHI_LON"], errors="coerce")
            # Fall back to blended LAT/LON where New Delhi's own report is blank
            lat = lat.fillna(pd.to_numeric(subset["LAT"], errors="coerce"))
            lon = lon.fillna(pd.to_numeric(subset["LON"], errors="coerce"))
        else:
            lat = pd.to_numeric(subset["LAT"], errors="coerce")
            lon = pd.to_numeric(subset["LON"], errors="coerce")

        out = pd.DataFrame({
            "event_id": event["event_id"],
            "timestamp": subset["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lat": lat.values,
            "lon": lon.values,
            "wmo_wind_kts": subset.get("WMO_WIND"),
            "wmo_pres_mb": subset.get("WMO_PRES"),
        })
        out = out.dropna(subset=["lat", "lon"])

        out_path = os.path.join(GROUND_TRUTH_DIR, f"{event['event_id']}_best_track.csv")
        out.to_csv(out_path, index=False)
        print(f"{event['event_id']}: {len(out)} best-track points -> {out_path}")


if __name__ == "__main__":
    split_ibtracs()