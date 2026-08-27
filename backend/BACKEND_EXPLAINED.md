# CycloneWatch Backend — Explained in Plain Language

> **Who this is for:** You (Satyam), your teammates, and anyone who has never touched a backend before.
> No assumed knowledge. Every file is explained from scratch.
>
> **Rule:** If you read this top to bottom, you will understand exactly what every piece of code does,
> why it exists, and how the whole thing fits together — before looking at a single line of code.

---

## The Big Picture First

Think of the backend as a **restaurant kitchen**.

- The **frontend (React map)** and the **mobile app** are customers sitting at a table.
- They send **orders** (HTTP requests) to the kitchen.
- The kitchen (backend) looks at the order, goes to the fridge (database), calls the chef (ML model),
  plates the food (formats the JSON response), and sends it back.
- The customers never see the fridge, never talk to the chef directly. They only get the plate.

That is literally all a backend is. An order-taker that talks to a database and other services
and sends back clean answers.

---

## The Full Folder Map

```
backend/
│
├── app/                        ← All the actual application code lives here
│   ├── main.py                 ← The front door. Starts everything.
│   ├── core/
│   │   └── config.py           ← Settings (passwords, paths, on/off switches)
│   ├── db/
│   │   ├── session.py          ← How we talk to the database
│   │   └── geo_types.py        ← Special column type for map coordinates
│   ├── models/                 ← The shape of every table in the database
│   │   ├── base.py
│   │   ├── event.py
│   │   ├── satellite_frame.py
│   │   ├── classification.py
│   │   ├── prediction.py
│   │   └── metric_row.py
│   ├── schemas/                ← The shape of every request and response (JSON)
│   │   ├── common.py
│   │   ├── classify.py
│   │   ├── predict.py
│   │   ├── replay.py
│   │   ├── metrics.py
│   │   └── frames.py
│   ├── services/               ← The actual logic (what the code *does*)
│   │   ├── geo.py
│   │   ├── ml_adapter.py
│   │   ├── classify_service.py
│   │   └── predict_service.py
│   └── api/                    ← The endpoints (what URLs the frontend can call)
│       ├── health.py
│       ├── frames.py
│       ├── classify.py
│       ├── predict.py
│       ├── replay.py
│       └── metrics.py
│
├── alembic/                    ← Database migration scripts (how tables get created)
│   ├── env.py
│   └── versions/
│       └── 0001_initial_schema.py
│
├── scripts/                    ← One-off utility scripts (not part of the running API)
│   ├── seed_db.py
│   └── precompute_replay.py
│
├── tests/                      ← Automated checks that the code works
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_frames.py
│   ├── test_classify.py
│   ├── test_predict.py
│   ├── test_replay.py
│   ├── test_metrics.py
│   ├── test_geo.py
│   ├── test_ml_adapter.py
│   └── test_schemas.py
│
├── Dockerfile                  ← Recipe for packaging the app into a container
├── docker-compose.yml          ← How to run the app + database together (dev)
├── docker-compose.prod.yml     ← Same but for production (demo day)
├── pyproject.toml              ← List of all Python packages this project needs
├── alembic.ini                 ← Config file for the migration tool
├── .env                        ← Your secret passwords/settings (never commit this)
└── .env.example                ← Template showing what goes in .env
```

---

## Layer by Layer — How a Request Travels

When the frontend calls `POST /api/ps70/classify`, here is exactly what happens step by step:

```
Frontend sends HTTP request
        ↓
main.py receives it, routes it to api/classify.py
        ↓
api/classify.py validates the request using schemas/classify.py
        ↓
api/classify.py calls services/classify_service.py
        ↓
classify_service.py loads the satellite image file from disk
        ↓
classify_service.py calls services/ml_adapter.py
        ↓
ml_adapter.py either calls the real ML model OR returns a fake result (stub)
        ↓
classify_service.py returns the result back to api/classify.py
        ↓
api/classify.py saves the result to the database (models/classification.py)
        ↓
api/classify.py formats the response using schemas/classify.py
        ↓
Frontend receives the JSON response
```

Every endpoint follows this same pattern. The layers are:
`api/ → services/ → models/ → database`

---

## Every File, Explained

---

### `app/main.py` — The Front Door

**What it does in plain English:**
This is the very first file that runs when you start the backend. It does three things:
1. Creates the FastAPI application object (the thing that listens for incoming requests)
2. Sets up CORS — this is a browser security rule that says "yes, I allow requests from the frontend website"
3. Registers all the URL routes (tells the app: if someone asks for `/health`, send them to `health.py`)

**CORS explained simply:** Imagine your frontend is running at `localhost:3000` and the backend at `localhost:8000`. By default, browsers block cross-origin requests as a security measure. CORS is you telling the browser "it's fine, I allow it." In dev we allow everything (`*`). In prod you'd restrict it to your actual domain.

**Lifespan explained simply:** There's a `lifespan` function that runs once when the server starts (startup) and once when it shuts down. On shutdown it closes the database connection pool cleanly — like turning off the stove before leaving the kitchen.

**Who depends on this:** Everything. It's the entry point.

---

### `app/core/config.py` — The Settings File

**What it does in plain English:**
Reads your `.env` file and turns it into a Python object you can use anywhere in the code.

Instead of hardcoding your database password in 20 different files, you put it in `.env` once and every file that needs it imports `get_settings()` and reads `settings.database_url`.

The `@lru_cache` decorator means the settings are only read from disk once and then cached in memory. Calling `get_settings()` 100 times doesn't read the file 100 times.

**Settings it manages:**
- `DATABASE_URL` — how to connect to PostgreSQL (async, used by the API)
- `DATABASE_SYNC_URL` — how to connect to PostgreSQL (sync, used by migration scripts)
- `DEBUG` — when `true`, the DB prints every SQL query it runs (useful for development)
- `CORS_ORIGINS` — which frontend URLs are allowed to talk to this backend
- `DATA_ROOT` — where satellite image files live on disk inside the container
- `ML_FORCE_STUB` — when `true`, always use fake ML results (useful when ML team hasn't delivered yet)

**Who depends on this:** `db/session.py`, `services/ml_adapter.py`, `main.py`

---

### `app/db/session.py` — The Database Connection Manager

**What it does in plain English:**
Manages the connection to PostgreSQL. Think of it as a phone operator that handles calls to the database — you don't call the database directly, you go through this operator.

It uses **async** connections, meaning the server can handle multiple requests at the same time without one request blocking another while it waits for the database to respond. Like a waiter who takes table 1's order, goes to the kitchen, then takes table 2's order without standing around waiting for table 1's food to be ready.

**Connection pool explained simply:** Instead of opening and closing a database connection for every single request (which is slow), it keeps a pool of open connections ready to use — like a bunch of pre-heated ovens so you don't wait for the oven to warm up every time.

**`get_db()` explained simply:** This is a FastAPI "dependency". Every endpoint that needs the database has `db: AsyncSession = Depends(get_db)` in its function signature. FastAPI automatically calls `get_db()`, gives the session to the endpoint, and then — after the endpoint finishes — commits the transaction (saves the changes) or rolls it back if something went wrong.

**Who depends on this:** Every file in `app/api/`

---

### `app/db/geo_types.py` — The Map Coordinate Column Type

**What it does in plain English:**
This solves a specific compatibility problem. PostgreSQL with PostGIS has a special column type called `Geometry` for storing map coordinates (points, polygons, etc.). But when running tests, we use a lightweight database called SQLite which doesn't understand `Geometry` at all.

This file creates a "smart" column type (`_PortableGeometry`) that:
- On PostgreSQL → uses the real PostGIS `Geometry` type (full spatial power)
- On SQLite → stores the same data as plain text (just enough for tests to run)

**Why this matters:** Without this, tests would crash because SQLite would try to create a `geometry` column and fail. With this, tests run fine and production still uses real PostGIS geometry.

**`PointGeometry` and `PolygonGeometry`:** These are pre-built instances that model files import. `PointGeometry` is used for cyclone centre positions. `PolygonGeometry` is used for the uncertainty ellipse around a forecast.

**Who depends on this:** `models/classification.py`, `models/prediction.py`

---

## The Models — The Shape of the Database

The `app/models/` folder defines the **five tables** in the database. Think of each model as a blueprint for one spreadsheet tab — it defines the column names and what type of data each column holds.

---

### `app/models/base.py` — The Foundation

**What it does in plain English:**
One line. Creates the base class that all other models inherit from. SQLAlchemy needs this to know which classes represent database tables. Every model file has `class SomeName(Base)` because of this.

---

### `app/models/event.py` — The `events` Table

**What it stores:** One row per cyclone event. This is the parent record that everything else connects to.

| Column | What it holds | Example |
|---|---|---|
| `event_id` | Unique text ID (primary key) | `"biparjoy_2023"` |
| `name` | Storm name | `"Biparjoy"` |
| `year` | Year it happened | `2023` |
| `basin` | Ocean basin | `"NI"` (North Indian) |
| `start_time` | When it began (UTC) | `2023-06-06T00:00:00Z` |
| `end_time` | When it ended (UTC) | `2023-06-16T00:00:00Z` |
| `notes` | Any extra info | `"Primary demo event"` |

**Relationships:** An event has many frames, many classifications, many predictions, and many metric rows. If you delete an event, all its child records are automatically deleted too (cascade).

---

### `app/models/satellite_frame.py` — The `satellite_frames` Table

**What it stores:** Metadata about each satellite image file. Not the image itself — just information about it (where it is, what time it was taken, what channels it has).

| Column | What it holds | Example |
|---|---|---|
| `frame_id` | Unique text ID | `"frame_001"` |
| `event_id` | Which event this belongs to | `"biparjoy_2023"` |
| `timestamp` | When the image was taken (UTC) | `2023-06-14T12:00:00Z` |
| `channels` | JSON: which bands are available | `{"ir": "path/ir.tif", "water_vapor": "path/wv.tif"}` |
| `file_paths` | JSON: actual file paths on disk | `{"ir": "/data/biparjoy_...tif"}` |
| `crs` | Coordinate reference system | `"EPSG:4326"` (standard lat/lon) |
| `bbox` | Geographic bounding box | `[60.0, 5.0, 80.0, 25.0]` (min_lon, min_lat, max_lon, max_lat) |
| `resolution` | Image size in pixels | `{"width": 512, "height": 512}` |
| `source` | Which satellite | `"INSAT-3D"` |
| `local_path` | Single file path (for image serving) | `"/data/demo/frame_001.tif"` |

**Why JSON columns?** Channels and file paths are dictionaries — the number of channels varies per frame (some have visible, some don't). JSON columns let you store flexible structures in a single column.

---

### `app/models/classification.py` — The `classifications` Table

**What it stores:** Every time the ML model looks at a satellite frame and identifies the cyclone's structure, that result is saved here as one row.

| Column | What it holds | Example |
|---|---|---|
| `classification_id` | Auto-generated unique ID (UUID) | `b1c2d3e4-...` |
| `event_id` | Which event | `"biparjoy_2023"` |
| `frame_id` | Which frame was analyzed | `"frame_001"` |
| `timestamp` | Time of the frame | `2023-06-14T12:00:00Z` |
| `lat` | Cyclone centre latitude | `15.20` |
| `lon` | Cyclone centre longitude | `68.40` |
| `pattern` | What structure the ML saw | `"banding"` |
| `confidence` | How sure the ML was (0–1) | `0.72` |
| `model_name` | Which model version was used | `"ps70-classifier-stub"` |
| `model_version` | Version string | `"0.1.0"` |
| `geometry` | PostGIS Point (for map queries) | `POINT(68.40 15.20)` |
| `created_at` | When this row was inserted | auto-set by DB |

**What is a UUID?** A universally unique ID — a long random string like `b1c2d3e4-f5a6-7890-abcd-ef1234567890`. Used instead of 1, 2, 3 because multiple servers can generate IDs without colliding.

**What is the `geometry` column?** It stores the same lat/lon as a PostGIS Point — a special format the database understands geographically. This lets you do spatial queries like "find all classifications within 200km of this location". The plain `lat`/`lon` float columns are also stored for convenience.

---

### `app/models/prediction.py` — The `predictions` Table

**What it stores:** Every forecast the ML temporal model makes. One row per forecast horizon (so one "predict" call writes two rows — one for T+12 and one for T+24).

| Column | What it holds | Example |
|---|---|---|
| `prediction_id` | Auto UUID | `a1b2c3...` |
| `event_id` | Which event | `"biparjoy_2023"` |
| `base_time` | The time we ran the prediction from | `2023-06-14T00:00:00Z` |
| `valid_time` | The time we're predicting (base + horizon) | `2023-06-14T12:00:00Z` |
| `pred_lat` | Predicted centre latitude | `16.10` |
| `pred_lon` | Predicted centre longitude | `67.80` |
| `pattern_label` | Predicted pattern | `"eye"` |
| `pattern_confidence` | How confident (0–1) | `0.64` |
| `model_name` | Which model | `"ps70-temporal-stub"` |
| `model_version` | Version | `"0.1.0"` |
| `uncertainty_status` | `"provisional"` or `"calibrated"` | `"provisional"` |
| `uncertainty_geom` | PostGIS Polygon (the uncertainty ellipse) | polygon WKT |
| `created_at` | When inserted | auto-set |

**What is the uncertainty polygon?** The ML model isn't 100% certain where the cyclone will be. The polygon is an ellipse drawn around the predicted centre — the bigger the ellipse, the less certain the model is. Until the ML team calibrates their confidence scores (Day 6), this is labeled `"provisional"` and should never be shown to a judge as a calibrated probability.

---

### `app/models/metric_row.py` — The `metrics` Table

**What it stores:** After a prediction is made and reality plays out, we compare the prediction to the actual observed position. Each comparison is one row here. This is the table that powers the `/api/metrics` endpoint.

| Column | What it holds | Example |
|---|---|---|
| `metric_id` | Auto UUID | `...` |
| `event_id` | Which event | `"biparjoy_2023"` |
| `base_time` | When the prediction was made | `2023-06-14T00:00:00Z` |
| `horizon_hours` | How far ahead we predicted | `12` or `24` |
| `pred_lat` | What we predicted | `16.10` |
| `pred_lon` | What we predicted | `67.80` |
| `actual_lat` | What actually happened (from IBTrACS) | `16.20` |
| `actual_lon` | What actually happened | `67.70` |
| `error_km` | Distance between prediction and reality, in km | `15.8` |
| `ground_truth_label` | The correct pattern (from research team labels) | `"banding"` |
| `predicted_label` | What the ML model said | `"banding"` |
| `created_at` | When inserted | auto-set |

**What is MAE?** Mean Absolute Error. Average of all `error_km` values. This is the headline number that judges will ask about. "Our model's T+12 MAE is 54 km."

---

## The Schemas — The Shape of Every Request and Response

The `app/schemas/` folder defines exactly what JSON the frontend should send and exactly what JSON it will get back. Think of schemas as contracts — both sides agree on the exact format.

If the frontend sends a request that doesn't match the schema, FastAPI automatically rejects it with a clear error message. No bad data ever reaches the actual logic.

---

### `app/schemas/common.py` — Shared Building Blocks

These are reusable pieces used by multiple endpoints.

**`CenterPoint`** — holds a latitude and longitude. Has built-in validation: lat must be between -90 and 90, lon between -180 and 180. If you send `lat: 200`, it's rejected immediately.

**`PatternResult`** — holds a pattern label (e.g. `"banding"`) and a confidence score (0 to 1). Confidence is validated — can't be 1.5 or -0.1.

**`ModelMeta`** — just the model name and version. Attached to every response so it's always traceable which model produced which result.

**`GeoJSONPolygon`** — the uncertainty ellipse in GeoJSON format. Coordinates are `[longitude, latitude]` — longitude first. This is the GeoJSON standard and matters because map libraries expect this order.

**`UncertaintyBlock`** — wraps the polygon with a `status` field (`"provisional"` or `"calibrated"`) and an optional `coverage_target`. `coverage_target` is `null` until the ML team has actually measured it.

**`SourceRef`** — just the `frame_id` that was analyzed. Provides traceability: every classification response says exactly which frame it came from.

---

### `app/schemas/classify.py` — Classification Request and Response

**`ClassifyRequest`** — what the frontend sends:
```json
{ "event_id": "biparjoy_2023", "timestamp": "2023-06-14T12:00:00Z", "frame_id": "frame_001" }
```
The validator enforces that `timestamp` must include timezone info. A timestamp without timezone (`"2023-06-14T12:00:00"` — no `Z`) is rejected. This prevents silent timezone bugs.

**`ClassifyResponse`** — what the frontend receives back: event_id, timestamp, center, pattern, source frame, model info.

**`ClassificationListResponse`** — what the frontend gets when asking for all classifications of an event: a list of records sorted by time, with a count.

---

### `app/schemas/predict.py` — Prediction Request and Response

**`PredictRequest`** — the frontend sends the event ID and the time from which to predict. Same UTC enforcement.

**`PredictionStep`** — one forecast horizon. Has valid_time, center, and pattern.

**`PredictResponse`** — list of prediction steps (T+12 and T+24), plus the uncertainty block, plus model info.

---

### `app/schemas/replay.py` — Historical Replay Response

These schemas describe the full replay timeline that the frontend uses for its slider.

**`ReplayStep`** — one point in time during the replay. Contains:
- `time` — the analysis time
- `observation_frame` — which satellite image was visible at this time
- `prediction` — a dictionary: `"t12"` → what we predicted for T+12, `"t24"` → what we predicted for T+24
- `actual` — a dictionary: `"t12"` → where the cyclone actually was 12 hours later
- `errors` — `t12_km` and `t24_km` — the distance between prediction and reality in km

**`ReplayResponse`** — list of all steps sorted by time, with a count.

---

### `app/schemas/metrics.py` — Metrics Response

Describes the evaluation metrics returned by `/api/metrics`. Contains:
- `dataset` — how many events, how many forecasts
- `track` — MAE at T+12 and T+24 in km
- `classification` — accuracy (0–1) and how many samples were evaluated
- `uncertainty` — coverage (what fraction of actual positions fell inside the uncertainty polygon)
- `baseline` — comparison against a simple baseline model (filled in later)
- `note` — set to `"no data"` if the metrics table is empty

---

### `app/schemas/frames.py` — Frame Metadata Response

Describes what the frontend gets when it asks for a satellite frame's metadata: frame ID, event, timestamp, available channels, coordinate system, bounding box, resolution, source.

---

## The Services — Where the Real Logic Lives

The `app/services/` folder is the brain. API files just receive requests and send responses. Service files do the actual work.

---

### `app/services/geo.py` — Distance Calculator

**What it does in plain English:**
Contains one important function: `haversine_km(lat1, lon1, lat2, lon2)`.

**Why Haversine?** The Earth is a sphere. If you take the straight-line degree difference between two lat/lon points and call it kilometres, you get the wrong answer. A 1-degree difference in latitude is about 111 km, but a 1-degree difference in longitude depends on where you are (at the equator it's ~111 km, at the poles it's 0 km).

The Haversine formula correctly computes the great-circle distance — the shortest path along the surface of the sphere. This is what we use to compute "how far off was the prediction" in the metrics and replay endpoints.

Also contains `mean_absolute_error_km()` — takes a list of prediction/actual pairs and returns the average error in km.

**Used by:** `api/replay.py`, `api/metrics.py`, `scripts/precompute_replay.py`, `scripts/seed_db.py`

---

### `app/services/ml_adapter.py` — The Bridge to the ML Model

**What it does in plain English:**
This is the most important integration point in the whole backend. It is the only file that talks to the ML team's code.

It works like a smart switch:
- On startup, it checks: is the `ml.inference` Python module importable?
- If yes → **REAL MODE**: all calls go to the actual ML model
- If no (or if `ML_FORCE_STUB=true`) → **STUB MODE**: returns hardcoded demo data

**Why a stub?** The ML model won't exist on Day 1. The frontend needs to build their UI, the app dev needs to build their screens, and we need to test the API — all before the ML model is ready. The stub lets everything else continue without blocking.

**The stub data** (hardcoded in the file):
```
classify stub → center: lat 15.20, lon 68.40, pattern: "banding", confidence: 0.72
predict stub  → T+12: lat 16.10, lon 67.80, pattern: "eye"
               T+24: lat 17.20, lon 67.10, pattern: "eye"
```
These are clearly labeled with `"name": "ps70-classifier-stub"` so nobody mistakes them for real results.

**Two public functions:**
- `run_classify(frame_array)` — takes a numpy array `[C, H, W]`, returns center + pattern + model info
- `run_predict(sequence_array)` — takes a numpy array `[T, C, H, W]`, returns list of predictions

**Used by:** `services/classify_service.py`, `services/predict_service.py`

**What ML team needs to provide:** A file at `ml/inference.py` (or `ml/src/inference.py` importable as `ml.inference`) with two functions:
```python
def predict_frame(frame: np.ndarray) -> dict: ...
def predict_sequence(sequence: np.ndarray) -> dict: ...
```
The exact return format is in the integration checklist at the bottom of this document.

---

### `app/services/classify_service.py` — Classification Logic

**What it does in plain English:**
Given a frame ID and its metadata, this service:
1. Looks at `file_paths` (e.g. `"/data/biparjoy_...ir.tif"`)
2. Tries to open each GeoTIFF file using `rasterio` (a library for reading satellite image files)
3. Reads the pixel data as a numpy array `[H, W]` for each channel (IR, water vapor, visible)
4. Stacks them into `[C, H, W]` — channels × height × width
5. Passes the array to `ml_adapter.run_classify()`
6. Returns the result

**If files don't exist on disk:** Falls back to a zero-filled mock array. The ML model still runs (or the stub returns). This means the classification API works even before satellite files are loaded — you just get stub results.

**Shape convention:** Always `[C, H, W]`. Channel index first. Never `[H, W, C]` (which is what cameras typically produce). The ML team must expect this shape.

---

### `app/services/predict_service.py` — Prediction Logic

**What it does in plain English:**
Given a list of frames (the observation sequence leading up to a base time), this service:
1. Loads each frame from disk as a numpy array `[C, H, W]`
2. Stacks all frames into `[T, C, H, W]` — time × channels × height × width
3. Passes the sequence to `ml_adapter.run_predict()`
4. For each prediction horizon (T+12, T+24), builds an uncertainty ellipse polygon using Shapely
5. Converts the polygon to WKT (Well-Known Text) format for storing in PostGIS
6. Returns the full prediction result

**The uncertainty ellipse explained simply:**
- Take the predicted centre point
- Draw a circle around it
- Stretch the circle horizontally by `sigma_lon` and vertically by `sigma_lat`
- The result is an egg shape (ellipse) — the model is saying "the real position is probably somewhere inside this egg"
- The bigger the sigma values, the bigger the egg, the less certain the model is

Until Day 6 calibration, `sigma_lat = 0.5` and `sigma_lon = 0.5` are used as provisional defaults. After calibration, ML team provides real sigma values from their confidence calibration.

---

## The API Layer — The URLs the Frontend Calls

The `app/api/` folder defines the actual HTTP endpoints. Each file is a group of related URLs.

---

### `app/api/health.py` — `GET /health`

**What it does:** Returns `{"status": "ok", "db": "ok"}`.

This is the simplest possible endpoint. The frontend and the demo setup can call this first to verify the whole system is running. If `db` is `"degraded"`, the database isn't responding.

**What it checks:** Runs `SELECT 1` against PostgreSQL. If that works, db is ok.

---

### `app/api/frames.py` — `GET /api/ps70/frames/{frame_id}`

**What it does:** Looks up a satellite frame by its ID in the `satellite_frames` table and returns its metadata.

With `?format=image` added to the URL, instead of returning JSON metadata, it streams the actual satellite image file back to the caller. The frontend can then display it on the Leaflet map.

**Returns 404 if:** The frame ID doesn't exist in the DB, or if `format=image` is requested but no file exists on disk.

---

### `app/api/classify.py` — `POST /api/ps70/classify` and `GET /api/ps70/classifications/{event_id}`

**POST /api/ps70/classify — What it does step by step:**
1. Checks that the `event_id` exists in the `events` table (returns 422 if not)
2. Checks that the `frame_id` exists in `satellite_frames` (returns 422 if not)
3. Calls `classify_service.run_classification()` to get the ML result
4. Creates a new `Classification` row and saves it to the database
5. Returns the classification response JSON

**GET /api/ps70/classifications/{event_id} — What it does:**
Returns all classification results for an event, sorted oldest-to-newest by timestamp. The frontend uses this to plot the history of where the cyclone centre was detected over time.

---

### `app/api/predict.py` — `POST /api/ps70/predict`

**What it does step by step:**
1. Validates the event exists
2. Loads all satellite frames for this event that are at or before the requested `start_timestamp` (sorted by time)
3. Calls `predict_service.run_prediction()` with the full sequence
4. Writes two `Prediction` rows to the database (one for T+12, one for T+24)
5. Returns the prediction response with the uncertainty polygon

**Why does it load all frames up to start_timestamp?** Because the temporal model needs a sequence of observations to predict the future — like how a doctor needs to see the trend of your temperature over time, not just the current reading.

---

### `app/api/replay.py` — `GET /api/replay/{event_id}`

**What it does in plain English:**
Returns the complete "rewind the clock" data for a cyclone event. The frontend uses this to power the timeline slider.

This endpoint **never calls the ML model**. It only reads from the database. All the classifications and predictions must already be stored there (via `precompute_replay.py`).

**For each analysis time it returns:**
- Which satellite frame was available at that moment
- What the model predicted at T+12 and T+24 from that moment
- What actually happened (from IBTrACS best-track data)
- The error in km between prediction and reality

All steps are sorted by time, oldest first.

**Why precompute?** The demo has no internet. If replay called the ML model live, a slow model or missing file would crash the demo. By precomputing everything and storing it in the database, replay is just reading rows — it can never fail due to ML issues.

---

### `app/api/metrics.py` — `GET /api/metrics`

**What it does:**
Aggregates everything in the `metrics` table into summary numbers for the judge's Q&A.

- `track.mae_km_t12` — average error at T+12 across all forecasts in km
- `track.mae_km_t24` — average error at T+24
- `classification.accuracy` — percentage of pattern labels that matched ground truth
- `uncertainty.coverage` — percentage of actual cyclone positions that fell inside the predicted uncertainty polygon (requires PostGIS; returns null in tests)
- `baseline` — comparison against a simple model (filled in when baseline is implemented)

Accepts optional `?event_id=biparjoy_2023` to filter to one event.
Returns `{"note": "no data"}` if the metrics table is empty, instead of crashing.

---

## The Migration System — How Tables Are Created

---

### `alembic/` — Database Migration Tool

**What migrations are in plain English:**
Imagine you have a database with tables. A month later you want to add a new column. How do you safely change the table without losing data? Migrations.

A migration is a Python script that describes exactly what changes to make to the database schema. Alembic runs these scripts in order and keeps track of which ones have been applied.

**`alembic/env.py`** — tells Alembic where the database is (reads `DATABASE_SYNC_URL` from environment) and which Python models to look at when detecting changes.

**`alembic/versions/0001_initial_schema.py`** — the first (and currently only) migration. It:
1. Runs `CREATE EXTENSION IF NOT EXISTS postgis;` — enables the PostGIS extension in PostgreSQL
2. Creates all 5 tables with all their columns and indexes
3. Has an `upgrade()` function (apply) and a `downgrade()` function (undo)

**How to run it:** `alembic upgrade head` — applies all pending migrations. Run this once after starting the database for the first time.

---

## The Scripts — One-Off Tools

---

### `scripts/seed_db.py` — Demo Data Loader

**What it does in plain English:**
Inserts fake-but-realistic demo data into the database so every API endpoint returns something useful immediately — without needing real satellite files or a trained model.

**What it inserts:**
- 1 cyclone event: Biparjoy 2023
- 3 satellite frame metadata records (pointing to file paths that may not exist yet)
- 3 classification results (where the model "detected" the cyclone)
- 2 predictions (T+12 and T+24 from a demo base time)
- 5 metric rows (pre-computed errors for the metrics endpoint)

**How to use it:**
```bash
docker compose exec api python -m scripts.seed_db
# Re-seed from scratch (wipes existing seed data first):
docker compose exec api python -m scripts.seed_db --reset
```

**It's idempotent:** If you run it twice, the second run does nothing (it checks if `biparjoy_2023` already exists before inserting).

---

### `scripts/precompute_replay.py` — Offline Demo Preparator

**What it does in plain English:**
This is the script you run before the demo to make sure everything works offline.

It goes through every satellite frame of an event, runs classification and prediction on each one (using whatever model is available — stub or real), loads the IBTrACS best-track actual positions from a CSV file, computes the errors, and stores everything in the database.

After this runs, `GET /api/replay/biparjoy_2023` will return a fully populated replay with real predictions and errors — no internet needed, no ML calls at demo time.

**How to use it:**
```bash
docker compose exec api python -m scripts.precompute_replay --event_id biparjoy_2023
```

**Depends on:** The `data/ground_truth/biparjoy_2023_best_track.csv` file existing (provided by Research team). If the file doesn't exist, it still runs but actual positions will be empty.

---

## The Tests — Proof That Everything Works

The `tests/` folder has 93 automated tests. Run them with `pytest -v`. They use an in-memory SQLite database so you don't need Docker to run them.

---

### `tests/conftest.py` — Test Setup

**What it does:** Creates the test environment before any test runs.
- Sets `DATABASE_URL` to SQLite (so tests don't need PostgreSQL)
- Creates all database tables fresh for every test
- Provides reusable helper objects: `client` (a fake browser that calls the API), `db_session` (a DB session), `seeded_event` and `seeded_frame` (pre-inserted rows for tests that need them)

---

### `tests/test_schemas.py` — Schema Validation Tests

Verifies that the Pydantic schemas correctly reject bad data:
- `lat=200` → rejected
- `confidence=1.5` → rejected
- timestamp without timezone → rejected
- missing required fields → rejected

---

### `tests/test_health.py` — Health Endpoint Tests

Verifies `/health` returns 200, has the right keys, and status is a string.

---

### `tests/test_frames.py` — Frames Endpoint Tests

Verifies frame metadata is returned correctly, 404 on unknown frames, 404 for image format when no local path.

---

### `tests/test_geo.py` — Distance Calculator Tests

Verifies the Haversine formula with known real-world distances:
- Delhi to Mumbai ≈ 1150 km
- Two points 1 degree apart on the equator ≈ 111 km
- Same point ≈ 0 km

These test cases are important — if the distance formula is wrong, every error metric in the system is wrong.

---

### `tests/test_ml_adapter.py` — ML Adapter Tests

Verifies stub mode works correctly:
- Returns the right keys
- Coordinates are in valid range
- Confidence is between 0 and 1
- Model name contains "stub" (so it's never mistaken for a real result)
- T+12 and T+24 horizons are both present
- Accepts numpy arrays without crashing

---

### `tests/test_classify.py` — Classification Endpoint Tests

Verifies the full classify flow:
- Happy path returns 200 with correct schema
- Unknown event_id returns 422
- Unknown frame_id returns 422
- Naive timestamp (no timezone) returns 422
- Multiple classifications are returned sorted by timestamp

---

### `tests/test_predict.py` — Prediction Endpoint Tests

Verifies:
- Returns 200 with 2 prediction steps
- Valid times are in the future relative to base_time
- Uncertainty polygon is present and correctly formatted
- Status is "provisional"
- `coverage_target` is null (not set until calibration)

---

### `tests/test_replay.py` — Replay Endpoint Tests

Verifies:
- Unknown event returns 404
- Empty event (no predictions yet) returns 200 with empty steps
- Steps are sorted by time ascending
- Errors are floats in km
- **The replay endpoint never calls the ML adapter** (verified with a monkeypatch)

---

### `tests/test_metrics.py` — Metrics Endpoint Tests

Verifies:
- Empty DB returns `{"note": "no data"}`
- T+12 MAE is correctly computed from seeded data
- T+24 MAE is correctly computed
- Classification accuracy is 1.0 when all labels match
- All required keys are present in the response

---

## The Docker Setup

---

### `Dockerfile` — How to Package the App

Has three build stages:

**`base`** — installs system dependencies (GDAL for rasterio, libpq for PostgreSQL, gcc for compiling Python packages). Installs `uv` (the fast Python package manager).

**`dev`** — extends base, installs all Python packages including dev/test packages, starts the server with `--reload` (auto-restarts when you save a file).

**`docker compose up`** uses the `dev` stage by default, mounts your source code as a volume (so changes are instant without rebuilding), and mounts `../ml` so the ML package is importable.

**`prod`** — extends base, installs only production packages, copies the source code into the image (no volume mounts), starts with 4 worker processes for performance.

---

### `docker-compose.yml` — Dev Environment

Defines two services:

**`db`** — runs `postgis/postgis:15-3.3` (PostgreSQL 15 with PostGIS 3.3 pre-installed). Stores data in a named volume `postgres_data` so it persists between restarts. Has a health check so the API waits for the database to be ready before starting.

**`api`** — builds the `dev` stage of the Dockerfile. Mounts three volumes:
- `.:/app` — your backend source code (hot reload)
- `../ml:/ml` — the ML package from the sibling folder
- `../data:/data` — satellite image data

Sets `PYTHONPATH=/ml:/app` so `import ml.inference` and `import app.xxx` both work inside the container.

---

### `docker-compose.prod.yml` — Production Environment

Same structure but:
- Database is NOT exposed on port 5432 to the host (security)
- API image is baked (no volume mounts — all source code is inside the image)
- Reads from `.env.prod` instead of `.env`
- No dev dependencies installed

---

### `pyproject.toml` — Python Package List

Lists every Python package the project needs with pinned exact versions. Managed by `uv`.

Key packages and why they're needed:

| Package | Why it's needed |
|---|---|
| `fastapi` | The web framework — handles HTTP requests |
| `uvicorn` | The server that runs FastAPI |
| `sqlalchemy` | ORM — Python objects ↔ database rows |
| `alembic` | Database migrations |
| `asyncpg` | Fast async PostgreSQL driver |
| `psycopg2-binary` | Sync PostgreSQL driver (for Alembic scripts) |
| `pydantic` | Schema validation (request/response shapes) |
| `pydantic-settings` | Reading settings from `.env` |
| `geoalchemy2` | PostGIS integration for SQLAlchemy |
| `shapely` | Building geometric shapes (uncertainty ellipse) |
| `numpy` | Arrays for satellite image data |
| `rasterio` | Reading GeoTIFF satellite image files |
| `httpx` | HTTP client (used in tests to call the API) |
| `aiosqlite` | SQLite async driver (tests only) |

---

## Integration Checklist — What Each Team Needs to Do

This section is the most important for making everything work in one iteration.

---

### ML Team (Aditya) — What the Backend Needs From You

**The one thing that matters most:**

Create a Python file at `ml/inference.py` (so it's importable as `ml.inference`). It must contain exactly these two functions:

```python
import numpy as np
from typing import Any

def predict_frame(frame: np.ndarray) -> dict[str, Any]:
    """
    Classify a single satellite frame.

    Input:
        frame: numpy array, shape [C, H, W], dtype float32, normalised
               C = number of channels (IR, water vapor, visible = up to 3)
               H, W = spatial dimensions (e.g. 256x256 or 512x512)

    Output:
        {
            "center": {"lat": float, "lon": float},
            "pattern": {"label": str, "confidence": float},
            "model": {"name": str, "version": str}
        }
    """
    ...


def predict_sequence(sequence: np.ndarray) -> dict[str, Any]:
    """
    Predict future positions from a sequence of frames.

    Input:
        sequence: numpy array, shape [T, C, H, W], dtype float32, normalised
                  T = number of time steps (however many frames are available)
                  C, H, W = same as above

    Output:
        {
            "predictions": [
                {
                    "horizon_hours": 12,
                    "center": {"lat": float, "lon": float},
                    "pattern": {"label": str, "confidence": float},
                    "sigma_lat": float,   # uncertainty in latitude (degrees)
                    "sigma_lon": float,   # uncertainty in longitude (degrees)
                },
                {
                    "horizon_hours": 24,
                    ...
                }
            ],
            "model": {"name": str, "version": str}
        }
    """
    ...
```

**Critical rules:**
- Input shape is `[C, H, W]` for single frame — **not** `[H, W, C]`, **not** `[1, C, H, W]`
- Input shape is `[T, C, H, W]` for sequence — **not** `[C, T, H, W]`
- All lat/lon values are floats (degrees)
- `confidence` is a float between 0 and 1
- `sigma_lat` and `sigma_lon` are in degrees (0.5 = ~55 km uncertainty)
- Pattern labels must be from: `eye`, `banding`, `curved_band`, `shear_affected`, `disorganized`
- `model.name` must NOT contain "stub" — the stub detection checks for this

**Once your model is ready:**
1. Make sure `ml/inference.py` is importable from inside Docker
2. Set `ML_FORCE_STUB=false` in `.env`
3. Restart the API: `docker compose restart api`
4. Check the logs: should print `[ML ADAPTER] Running in REAL MODE`
5. Run `pytest` — all tests must still pass

**For the calibrated uncertainty (Day 6):**
After calibration, provide real `sigma_lat` and `sigma_lon` values from your confidence calibration. Tell Satyam when this is done so the uncertainty status can be changed from `"provisional"` to `"calibrated"`.

---

### Data Team (Abhinav) — What the Backend Needs From You

**1. Satellite files — naming convention:**

Files must be placed at `data/normalized/` and named exactly:
```
biparjoy_2023-06-14T1200Z_ir_insat.tif
biparjoy_2023-06-14T1200Z_wv_insat.tif
biparjoy_2023-06-14T1200Z_visible_insat.tif
```
Pattern: `{event_id}_{timestamp}_{channel}_{source}.tif`

**2. Register frames in the database:**

After placing files, run:
```bash
docker compose exec api python -m scripts.seed_db --reset
```
Or write a script that inserts `SatelliteFrame` rows pointing to the actual file paths. The seed script shows exactly how to insert a frame row — copy that pattern.

**3. Best-track ground truth CSV:**

Place at `data/ground_truth/biparjoy_2023_best_track.csv` with exactly this format:
```csv
event_id,timestamp,lat,lon
biparjoy_2023,2023-06-06T00:00:00Z,8.5,65.2
biparjoy_2023,2023-06-06T06:00:00Z,8.8,65.5
...
```
The precompute script reads this file to fill in actual positions for the replay and metrics.

**4. Tell the backend when files are ready:**

When your normalized files are in place, Satyam runs `precompute_replay.py` to populate the replay database. This is the trigger for the replay and metrics endpoints to show real data.

---

### Research Team (Arshit) — What the Backend Needs From You

**Ground-truth pattern labels:**

If you have manually labeled pattern categories for specific frames, provide them as a CSV:
```csv
event_id,frame_id,timestamp,ground_truth_label
biparjoy_2023,frame_001,2023-06-14T12:00:00Z,banding
biparjoy_2023,frame_002,2023-06-14T18:00:00Z,eye
```

Satyam will update the `ground_truth_label` column in the `metrics` table from this CSV. Without this, the classification accuracy metric will be `null`.

**Pattern taxonomy labels used in the code:**
`eye`, `banding`, `curved_band`, `shear_affected`, `disorganized`

If your taxonomy uses different names, tell Satyam before classification runs so the enum can be agreed on. Do not change label names after data is in the database without a coordinated migration.

---

### Frontend Team (Kavya) — What to Call and How

**Base URL:** `http://localhost:8000` in dev. Replace with the server IP on demo day.

**The 6 endpoints you can call:**

| What you need | Call |
|---|---|
| Is the backend running? | `GET /health` |
| Get satellite frame info | `GET /api/ps70/frames/{frame_id}` |
| Stream actual satellite image | `GET /api/ps70/frames/{frame_id}?format=image` |
| Run classification on a frame | `POST /api/ps70/classify` |
| Get all classifications for an event | `GET /api/ps70/classifications/biparjoy_2023` |
| Run prediction from a base time | `POST /api/ps70/predict` |
| Get full historical replay | `GET /api/replay/biparjoy_2023` |
| Get evaluation metrics | `GET /api/metrics?event_id=biparjoy_2023` |

**For the interactive docs with real request/response examples:** `http://localhost:8000/docs`

**The Leaflet map — serving satellite tiles:**
Currently the frames endpoint streams a raw GeoTIFF. If Leaflet needs XYZ tiles instead of a raw file, tell Satyam and a tile-serving layer (e.g. using `rio-tiler`) can be added on top of the existing frames endpoint. Raise this early — don't raise it on Day 7.

**While the backend is being set up:**
Use the fixtures in `docs/api_contract.md` as mock data. The response shapes are exact — you can hardcode them in your frontend and swap for real calls when the API is running.

---

### App Dev Team (Aniket) — What to Call and How

The mobile app only needs three endpoints:

| What you need | Call |
|---|---|
| Current cyclone status + pattern | `GET /api/ps70/classifications/biparjoy_2023` → take the last item |
| Prediction (T+12, T+24) | `POST /api/ps70/predict` with current timestamp |
| Offline fallback | Bundle the seed data JSON responses as fixtures in the app |

**For the offline demo mode:**
Run the app once with internet → cache the API responses locally → in offline mode, serve the cached responses. Do not make live API calls during the demo if connectivity can't be guaranteed.

---

## The Full Request Flow — One More Time, Even Simpler

Imagine a judge asks: "Show me the classification of Biparjoy at 12:00 UTC on June 14."

1. **Frontend** calls `POST /api/ps70/classify` with `event_id=biparjoy_2023`, `timestamp=2023-06-14T12:00:00Z`, `frame_id=frame_001`

2. **`api/classify.py`** receives it. Checks: does `biparjoy_2023` exist in `events` table? Yes. Does `frame_001` exist in `satellite_frames`? Yes.

3. **`services/classify_service.py`** is called. Opens the file at `/data/normalized/biparjoy_2023-06-14T1200Z_ir_insat.tif` using rasterio. Reads pixel data. Stacks channels into a `[3, 512, 512]` array.

4. **`services/ml_adapter.py`** is called with the array. Checks: is `ml.inference` available? If yes → calls real model. If no → returns stub `{center: {lat:15.20, lon:68.40}, pattern: {label: "banding", confidence: 0.72}}`.

5. **`api/classify.py`** saves a new row to the `classifications` table: lat 15.20, lon 68.40, pattern "banding", confidence 0.72, geometry `POINT(68.40 15.20)`.

6. **Frontend** receives:
```json
{
  "event_id": "biparjoy_2023",
  "timestamp": "2023-06-14T12:00:00Z",
  "center": {"lat": 15.20, "lon": 68.40},
  "pattern": {"label": "banding", "confidence": 0.72},
  "source": {"frame_id": "frame_001"},
  "model": {"name": "ps70-classifier-stub", "version": "0.1.0"}
}
```

7. **Leaflet map** puts a marker at 15.20°N, 68.40°E. The confidence card shows "72%". The judge sees the result with a clear "stub" label until the real model is wired in.

That's the whole system.

---

## What Can Go Wrong and How to Fix It

| Problem | Likely cause | Fix |
|---|---|---|
| `docker compose up` fails | Docker not running, or port 5432/8000 already in use | Check Docker Desktop is running. Check `netstat -a` for port conflicts. |
| `/health` returns `{"db": "degraded"}` | Database container not ready yet, or wrong credentials | Wait 10 seconds and retry. Check `.env` passwords match what's in `docker-compose.yml`. |
| `alembic upgrade head` fails | PostGIS extension not installed in PostgreSQL | Use the `postgis/postgis` Docker image, not plain `postgres`. Already set correctly in our compose file. |
| Classification returns stub data | ML package not importable | Check `ML_FORCE_STUB=false` in `.env`. Check `ml/inference.py` exists and is importable. |
| Replay returns empty steps | `precompute_replay.py` hasn't been run yet | Run it. Or run `seed_db.py` for demo data. |
| Tests fail with `IntegrityError` | Test DB not isolated | Tests use function-scoped SQLite DB. If you're running tests in parallel, stop. Run `pytest` sequentially. |
| `rasterio` error on satellite file | Wrong file path or file format | Check the file path in `satellite_frames.file_paths`. Check the file is a valid GeoTIFF. |
| Uncertainty polygon missing | `shapely` not installed | Run `uv pip install --python .venv shapely==2.0.5` in the backend directory. |

---

*This document was written alongside the code. If any behaviour changes, update this document in the same commit.*
