"""
validate_and_join.py — Ground-truth join for PS70 CycloneWatch

Fixes vs. previous version:
- Reads data/normalized/normalized_manifest.csv (written by the fixed
  standardize_data.py) for event_id/timestamp instead of regex-guessing a
  timestamp back out of the .npz filename. This is what actually made the
  original join fail: filenames like "2020.npz" have no embedded timestamp
  at all, and even with the new "<event>_<ts>.npz" naming, exact-match
  regex parsing is one filename-convention change away from silently
  breaking again.
- Ground-truth join uses NEAREST timestamp within a tolerance window
  (default 90 minutes) instead of exact equality. Satellite frames land on
  the hour; best-track points aren't guaranteed to line up to the second,
  per the cyclone dossier's own caveat about confirming cadence/alignment
  before computing MAE. Exact `==` silently drops valid matches.
- Reports match distance (minutes) per row so you can audit alignment
  quality, and flags any frame with no ground-truth match within tolerance
  instead of leaving lat/lon blank with no explanation.
- pattern_label stays "unlabeled" until Research's taxonomy labels are
  wired in — this script only owns the position join, not classification
  labels. Flagged explicitly in the printed summary so it isn't mistaken
  for a finished training manifest.
"""

import os
import glob
import csv
import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NORMALIZED_DIR = os.path.join(PROJECT_ROOT, "data", "normalized")
NORMALIZED_MANIFEST = os.path.join(NORMALIZED_DIR, "normalized_manifest.csv")
GROUND_TRUTH_DIR = os.path.join(PROJECT_ROOT, "data", "ground_truth")
OUTPUT_MANIFEST = os.path.join(PROJECT_ROOT, "data", "training_manifest.csv")

MATCH_TOLERANCE_MINUTES = 90

EVENT_KEY_MAP = {
    "biparjoy_2023": "biparjoy",
    "amphan_2020": "amphan",
}


def load_ground_truth() -> dict:
    gt_dfs = {}
    gt_files = glob.glob(os.path.join(GROUND_TRUTH_DIR, "*.csv"))
    for gt_file in gt_files:
        try:
            df_gt = pd.read_csv(gt_file, low_memory=False)
            time_col = next((c for c in ['timestamp', 'ISO_TIME', 'ISO TIME', 'time', 'DATE']
                              if c in df_gt.columns), None)
            if not time_col:
                print(f"Warning: no time column in {gt_file}. Columns: {list(df_gt.columns)}")
                continue

            df_gt['timestamp_dt'] = pd.to_datetime(df_gt[time_col], errors='coerce', utc=True)
            df_gt = df_gt.dropna(subset=['timestamp_dt']).sort_values('timestamp_dt')

            lat_col = next((c for c in df_gt.columns if c.upper() in ['LAT', 'LATITUDE']), None)
            lon_col = next((c for c in df_gt.columns if c.upper() in ['LON', 'LONGITUDE', 'LONG']), None)
            if not lat_col or not lon_col:
                print(f"Warning: no lat/lon columns found in {gt_file}. Skipping.")
                continue

            event_name = os.path.basename(gt_file).split("_")[0].lower()
            gt_dfs[event_name] = {"df": df_gt, "lat_col": lat_col, "lon_col": lon_col}
        except Exception as e:
            print(f"Error reading {gt_file}: {e}")
    return gt_dfs


def nearest_match(df_gt: pd.DataFrame, target_ts: pd.Timestamp, tolerance_minutes: int):
    """Returns (row, distance_minutes) for the closest ground-truth timestamp within tolerance, else (None, None)."""
    if df_gt.empty:
        return None, None
    diffs = (df_gt['timestamp_dt'] - target_ts).abs()
    idx_min = diffs.idxmin()
    min_diff = diffs.loc[idx_min]
    if min_diff <= pd.Timedelta(minutes=tolerance_minutes):
        return df_gt.loc[idx_min], min_diff.total_seconds() / 60.0
    return None, None


def validate_and_join():
    print("Starting data validation and ground-truth join...")

    if not os.path.exists(NORMALIZED_MANIFEST):
        print(f"Error: {NORMALIZED_MANIFEST} not found. Run standardize_data.py first.")
        return

    manifest_df = pd.read_csv(NORMALIZED_MANIFEST)
    manifest_df = manifest_df[manifest_df["status"].isin(["PASS", "REVIEW"])]
    if manifest_df.empty:
        print("Error: no PASS/REVIEW frames in normalized_manifest.csv.")
        return

    gt_dfs = load_ground_truth()

    validation_records = []
    unmatched_count = 0

    for _, record in manifest_df.iterrows():
        npz_path = record["npz_path"]
        event_id = record["event_id"]
        event_key = EVENT_KEY_MAP.get(event_id, event_id.split("_")[0])

        if not npz_path or not os.path.exists(npz_path):
            print(f"SKIP (file missing on disk): {npz_path}")
            continue

        data = np.load(npz_path)
        array_key = 'image' if 'image' in data else list(data.keys())[0]
        arr = data[array_key]

        nan_percentage = float(np.isnan(arr).mean() * 100)
        is_all_zeros = bool(np.all(arr == 0))

        lat, lon, pattern, match_distance_min = "", "", "unlabeled", ""

        if event_key in gt_dfs:
            target_ts = pd.to_datetime(record["timestamp"], utc=True, errors="coerce")
            if pd.notna(target_ts):
                gt_entry = gt_dfs[event_key]
                match_row, distance = nearest_match(gt_entry["df"], target_ts, MATCH_TOLERANCE_MINUTES)
                if match_row is not None:
                    lat = float(match_row[gt_entry["lat_col"]])
                    lon = float(match_row[gt_entry["lon_col"]])
                    match_distance_min = round(distance, 1)
                else:
                    unmatched_count += 1
        else:
            unmatched_count += 1

        validation_records.append({
            "file_id": os.path.basename(npz_path),
            "event_id": event_id,
            "timestamp": record["timestamp"],
            "tensor_shape": record["tensor_shape"],
            "nan_percentage": round(nan_percentage, 2),
            "center_lat": lat,
            "center_lon": lon,
            "gt_match_distance_min": match_distance_min,
            "pattern_label": pattern,
            "validation_status": "PASS" if nan_percentage < 5.0 and not is_all_zeros else "REVIEW",
        })

    out_df = pd.DataFrame(validation_records)
    out_df.to_csv(OUTPUT_MANIFEST, index=False)

    matched = len(out_df[out_df["center_lat"] != ""])
    print(f"\nJoin complete: {matched}/{len(out_df)} frames matched to ground truth "
          f"(within {MATCH_TOLERANCE_MINUTES} min tolerance).")
    if unmatched_count:
        print(f"WARNING: {unmatched_count} frames had no ground-truth match — "
              f"check event naming in data/ground_truth/*.csv matches {list(EVENT_KEY_MAP.values())}.")
    print("NOTE: pattern_label is still 'unlabeled' for every row — this script only joins "
          "position (lat/lon), not taxonomy labels. Those come from Research's classification "
          "labels and need a separate join before this is training-complete for the classifier head.")
    print(f"Training manifest written to: {OUTPUT_MANIFEST}")


if __name__ == "__main__":
    validate_and_join()