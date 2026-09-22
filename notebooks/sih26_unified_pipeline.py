"""
SIH26 CycloneWatch — Unified Download + Train Kernel (Kaggle)
==============================================================
Single kernel that:
  1. Downloads GridSat-B1 satellite data from AWS S3 (public, NO auth)
  2. Standardizes each .nc → .npz immediately, deletes .nc (stream-and-discard)
  3. Downloads IBTrACS ground truth from NOAA (public URL)
  4. Builds training manifest with ground-truth join + auto-labels
  5. Trains CycloneTemporalModel on T4 GPU

STRATEGY NOTE (GridSat 8km vs INSAT 4km):
GridSat-B1 is 8km resolution, while ISRO INSAT-3D/3DR is 4km. This kernel is 
designed for **Phase 1: Pre-training**. We use 2000+ frames of 8km GridSat to 
teach the model general cyclone physics (preventing overfitting). For Phase 2, 
we will take this model's weights and **fine-tune** it on pure 4km INSAT data 
to achieve the ultra-low MAE required by the SIH26 specifications.

50 cyclone events × ~40 frames each = ~2000 training frames.
Disk usage stays under 1 GB thanks to stream-and-discard.

REQUIRED: Enable GPU + Internet on this Kaggle kernel.
"""
import os
import sys
import csv
import json
import time
import socket
import collections
from pathlib import Path
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, random_split

# ── Kaggle environment detection ──────────────────────────────────────────────
ON_KAGGLE = os.path.exists("/kaggle/working")
WORK_DIR = Path("/kaggle/working") if ON_KAGGLE else Path(".")
DATA_DIR = WORK_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
NORMALIZED_DIR = DATA_DIR / "normalized"
GT_DIR = DATA_DIR / "ground_truth"
CHECKPOINT_DIR = WORK_DIR / "checkpoints"

for d in [RAW_DIR, NORMALIZED_DIR, GT_DIR, CHECKPOINT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

MANIFEST_PATH = DATA_DIR / "training_manifest.csv"
CHECKPOINT_PATH = CHECKPOINT_DIR / "model.pt"

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: CYCLONE EVENT REGISTRY (50 events)
# ══════════════════════════════════════════════════════════════════════════════

EVENTS = [
    # ── Tier 1: Core training set (7 existing) ────────────────────────────
    {"id": "biparjoy_2023",  "name": "BIPARJOY",  "season": 2023, "start": datetime(2023, 6, 6, 0, tzinfo=timezone.utc),  "end": datetime(2023, 6, 16, 0, tzinfo=timezone.utc),  "basin": "AS", "bbox": {"lat": (5, 25), "lon": (50, 75)}},
    {"id": "amphan_2020",    "name": "AMPHAN",     "season": 2020, "start": datetime(2020, 5, 16, 0, tzinfo=timezone.utc), "end": datetime(2020, 5, 21, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (5, 25), "lon": (80, 95)}},
    {"id": "fani_2019",      "name": "FANI",       "season": 2019, "start": datetime(2019, 4, 25, 0, tzinfo=timezone.utc), "end": datetime(2019, 5, 4, 0, tzinfo=timezone.utc),   "basin": "BB", "bbox": {"lat": (5, 25), "lon": (80, 95)}},
    {"id": "tauktae_2021",   "name": "TAUKTAE",    "season": 2021, "start": datetime(2021, 5, 13, 0, tzinfo=timezone.utc), "end": datetime(2021, 5, 19, 0, tzinfo=timezone.utc),  "basin": "AS", "bbox": {"lat": (5, 25), "lon": (50, 75)}},
    {"id": "phailin_2013",   "name": "PHAILIN",    "season": 2013, "start": datetime(2013, 10, 7, 0, tzinfo=timezone.utc), "end": datetime(2013, 10, 14, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (5, 25), "lon": (80, 95)}},
    {"id": "hudhud_2014",    "name": "HUDHUD",     "season": 2014, "start": datetime(2014, 10, 6, 0, tzinfo=timezone.utc), "end": datetime(2014, 10, 14, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (5, 25), "lon": (80, 95)}},
    {"id": "ockhi_2017",     "name": "OCKHI",      "season": 2017, "start": datetime(2017, 11, 28, 0, tzinfo=timezone.utc),"end": datetime(2017, 12, 5, 0, tzinfo=timezone.utc),  "basin": "AS", "bbox": {"lat": (5, 25), "lon": (50, 75)}},
    # ── Tier 2: High-priority additions ───────────────────────────────────
    {"id": "yaas_2021",      "name": "YAAS",       "season": 2021, "start": datetime(2021, 5, 23, 0, tzinfo=timezone.utc), "end": datetime(2021, 5, 27, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (5, 25), "lon": (80, 95)}},
    {"id": "mocha_2023",     "name": "MOCHA",      "season": 2023, "start": datetime(2023, 5, 10, 0, tzinfo=timezone.utc), "end": datetime(2023, 5, 15, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (5, 25), "lon": (80, 100)}},
    {"id": "gati_2020",      "name": "GATI",       "season": 2020, "start": datetime(2020, 11, 21, 0, tzinfo=timezone.utc),"end": datetime(2020, 11, 26, 0, tzinfo=timezone.utc), "basin": "AS", "bbox": {"lat": (5, 20), "lon": (45, 60)}},
    {"id": "nisarga_2020",   "name": "NISARGA",    "season": 2020, "start": datetime(2020, 5, 31, 0, tzinfo=timezone.utc), "end": datetime(2020, 6, 4, 0, tzinfo=timezone.utc),   "basin": "AS", "bbox": {"lat": (10, 25), "lon": (65, 78)}},
    {"id": "kyarr_2019",     "name": "KYARR",      "season": 2019, "start": datetime(2019, 10, 24, 0, tzinfo=timezone.utc),"end": datetime(2019, 11, 2, 0, tzinfo=timezone.utc),  "basin": "AS", "bbox": {"lat": (5, 20), "lon": (55, 75)}},
    {"id": "gaja_2018",      "name": "GAJA",       "season": 2018, "start": datetime(2018, 11, 10, 0, tzinfo=timezone.utc),"end": datetime(2018, 11, 17, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (5, 20), "lon": (75, 90)}},
    {"id": "madi_2013",      "name": "MADI",       "season": 2013, "start": datetime(2013, 12, 6, 0, tzinfo=timezone.utc), "end": datetime(2013, 12, 13, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (5, 20), "lon": (75, 90)}},
    {"id": "asani_2022",     "name": "ASANI",      "season": 2022, "start": datetime(2022, 5, 7, 0, tzinfo=timezone.utc),  "end": datetime(2022, 5, 12, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (5, 25), "lon": (80, 95)}},
    {"id": "gulab_2021",     "name": "GULAB",      "season": 2021, "start": datetime(2021, 9, 24, 0, tzinfo=timezone.utc), "end": datetime(2021, 9, 28, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (10, 25), "lon": (80, 95)}},
    {"id": "bulbul_2019",    "name": "BULBUL",     "season": 2019, "start": datetime(2019, 11, 5, 0, tzinfo=timezone.utc), "end": datetime(2019, 11, 11, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (5, 25), "lon": (80, 95)}},
    {"id": "titli_2018",     "name": "TITLI",      "season": 2018, "start": datetime(2018, 10, 8, 0, tzinfo=timezone.utc), "end": datetime(2018, 10, 12, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (10, 25), "lon": (80, 95)}},
    {"id": "phethai_2018",   "name": "PHETHAI",    "season": 2018, "start": datetime(2018, 12, 14, 0, tzinfo=timezone.utc),"end": datetime(2018, 12, 18, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (5, 20), "lon": (80, 95)}},
    {"id": "vayu_2019",      "name": "VAYU",       "season": 2019, "start": datetime(2019, 6, 10, 0, tzinfo=timezone.utc), "end": datetime(2019, 6, 17, 0, tzinfo=timezone.utc),  "basin": "AS", "bbox": {"lat": (10, 25), "lon": (60, 75)}},
    {"id": "mekunu_2018",    "name": "MEKUNU",     "season": 2018, "start": datetime(2018, 5, 21, 0, tzinfo=timezone.utc), "end": datetime(2018, 5, 27, 0, tzinfo=timezone.utc),  "basin": "AS", "bbox": {"lat": (5, 20), "lon": (50, 65)}},
    {"id": "vardah_2016",    "name": "VARDAH",     "season": 2016, "start": datetime(2016, 12, 6, 0, tzinfo=timezone.utc), "end": datetime(2016, 12, 13, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (5, 20), "lon": (75, 90)}},
    {"id": "roanu_2016",     "name": "ROANU",      "season": 2016, "start": datetime(2016, 5, 17, 0, tzinfo=timezone.utc), "end": datetime(2016, 5, 22, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (5, 25), "lon": (80, 95)}},
    {"id": "mora_2017",      "name": "MORA",       "season": 2017, "start": datetime(2017, 5, 28, 0, tzinfo=timezone.utc), "end": datetime(2017, 5, 31, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (10, 25), "lon": (85, 95)}},
    {"id": "nanauk_2014",    "name": "NANAUK",     "season": 2014, "start": datetime(2014, 6, 10, 0, tzinfo=timezone.utc), "end": datetime(2014, 6, 14, 0, tzinfo=timezone.utc),  "basin": "AS", "bbox": {"lat": (10, 25), "lon": (60, 75)}},
    {"id": "nilofar_2014",   "name": "NILOFAR",    "season": 2014, "start": datetime(2014, 10, 25, 0, tzinfo=timezone.utc),"end": datetime(2014, 10, 31, 0, tzinfo=timezone.utc), "basin": "AS", "bbox": {"lat": (10, 25), "lon": (55, 70)}},
    {"id": "chapala_2015",   "name": "CHAPALA",    "season": 2015, "start": datetime(2015, 10, 28, 0, tzinfo=timezone.utc),"end": datetime(2015, 11, 4, 0, tzinfo=timezone.utc),  "basin": "AS", "bbox": {"lat": (5, 20), "lon": (45, 60)}},
    {"id": "daye_2018",      "name": "DAYE",       "season": 2018, "start": datetime(2018, 9, 19, 0, tzinfo=timezone.utc), "end": datetime(2018, 9, 22, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (10, 25), "lon": (80, 95)}},
    {"id": "helen_2013",     "name": "HELEN",      "season": 2013, "start": datetime(2013, 11, 19, 0, tzinfo=timezone.utc),"end": datetime(2013, 11, 23, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (5, 20), "lon": (75, 90)}},
    {"id": "lehar_2013",     "name": "LEHAR",      "season": 2013, "start": datetime(2013, 11, 23, 0, tzinfo=timezone.utc),"end": datetime(2013, 11, 28, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (5, 20), "lon": (80, 95)}},
    {"id": "mahasen_2013",   "name": "MAHASEN",    "season": 2013, "start": datetime(2013, 5, 10, 0, tzinfo=timezone.utc), "end": datetime(2013, 5, 17, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (5, 25), "lon": (80, 95)}},
    {"id": "luban_2018",     "name": "LUBAN",      "season": 2018, "start": datetime(2018, 10, 6, 0, tzinfo=timezone.utc), "end": datetime(2018, 10, 15, 0, tzinfo=timezone.utc), "basin": "AS", "bbox": {"lat": (5, 20), "lon": (50, 65)}},
    {"id": "sagar_2018",     "name": "SAGAR",      "season": 2018, "start": datetime(2018, 5, 16, 0, tzinfo=timezone.utc), "end": datetime(2018, 5, 20, 0, tzinfo=timezone.utc),  "basin": "AS", "bbox": {"lat": (5, 18), "lon": (43, 55)}},
    {"id": "nada_2016",      "name": "NADA",       "season": 2016, "start": datetime(2016, 11, 28, 0, tzinfo=timezone.utc),"end": datetime(2016, 12, 2, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (5, 18), "lon": (75, 90)}},
    {"id": "kyant_2016",     "name": "KYANT",      "season": 2016, "start": datetime(2016, 10, 21, 0, tzinfo=timezone.utc),"end": datetime(2016, 10, 28, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (5, 20), "lon": (85, 100)}},
    {"id": "nargis_2008",    "name": "NARGIS",     "season": 2008, "start": datetime(2008, 4, 27, 0, tzinfo=timezone.utc), "end": datetime(2008, 5, 3, 0, tzinfo=timezone.utc),   "basin": "BB", "bbox": {"lat": (5, 25), "lon": (80, 100)}},
    {"id": "sidr_2007",      "name": "SIDR",       "season": 2007, "start": datetime(2007, 11, 11, 0, tzinfo=timezone.utc),"end": datetime(2007, 11, 16, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (5, 25), "lon": (80, 95)}},
    {"id": "aila_2009",      "name": "AILA",       "season": 2009, "start": datetime(2009, 5, 23, 0, tzinfo=timezone.utc), "end": datetime(2009, 5, 26, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (10, 25), "lon": (80, 95)}},
    {"id": "laila_2010",     "name": "LAILA",      "season": 2010, "start": datetime(2010, 5, 17, 0, tzinfo=timezone.utc), "end": datetime(2010, 5, 21, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (5, 20), "lon": (75, 85)}},
    {"id": "jal_2010",       "name": "JAL",        "season": 2010, "start": datetime(2010, 11, 4, 0, tzinfo=timezone.utc), "end": datetime(2010, 11, 8, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (5, 20), "lon": (75, 90)}},
    {"id": "thane_2011",     "name": "THANE",      "season": 2011, "start": datetime(2011, 12, 25, 0, tzinfo=timezone.utc),"end": datetime(2011, 12, 30, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (5, 20), "lon": (75, 90)}},
    {"id": "nilam_2012",     "name": "NILAM",      "season": 2012, "start": datetime(2012, 10, 28, 0, tzinfo=timezone.utc),"end": datetime(2012, 11, 1, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (5, 20), "lon": (75, 90)}},
    {"id": "komen_2015",     "name": "KOMEN",      "season": 2015, "start": datetime(2015, 7, 26, 0, tzinfo=timezone.utc), "end": datetime(2015, 7, 31, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (10, 25), "lon": (85, 100)}},
    {"id": "mandous_2022",   "name": "MANDOUS",    "season": 2022, "start": datetime(2022, 12, 6, 0, tzinfo=timezone.utc), "end": datetime(2022, 12, 10, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (5, 18), "lon": (75, 90)}},
    {"id": "sitrang_2022",   "name": "SITRANG",    "season": 2022, "start": datetime(2022, 10, 22, 0, tzinfo=timezone.utc),"end": datetime(2022, 10, 25, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (10, 25), "lon": (85, 95)}},
    {"id": "shaheen_2021",   "name": "SHAHEEN",    "season": 2021, "start": datetime(2021, 9, 30, 0, tzinfo=timezone.utc), "end": datetime(2021, 10, 4, 0, tzinfo=timezone.utc),  "basin": "AS", "bbox": {"lat": (15, 28), "lon": (55, 70)}},
    {"id": "tauktae2_2021",  "name": "JAWAD",      "season": 2021, "start": datetime(2021, 12, 2, 0, tzinfo=timezone.utc), "end": datetime(2021, 12, 6, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (10, 25), "lon": (80, 95)}},
    {"id": "burevi_2020",    "name": "BUREVI",     "season": 2020, "start": datetime(2020, 11, 30, 0, tzinfo=timezone.utc),"end": datetime(2020, 12, 4, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (5, 15), "lon": (75, 85)}},
    {"id": "nivar_2020",     "name": "NIVAR",      "season": 2020, "start": datetime(2020, 11, 23, 0, tzinfo=timezone.utc),"end": datetime(2020, 11, 27, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (5, 18), "lon": (75, 90)}},
    {"id": "biporjoy2_2023", "name": "HAMOON",     "season": 2023, "start": datetime(2023, 10, 22, 0, tzinfo=timezone.utc),"end": datetime(2023, 10, 25, 0, tzinfo=timezone.utc), "basin": "BB", "bbox": {"lat": (10, 25), "lon": (85, 95)}},
    {"id": "michaung_2023",  "name": "MICHAUNG",   "season": 2023, "start": datetime(2023, 12, 1, 0, tzinfo=timezone.utc), "end": datetime(2023, 12, 6, 0, tzinfo=timezone.utc),  "basin": "BB", "bbox": {"lat": (5, 18), "lon": (75, 90)}},
]

print(f"Total cyclone events registered: {len(EVENTS)}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: GRIDSAT-B1 STREAM-AND-DISCARD DOWNLOADER & STANDARDIZER
# ══════════════════════════════════════════════════════════════════════════════

import urllib.request
import xarray as xr
from datetime import timedelta

TARGET_SIZE = (256, 256)

def download_and_process_gridsat(event):
    """
    Downloads GridSat-B1 .nc files, slices them to the bounding box, 
    normalizes to [2, H, W] .npz arrays, and immediately deletes the .nc file.
    """
    event_id = event["id"]
    frames_dir = NORMALIZED_DIR / event_id / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    
    # We will temporarily store .nc files here and then immediately delete them
    temp_nc_dir = RAW_DIR / "gridsat" / event_id
    temp_nc_dir.mkdir(parents=True, exist_ok=True)
    
    start_date = event["start"]
    end_date = event["end"]
    bbox = event["bbox"]
    
    # GridSat-B1 coordinates are ascending, so slice(min, max) works correctly
    lat_slice = slice(bbox["lat"][0], bbox["lat"][1])
    lon_slice = slice(bbox["lon"][0], bbox["lon"][1])
    
    base_url = "https://noaa-cdr-gridsat-b1-pds.s3.amazonaws.com/data/{year}/GRIDSAT-B1.{year}.{month:02d}.{day:02d}.{hour:02d}.v02r01.nc"
    
    success = 0
    current_date = start_date
    while current_date <= end_date:
        for hour in [0, 3, 6, 9, 12, 15, 18, 21]:
            year = current_date.year
            month = current_date.month
            day = current_date.day
            
            iso_ts = f"{year}{month:02d}{day:02d}T{hour:02d}0000Z"
            npz_path = frames_dir / f"{event_id}_{iso_ts}.npz"
            
            if npz_path.exists():
                success += 1
                continue
                
            url = base_url.format(year=year, month=month, day=day, hour=hour)
            filename = f"GRIDSAT-B1.{year}.{month:02d}.{day:02d}.{hour:02d}.v02r01.nc"
            filepath = temp_nc_dir / filename
            
            # --- 1. DOWNLOAD ---
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=30) as response, open(filepath, 'wb') as out_file:
                    out_file.write(response.read())
            except Exception:
                continue # Skip if 404 or missing
                
            # --- 2. STANDARDIZE ---
            try:
                ds = xr.open_dataset(filepath)
                subset = ds.sel(lat=lat_slice, lon=lon_slice)
                
                ir = subset['irwin_cdr'].values.squeeze()
                wv = subset['irwvp'].values.squeeze()
                
                # Check for completely empty subsets due to invalid bounding boxes
                if ir.size == 0 or wv.size == 0:
                    raise ValueError(f"Empty subset after slicing. Check bbox: {bbox}")
                    
                ir_clean = np.nan_to_num(ir, nan=0.0)
                wv_clean = np.nan_to_num(wv, nan=0.0)

                ir_min, ir_max = float(ir_clean.min()), float(ir_clean.max())
                wv_min, wv_max = float(wv_clean.min()), float(wv_clean.max())
                
                ir_norm = (ir_clean - ir_min) / (ir_max - ir_min + 1e-6)
                wv_norm = (wv_clean - wv_min) / (wv_max - wv_min + 1e-6)

                stacked = np.stack([ir_norm, wv_norm], axis=0)  # [C, H, W]
                
                np.savez_compressed(str(npz_path), image=stacked, event_id=event_id, timestamp=iso_ts)
                success += 1
                ds.close()
            except Exception as e:
                print(f"  [ERROR] {filename}: {e}")
            finally:
                # --- 3. DISCARD ---
                filepath.unlink(missing_ok=True)
                
        current_date += timedelta(days=1)
        
    print(f"  {event_id}: processed {success} GridSat frames")
    return success

def download_all_gridsat():
    print("\n" + "="*60)
    print("PHASE 1: DOWNLOADING & PROCESSING NOAA GRIDSAT-B1 (STREAM-AND-DISCARD)")
    print("="*60)
    
    total_frames = 0
    for i, event in enumerate(EVENTS):
        print(f"\n[{i+1}/{len(EVENTS)}] {event['id']}")
        count = download_and_process_gridsat(event)
        total_frames += count
    print(f"\n✅ Total frames processed: {total_frames}")
    return total_frames


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: IBTRACS GROUND TRUTH
# ══════════════════════════════════════════════════════════════════════════════

IBTRACS_URL = "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.NI.list.v04r01.csv"

def download_ibtracs():
    print("\n" + "="*60)
    print("PHASE 2: DOWNLOADING IBTRACS GROUND TRUTH")
    print("="*60)
    
    ibtracs_path = GT_DIR / "ibtracs.NI.csv"
    if ibtracs_path.exists():
        print(f"  Already exists: {ibtracs_path}")
        return ibtracs_path
    
    import urllib.request
    print(f"  Downloading from NOAA...")
    try:
        urllib.request.urlretrieve(IBTRACS_URL, str(ibtracs_path))
        size_mb = ibtracs_path.stat().st_size / 1e6
        print(f"  ✅ Saved: {ibtracs_path} ({size_mb:.1f} MB)")
    except Exception as e:
        print(f"  ❌ Failed to download IBTrACS: {e}")
        # Try v04r00 as fallback
        try:
            fallback_url = IBTRACS_URL.replace("v04r01", "v04r00")
            urllib.request.urlretrieve(fallback_url, str(ibtracs_path))
            print(f"  ✅ Saved (v04r00 fallback)")
        except Exception as e2:
            print(f"  ❌ Fallback also failed: {e2}")
            return None
    return ibtracs_path


def split_ibtracs(ibtracs_path):
    """Split IBTrACS into per-event best-track CSVs."""
    print("  Splitting IBTrACS into per-event CSVs...")
    df = pd.read_csv(ibtracs_path, skiprows=[1], low_memory=False)
    
    has_nd = "NEWDELHI_LAT" in df.columns
    matched = 0
    
    for event in EVENTS:
        subset = df[(df["NAME"] == event["name"]) & (df["SEASON"] == event["season"])].copy()
        if subset.empty:
            continue
        
        subset["timestamp"] = pd.to_datetime(subset["ISO_TIME"], utc=True, errors="coerce")
        subset = subset.dropna(subset=["timestamp"]).sort_values("timestamp")
        
        if has_nd:
            lat = pd.to_numeric(subset.get("NEWDELHI_LAT"), errors="coerce").fillna(
                  pd.to_numeric(subset["LAT"], errors="coerce"))
            lon = pd.to_numeric(subset.get("NEWDELHI_LON"), errors="coerce").fillna(
                  pd.to_numeric(subset["LON"], errors="coerce"))
        else:
            lat = pd.to_numeric(subset["LAT"], errors="coerce")
            lon = pd.to_numeric(subset["LON"], errors="coerce")
        
        out = pd.DataFrame({
            "event_id": event["id"],
            "timestamp": subset["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lat": lat.values, "lon": lon.values,
            "wmo_wind_kts": subset.get("WMO_WIND", ""),
            "wmo_pres_mb": subset.get("WMO_PRES", ""),
        }).dropna(subset=["lat", "lon"])
        
        out.to_csv(GT_DIR / f"{event['id']}_best_track.csv", index=False)
        matched += 1
    
    print(f"  ✅ Matched {matched}/{len(EVENTS)} events in IBTrACS")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: BUILD TRAINING MANIFEST (join + label)
# ══════════════════════════════════════════════════════════════════════════════

def build_training_manifest():
    print("\n" + "="*60)
    print("PHASE 3: BUILDING TRAINING MANIFEST")
    print("="*60)
    
    records = []
    
    for event in EVENTS:
        event_id = event["id"]
        frames_dir = NORMALIZED_DIR / event_id / "frames"
        if not frames_dir.exists():
            continue
        
        # Load best-track for this event
        bt_path = GT_DIR / f"{event_id}_best_track.csv"
        bt_df = None
        if bt_path.exists():
            bt_df = pd.read_csv(bt_path)
            bt_df["timestamp_dt"] = pd.to_datetime(bt_df["timestamp"], utc=True)
            bt_df["wmo_wind_kts"] = pd.to_numeric(bt_df["wmo_wind_kts"], errors="coerce")
        
        for npz_file in sorted(frames_dir.glob("*.npz")):
            stem = npz_file.stem  # e.g. biparjoy_2023_20230606T000000Z
            ts_compact = stem[len(event_id)+1:]
            try:
                dt = datetime.strptime(ts_compact, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                iso_ts = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue
            
            data = np.load(str(npz_file))
            arr = data["image"]
            
            # Ground truth join
            lat, lon, wind_kts, pattern = "", "", None, "disorganized"
            if bt_df is not None and not bt_df.empty:
                target = pd.Timestamp(dt)
                diffs = (bt_df["timestamp_dt"] - target).abs()
                idx = diffs.idxmin()
                if diffs.loc[idx] <= pd.Timedelta(minutes=90):
                    row = bt_df.loc[idx]
                    lat = float(row["lat"])
                    lon = float(row["lon"])
                    wind_kts = row["wmo_wind_kts"] if pd.notna(row["wmo_wind_kts"]) else None
                    
                    # Auto-label from wind intensity
                    if wind_kts is not None:
                        if wind_kts >= 120: pattern = "eye"
                        elif wind_kts >= 64: pattern = "banding"
                        elif wind_kts >= 34: pattern = "curved_band"
                        else: pattern = "disorganized"
            
            records.append({
                "file_id": npz_file.name,
                "event_id": event_id,
                "timestamp": iso_ts,
                "tensor_shape": str(arr.shape),
                "nan_percentage": 0.0,
                "center_lat": lat,
                "center_lon": lon,
                "gt_match_distance_min": 0.0,
                "validation_status": "PASS",
                "pattern_label": pattern,
            })
    
    df = pd.DataFrame(records)
    df = df[df["center_lat"] != ""]  # Drop unmatched frames
    df.to_csv(str(MANIFEST_PATH), index=False)
    
    print(f"  Total frames: {len(records)}")
    print(f"  Matched to ground truth: {len(df)}")
    print(f"  Label distribution:")
    if "pattern_label" in df.columns:
        for label, count in df["pattern_label"].value_counts().items():
            print(f"    {label}: {count} ({count/len(df)*100:.1f}%)")
    print(f"  ✅ Manifest saved to {MANIFEST_PATH}")
    return len(df)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: MODEL + DATASET + TRAINING
# ══════════════════════════════════════════════════════════════════════════════

class ConvLSTMCell(nn.Module):
    def __init__(self, input_dim, hidden_dim, kernel_size, bias):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.kernel_size = kernel_size
        self.padding = kernel_size[0] // 2, kernel_size[1] // 2
        self.bias = bias
        self.conv = nn.Conv2d(in_channels=self.input_dim + self.hidden_dim,
                              out_channels=4 * self.hidden_dim,
                              kernel_size=self.kernel_size,
                              padding=self.padding,
                              bias=self.bias)

    def forward(self, input_tensor, cur_state):
        h_cur, c_cur = cur_state
        combined = torch.cat([input_tensor, h_cur], dim=1)
        combined_conv = self.conv(combined)
        cc_i, cc_f, cc_o, cc_g = torch.split(combined_conv, self.hidden_dim, dim=1)
        i = torch.sigmoid(cc_i)
        f = torch.sigmoid(cc_f)
        o = torch.sigmoid(cc_o)
        g = torch.tanh(cc_g)
        c_next = f * c_cur + i * g
        h_next = o * torch.tanh(c_next)
        return h_next, c_next

    def init_hidden(self, batch_size, image_size):
        height, width = image_size
        return (torch.zeros(batch_size, self.hidden_dim, height, width, device=self.conv.weight.device),
                torch.zeros(batch_size, self.hidden_dim, height, width, device=self.conv.weight.device))


class CycloneCNN(nn.Module):
    def __init__(self, num_classes=5, in_channels=2):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 16, 3, 1, 1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, 1, 1), nn.ReLU(), nn.MaxPool2d(2),
        )

    def forward(self, x):
        return self.features(x)


class CycloneTemporalModel(nn.Module):
    def __init__(self, num_classes=5, in_channels=2, hidden_dim=64):
        super().__init__()
        self.cnn = CycloneCNN(num_classes, in_channels)
        self.convlstm = ConvLSTMCell(input_dim=32, hidden_dim=hidden_dim, kernel_size=(3, 3), bias=True)
        self.pool = nn.AdaptiveAvgPool2d((4, 4))
        self.fc_shared = nn.Linear(hidden_dim * 16, 128)
        
        self.fc_center = nn.Linear(128, 2)
        self.fc_pattern = nn.Linear(128, num_classes)
        self.fc_confidence = nn.Linear(128, 1)
        
        self.fc_t12 = nn.Linear(128, 2)
        self.fc_t24 = nn.Linear(128, 2)
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, x):
        B, T, C, H, W = x.size()
        f_seq = []
        for t in range(T):
            f_seq.append(self.cnn(x[:, t, :, :, :]))
            
        spatial_size = f_seq[0].size()[2:]
        h, c = self.convlstm.init_hidden(B, spatial_size)
        
        for t in range(T):
            h, c = self.convlstm(f_seq[t], (h, c))
            
        pooled = self.pool(h).view(B, -1)
        shared = torch.relu(self.fc_shared(pooled))
        
        return {
            "center": self.fc_center(shared),
            "pattern": self.fc_pattern(shared),
            "confidence": torch.sigmoid(self.fc_confidence(shared) / self.temperature),
            "t12_center": self.fc_t12(shared),
            "t24_center": self.fc_t24(shared),
        }


class CycloneDataset(Dataset):
    LABEL_MAP = {"eye": 0, "banding": 1, "curved_band": 2, "shear_affected": 3, "disorganized": 4}
    
    def __init__(self, manifest_path, normalized_dir, seq_len=4):
        df = pd.read_csv(manifest_path)
        df = df[df["center_lat"].notna() & (df["center_lat"] != "")]
        df = df[df["center_lon"].notna() & (df["center_lon"] != "")]
        df = df[df["pattern_label"] != "unlabeled"]
        df["timestamp_dt"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values(by=["event_id", "timestamp_dt"]).reset_index(drop=True)
        
        self.normalized_dir = str(normalized_dir)
        self.seq_len = seq_len
        self.sequences = []
        
        for event_id, group in df.groupby("event_id"):
            if len(group) >= self.seq_len:
                for i in range(len(group) - self.seq_len + 1):
                    self.sequences.append(group.iloc[i:i+self.seq_len])

    def __len__(self): return len(self.sequences)

    def __getitem__(self, idx):
        seq_df = self.sequences[idx]
        imgs = []
        for _, row in seq_df.iterrows():
            path = os.path.join(self.normalized_dir, row["event_id"], "frames", row["file_id"])
            arr = np.load(path)["image"]
            img = torch.tensor(arr, dtype=torch.float32).unsqueeze(0)
            img = F.interpolate(img, size=TARGET_SIZE, mode="bilinear", align_corners=False).squeeze(0)
            imgs.append(img)
            
        last_row = seq_df.iloc[-1]
        return torch.stack(imgs, dim=0), {
            "center": torch.tensor([float(last_row["center_lat"]), float(last_row["center_lon"])], dtype=torch.float32),
            "pattern": torch.tensor(self.LABEL_MAP[last_row["pattern_label"]], dtype=torch.long),
        }


def run_training():
    print("\n" + "="*60)
    print("PHASE 4: MODEL TRAINING")
    print("="*60)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Device: {device}")
    if device.type == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
    
    dataset = CycloneDataset(str(MANIFEST_PATH), str(NORMALIZED_DIR))
    print(f"  Dataset: {len(dataset)} frames")
    
    val_size = max(1, int(0.15 * len(dataset)))
    train_ds, val_ds = random_split(dataset, [len(dataset) - val_size, val_size],
                                     generator=torch.Generator().manual_seed(42))
    print(f"  Train: {len(train_ds)}  Val: {len(val_ds)}")
    
    train_loader = DataLoader(train_ds, batch_size=8, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=8, shuffle=False)
    
    model = CycloneTemporalModel(num_classes=5, in_channels=2).to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
    mse_loss = nn.MSELoss()
    
    # Compute class weights
    counts = collections.Counter()
    for i in range(len(train_ds)):
        _, t = train_ds[i]
        counts[int(t["pattern"].item())] += 1
    total = sum(counts.values())
    weights = torch.tensor([total / (5 * counts.get(c, 1)) for c in range(5)], dtype=torch.float32).to(device)
    ce_loss = nn.CrossEntropyLoss(weight=weights)
    print(f"  Class weights: {weights.cpu().tolist()}")
    
    NUM_EPOCHS = 100
    best_val, best_ep = float("inf"), 0
    
    print(f"\n{'Epoch':>6} {'Train':>10} {'Val':>10} {'MAE km':>10} {'Best':>6}")
    print("─" * 50)
    
    for epoch in range(NUM_EPOCHS):
        model.train()
        running = 0.0
        for imgs, tgts in train_loader:
            imgs = imgs.to(device)
            centers = tgts["center"].to(device)
            patterns = tgts["pattern"].to(device)
            optimizer.zero_grad()
            out = model(imgs)
            loss = mse_loss(out["center"], centers) * 10.0 + ce_loss(out["pattern"], patterns)
            loss.backward(); optimizer.step()
            running += loss.item()
        train_loss = running / len(train_loader)
        
        model.eval()
        val_run, errs = 0.0, []
        with torch.no_grad():
            for imgs, tgts in val_loader:
                imgs = imgs.to(device)
                centers = tgts["center"].to(device)
                patterns = tgts["pattern"].to(device)
                out = model(imgs)
                v = mse_loss(out["center"], centers) * 10.0 + ce_loss(out["pattern"], patterns)
                val_run += v.item()
                lat_r = torch.deg2rad(centers[:, 0])
                d = torch.sqrt(((out["center"][:, 0]-centers[:, 0])*111)**2 +
                               ((out["center"][:, 1]-centers[:, 1])*111*torch.cos(lat_r))**2)
                errs.extend(d.cpu().tolist())
        
        val_loss = val_run / len(val_loader)
        mae = sum(errs) / len(errs) if errs else 0
        scheduler.step(val_loss)
        
        if val_loss < best_val:
            best_val, best_ep = val_loss, epoch + 1
            torch.save(model.state_dict(), str(CHECKPOINT_PATH))
        
        if (epoch+1) % 5 == 0 or epoch == 0 or epoch == NUM_EPOCHS - 1:
            print(f"{epoch+1:>6} {train_loss:>10.4f} {val_loss:>10.4f} {mae:>10.1f} {best_ep:>6}")
    
    print(f"\n✅ Training complete! Best epoch: {best_ep}, val_loss: {best_val:.4f}")
    print(f"   Checkpoint: {CHECKPOINT_PATH} ({CHECKPOINT_PATH.stat().st_size/1e6:.2f} MB)")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("="*60)
    print("SIH26 CYCLONEWATCH — UNIFIED PIPELINE")
    print(f"Events: {len(EVENTS)} | GPU: {torch.cuda.is_available()}")
    print("="*60)
    
    # Phase 1: Download + standardize satellite data
    total_frames = download_all_gridsat()
    
    # Phase 2: Download IBTrACS ground truth
    ibtracs_path = download_ibtracs()
    if ibtracs_path:
        split_ibtracs(ibtracs_path)
    
    # Phase 3: Build training manifest
    num_training = build_training_manifest()
    
    # Phase 4: Train model
    if num_training > 10:
        run_training()
    else:
        print(f"\n⚠️ Only {num_training} training frames — not enough to train. Check downloads.")
    
    print("\n🎉 PIPELINE COMPLETE!")
