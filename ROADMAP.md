# CycloneWatch — Future Roadmap

> **Last Updated:** September 2026 | **Status:** Active  
> For the full technical deep-dive, see [docs/future_implementation.md](docs/future_implementation.md)

This document provides a clear, prioritized summary of everything that remains to be implemented.

---

## ✅ Recently Completed

These items have been implemented and are live in the current codebase:

| Feature | Details |
|---------|---------|
| **Dynamic Coast Distance** | `GET /api/coastline/distance` computes real Haversine distance to Indian coastline |
| **Dynamic Time to Impact** | Calculated from actual storm translation speed (not hardcoded) |
| **Dynamic Uncertainty Cone** | Scales with the model's actual T+24h MAE error (`t24_km`) |
| **Black Mark Elimination** | IR GIBS layer + `mix-blend-mode: screen` + brightness/contrast CSS |
| **Smooth Cloud Animation** | 2s opacity crossfade transitions + 120s cloud-drift CSS keyframe |
| **Logo Integration** | Custom CycloneWatch logo in left sidebar navigation |
| **Left Sidebar Layout** | SideNav with Live/Historical mode toggle (Git conflict resolved) |
| **Coastline API Endpoint** | New `backend/app/api/coastline.py` router wired into main.py |
| **Reports API Endpoint** | New `backend/app/api/reports.py` for ground destruction reports |
| **Replay Source Parameter** | `/api/replay/{event_id}?source=nasa|isro` toggle ready |

---

## 🔴 Immediate Priority — ML Model Retraining

**Timeline:** This week  
**Owner:** ML team  
**Impact:** This is the single most impactful change remaining.

### What needs to happen:
1. **Run the Kaggle pipeline** (`notebooks/sih26_unified_pipeline.py`) to process all 51 cyclone events
2. **Retrain the model** with the expanded 51-event dataset using `python -m ml.src.train`
3. **Validate** that pattern accuracy improves from 78.3% → ≥85% and T+12h MAE drops from ~255 km → ~140 km
4. **Replace** `ml/checkpoints/model.pt` with the new checkpoint
5. **Re-run** `python -m scripts.precompute_replay` to rebuild historical replay data with new predictions

### Why this matters:
The current model was trained on only 7 cyclones (423 frames). The Kaggle pipeline has already prepared data for 51 cyclones. Running the training loop is the single change that will deliver the largest performance improvement.

---

## 🟡 Short-Term (Weeks 1–2)

### ConvLSTM Sequence Training
- **What:** Replace the fake `T=1` sequence input with real `T=5` sliding window sequences
- **Why:** The GRU head currently receives a single frame — it has never learned temporal motion
- **How:** Create `CycloneSequenceDataset` in `ml/src/dataset.py`, modify `train.py` to feed `[B, T=5, C, H, W]`
- **Target:** T+12h MAE ≤ 120 km, T+24h MAE ≤ 100 km

### ERA5 Atmospheric Context
- **What:** Expand input tensor from 2 channels (IR + WV) → 6+ channels (add wind shear, vorticity, pressure, SST)
- **Why:** Atmospheric context like 200-850 hPa wind shear is the strongest predictor of rapid intensification
- **How:** Run `scripts/download_era5.py` (requires free Copernicus CDS API key)
- **Files:** `ml/src/dataset.py`, `scripts/download_era5.py`

### Confidence Calibration
- **What:** Enable `predict_confidence=True` in `model_config.json` and apply Platt/temperature scaling
- **Why:** Current confidence values are raw sigmoid outputs from an untrained linear layer
- **Files:** `ml/configs/model_config.json`, `ml/src/model.py`

---

## 🟠 Medium-Term (Weeks 3–4)

### PostgreSQL Migration
- **What:** Replace SQLite with PostgreSQL + PostGIS for spatial queries and production scale
- **How:** `docker compose up postgres -d`, update `backend/.env`, run `alembic upgrade head`
- **Schema additions:** Expand `classifications` table with `t12_lat/lon`, `t24_lat/lon`, `damage_class`, `severity_score`

### M+G+S Multi-Task Impact Engine
- **What:** Add Ground Damage (G0–G11) and Severity (S0–S4) prediction heads to the model
- **Why:** Transforms CycloneWatch from an atmospheric classifier into a disaster impact predictor
- **Data sources needed:** NDRF post-disaster reports, Copernicus EMS damage maps, NIDM database
- **Files:** `ml/src/model.py` (new `fc_damage`, `fc_severity` heads), `backend/app/services/impact_service.py`

### Real-Time INSAT Polling (Live Mode)
- **What:** Poll MOSDAC WMS endpoint every 15 minutes for fresh INSAT-3DR imagery
- **Why:** Currently Live Mode shows NASA MODIS from the last 3 days — INSAT gives 30-minute updates
- **Files:** `frontend/src/components/Dashboard/LeafletMap.tsx`, `frontend/src/store/useCycloneStore.ts`

---

## 🔵 Long-Term (Weeks 5+)

### Dynamic Track Color Coding
Intensity-based polyline segment colors on the historical track:

| Wind Speed | Color | Category |
|---|---|---|
| < 35 kt | `#6b7280` grey | Depression |
| 35–60 kt | `#eab308` yellow | CS |
| 60–90 kt | `#f97316` orange | SCS |
| 90–115 kt | `#ef4444` red | VSCS |
| ≥ 115 kt | `#9333ea` purple | SUCS/Eye |

### Admin Panel & Dual Data Source Toggle
- Protected route `/admin` to compare NASA GIBS vs INSAT predictions side-by-side
- `dataSource: 'NASA' | 'ISRO'` toggle in Zustand store

### Ground Destruction Reporting
- Populate `ground_reports` table with NDRF field data
- Map overlay with red pin markers at each geolocated damage report
- Admin verification badge system

### 3D CesiumJS Globe UI (Optional)
- Replace Leaflet 2D map with WebGL-powered 3D Earth using `cesium` + `resium`
- Geodesic track lines, CZML time animation, progressive cloud overlay

---

## 📊 Performance Targets

| Metric | Current | Target |
|--------|---------|--------|
| T+12h MAE | ~255 km | ≤ 120 km |
| T+24h MAE | ~400 km | ≤ 100 km |
| Pattern Accuracy | 78.3% | ≥ 88% |
| Training Events | 7 | 51 |
| Input Channels | 2 | 6 → 32 |
| Distance to Coast | ✅ Dynamic | ✅ Dynamic |
| Time to Impact | ✅ Dynamic | ✅ Dynamic |
| Uncertainty Cone | ✅ Dynamic | ✅ Dynamic |

> **Operational threshold for IMD integration:** T+24h MAE < 100 km, Pattern Accuracy > 90%.
