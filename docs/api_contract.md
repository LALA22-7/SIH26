# CycloneWatch API Contract

> **Scope:** PS70 sprint only. This contract covers the backend API served by `cyclonewatch_api` on port 8000.
>
> **Coordinate convention:** All GeoJSON uses `[longitude, latitude]` order. All timestamps are UTC ISO 8601.
>
> **Stub mode:** Until the ML model is handed off, all inference endpoints return stub responses clearly labeled `"name": "ps70-classifier-stub"`. Do not treat stub confidence values as scientifically meaningful.

---

## Base URL

```
http://localhost:8000          (dev)
http://<server-ip>:8000        (prod)
```

---

## 1. Health check

### `GET /health`

Returns API liveness and database connectivity status.

**Response `200 OK`**
```json
{
  "status": "ok",
  "db": "ok"
}
```

`db` is `"ok"` if the database responded to `SELECT 1`, or `"degraded"` if it did not.

**curl**
```bash
curl http://localhost:8000/health
```

---

## 2. Satellite frames

### `GET /api/ps70/frames/{frame_id}`

Return metadata for a satellite frame, or stream the raw image file.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `frame_id` | string | Frame identifier stored in `satellite_frames` table |

**Query parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `format` | string | `json` | `json` returns metadata; `image` streams the file |

**Response `200 OK` (format=json)**
```json
{
  "frame_id": "frame_001",
  "event_id": "biparjoy_2023",
  "timestamp": "2023-06-14T12:00:00Z",
  "channels": ["ir", "water_vapor"],
  "crs": "EPSG:4326",
  "bbox": [60.0, 5.0, 80.0, 25.0],
  "resolution": { "width": 512, "height": 512 },
  "source": "INSAT-3D",
  "local_path": null
}
```

**Error responses**

| Code | Condition |
|---|---|
| `404` | `frame_id` not found in DB |
| `404` | `format=image` but no file on disk |

**curl**
```bash
# Metadata
curl http://localhost:8000/api/ps70/frames/frame_001

# Stream image (if file exists on disk)
curl http://localhost:8000/api/ps70/frames/frame_001?format=image -o frame.tif
```

---

## 3. Classification

### `POST /api/ps70/classify`

Run classification inference on a satellite frame and persist the result.

**Request body**
```json
{
  "event_id": "biparjoy_2023",
  "timestamp": "2023-06-14T12:00:00Z",
  "frame_id": "frame_001"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `event_id` | string | yes | Must exist in `events` table |
| `timestamp` | ISO 8601 datetime | yes | Must include timezone (UTC) |
| `frame_id` | string | yes | Must exist in `satellite_frames` table |

**Response `200 OK`**
```json
{
  "event_id": "biparjoy_2023",
  "timestamp": "2023-06-14T12:00:00Z",
  "center": {
    "lat": 15.20,
    "lon": 68.40
  },
  "pattern": {
    "label": "banding",
    "confidence": 0.72
  },
  "source": {
    "frame_id": "frame_001"
  },
  "model": {
    "name": "ps70-classifier-stub",
    "version": "0.1.0"
  }
}
```

**Pattern labels** (from taxonomy): `eye`, `banding`, `curved_band`, `shear_affected`, `disorganized`

**Error responses**

| Code | Condition |
|---|---|
| `422` | `event_id` not found |
| `422` | `frame_id` not found |
| `422` | `timestamp` missing timezone |

**curl**
```bash
curl -X POST http://localhost:8000/api/ps70/classify \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "biparjoy_2023",
    "timestamp": "2023-06-14T12:00:00Z",
    "frame_id": "frame_001"
  }'
```

---

### `GET /api/ps70/classifications/{event_id}`

Return all stored classifications for an event, sorted by timestamp ascending.
Used by the frontend for the time-series view.

**Response `200 OK`**
```json
{
  "event_id": "biparjoy_2023",
  "count": 3,
  "classifications": [
    {
      "classification_id": "b1c2d3e4-...",
      "event_id": "biparjoy_2023",
      "frame_id": "frame_001",
      "timestamp": "2023-06-14T00:00:00Z",
      "center": { "lat": 14.80, "lon": 68.90 },
      "pattern": { "label": "curved_band", "confidence": 0.68 },
      "model": { "name": "ps70-classifier-stub", "version": "0.1.0" }
    }
  ]
}
```

**Error responses**

| Code | Condition |
|---|---|
| `404` | `event_id` not found |

**curl**
```bash
curl http://localhost:8000/api/ps70/classifications/biparjoy_2023
```

---

## 4. Temporal prediction

### `POST /api/ps70/predict`

Run temporal prediction (T+12 and T+24) from a base timestamp.
Persists predictions and provisional uncertainty polygon to DB.

**Request body**
```json
{
  "event_id": "biparjoy_2023",
  "start_timestamp": "2023-06-14T00:00:00Z"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `event_id` | string | yes | Must exist in `events` table |
| `start_timestamp` | ISO 8601 datetime | yes | Analysis time, UTC required |

**Response `200 OK`**
```json
{
  "event_id": "biparjoy_2023",
  "base_time": "2023-06-14T00:00:00Z",
  "predictions": [
    {
      "valid_time": "2023-06-14T12:00:00Z",
      "center": { "lat": 16.10, "lon": 67.80 },
      "pattern": { "label": "eye", "confidence": 0.64 }
    },
    {
      "valid_time": "2023-06-15T00:00:00Z",
      "center": { "lat": 17.20, "lon": 67.10 },
      "pattern": { "label": "eye", "confidence": 0.59 }
    }
  ],
  "uncertainty": {
    "status": "provisional",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[67.30, 16.30], [67.30, 17.10], [68.30, 17.10], [68.30, 16.30], [67.30, 16.30]]]
    },
    "coverage_target": null
  },
  "model": {
    "name": "ps70-temporal-stub",
    "version": "0.1.0"
  }
}
```

> `uncertainty.status` is always `"provisional"` until Day-6 calibration. `coverage_target` is `null` until the uncertainty region has been evaluated against held-out data.

**Error responses**

| Code | Condition |
|---|---|
| `422` | `event_id` not found |
| `422` | `start_timestamp` missing timezone |

**curl**
```bash
curl -X POST http://localhost:8000/api/ps70/predict \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "biparjoy_2023",
    "start_timestamp": "2023-06-14T00:00:00Z"
  }'
```

---

## 5. Historical replay

### `GET /api/replay/{event_id}`

Return the full historical replay sequence for a cyclone event.

**This endpoint never calls ML.** All data must be pre-populated via
`scripts/precompute_replay.py` before using this endpoint in a demo.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `event_id` | string | Cyclone event identifier |

**Response `200 OK`**
```json
{
  "event_id": "biparjoy_2023",
  "total_steps": 3,
  "steps": [
    {
      "time": "2023-06-13T00:00:00Z",
      "observation_frame": "frame_001",
      "prediction": {
        "t12": {
          "valid_time": "2023-06-13T12:00:00Z",
          "center": { "lat": 15.20, "lon": 68.40 },
          "pattern": { "label": "banding", "confidence": 0.72 }
        },
        "t24": {
          "valid_time": "2023-06-14T00:00:00Z",
          "center": { "lat": 16.10, "lon": 67.80 },
          "pattern": { "label": "eye", "confidence": 0.64 }
        }
      },
      "actual": {
        "t12": {
          "valid_time": "2023-06-13T12:00:00Z",
          "center": { "lat": 15.30, "lon": 68.30 }
        },
        "t24": {
          "valid_time": "2023-06-14T00:00:00Z",
          "center": { "lat": 16.20, "lon": 67.70 }
        }
      },
      "errors": {
        "t12_km": 14.2,
        "t24_km": 15.8
      }
    }
  ]
}
```

Steps are sorted strictly by `time` ascending.
`actual` entries are populated only when best-track data exists in the metrics table.
`errors` values are Haversine (great-circle) distances in km — not raw degree differences.

**Error responses**

| Code | Condition |
|---|---|
| `404` | `event_id` not found |

**curl**
```bash
curl http://localhost:8000/api/replay/biparjoy_2023
```

---

## 6. Metrics

### `GET /api/metrics`

Return aggregated evaluation metrics. Optionally filtered by event.

**Query parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `event_id` | string | no | Filter to a single event; omit for aggregate |

**Response `200 OK` (with data)**
```json
{
  "event_id": "biparjoy_2023",
  "dataset": {
    "events": 1,
    "forecasts": 10
  },
  "track": {
    "mae_km_t12": 54.2,
    "mae_km_t24": 91.8
  },
  "classification": {
    "accuracy": 0.81,
    "sample_count": 42
  },
  "uncertainty": {
    "coverage": 0.86,
    "forecasts_evaluated": 42
  },
  "baseline": {
    "mae_km_t12": null,
    "mae_km_t24": null
  },
  "note": null
}
```

**Response `200 OK` (no data yet)**
```json
{
  "event_id": "biparjoy_2023",
  "dataset": { "events": 0, "forecasts": 0 },
  "track": { "mae_km_t12": null, "mae_km_t24": null },
  "classification": { "accuracy": null, "sample_count": 0 },
  "uncertainty": { "coverage": null, "forecasts_evaluated": 0 },
  "baseline": { "mae_km_t12": null, "mae_km_t24": null },
  "note": "no data"
}
```

> All MAE values are in **kilometres** computed via the Haversine formula. Never present raw degree differences as km.
>
> `uncertainty.coverage` requires PostGIS spatial query (`ST_Contains`). It will be `null` when running against SQLite.
>
> `baseline` values are `null` until the persistence baseline model is implemented and evaluated.

**curl**
```bash
# All events
curl http://localhost:8000/api/metrics

# Single event
curl "http://localhost:8000/api/metrics?event_id=biparjoy_2023"
```

---

## Error response format

All error responses follow the FastAPI default format:

```json
{
  "detail": "Human-readable description of the error"
}
```

For validation errors (422), `detail` is a list of Pydantic validation error objects.

---

## Adding a new event

Before classification or prediction can be run, the event and its frames must be registered:

1. Insert an `Event` row (via `scripts/seed_db.py` or a future admin endpoint)
2. Insert `SatelliteFrame` rows with metadata and file paths
3. Call `POST /api/ps70/classify` per frame
4. Call `POST /api/ps70/predict` per analysis time
5. For offline demo: run `scripts/precompute_replay.py --event_id <id>`

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-27 | Initial contract — all endpoints defined, stub mode active |
