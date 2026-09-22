"""
SIH26 Cloud Downloader — Kaggle Kernel
=======================================
Downloads INSAT-3DR (MOSDAC) and ERA5 (Copernicus) data on Kaggle's
high-speed network, then saves outputs to /kaggle/working/ for download.

IMPORTANT: This kernel requires internet access (enable_internet=true)
and the following Kaggle Secrets to be configured:
  - MOSDAC_USERNAME
  - MOSDAC_PASSWORD
  - CDSAPI_URL
  - CDSAPI_KEY

To set secrets: Kaggle notebook → Add-ons → Secrets → Add a new secret
"""
import os
import sys
import json
import subprocess
from pathlib import Path

# ── Kaggle environment detection ──────────────────────────────────────────────
ON_KAGGLE = os.path.exists("/kaggle/working")
WORK_DIR = Path("/kaggle/working") if ON_KAGGLE else Path(".")
DATA_DIR = WORK_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Load credentials from Kaggle Secrets ──────────────────────────────────────
def get_secret(key):
    """Read a Kaggle Secret. Falls back to env vars for local testing."""
    try:
        from kaggle_secrets import UserSecretsClient
        client = UserSecretsClient()
        return client.get_secret(key)
    except Exception:
        return os.environ.get(key, "")

MOSDAC_USERNAME = get_secret("MOSDAC_USERNAME")
MOSDAC_PASSWORD = get_secret("MOSDAC_PASSWORD")
CDSAPI_URL = get_secret("CDSAPI_URL")
CDSAPI_KEY = get_secret("CDSAPI_KEY")


# ── Install dependencies that aren't pre-installed on Kaggle ──────────────────
def install_deps():
    """Try to install extra deps. Non-fatal if internet is restricted."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                               "cdsapi", "python-dotenv", "beautifulsoup4"],
                              timeout=30)
    except Exception as e:
        print(f"  ⚠️  pip install failed (probably no internet): {e}")
        print("  Continuing with pre-installed packages...")

# ══════════════════════════════════════════════════════════════════════════════
# PART 1: ERA5 Download (Copernicus CDS)
# ══════════════════════════════════════════════════════════════════════════════

# Target cyclone events with date ranges
CYCLONE_EVENTS = [
    # Tier 1 — already have GridSat, add ERA5 context
    {"name": "biparjoy_2023", "year": "2023", "months": ["06"], "days": [f"{d:02d}" for d in range(1, 19)]},
    {"name": "amphan_2020",   "year": "2020", "months": ["05"], "days": [f"{d:02d}" for d in range(16, 22)]},
    {"name": "fani_2019",     "year": "2019", "months": ["04", "05"],
     "days": [f"{d:02d}" for d in range(25, 32)] + [f"{d:02d}" for d in range(1, 5)]},
    {"name": "tauktae_2021",  "year": "2021", "months": ["05"], "days": [f"{d:02d}" for d in range(13, 20)]},
    {"name": "phailin_2013",  "year": "2013", "months": ["10"], "days": [f"{d:02d}" for d in range(7, 15)]},
    {"name": "hudhud_2014",   "year": "2014", "months": ["10"], "days": [f"{d:02d}" for d in range(6, 15)]},
    {"name": "ockhi_2017",    "year": "2017", "months": ["11", "12"],
     "days": [f"{d:02d}" for d in range(28, 32)] + [f"{d:02d}" for d in range(1, 6)]},
]

# ERA5 variables we need (parameters 7-14 from the implementation plan)
ERA5_VARIABLES = [
    '10m_u_component_of_wind',           # Wind speed components
    '10m_v_component_of_wind',
    'mean_sea_level_pressure',           # MSLP
    '2m_temperature',                    # Surface temp
    'relative_humidity',                 # Humidity (pressure level)
]

ERA5_PRESSURE_VARIABLES = [
    'vorticity',                         # 850 hPa vorticity
    'u_component_of_wind',               # For wind shear (200 & 850 hPa)
    'v_component_of_wind',
    'relative_humidity',                 # 700 hPa
    'geopotential',                      # 500 hPa geopotential height
]

def download_era5_for_event(event):
    """Download ERA5 single-level reanalysis data for one cyclone event."""
    import cdsapi
    
    print(f"\n{'='*60}")
    print(f"Downloading ERA5 for: {event['name']}")
    print(f"{'='*60}")

    c = cdsapi.Client(url=CDSAPI_URL, key=CDSAPI_KEY)
    
    out_dir = DATA_DIR / "era5" / event["name"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{event['name']}_era5_single_levels.nc"
    
    if out_file.exists():
        print(f"  Already exists, skipping: {out_file}")
        return
    
    # Build the valid days list (filter out invalid day numbers per month)
    valid_days = []
    for d in event["days"]:
        day_int = int(d)
        if 1 <= day_int <= 31:
            valid_days.append(d)

    print(f"  Variables: {len(ERA5_VARIABLES)}")
    print(f"  Months: {event['months']}, Days: {valid_days[:5]}...")
    
    try:
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': ERA5_VARIABLES,
                'year': event['year'],
                'month': event['months'],
                'day': valid_days,
                'time': ['00:00', '03:00', '06:00', '09:00',
                         '12:00', '15:00', '18:00', '21:00'],
                'area': [30, 50, 0, 100],  # North Indian Ocean bounding box
            },
            str(out_file)
        )
        print(f"  ✅ Saved to {out_file} ({out_file.stat().st_size / 1e6:.1f} MB)")
    except Exception as e:
        print(f"  ❌ ERA5 download failed for {event['name']}: {e}")


def download_all_era5():
    """Download ERA5 data for all cyclone events."""
    print("\n" + "="*60)
    print("STARTING ERA5 (COPERNICUS) DOWNLOADS")
    print("="*60)
    
    if not CDSAPI_URL or not CDSAPI_KEY:
        print("❌ ERROR: CDSAPI credentials not found!")
        print("   Set CDSAPI_URL and CDSAPI_KEY as Kaggle Secrets.")
        return False
    
    for event in CYCLONE_EVENTS:
        download_era5_for_event(event)
    
    print("\n✅ All ERA5 downloads complete!")
    return True


# ══════════════════════════════════════════════════════════════════════════════
# PART 2: MOSDAC Download (INSAT-3DR)
# ══════════════════════════════════════════════════════════════════════════════

# MOSDAC events with date ranges
MOSDAC_EVENTS = [
    {"name": "biparjoy_2023", "start": "2023-06-01", "end": "2023-06-18"},
    {"name": "amphan_2020",   "start": "2020-05-16", "end": "2020-05-21"},
    {"name": "fani_2019",     "start": "2019-04-25", "end": "2019-05-04"},
    {"name": "tauktae_2021",  "start": "2021-05-13", "end": "2021-05-19"},
    {"name": "phailin_2013",  "start": "2013-10-07", "end": "2013-10-14"},
    {"name": "hudhud_2014",   "start": "2014-10-06", "end": "2014-10-14"},
    {"name": "ockhi_2017",    "start": "2017-11-28", "end": "2017-12-05"},
]

def download_mosdac_for_event(event):
    """
    Download INSAT-3DR data from MOSDAC for one event.
    Uses the MOSDAC REST API directly (no mdapi.py dependency).
    """
    import requests
    
    print(f"\n{'='*60}")
    print(f"Downloading MOSDAC INSAT-3DR for: {event['name']}")
    print(f"  Date range: {event['start']} → {event['end']}")
    print(f"{'='*60}")

    out_dir = DATA_DIR / "insat" / event["name"]
    out_dir.mkdir(parents=True, exist_ok=True)

    # MOSDAC API endpoints
    SEARCH_URL = "https://mosdac.gov.in/apiresources/sih_rest_search"
    DOWNLOAD_URL = "https://mosdac.gov.in/apiresources/sih_rest_download"
    
    # Step 1: Search for files
    search_payload = {
        "datasetId": "3RIMG_L1B_STD",
        "startTime": event["start"],
        "endTime": event["end"],
    }
    
    try:
        print("  Searching MOSDAC catalog...")
        resp = requests.post(SEARCH_URL, json=search_payload, timeout=60)
        resp.raise_for_status()
        results = resp.json()
        
        files = results.get("files", results.get("data", []))
        if not files:
            print(f"  ⚠️  No files found for {event['name']}. Raw response keys: {list(results.keys())}")
            # Save the raw response for debugging
            debug_file = out_dir / "search_response_debug.json"
            with open(debug_file, "w") as f:
                json.dump(results, f, indent=2)
            print(f"  Debug response saved to {debug_file}")
            return
        
        print(f"  Found {len(files)} files. Downloading first 5 for validation...")
        
        # Step 2: Download files (limit to 5 for initial validation)
        for i, file_info in enumerate(files[:5]):
            file_id = file_info.get("fileId", file_info.get("id", f"unknown_{i}"))
            file_name = file_info.get("fileName", file_info.get("name", f"insat_{event['name']}_{i}.h5"))
            out_path = out_dir / file_name
            
            if out_path.exists():
                print(f"  [{i+1}/5] Already exists: {file_name}")
                continue
                
            print(f"  [{i+1}/5] Downloading: {file_name}...")
            
            dl_payload = {
                "username": MOSDAC_USERNAME,
                "password": MOSDAC_PASSWORD,
                "fileId": file_id,
            }
            
            try:
                dl_resp = requests.post(DOWNLOAD_URL, json=dl_payload, stream=True, timeout=300)
                dl_resp.raise_for_status()
                
                with open(out_path, "wb") as f:
                    for chunk in dl_resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                size_mb = out_path.stat().st_size / 1e6
                print(f"         ✅ Saved ({size_mb:.1f} MB)")
            except Exception as e:
                print(f"         ❌ Download failed: {e}")
    
    except Exception as e:
        print(f"  ❌ MOSDAC search failed: {e}")


def download_all_mosdac():
    """Download INSAT-3DR data for all events."""
    print("\n" + "="*60)
    print("STARTING MOSDAC (INSAT-3DR) DOWNLOADS")
    print("="*60)
    
    if not MOSDAC_USERNAME or not MOSDAC_PASSWORD:
        print("❌ ERROR: MOSDAC credentials not found!")
        print("   Set MOSDAC_USERNAME and MOSDAC_PASSWORD as Kaggle Secrets.")
        return False
    
    for event in MOSDAC_EVENTS:
        download_mosdac_for_event(event)
    
    print("\n✅ All MOSDAC downloads complete!")
    return True


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("SIH26 CYCLONEWATCH — CLOUD DATA DOWNLOADER")
    print("=" * 60)
    print(f"Running on Kaggle: {ON_KAGGLE}")
    print(f"Output directory:  {DATA_DIR}")
    print()
    
    # Install dependencies
    print("Installing dependencies...")
    install_deps()
    
    # Run ERA5 downloads
    era5_ok = download_all_era5()
    
    # Run MOSDAC downloads
    mosdac_ok = download_all_mosdac()
    
    # Summary
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"  ERA5 (Copernicus):  {'✅ OK' if era5_ok else '❌ FAILED'}")
    print(f"  MOSDAC (INSAT-3DR): {'✅ OK' if mosdac_ok else '❌ FAILED'}")
    
    # List what was downloaded
    print(f"\nFiles in {DATA_DIR}:")
    for root, dirs, files in os.walk(DATA_DIR):
        for f in files:
            fpath = Path(root) / f
            size_mb = fpath.stat().st_size / 1e6
            print(f"  {fpath.relative_to(DATA_DIR)} ({size_mb:.1f} MB)")
    
    print("\n🎉 Done! Download the output from /kaggle/working/data/")


if __name__ == "__main__":
    main()
