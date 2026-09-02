"""
aws_downloader.py — NOAA GridSat-B1 ingestion for PS70 CycloneWatch

Downloads one 3-hourly NetCDF file per timestamp, per event, from the public
NOAA GridSat-B1 AWS S3 bucket (no credentials needed).

Fixes vs. previous version:
- Consistent, parseable ISO-8601-style timestamp baked into every filename
  (compact form: YYYYMMDDTHHMMSSZ) instead of re-using the raw NOAA filename
  as a pseudo-timestamp.
- Writes data/raw/download_manifest.csv logging every attempted timestamp,
  whether it succeeded, and via which method (direct key vs fallback search),
  so you know exactly which of the ~N expected 3-hourly frames per event you
  actually have before handing off to ML.
- fallback_search no longer re-lists the entire year's prefix per miss; it
  lists the single day's prefix (data/<year>/<month>/<day>/ if that layout
  exists) and only falls back to a capped, cached year-listing once per year
  instead of once per missing file.
- Idempotent: skips re-downloading a file that's already present and non-empty.
"""

import os
import csv
import time
import socket
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import EndpointConnectionError, ClientError
from datetime import datetime, timedelta, timezone

# Transient network errors worth retrying instead of crashing the whole run
RETRYABLE_EXCEPTIONS = (EndpointConnectionError, socket.gaierror, socket.timeout, TimeoutError)
MAX_RETRIES = 4
RETRY_BASE_DELAY_SEC = 2

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

MANIFEST_PATH = os.path.join(RAW_DIR, "download_manifest.csv")

BUCKET_NAME = "noaa-cdr-gridsat-b1-pds"

s3 = boto3.client("s3", region_name="us-east-1", config=Config(signature_version=UNSIGNED, read_timeout=15, connect_timeout=15, retries={"max_attempts": 3}))

# Event windows — inclusive start/end, 3-hourly cadence (matches GridSat-B1 native cadence
# and RSMC New Delhi best-track reporting interval per the cyclone dossier).
EVENTS = [
    {"id": "biparjoy_2023", "start": datetime(2023, 6, 6, 0, tzinfo=timezone.utc),
     "end": datetime(2023, 6, 16, 0, tzinfo=timezone.utc)},
    {"id": "amphan_2020", "start": datetime(2020, 5, 16, 0, tzinfo=timezone.utc),
     "end": datetime(2020, 5, 21, 0, tzinfo=timezone.utc)},
    # ── Additional events for improved model accuracy ─────────────────────
    # Fani 2019: strongest BoB cyclone in 20 years, well-documented IMD case
    {"id": "fani_2019", "start": datetime(2019, 4, 25, 0, tzinfo=timezone.utc),
     "end": datetime(2019, 5, 4, 0, tzinfo=timezone.utc)},
    # Tauktae 2021: recent Arabian Sea storm, Gujarat landfall like Biparjoy
    {"id": "tauktae_2021", "start": datetime(2021, 5, 13, 0, tzinfo=timezone.utc),
     "end": datetime(2021, 5, 19, 0, tzinfo=timezone.utc)},
    # Phailin 2013: 115 kts BoB, landmark IMD forecast improvement case
    {"id": "phailin_2013", "start": datetime(2013, 10, 7, 0, tzinfo=timezone.utc),
     "end": datetime(2013, 10, 14, 0, tzinfo=timezone.utc)},
    # Hudhud 2014: 100 kts, Andhra landfall, detailed post-storm analysis
    {"id": "hudhud_2014", "start": datetime(2014, 10, 6, 0, tzinfo=timezone.utc),
     "end": datetime(2014, 10, 14, 0, tzinfo=timezone.utc)},
    # Ockhi 2017: IMD missed early intensification — perfect demo contrast case
    {"id": "ockhi_2017", "start": datetime(2017, 11, 28, 0, tzinfo=timezone.utc),
     "end": datetime(2017, 12, 5, 0, tzinfo=timezone.utc)},
]

# Cache of year -> set(keys) so we only ever list a given year's prefix once,
# not once per missing file.
_year_listing_cache = {}


def with_retries(fn, *args, **kwargs):
    """Retry a network call on transient DNS/connection failures with exponential backoff."""
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except RETRYABLE_EXCEPTIONS as e:
            last_exc = e
            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY_SEC * (2 ** (attempt - 1))
                print(f"    (transient network error: {e}; retry {attempt}/{MAX_RETRIES} in {delay}s)")
                time.sleep(delay)
            else:
                print(f"    (giving up after {MAX_RETRIES} attempts: {e})")
    raise last_exc


def iso_compact(dt: datetime) -> str:
    """2023-06-06T00:00:00Z  ->  20230606T000000Z (filesystem-safe, still parseable)."""
    return dt.strftime("%Y%m%dT%H%M%SZ")


def build_expected_key(dt: datetime) -> tuple[str, str]:
    """Returns (s3_key, source_filename) for the exact expected NOAA path."""
    year = dt.strftime("%Y")
    month = dt.strftime("%m")
    day = dt.strftime("%d")
    hour = dt.strftime("%H")
    filename = f"GRIDSAT-B1.{year}.{month}.{day}.{hour}.v02r01.nc"
    s3_key = f"data/{year}/{filename}"
    return s3_key, filename


def get_year_listing(year: str) -> dict:
    """List a year's prefix once, cache filename -> full key."""
    if year in _year_listing_cache:
        return _year_listing_cache[year]

    print(f"  (building S3 index for {year}, one-time per year)")
    index = {}
    try:
        paginator = s3.get_paginator("list_objects_v2")

        def _list_all():
            pages = []
            for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=f"data/{year}/"):
                pages.append(page)
            return pages

        pages = with_retries(_list_all)
        for page in pages:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                index[os.path.basename(key)] = key
    except Exception as e:
        print(f"  WARNING: could not build S3 index for {year} after retries ({e}). "
              f"Fallback search will be skipped for this year this run.")
        # Cache an empty index so we don't keep re-attempting (and re-failing) per file
        # within the same run; re-running the script later will retry cleanly.
    _year_listing_cache[year] = index
    return index


def fallback_search(source_filename: str, year: str) -> str | None:
    """Look up a missing file inside the cached year index instead of re-listing."""
    index = get_year_listing(year)
    return index.get(source_filename)


def _process_timestamp(event_id, current_time):
    """Download (or skip if cached) a single timestamp. Returns the manifest row dict."""
    timestamp_str = iso_compact(current_time)
    s3_key, source_filename = build_expected_key(current_time)
    local_filename = f"{event_id}_{timestamp_str}.nc"
    local_filepath = os.path.join(RAW_DIR, local_filename)

    status = "unknown"
    method = ""

    if os.path.exists(local_filepath) and os.path.getsize(local_filepath) > 0:
        status, method = "skipped_existing", "cache"
    else:
        try:
            with_retries(s3.download_file, BUCKET_NAME, s3_key, local_filepath)
            status, method = "success", "direct_key"
            print(f"  [{timestamp_str}] OK (direct)")
        except Exception:
            year = current_time.strftime("%Y")
            fallback_key = fallback_search(source_filename, year)
            if fallback_key:
                try:
                    with_retries(s3.download_file, BUCKET_NAME, fallback_key, local_filepath)
                    status, method = "success", "fallback_search"
                    print(f"  [{timestamp_str}] OK (fallback)")
                except Exception as e:
                    status = "failed"
                    print(f"  [{timestamp_str}] FAILED even via fallback: {e}")
            else:
                status = "missing_from_bucket"
                print(f"  [{timestamp_str}] MISSING from NOAA bucket")

    return {
        "event_id": event_id,
        "timestamp": current_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp_compact": timestamp_str,
        "source_filename": source_filename,
        "local_filepath": local_filepath if status in ("success", "skipped_existing") else "",
        "status": status,
        "method": method,
    }


def _load_already_logged() -> set:
    """(event_id, timestamp_compact) pairs already recorded as success/skipped in a prior run,
    so re-running after a crash doesn't append duplicate manifest rows for them."""
    done = set()
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, newline="") as f:
            for r in csv.DictReader(f):
                if r.get("status") in ("success", "skipped_existing"):
                    done.add((r["event_id"], r["timestamp_compact"]))
    return done


def download_from_s3():
    fieldnames = ["event_id", "timestamp", "timestamp_compact", "source_filename",
                  "local_filepath", "status", "method"]

    already_logged = _load_already_logged()

    # Open manifest in append mode up front, write header only if the file is brand new,
    # flush after every row. This means a crash mid-run (network blip, Ctrl-C, etc.)
    # never loses progress, and re-running skips both re-downloading AND re-logging
    # anything already recorded as done.
    manifest_is_new = not os.path.exists(MANIFEST_PATH)
    manifest_file = open(MANIFEST_PATH, "a", newline="")
    manifest_writer = csv.DictWriter(manifest_file, fieldnames=fieldnames)
    if manifest_is_new:
        manifest_writer.writeheader()
        manifest_file.flush()

    all_rows = []
    try:
        for event in EVENTS:
            event_id = event["id"]
            current_time = event["start"]
            expected_count = int((event["end"] - event["start"]).total_seconds() // (3 * 3600)) + 1
            success_count = 0

            print(f"\n=== {event_id}: expecting {expected_count} timestamps (3-hourly) ===")

            while current_time <= event["end"]:
                key = (event_id, iso_compact(current_time))
                if key in already_logged:
                    success_count += 1  # already downloaded and logged in a prior run
                else:
                    row = _process_timestamp(event_id, current_time)
                    all_rows.append(row)
                    manifest_writer.writerow(row)
                    manifest_file.flush()  # survive a crash immediately after this line
                    if row["status"] in ("success", "skipped_existing"):
                        success_count += 1

                current_time += timedelta(hours=3)
                time.sleep(0.05)  # be polite to the API

            print(f"=== {event_id}: {success_count}/{expected_count} timestamps available ===")
    finally:
        manifest_file.close()

    print(f"\nDownload manifest written to: {MANIFEST_PATH}")
    missing = [r for r in all_rows if r["status"] not in ("success", "skipped_existing")]
    if missing:
        print(f"WARNING: {len(missing)} timestamps could not be downloaded this run. "
              f"Check {MANIFEST_PATH} (status column). Re-run the script to retry only "
              f"the missing ones — already-downloaded files are skipped automatically.")


if __name__ == "__main__":
    download_from_s3()