"""
update_metadata.py — Provenance manifest for PS70 CycloneWatch

Fixes vs. previous version:
- No longer re-parses timestamps out of raw .nc filenames (that broke as soon
  as filenames became `<event>_<timestamp>.nc`, since event_id itself
  contains an underscore and shifted the split index).
- Sources everything from data/normalized/normalized_manifest.csv and each
  frame's sidecar .json (both written by the fixed standardize_data.py),
  which already carry a correctly-parsed ISO timestamp and the real per-file
  bbox/crs/normalization stats — no re-deriving anything from filenames.
- Only includes frames that actually made it through standardization
  (status PASS or REVIEW); a raw .nc that failed to standardize doesn't
  belong in a "here's what's usable" manifest.
- License field is explicit rather than a vague "open_data" placeholder.
"""

import os
import csv
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NORMALIZED_DIR = os.path.join(PROJECT_ROOT, "data", "normalized")
NORMALIZED_MANIFEST = os.path.join(NORMALIZED_DIR, "normalized_manifest.csv")
METADATA_PATH = os.path.join(PROJECT_ROOT, "data", "metadata.csv")

LICENSE_NOTE = "NOAA CDR GridSat-B1 — U.S. Government work, public domain / open data"


def load_sidecar(npz_path: str) -> dict:
    """Each frame has a <stem>.json written alongside it by standardize_data.py."""
    sidecar_path = npz_path.replace(".npz", ".json")
    if os.path.exists(sidecar_path):
        with open(sidecar_path) as f:
            return json.load(f)
    return {}


def build_metadata():
    if not os.path.exists(NORMALIZED_MANIFEST):
        print(f"Error: {NORMALIZED_MANIFEST} not found. Run standardize_data.py first.")
        return

    header = [
        "file_id", "event_id", "source", "satellite", "product", "channel",
        "timestamp", "crs", "bbox", "resolution", "license", "status",
    ]
    rows = []
    skipped = 0

    with open(NORMALIZED_MANIFEST, newline="") as f:
        reader = csv.DictReader(f)
        for record in reader:
            if record["status"] not in ("PASS", "REVIEW"):
                skipped += 1
                continue

            npz_path = record["npz_path"]
            if not npz_path or not os.path.exists(npz_path):
                skipped += 1
                continue

            sidecar = load_sidecar(npz_path)
            bbox = sidecar.get("bbox", "")
            resolution = sidecar.get("resolution", {})
            resolution_str = f"{resolution.get('height', '')}x{resolution.get('width', '')}" if resolution else ""

            rows.append([
                os.path.basename(npz_path),
                record["event_id"],
                sidecar.get("source", "noaa_gridsat_b1"),
                "merged_geostationary",
                "gridsat_b1_cdr",
                "ir_wv_merged",
                record["timestamp"],
                sidecar.get("crs", "EPSG:4326"),
                ",".join(str(c) for c in bbox) if isinstance(bbox, list) else bbox,
                resolution_str,
                LICENSE_NOTE,
                record["status"],
            ])

    os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
    with open(METADATA_PATH, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"metadata.csv written with {len(rows)} usable frames ({skipped} skipped: failed/missing).")
    print(f"-> {METADATA_PATH}")


if __name__ == "__main__":
    build_metadata()