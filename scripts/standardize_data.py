"""
standardize_data.py — GridSat-B1 raw NetCDF -> canonical [C, H, W] tensors

Fixes vs. previous version:
- Removed the duplicate RAW_DIR / NORMALIZED_DIR assignment bug (the second,
  relative-path definitions were silently overriding the PROJECT_ROOT-based
  ones).
- Timestamp is parsed from the *filename we control* (written by the fixed
  aws_downloader.py as `<event>_<YYYYMMDDTHHMMSSZ>.nc`) instead of a fragile
  `split("_")[1]` on the raw NOAA filename. Output npz files are named
  `<event>_<timestamp>.npz`, matching the manual's per-timestamp convention
  and making them directly joinable against IBTrACS on timestamp.
- Writes a sidecar per-frame JSON with full provenance (source, bbox, crs,
  normalization stats) as specified in the shared data contract (section 3.1
  of the execution manual).
- Writes data/normalized/normalized_manifest.csv summarizing every frame:
  event_id, timestamp (ISO), npz_path, tensor_shape, channels, nan_pct,
  min/max — this is the file validate_and_join.py should actually consume,
  since it has a real, parseable timestamp column instead of trying to
  regex it back out of a filename.
- Per-file try/except so one corrupt/missing-variable NetCDF doesn't kill
  the whole batch; failures are logged to the manifest with status=FAILED
  and a reason, matching the manual's "reject corrupt files clearly" rule.
"""

import os
import csv
import glob
import json
import numpy as np
import xarray as xr

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
NORMALIZED_DIR = os.path.join(PROJECT_ROOT, "data", "normalized")
MANIFEST_PATH = os.path.join(NORMALIZED_DIR, "normalized_manifest.csv")

os.makedirs(NORMALIZED_DIR, exist_ok=True)

BBOXES = {
    "biparjoy_2023": {"lat": slice(5.0, 25.0), "lon": slice(50.0, 75.0)},
    "amphan_2020": {"lat": slice(5.0, 25.0), "lon": slice(80.0, 95.0)},
    "fani_2019": {"lat": slice(5.0, 25.0), "lon": slice(80.0, 95.0)},
    "tauktae_2021": {"lat": slice(5.0, 25.0), "lon": slice(50.0, 75.0)},
    "phailin_2013": {"lat": slice(5.0, 25.0), "lon": slice(80.0, 95.0)},
    "hudhud_2014": {"lat": slice(5.0, 25.0), "lon": slice(80.0, 95.0)},
    "ockhi_2017": {"lat": slice(5.0, 25.0), "lon": slice(50.0, 75.0)},
}

# GridSat-B1 variable names for the channels we need
IR_VAR = "irwin_cdr"
WV_VAR = "irwvp"


def parse_event_and_timestamp(filename: str):
    """
    Expects filenames written by the fixed aws_downloader.py:
        <event_id>_<YYYYMMDDTHHMMSSZ>.nc
    e.g. biparjoy_2023_20230606T000000Z.nc
    """
    stem = filename.replace(".nc", "")
    for event_id in BBOXES.keys():
        prefix = event_id + "_"
        if stem.startswith(prefix):
            ts_compact = stem[len(prefix):]
            try:
                from datetime import datetime, timezone
                dt = datetime.strptime(ts_compact, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                iso_ts = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                return event_id, ts_compact, iso_ts
            except ValueError:
                return event_id, None, None
    return None, None, None


def standardize_file(nc_path: str, manifest_rows: list):
    filename = os.path.basename(nc_path)
    event_id, ts_compact, iso_ts = parse_event_and_timestamp(filename)

    row = {
        "event_id": event_id or "UNKNOWN",
        "timestamp": iso_ts or "",
        "source_file": filename,
        "npz_path": "",
        "tensor_shape": "",
        "channels": "ir,wv",
        "nan_percentage": "",
        "min_value": "",
        "max_value": "",
        "status": "FAILED",
        "reason": "",
    }

    if event_id is None or ts_compact is None:
        row["reason"] = "unparseable filename (expected <event>_<YYYYMMDDTHHMMSSZ>.nc)"
        manifest_rows.append(row)
        print(f"SKIP (bad filename): {filename}")
        return

    try:
        ds = xr.open_dataset(nc_path)

        if IR_VAR not in ds.variables or WV_VAR not in ds.variables:
            row["reason"] = f"missing variable(s); has {list(ds.data_vars)}"
            manifest_rows.append(row)
            print(f"SKIP (missing channel): {filename} -> {row['reason']}")
            ds.close()
            return

        bbox = BBOXES[event_id]
        subset = ds.sel(lat=bbox["lat"], lon=bbox["lon"])

        ir = subset[IR_VAR].values.squeeze()
        wv = subset[WV_VAR].values.squeeze()
        ds.close()

        if ir.size == 0 or wv.size == 0:
            row["reason"] = "empty array after bbox crop — check lat/lon slice matches storm region"
            manifest_rows.append(row)
            print(f"SKIP (empty crop): {filename}")
            return

        if ir.shape != wv.shape:
            row["reason"] = f"channel shape mismatch ir={ir.shape} wv={wv.shape}"
            manifest_rows.append(row)
            print(f"SKIP (shape mismatch): {filename}")
            return

        nan_pct = float(np.isnan(ir).mean() * 100 + np.isnan(wv).mean() * 100) / 2

        ir_clean = np.nan_to_num(ir, nan=0.0)
        wv_clean = np.nan_to_num(wv, nan=0.0)

        ir_min, ir_max = float(ir_clean.min()), float(ir_clean.max())
        wv_min, wv_max = float(wv_clean.min()), float(wv_clean.max())

        ir_norm = (ir_clean - ir_min) / (ir_max - ir_min + 1e-6)
        wv_norm = (wv_clean - wv_min) / (wv_max - wv_min + 1e-6)

        if np.all(ir_norm == 0) and np.all(wv_norm == 0):
            row["reason"] = "all-zero frame after normalization"
            manifest_rows.append(row)
            print(f"SKIP (all-zero): {filename}")
            return

        stacked_tensor = np.stack([ir_norm, wv_norm], axis=0)  # [C, H, W]

        event_out_dir = os.path.join(NORMALIZED_DIR, event_id, "frames")
        os.makedirs(event_out_dir, exist_ok=True)

        out_stem = f"{event_id}_{ts_compact}"
        out_path = os.path.join(event_out_dir, f"{out_stem}.npz")

        np.savez_compressed(
            out_path,
            image=stacked_tensor,
            channels=np.array(["ir", "wv"]),
            event_id=event_id,
            timestamp=iso_ts,
            crs="EPSG:4326",
        )

        # Sidecar metadata JSON per the shared data contract (section 3.1)
        sidecar = {
            "event_id": event_id,
            "timestamp": iso_ts,
            "source": "noaa_gridsat_b1",
            "source_file": filename,
            "channels": {"ir": IR_VAR, "water_vapor": WV_VAR},
            "crs": "EPSG:4326",
            "bbox": [bbox["lon"].start, bbox["lat"].start, bbox["lon"].stop, bbox["lat"].stop],
            "resolution": {"height": int(stacked_tensor.shape[1]), "width": int(stacked_tensor.shape[2])},
            "normalization": {
                "method": "per_frame_min_max",
                "ir_min": ir_min, "ir_max": ir_max,
                "wv_min": wv_min, "wv_max": wv_max,
            },
            "nan_percentage_pre_clean": round(nan_pct, 4),
        }
        with open(os.path.join(event_out_dir, f"{out_stem}.json"), "w") as f:
            json.dump(sidecar, f, indent=2)

        row.update({
            "npz_path": out_path,
            "tensor_shape": str(stacked_tensor.shape),
            "nan_percentage": round(nan_pct, 4),
            "min_value": 0.0,
            "max_value": 1.0,
            "status": "PASS" if nan_pct < 5.0 else "REVIEW",
            "reason": "" if nan_pct < 5.0 else "high NaN percentage pre-cleaning",
        })
        manifest_rows.append(row)
        print(f"Standardized: {out_path}  shape={stacked_tensor.shape}  nan%={nan_pct:.2f}")

    except Exception as e:
        row["reason"] = f"exception: {e}"
        manifest_rows.append(row)
        print(f"FAILED: {filename} -> {e}")


def main():
    nc_files = sorted(glob.glob(os.path.join(RAW_DIR, "*.nc")))
    if not nc_files:
        print(f"No .nc files found in {RAW_DIR}. Run aws_downloader.py first.")
        return

    manifest_rows = []
    for f in nc_files:
        standardize_file(f, manifest_rows)

    with open(MANIFEST_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "event_id", "timestamp", "source_file", "npz_path", "tensor_shape",
            "channels", "nan_percentage", "min_value", "max_value", "status", "reason",
        ])
        writer.writeheader()
        writer.writerows(manifest_rows)

    passed = sum(1 for r in manifest_rows if r["status"] == "PASS")
    review = sum(1 for r in manifest_rows if r["status"] == "REVIEW")
    failed = sum(1 for r in manifest_rows if r["status"] == "FAILED")
    print(f"\nStandardization complete: {passed} PASS, {review} REVIEW, {failed} FAILED")
    print(f"Manifest written to: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()