# CycloneWatch — Backend

FastAPI + PostgreSQL/PostGIS backend for the CycloneWatch PS70 system.

---

## Folder structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory, CORS, router registration
│   ├── core/
│   │   └── config.py        # Settings loaded from environment variables
│   ├── api/
│   │   ├── health.py        # GET /health
│   │   ├── frames.py        # GET /api/ps70/frames/{frame_id}
│   │   ├── classify.py      # POST /api/ps70/classify  |  GET /api/ps70/classifications/{event_id}
│   │   ├── predict.py       # POST /api/ps70/predict
│   │   ├── replay.py        # GET /api/replay/{event_id}
│   │   └── metrics.py       # GET /api/metrics
│   ├── db/
│   │   ├── session.py       # Async SQLAlchemy engine + get_db dependency
│   │   └── geo_types.py     # Portable geometry type (PostGIS / SQLite fallback)
│   ├── models/
│   │   ├── event.py
│   │   ├── satellite_frame.py
│   │   ├── classification.py
│   │   ├── prediction.py
│   │   └── metric_row.py
│   ├── schemas/             # Pydantic v2 request/response models
│   └── services/
│       ├── geo.py           # haversine_km, mean_absolute_error_km
│       ├── ml_adapter.py    # Bridges backend ↔ ml package (stub or real)
│       ├── classify_service.py
│       └── predict_service.py
├── alembic/                 # DB migrations
│   └── versions/
│       └── 0001_initial_schema.py
├── scripts/
│   ├── seed_db.py           # Insert demo data (run once after migration)
│   └── precompute_replay.py # Pre-run inference for offline replay
├── tests/                   # pytest test suite (93 tests)
├── Dockerfile               # Multi-stage: base / dev / prod
├── docker-compose.yml       # Dev (hot-reload, volumes)
├── docker-compose.prod.yml  # Prod (baked image, no mounts)
├── pyproject.toml           # uv-managed dependencies
├── alembic.ini
└── .env.example
```

---

## Quick start — development

### Prerequisites

- Docker Desktop (running)
- No local Python required — everything runs inside Docker

### 1. Copy environment file

```bash
cp .env.example .env
# Edit .env if you need non-default credentials
```

### 2. Start services

```bash
docker compose up
```

This starts:
- `cyclonewatch_db` — PostgreSQL 15 + PostGIS 3.3 on port 5432
- `cyclonewatch_api` — FastAPI on port 8000 with hot-reload

### 3. Run database migrations

In a second terminal (while compose is running):

```bash
docker compose exec api alembic upgrade head
```

### 4. Seed demo data

```bash
docker compose exec api python -m scripts.seed_db
```

To re-seed from scratch:

```bash
docker compose exec api python -m scripts.seed_db --reset
```

### 5. Verify

```bash
curl http://localhost:8000/health
# {"status":"ok","db":"ok"}

curl http://localhost:8000/api/ps70/frames/frame_001
curl -X POST http://localhost:8000/api/ps70/classify \
  -H "Content-Type: application/json" \
  -d '{"event_id":"biparjoy_2023","timestamp":"2023-06-14T12:00:00Z","frame_id":"frame_001"}'
```

Interactive docs: http://localhost:8000/docs

---

## Quick start — production

```bash
cp .env.example .env.prod
# Fill in production credentials in .env.prod

docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
docker compose -f docker-compose.prod.yml exec api python -m scripts.seed_db
```

---

## Running tests

Tests use in-memory SQLite — no Docker required.

```bash
# From the backend/ directory with the virtual environment active:
python -m pytest -v

# With coverage:
python -m pytest --cov=app --cov-report=term-missing
```

To set up the virtual environment locally:

```bash
uv venv .venv
uv pip install --python .venv -e ".[dev]"
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS
pytest -v
```

---

## Pre-compute offline replay

Before the demo, pre-populate all classifications and predictions so that
`GET /api/replay/{event_id}` works with no internet and no ML calls:

```bash
docker compose exec api python -m scripts.precompute_replay --event_id biparjoy_2023
```

This script:
1. Loads every frame for the event from the DB
2. Runs classify + predict for each frame (stub or real model)
3. Loads IBTrACS best-track actuals from `/data/ground_truth/biparjoy_2023_best_track.csv`
4. Computes Haversine errors and stores MetricRow entries

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `cyclone` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `cyclone_secret` | PostgreSQL password |
| `POSTGRES_DB` | `cyclonewatch` | Database name |
| `DATABASE_URL` | auto-set by compose | Async SQLAlchemy URL (`asyncpg`) |
| `DATABASE_SYNC_URL` | auto-set by compose | Sync SQLAlchemy URL (`psycopg2`, used by Alembic + scripts) |
| `DEBUG` | `true` | Enables SQLAlchemy query logging |
| `API_VERSION` | `v1` | Shown in OpenAPI metadata |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins (use `*` for dev) |
| `DATA_ROOT` | `/data` | Root path of satellite data inside container |
| `DEMO_DATA_ROOT` | `/data/demo` | Path to cached demo data |
| `ML_PACKAGE_PATH` | `/ml` | Path to ML package (set via `PYTHONPATH` in compose) |
| `ML_FORCE_STUB` | `false` | Force stub ML mode even if `ml.inference` is importable |

---

## ML integration

The backend integrates with the ML package via `app/services/ml_adapter.py`.

**Stub mode** (default until ML hands off the model):
- Returns deterministic fixture data
- Clearly labeled: `"name": "ps70-classifier-stub"`
- Activated automatically when `ml.inference` is not importable, or when `ML_FORCE_STUB=true`

**Real mode** (once ML delivers `ml/src/inference.py`):
- `ml_adapter.py` calls `ml.inference.predict_frame(frame_array)` and `ml.inference.predict_sequence(sequence)`
- The ML package must be mounted at `/ml` in the container (done automatically via `docker-compose.yml`)
- Expected return contract:
  ```python
  predict_frame(frame: np.ndarray) -> {
      "center": {"lat": float, "lon": float},
      "pattern": {"label": str, "confidence": float},
      "model": {"name": str, "version": str}
  }
  ```

---

## API summary

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness + DB check |
| GET | `/api/ps70/frames/{frame_id}` | Frame metadata (+ `?format=image` to stream file) |
| POST | `/api/ps70/classify` | Run classification on a frame |
| GET | `/api/ps70/classifications/{event_id}` | Time-series of all classifications |
| POST | `/api/ps70/predict` | Run temporal prediction (T+12, T+24) |
| GET | `/api/replay/{event_id}` | Full historical replay (DB-only, no ML) |
| GET | `/api/metrics` | Aggregated MAE, accuracy, uncertainty coverage |

Full schema documentation: http://localhost:8000/docs  
API contract reference: [`../docs/api_contract.md`](../docs/api_contract.md)

---

## Key conventions

- All timestamps are UTC (`timezone.utc`)
- GeoJSON coordinate order: `[longitude, latitude]`
- ML tensor shapes: `[C, H, W]` (single frame), `[T, C, H, W]` (sequence)
- PostGIS geometry inserts: `ST_SetSRID(ST_MakePoint(lon, lat), 4326)` — lon first
- Uncertainty is labeled `"provisional"` until Day-6 calibration. Never set `coverage_target` without measured validation.
- Replay endpoint never calls ML. All inference must be pre-computed via `precompute_replay.py`.

---

## Integration Handoff — How Every Team Connects to the Backend

> **Read this before merging.** The backend is complete and tested. When other teams finish their work, this section tells you exactly what to provide, where to put it, and what to run to make the full system work in one iteration.
>
> Backend status: **complete, 93/93 tests passing, stub mode active.**
> The system works end-to-end right now with fake ML results. Swap in real data + real model using the steps below.

---

### Current state at any point in time

Run this to see what is real vs. stub:

```bash
# Check if real ML model is active
docker compose exec api python -c "from app.services.ml_adapter import _get_mode; print(_get_mode())"
# Prints: stub   ← until ml/inference.py exists
# Prints: real   ← after ML team delivers

# Check all endpoints are responding
curl http://localhost:8000/health
curl http://localhost:8000/api/ps70/classifications/biparjoy_2023
curl "http://localhost:8000/api/metrics?event_id=biparjoy_2023"
```

---

### ML Team (Aditya) — Integration steps

**What the backend expects from you, exactly:**

Create `ml/inference.py` at the root of the `ml/` folder. It must export two functions:

```python
# ml/inference.py

import numpy as np
from typing import Any

def predict_frame(frame: np.ndarray) -> dict[str, Any]:
    """
    Single frame classification.

    Input  : float32 numpy array, shape [C, H, W]
             C = channels (IR=0, water_vapor=1, visible=2)
             H, W = spatial dims (whatever you trained on, e.g. 256 or 512)

    Output : {
        "center":  {"lat": float, "lon": float},
        "pattern": {"label": str,   "confidence": float},   # confidence: 0.0–1.0
        "model":   {"name": str,    "version": str}
    }
    """
    ...

def predict_sequence(sequence: np.ndarray) -> dict[str, Any]:
    """
    Temporal prediction from a sequence of frames.

    Input  : float32 numpy array, shape [T, C, H, W]
             T = number of frames in the sequence (all frames up to base_time)

    Output : {
        "predictions": [
            {
                "horizon_hours": 12,
                "center":  {"lat": float, "lon": float},
                "pattern": {"label": str, "confidence": float},
                "sigma_lat": float,   # std-dev uncertainty in lat (degrees). e.g. 0.5
                "sigma_lon": float,   # std-dev uncertainty in lon (degrees). e.g. 0.5
            },
            {
                "horizon_hours": 24,
                ... same structure ...
            }
        ],
        "model": {"name": str, "version": str}
    }
    """
    ...
```

**Rules that matter:**
- Shape is `[C, H, W]` for single frame. **Not** `[H, W, C]`. **Not** `[1, C, H, W]`.
- Shape is `[T, C, H, W]` for sequence. **Not** `[C, T, H, W]`.
- `model.name` must **not** contain the word `"stub"` — the adapter detects stub mode by checking for this string.
- Pattern labels must be one of: `eye`, `banding`, `curved_band`, `shear_affected`, `disorganized`. Agree with Research before training — the label set is locked.
- `sigma_lat` and `sigma_lon` are in degrees. 0.5 ≈ 55 km uncertainty. Provide these even before calibration.

**Steps to activate real mode:**

```bash
# 1. Make sure ml/inference.py exists and is importable
#    (it's mounted at /ml inside the container via docker-compose.yml)

# 2. In .env, set:
ML_FORCE_STUB=false

# 3. Restart the API
docker compose restart api

# 4. Confirm real mode
docker compose exec api python -c "from app.services.ml_adapter import _get_mode; print(_get_mode())"
# Should print: real

# 5. Run the full test suite — all 93 must still pass
cd backend
python -m pytest -v
```

**After Day-6 calibration (uncertainty upgrade):**

When your calibrated `sigma_lat`/`sigma_lon` values are ready, update `predict_sequence` to return real values instead of provisional ones. Then tell Satyam so the `uncertainty_status` field can be changed from `"provisional"` to `"calibrated"` and `coverage_target` can be set.

No backend code changes are needed for this — the API already handles it automatically when real sigma values come from the model.

---

### Data Team (Abhinav) — Integration steps

**1. File naming — follow this exactly:**

```
data/normalized/{event_id}_{timestamp}_{channel}_{source}.tif

Examples:
  biparjoy_2023-06-14T1200Z_ir_insat.tif
  biparjoy_2023-06-14T1200Z_wv_insat.tif
  biparjoy_2023-06-14T1200Z_visible_insat.tif
```

Timestamp format: `YYYY-MM-DDTHHmmZ` (no colons in filename, Z at end for UTC).

**2. Register frames in the database:**

After placing normalized files, insert `SatelliteFrame` rows so the backend knows they exist. The easiest way is to update `scripts/seed_db.py` with your real frame list — copy the existing pattern:

```python
# In seed_db.py, add your real frames alongside or replacing the demo frames:
frame = SatelliteFrame(
    frame_id="biparjoy_2023-06-14T1200Z",           # unique ID
    event_id="biparjoy_2023",
    timestamp=datetime(2023, 6, 14, 12, 0, tzinfo=timezone.utc),
    channels={"ir": "ir.tif", "water_vapor": "wv.tif"},
    file_paths={
        "ir":          "/data/normalized/biparjoy_2023-06-14T1200Z_ir_insat.tif",
        "water_vapor": "/data/normalized/biparjoy_2023-06-14T1200Z_wv_insat.tif",
    },
    crs="EPSG:4326",
    bbox=[60.0, 5.0, 80.0, 25.0],          # [min_lon, min_lat, max_lon, max_lat]
    resolution={"width": 512, "height": 512},
    source="INSAT-3D",
    local_path="/data/normalized/biparjoy_2023-06-14T1200Z_ir_insat.tif",
)
```

Run `docker compose exec api python -m scripts.seed_db --reset` after updating.

**3. Best-track ground-truth CSV (required for metrics and replay):**

Place at `data/ground_truth/biparjoy_2023_best_track.csv`:

```csv
event_id,timestamp,lat,lon
biparjoy_2023,2023-06-06T00:00:00Z,8.5,65.2
biparjoy_2023,2023-06-06T06:00:00Z,8.8,65.5
```

All timestamps UTC. `lat`/`lon` in decimal degrees. This is consumed by `precompute_replay.py`.

**4. Trigger the replay precompute (coordinate with Satyam):**

Once files are registered and best-track is placed:
```bash
docker compose exec api python -m scripts.precompute_replay --event_id biparjoy_2023
```

After this runs, `/api/replay/biparjoy_2023` and `/api/metrics` will show real data.

---

### Research Team (Arshit) — Integration steps

**What the backend needs from you:**

**1. Lock the pattern label set before ML trains.**

The backend already uses: `eye`, `banding`, `curved_band`, `shear_affected`, `disorganized`.

If your taxonomy uses different names, coordinate with Satyam **before** any model training or database insertion. Changing label names after data is in the DB requires a migration.

**2. Ground-truth labels for classification accuracy.**

After Research assigns manual labels to specific frames, provide a CSV:

```csv
event_id,frame_id,ground_truth_label
biparjoy_2023,frame_001,banding
biparjoy_2023,frame_002,eye
biparjoy_2023,frame_003,curved_band
```

Satyam will load this into the `ground_truth_label` column of the `metrics` table. Without it, `classification.accuracy` stays `null` in `/api/metrics`.

**3. IBTrACS best-track verification.**

The Data team places the best-track CSV. Research team verifies the timestamp format and lat/lon values are correct before the precompute script runs. A mistake here corrupts every error metric.

---

### Frontend Team (Kavya) — Integration steps

**The backend is ready to call right now** with stub data. Start building against live endpoints immediately.

**Base URL (dev):** `http://localhost:8000`

**The 7 calls your UI makes:**

```
1. GET  /health
   → Verify the API is up before showing the dashboard

2. GET  /api/ps70/frames/{frame_id}
   → Get frame metadata (channels available, bbox, timestamp, source)

3. GET  /api/ps70/frames/{frame_id}?format=image
   → Stream the satellite image file for Leaflet display

4. POST /api/ps70/classify
   Body: {"event_id":"biparjoy_2023","timestamp":"2023-06-14T12:00:00Z","frame_id":"frame_001"}
   → Get centre position + pattern + confidence → render marker + pattern card

5. GET  /api/ps70/classifications/biparjoy_2023
   → Full time-series of all classifications → render track line on map

6. POST /api/ps70/predict
   Body: {"event_id":"biparjoy_2023","start_timestamp":"2023-06-14T00:00:00Z"}
   → Get T+12 and T+24 positions + uncertainty polygon → render predicted track + cone

7. GET  /api/replay/biparjoy_2023
   → Full step-by-step replay data → power the timeline slider

8. GET  /api/metrics?event_id=biparjoy_2023
   → MAE numbers and accuracy → populate the metrics/evidence panel
```

**While the backend is not yet running locally:**
Copy the example responses from `docs/api_contract.md` and hardcode them as JSON fixtures in your frontend. The shapes are exact — swap for real API calls without changing your component logic.

**CORS is already set to `*` in dev** — no browser errors when calling from `localhost:3000`.

**For satellite tile serving on Leaflet:**
The `?format=image` endpoint streams a raw GeoTIFF. If Leaflet needs it as XYZ tiles (`/tiles/{z}/{x}/{y}.png`), raise this with Satyam by Day 3 at the latest so a tile-serving layer can be added. Do not raise it on Day 6.

**Coordinate conventions (important for map rendering):**
- All GeoJSON coordinates in API responses are `[longitude, latitude]` — this is what Leaflet and GeoJSON standard expect
- `center.lat` and `center.lon` in the classify/predict responses are plain floats — pass them directly to `L.marker([lat, lon])` (Leaflet takes lat first here, opposite of GeoJSON)
- Uncertainty polygon coordinates are already `[lon, lat]` GeoJSON — pass directly to `L.geoJSON()`

---

### App Dev Team (Aniket) — Integration steps

**The three endpoints you need:**

```
1. GET /api/ps70/classifications/biparjoy_2023
   → Take the last item for "current status" screen
   → Shows: pattern, confidence, centre lat/lon, timestamp

2. POST /api/ps70/predict
   Body: {"event_id":"biparjoy_2023","start_timestamp":"<current_time_utc>"}
   → Shows: T+12 and T+24 predicted positions + pattern

3. GET /api/metrics?event_id=biparjoy_2023
   → Shows: MAE numbers for the "how accurate is this?" screen
```

**Offline fixture strategy (critical for demo):**

The demo may have no internet. Before the demo:
1. Call the three endpoints above while online
2. Save the responses as JSON files bundled inside the app
3. Build a toggle: if API unreachable → load from fixture files
4. Test the offline path on the actual demo device

The API responses will not change shape between now and demo day — safe to bundle.

---

### The One-Shot Integration Sequence

When all teams are ready, this is the exact order to run everything once:

```
Step 1 — Data team places normalized satellite files in data/normalized/
Step 2 — Research team places best-track CSV in data/ground_truth/
Step 3 — ML team delivers ml/inference.py
Step 4 — Update scripts/seed_db.py with real frame paths (Data team coordinates with Satyam)
Step 5 — docker compose up
Step 6 — docker compose exec api alembic upgrade head
Step 7 — docker compose exec api python -m scripts.seed_db --reset
Step 8 — Set ML_FORCE_STUB=false in .env, restart API
Step 9 — Confirm: docker compose exec api python -c "from app.services.ml_adapter import _get_mode; print(_get_mode())"
          Must print: real
Step 10 — docker compose exec api python -m scripts.precompute_replay --event_id biparjoy_2023
Step 11 — python -m pytest -v   (run from backend/ — all 93 must still pass)
Step 12 — Test all endpoints manually:
          curl http://localhost:8000/health
          curl http://localhost:8000/api/ps70/classifications/biparjoy_2023
          curl -X POST http://localhost:8000/api/ps70/predict -H "Content-Type: application/json" \
               -d '{"event_id":"biparjoy_2023","start_timestamp":"2023-06-14T00:00:00Z"}'
          curl http://localhost:8000/api/replay/biparjoy_2023
          curl "http://localhost:8000/api/metrics?event_id=biparjoy_2023"
Step 13 — Frontend connects to http://localhost:8000 and verifies map loads with real data
Step 14 — App connects to http://<server-ip>:8000 and verifies status screen shows real data
Step 15 — Run precompute_replay.py for all events, verify replay slider works offline
Step 16 — Disable internet, verify all endpoints still respond (no external calls allowed)
Step 17 — Done. The system is integrated.
```

---

### What Will NOT Change After Integration

The following are frozen. Do not change these without a backend migration and a team-wide announcement:

| Thing | Frozen value |
|---|---|
| Pattern labels | `eye`, `banding`, `curved_band`, `shear_affected`, `disorganized` |
| ML input shape (single frame) | `[C, H, W]` float32 |
| ML input shape (sequence) | `[T, C, H, W]` float32 |
| GeoJSON coordinate order | `[longitude, latitude]` |
| Timestamp format | UTC ISO 8601 with Z or +00:00 |
| Uncertainty status before calibration | `"provisional"` — never claim a percentage |
| Replay endpoint behaviour | Read DB only — never calls ML at serve time |
| API base paths | `/api/ps70/`, `/api/replay/`, `/api/metrics` |

---

### Raising Issues

If any integration step fails or a contract needs to change:

1. Tell Satyam immediately — do not silently work around it
2. State: what you expected, what actually happened, which file/endpoint
3. If you need to change an API field, data shape, or label name — say so explicitly. Do not change silently.
4. If blocked for more than 30 minutes, escalate

The backend has no hidden dependencies on external services. If it's running on your machine with Docker, it will run on demo day.

---

*For deeper explanation of how every file works: see [`BACKEND_EXPLAINED.md`](./BACKEND_EXPLAINED.md)*

---

## Remaining Backend Work

Everything below is backend work that cannot be done until another team delivers their piece.
Each item is small — none requires more than a few hours once the dependency arrives.

---

### 1. Wire calibrated uncertainty (waiting on: ML — Day 6)

**Trigger:** ML team updates `predict_sequence()` to return real `sigma_lat`/`sigma_lon` from their calibrated model.

**What to do:**
- Set `ML_FORCE_STUB=false` if not already done and restart the API
- Run `precompute_replay.py --event_id biparjoy_2023` to regenerate predictions with real sigma values
- Update the uncertainty status in new predictions from `"provisional"` to `"calibrated"` by adding a flag check in `api/predict.py`:

```python
# In api/predict.py, inside the prediction loop, change:
uncertainty_status = pred["uncertainty_status"]
# to:
uncertainty_status = "calibrated" if pred.get("sigma_lat") and not settings.ml_force_stub else "provisional"
```

- Set `coverage_target` in `UncertaintyBlock` only after measuring actual coverage from the metrics table
- Rerun the full test suite — all 93 must still pass

**Files to touch:** `app/api/predict.py`, `app/schemas/common.py` (remove `coverage_target: None` default if needed)

---

### 2. Load Research team's ground-truth labels (waiting on: Research — Day 4/5)

**Trigger:** Arshit delivers `data/labels/ground_truth_labels.csv` with columns `event_id, frame_id, ground_truth_label`.

**What to do:**
Write a one-off loader (or add to `seed_db.py`) that reads the CSV and updates the `ground_truth_label` column in the `metrics` table:

```python
# scripts/load_ground_truth.py  (to be created)
import csv
from sqlalchemy.orm import Session
from app.models.metric_row import MetricRow

with Session(engine) as db:
    with open("data/labels/ground_truth_labels.csv") as f:
        for row in csv.DictReader(f):
            db.execute(
                update(MetricRow)
                .where(MetricRow.event_id == row["event_id"])
                .where(MetricRow.predicted_label == row["frame_id"])   # match by frame
                .values(ground_truth_label=row["ground_truth_label"])
            )
    db.commit()
```

Without this, `classification.accuracy` in `/api/metrics` stays `null`.

**Files to create:** `scripts/load_ground_truth.py`

---

### 3. Register real satellite frames (waiting on: Data — Day 1/2)

**Trigger:** Abhinav delivers normalized GeoTIFF files in `data/normalized/`.

**What to do:**
Update `scripts/seed_db.py` — replace or extend the 3 demo frame rows with real frame metadata. Each real frame needs:
- `frame_id` matching the file naming convention
- `timestamp` (UTC) matching the actual capture time
- `file_paths` pointing to the real file paths inside the container
- `bbox` set to the actual geographic extent of the image
- `resolution` set to the actual pixel dimensions

Then run:
```bash
docker compose exec api python -m scripts.seed_db --reset
docker compose exec api python -m scripts.precompute_replay --event_id biparjoy_2023
```

**Files to touch:** `scripts/seed_db.py`

---

### 4. Satellite tile serving for Leaflet (waiting on: Frontend — Day 2/3)

**Trigger:** Kavya confirms whether Leaflet can display a raw GeoTIFF via `?format=image` or needs XYZ tiles.

**If raw GeoTIFF works:** No backend change needed. Done.

**If XYZ tiles are needed**, add `rio-tiler` to `pyproject.toml` and create a new endpoint:

```
GET /api/ps70/tiles/{frame_id}/{z}/{x}/{y}.png
```

This uses `rio-tiler` to slice the GeoTIFF on-the-fly into map tiles. Estimated work: 2–3 hours.

**Files to create:** `app/api/tiles.py` (if needed), register in `main.py`

---

### 5. Second event support (waiting on: Data + Research — Day 2/3)

**Trigger:** Data team delivers a second cyclone event dataset.

**What to do:**
- Add the second event row to `scripts/seed_db.py`
- Register all its frames
- Run `precompute_replay.py --event_id <second_event_id>`
- Verify `/api/metrics` (no filter) aggregates across both events correctly

No backend code changes needed — the API already handles multiple events. Just data registration.

---

### 6. Baseline model MAE (waiting on: ML — Day 5/6)

**Trigger:** ML team implements and evaluates a persistence baseline (current position + recent motion vector).

**What to do:**
Populate the `baseline` block in `/api/metrics`. Options:
- ML team runs the baseline and provides MAE numbers → hard-code them into the `BaselineMetrics` response in `api/metrics.py`
- Or: store baseline predictions in the `predictions` table with a different `model_name` (e.g. `"persistence-baseline"`) and compute MAE the same way

The `baseline` field in `MetricsResponse` already exists and returns `null` — just needs values.

**Files to touch:** `app/api/metrics.py` (simplest: add a config dict of known baseline MAE values)

---

### 7. Day-7 API freeze checklist

Run these on Day 7 before freezing:

```bash
# Full test suite — must be 93/93 (or more if new tests added)
cd backend
python -m pytest -v

# Stress-test replay for all events
docker compose exec api python -m scripts.precompute_replay --event_id biparjoy_2023
# repeat for second event

# Verify offline operation — disable network, all endpoints must still respond
# (Docker internal network is fine — no external HTTP calls allowed)

# Verify metrics shows real numbers, not null
curl "http://localhost:8000/api/metrics?event_id=biparjoy_2023"
# track.mae_km_t12 and mae_km_t24 must be non-null floats
# classification.accuracy must be non-null if Research delivered labels

# Check uncertainty status
curl -X POST http://localhost:8000/api/ps70/predict \
  -H "Content-Type: application/json" \
  -d '{"event_id":"biparjoy_2023","start_timestamp":"2023-06-14T00:00:00Z"}' \
  | python -m json.tool | grep uncertainty_status
# Must be "calibrated" if ML calibration is done, "provisional" if not

# After all checks pass — tag the release
git tag v1.0-day7-freeze
git push origin v1.0-day7-freeze
```

After Day 7: **no new features, no schema changes, no new endpoints.** Bug fixes only.

---

### Summary of remaining items

| Item | Waiting on | Estimated effort when unblocked |
|---|---|---|
| Calibrated uncertainty wiring | ML (Day 6) | 1 hour |
| Ground-truth label loader script | Research (Day 4) | 1 hour |
| Real satellite frame registration | Data (Day 1/2) | 1 hour |
| Satellite tile serving (if needed) | Frontend (Day 2/3) | 2–3 hours (only if needed) |
| Second event support | Data + Research (Day 2/3) | 30 min (data registration only) |
| Baseline MAE wiring | ML (Day 5/6) | 30 min |
| Day-7 freeze + stress test | All teams done | 2 hours |

**Total remaining backend work: ~6–9 hours, all blocked on other teams, none blocked on backend.**
