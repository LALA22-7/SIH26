# CycloneWatch: Comprehensive Future Implementation Plan

> **Document Status:** Active | **Last Updated:** September 2026 (post-cleanup) | **Maintained by:** CycloneWatch Team, SIH26
>
> **See also:** [ROADMAP.md](../ROADMAP.md) for a concise summary of what's next.

This document is the single authoritative source for every planned future change to the CycloneWatch platform — from minor UI tweaks to complete ML architecture overhauls. Each section covers what the change is, why it's needed, exactly how it will be built, what data sources we will use, and what performance improvements we expect.

---

## Table of Contents

1. [Phase 2 — MAE Reduction: ISRO MOSDAC 1km Integration](#1-phase-2--mae-reduction-isro-mosdac-1km-integration)
2. [Phase 2 — Temporal Forecasting: ConvLSTM Architecture Shift](#2-phase-2--temporal-forecasting-convlstm-architecture-shift)
3. [Phase 2 — Expanded Training Dataset Pipeline](#3-phase-2--expanded-training-dataset-pipeline)
4. [Phase 3 — Ground Destruction Engine: The M+G+S Taxonomy](#4-phase-3--ground-destruction-engine-the-mgs-taxonomy)
5. [Phase 3 — 3D CesiumJS Globe UI](#5-phase-3--3d-cesiumjs-globe-ui)
6. [Phase 3 — Real-Time Frame Animation Engine](#6-phase-3--real-time-frame-animation-engine)
7. [Phase 4 — Admin Panel & Dual Data Source Toggle](#7-phase-4--admin-panel--dual-data-source-toggle)
8. [Phase 4 — Dynamic Tracking Path Colors](#8-phase-4--dynamic-tracking-path-colors)
9. [Phase 4 — On-Ground Destruction Reporting](#9-phase-4--on-ground-destruction-reporting)
10. [Phase 4 — Confidence Calibration & Uncertainty Cones](#10-phase-4--confidence-calibration--uncertainty-cones)
11. [Minor UI Improvements Queue](#11-minor-ui-improvements-queue)
12. [MAE Reduction Roadmap Summary](#12-mae-reduction-roadmap-summary)

---

## 1. Phase 2 — MAE Reduction: ISRO MOSDAC 1km Integration

**Priority:** Critical  
**Estimated Timeline:** 1–2 months after access approval  
**Expected Impact:** T+12h MAE drops from ~255 km → ~150 km; Pattern accuracy improves to >85%

### The Problem
Our current satellite data source is **NOAA GridSat-B1** at **4 km/pixel** resolution. At this resolution, when a depression is still disorganized (the satellite structure is spread over thousands of km), the exact vortex center can be anywhere in a 300+ km window. The CNN is guessing the center within a fog.

More critically, 4km/pixel makes it **impossible to detect micro-structures** that precede Rapid Intensification:
- Inner eyewall formation (only visible at <2km resolution)
- Individual spiral feeder bands (need <3km to resolve)
- Early concentric eyewall cycles

### The Fix: INSAT-3DR via MOSDAC
ISRO's **MOSDAC (Meteorological and Oceanographic Satellite Data Archival Centre)** provides free research access to INSAT-3DR data at **1 km/pixel** — a 16× increase in spatial detail per frame.

### Implementation Steps
1. **Access Request:** Submit formal research access application to MOSDAC at `mosdac.gov.in`. Our institutional affiliation (SIH/IMD collaboration) expedites approval.
2. **New Ingestion Script (`scripts/download_insat.py`):** We will write a MOSDAC API client that downloads INSAT-3DR HDF5 files by date range, parallel to our existing `download_gridsat.py`.
3. **Dual-Source Normalization:** Extend `standardize_data.py` to handle both GridSat NetCDF and INSAT HDF5 file formats, outputting the same `NPZ [C, H, W]` tensor format the model expects.
4. **Model Retrain:** Run `python -m ml.src.train` with the new 1km tensors. No architecture change needed — `CycloneCNN` uses `AdaptiveAvgPool2d(16×16)` which handles any spatial resolution automatically.
5. **Verification against NASA GIBS:** Every INSAT-derived prediction will be cross-referenced against our existing NASA GIBS ground truth to catch systematic offsets before they contaminate the training set.
6. **IBTrACS Cross-check:** Center predictions validated against IBTrACS best-track positions using Haversine MAE as the final acceptance gate.

### Data Sources for This Phase
| Source | URL / Access | What We Use It For |
|--------|-------------|-------------------|
| ISRO MOSDAC | mosdac.gov.in (research access) | Primary 1km IR + WV imagery |
| NASA GIBS | gibs.earthdata.nasa.gov | Visual verification layer |
| IBTrACS v4.01 | ncei.noaa.gov/ibtracs | Ground truth position & intensity |

---

## 2. Phase 2 — Temporal Forecasting: ConvLSTM Architecture Shift

**Priority:** High  
**Estimated Timeline:** 2 months (after MOSDAC data secured)  
**Expected Impact:** T+24h MAE drops from extrapolated → <100 km (operational level)

### The Problem
The current `CycloneTemporalModel` in `ml/src/model.py` already has a GRU head (`self.gru`) built in — but the training loop only feeds it a **single frame** (`images.unsqueeze(1)` adds a fake T=1 dimension). This means the temporal model has never actually *seen* a sequence. The T+12 and T+24 center predictions in `ml/inference.py` are simply copying the current center (`t12_lat = cur_lat`), which is the persistence baseline.

### The Fix: True Sequence Training
1. **New Dataset class (`CycloneSequenceDataset`):** Instead of returning a single `[C, H, W]` frame, this dataset returns a sliding window of `T=5` frames from the same cyclone event in chronological order → tensor `[T=5, C, H, W]`. It also returns the **ground truth centers at T+12h and T+24h** as training targets.
2. **Sequence Training Loop:** The `train.py` main loop is upgraded to use `CycloneSequenceDataset`. The model now receives `[B, T=5, C, H, W]` and outputs `t12_center` and `t24_center` with proper MSE supervision.
3. **Architecture Upgrade (Optional — ConvLSTM):** If the GRU fails to converge on long-range recurvature events, we upgrade to a full ConvLSTM layer that preserves spatial structure through time instead of collapsing it to a 1D vector. This requires the `convlstm` PyPI package.
4. **Motion Vector Learning:** The model learns to detect motion directly from the sequence — storms moving NW at 15 km/h will look different in the tensor from storms moving NE at 8 km/h, and the GRU captures this implicitly.

### Architecture After Upgrade

```
Input: [B, T=5, C=2, H, W]  (5 frames × IR + WV)
    ↓
CycloneCNN backbone (shared weights, processes each frame)
    ↓
Feature sequences: [B, T=5, 128]
    ↓
GRU / ConvLSTM  →  hidden state [B, 128]
    ↓
┌─────────────────────┬──────────────────────┬──────────────────────┐
│  Current center     │  T+12h center        │  T+24h center        │
│  (lat/lon)          │  (lat/lon supervised) │  (lat/lon supervised) │
└─────────────────────┴──────────────────────┴──────────────────────┘
```

---

## 3. Phase 2 — Expanded Training Dataset Pipeline

**Priority:** High  
**Estimated Timeline:** Ongoing (runs parallel to MOSDAC integration)  
**Expected Impact:** Generalization to unusual storm types; curved_band F1 improves from 0.55 → >0.70

### The Problem
The model is trained on only 7 cyclones and 423 labeled frames. The `curved_band` class has the lowest F1 (0.545) because it is the rarest and most structurally variable class. The model is overfitting to the specific visual signatures of Amphan and Biparjoy.

### The Fix
1. **Add 20+ more cyclone events** to the `model_config.json → training_data.events` list, including:
   - **Yaas 2021** (Bay of Bengal, rapid intensification case)
   - **Mocha 2023** (extreme peak intensity, Bangladesh landfall)
   - **Gaja 2018** (unusual track, Tamil Nadu landfall)
   - **Madi 2013** (rare BoB recurvature)
   - **Asani 2022** (hard negative — looked dangerous, weakened before landfall)
2. **EU ECMWF ERA5 Reanalysis data** as a secondary source for atmospheric context (wind shear, vorticity) to pair with each satellite frame.
3. **Hard Negative Mining:** Deliberately include 5–10 cases of disturbances that looked like forming cyclones but never organized (hard negatives). This prevents the model from overcalling risk.
4. **Data Augmentation:** Add horizontal flips, 90° rotations, and small brightness jitter to the `CycloneDataset.__getitem__()` method to synthetically triple the effective dataset size.

### Data Sources
| Source | What We Collect |
|--------|----------------|
| NOAA GridSat-B1 (existing) | Historical IR + WV frames for new events |
| IBTrACS v4.01 (existing) | Ground truth labels via `ibtracs_intensity_rules` |
| EU ECMWF ERA5 | Atmospheric reanalysis context (wind shear, SST) |
| IMD Cyclone E-Atlas | Supplementary track and intensity data |

---

## 4. Phase 3 — Ground Destruction Engine: The M+G+S Taxonomy

**Priority:** High (differentiator feature)  
**Estimated Timeline:** 3–6 months  
**Expected Impact:** Transforms CycloneWatch from atmospheric classifier → disaster impact predictor

### The Problem
Two cyclones with identical Eye morphology (M4) can produce wildly different ground-level consequences depending on landfall location, coastal geometry, population density, and terrain. Our current model tells you **what the storm looks like** but not **what it will do to the ground**.

### The Three-Layer Classification System

| Layer | Code | What It Represents | Example Values |
|-------|----|-------------------|----------------|
| Morphology (M) | M0–M4 | Satellite cloud structure | M0=Disorganized, M4=Eye |
| Ground Damage (G) | G0–G11 | Type of destruction caused | G1=Vegetation, G3=Power Grid, G6=Coastal Flooding |
| Severity (S) | S0–S4 | Magnitude of destruction | S0=None, S4=Catastrophic |

### Implementation Steps
1. **Ground Truth Data Collection:** Build a scraper pipeline to ingest NDRF post-disaster reports, verified satellite damage imagery (Sentinel-2 before/after pairs), IMD bulletin archives, and disaster assessment CSVs from NIDM (National Institute of Disaster Management).
2. **Damage Label CSV Generation:** For each cyclone event in the training set, create a new `ground_damage_labels.csv` mapping `(event_id, timestamp, landfall_region) → (G_class, S_score)`.
3. **Multi-Task Model Upgrade:** Add two new prediction heads to `CycloneTemporalModel`:
   - `self.fc_damage` → 12-class CrossEntropyLoss for G label
   - `self.fc_severity` → regression head for S score (0.0–4.0)
4. **Cascade Logic Engine (`services/impact_service.py`):** A rule-based post-processor that combines M, G, and S outputs with coastal topography (loaded from GeoJSON) to generate a human-readable impact narrative.
5. **Frontend Display:** New `ImpactPanel` component in the right metrics column showing the predicted G+S cascade timeline for a landfall scenario.

### Data Sources for This Phase
| Source | Data Type |
|--------|----------|
| NDRF Post-Disaster Reports | Structured damage narratives |
| Copernicus Emergency Management (EMS) | Sentinel-2 damage assessment maps |
| NIDM Disaster Database | Historical damage statistics by event |
| ISRO Bhuvan | High-res Indian coastal terrain/topology |
| OpenStreetMap | Population density & infrastructure polygons |

---

## 5. Phase 3 — 3D CesiumJS Globe UI

**Priority:** Medium  
**Estimated Timeline:** 3–4 weeks (parallel sprint)  
**Expected Impact:** Eliminates 2D map projection distortions; smoother animated cloud playback

### The Problem
`react-leaflet` uses a Mercator 2D projection. This causes:
- Visual "stitch marks" where tiles meet at high zoom
- Storm tracks that appear straight but curve in reality
- No native support for animated 3D volume overlays

### The Fix
1. **Add CesiumJS dependency:** `npm install cesium resium` (Resium is the React wrapper for Cesium).
2. **Replace `LeafletMap.tsx` with `CesiumGlobe.tsx`:** The new component initializes a `Cesium.Viewer` instance and projects satellite imagery as `ImageryLayer` tiles (using NASA GIBS WMS, exactly the same source we use now).
3. **Animated Frame Playback:** Each historical NPZ frame's center and classification gets a `TimeIntervalCollection` assigned, enabling Cesium's built-in CZML time animation.
4. **3D Track Line:** The cyclone track polyline becomes a proper geodesic (great-circle) line on the globe, correcting the Mercator distortion.
5. **Smooth Cloud Overlay:** NASA GIBS WMTS tiles are loaded progressively into a `CesiumTerrainProvider`-backed layer so the cloud animation has no stutter or blank frames.

### Tech Stack for This Phase
- `cesium` + `resium` (React wrapper)
- NASA GIBS WMTS endpoint (same URL, just different tile format)
- CZML (Cesium Spatial-Temporal Language) for animated track

---

## 6. Phase 3 — Real-Time Frame Animation Engine

**Priority:** Medium  
**Estimated Timeline:** 2 weeks  
**Expected Impact:** Real-time cloud formations animate smoothly instead of static frame-by-frame jumps

### The Problem
In the current real-time mode, the satellite imagery tile on the map is a static NASA GIBS snapshot that only refreshes when the user reloads. There is no animation between frames.

### The Fix
1. **Frame Buffer Queue:** Add a `frameBuffer: string[]` array to `useCycloneStore.ts`. A background `useEffect` pre-fetches the next 3 NASA GIBS timestamps and caches them in this buffer.
2. **Animation Loop:** In `LeafletMap.tsx`, a `setInterval` cycles through the buffered frames at 1 frame/second, updating the WMS tile layer URL.
3. **Live Indicator Pulse:** The green dot on `SatellitePanel.tsx` transitions from a steady glow to a heartbeat pulse to indicate the animation is running.
4. **Frame Metadata Badge:** A small overlay shows the current frame timestamp (IST) and the frame source in the top-centre badge strip.

---

## 7. Phase 4 — Admin Panel & Dual Data Source Toggle

**Priority:** Medium  
**Estimated Timeline:** 1 week (UI only; backend already architected for this)

### The Problem
Once ISRO MOSDAC data is integrated, operators need to compare NASA GIBS predictions vs. INSAT-3DR predictions side-by-side. Currently the data source is hardcoded to NASA GIBS.

### The Fix
1. **Admin Route (`/admin`):** A protected React route behind a password gate. The admin view adds a source toggle to the top navigation.
2. **Data Source Toggle in Store:** Add `dataSource: 'NASA' | 'ISRO'` to `useCycloneStore`. When toggled, the `/api/replay/{eventId}` call appends `?source=isro` or `?source=nasa`.
3. **Backend `?source=` Param:** The replay endpoint in `backend/app/api/replay.py` is extended to filter classification results by the frame's `source` field in the DB.
4. **Side-by-Side Diff View:** Admin mode splits the metrics panel into two columns — NASA result left, ISRO result right — so researchers can audit disagreements directly.

---

## 8. Phase 4 — Dynamic Tracking Path Colors

**Priority:** Low  
**Estimated Timeline:** 3 days  
**Expected Impact:** Visual communication of intensification without reading numbers

### The Plan
Currently the cyclone track polyline on the Leaflet map is a single static color. This change makes each track segment's color reflect the cyclone's intensity at that timestamp.

**Color scheme (IBTrACS categories):**
| Wind Speed | Color | Meaning |
|-----------|-------|---------|
| < 35 kt | `#6b7280` (grey) | Disorganized / Depression |
| 35–60 kt | `#eab308` (yellow) | Curved Band / CS |
| 60–90 kt | `#f97316` (orange) | Banding / SCS |
| 90–115 kt | `#ef4444` (red) | Banding+ / VSCS |
| ≥ 115 kt | `#9333ea` (purple) | Eye / SUCS |

**Implementation:** In `LeafletMap.tsx`, replace the single `L.polyline` with a series of short `L.polyline` segments, each colored from the classification data at that step. This is pure frontend work — no backend changes needed.

---

## 9. Phase 4 — On-Ground Destruction Reporting

**Priority:** Medium  
**Estimated Timeline:** 4–6 weeks  
**Expected Impact:** Turns CycloneWatch into a post-disaster verification tool for NDRF/IMD

### The Plan
A crowdsourced or NDRF-fed reporting layer on the map where verified field agents can mark specific geolocated damage reports. Implemented as:
1. **New DB table: `ground_reports`** — `(event_id, lat, lon, damage_type, severity, timestamp, reporter_id, verified)`.
2. **API endpoints:** `POST /api/reports` (submit), `GET /api/reports/{event_id}` (fetch all).
3. **Map Overlay:** Red pin markers on the Leaflet/Cesium map at each report location, with click-to-expand detail cards.
4. **NDRF Integration:** An admin-verified badge system ensures only vetted reports appear on the public dashboard.

---

## 10. Phase 4 — Confidence Calibration & Uncertainty Cones

**Priority:** Medium  
**Estimated Timeline:** 2 weeks (after T+24 model is trained)  
**Expected Impact:** Confidence scores become statistically meaningful probabilities

### The Problem
The current model's confidence output (`fc_confidence` head) is **not trained** (`predict_confidence=false` in `model_config.json`). The displayed confidence values are raw sigmoid outputs from an untrained linear layer — essentially random numbers that happen to look reasonable.

### The Fix
1. **Enable `predict_confidence=True`** in `model_config.json` and re-run training.
2. **Platt Scaling / Temperature Scaling:** After training, apply temperature calibration (the `self.temperature` parameter already exists in `CycloneTemporalModel`) to map raw logits to true probabilities.
3. **Calibration Evaluation:** Generate a reliability diagram (predicted confidence vs actual accuracy) on the held-out validation set to prove calibration.
4. **Uncertainty Cones on Map:** The T+12h and T+24h forecast positions gain a 1-sigma and 2-sigma ellipse overlay (replacing the current hardcoded `sigma_lat=0.5`).

---

## 11. Phase 5 — Model Retraining & Impact Metric Engine

**Priority:** High (Technical Debt)  
**Estimated Timeline:** 1 week (pre-requisite for production)  
**Expected Impact:** Live inference stops outputting "Disorganized", and Impact Metrics become mathematically accurate.

### The Problem (Untrained Model Bias & Hardcoded UI)
1. **Live Inference Bias:** Currently, if live inference is run, the backend calls `ml/inference.py`. Because the `model.pt` checkpoint hasn't been generated via a full training loop in the current environment, PyTorch defaults to an untrained model with random weights. This causes a heavy bias where it classifies almost everything as "Disorganized".
2. ~~**Hardcoded Metrics:** The "Distance to Coast" (320km) and "Time to Impact" (24hrs) metrics on the dashboard are currently UI placeholders for the demo phase.~~ **✅ RESOLVED (Sep 2026)**

### The Fix
1. **Run the Training Loop:** Execute `python -m ml.src.train` to train the CNN on the 423 labeled frames and generate a valid `model.pt` checkpoint. This will restore the 78.3% pattern accuracy for live predictions.
2. ~~**Geospatial Math Integration:** Replace the hardcoded UI metrics by implementing a Haversine intersection algorithm.~~ **✅ DONE** — `GET /api/coastline/distance` endpoint now computes real Haversine distance to the Indian coastline using `india_coastline.geojson`.
3. ~~**Time to Impact Calculation:** Divide the exact distance to the coast by the storm's calculated movement speed vector.~~ **✅ DONE** — `MetricsPanel.tsx` now dynamically computes storm translation speed from consecutive frame coordinates and derives Time to Impact.

---

## 12. Minor UI Improvements Queue

These are small, self-contained changes that can be implemented in 1–2 days each:

| Change | File(s) | Status | Notes |
|--------|---------|--------|-------|
| `cursor: pointer` on all event table rows | `TopNavigation.tsx`, `MetricsPanel.tsx` | ⏳ Queued | `hover:cursor-pointer` class addition |
| Map text color visibility (contrast fix) | `index.css`, `LeafletMap.tsx` | ⏳ Queued | Increase leaflet popup text contrast |
| Alert / Profile page redesign | New component files | ⏳ Queued | Currently placeholder buttons |
| Cyclone regions (beyond 2 basins) | `cyclones.ts`, `TopNavigation.tsx` | ⏳ Queued | Add: BoA, Somalia Basin sub-regions |
| Risk formation % heuristic | `MetricsPanel.tsx` | ✅ Done | SST + wind heuristic added |
| Distance to coast display | `MetricsPanel.tsx` | ✅ Done | **Dynamic Haversine via `/api/coastline/distance`** |
| Time to impact display | `MetricsPanel.tsx` | ✅ Done | **Dynamic — computed from real storm speed** |
| Uncertainty cone scaling | `LeafletMap.tsx` | ✅ Done | **Dynamic — scales with `t24_km` MAE** |
| IST timezone globally | All UI components | ✅ Done | |
| Map layout 70:30 | `App.tsx` | ✅ Done | |
| Green live indicator dot | `SatellitePanel.tsx` | ✅ Done | |
| Historical archive classification fix | `cyclonewatch.db` (patch) | ✅ Done | 423 frames patched |

---

## 13. MAE Reduction Roadmap Summary

| Phase | Change | T+12h MAE Target | Pattern Accuracy Target |
|-------|--------|-----------------|------------------------|
| **Now (prototype)** | 7 events, 4km GridSat | ~255 km | 78.3% |
| **Phase 2a** | ISRO MOSDAC 1km | ~150 km | >85% |
| **Phase 2b** | ConvLSTM + sequence supervision | ~120 km | >85% |
| **Phase 2c** | 30+ events, EU+ISRO pipeline | ~100 km | >88% |
| **Phase 3** | M+G+S Multi-Task, full calibration | <80 km | >90% |

> **Operational threshold for IMD integration:** T+24h MAE < 100 km, Pattern Accuracy > 90%.  
> This is achievable in Phase 2c with full MOSDAC access.
