# PS70 CycloneWatch — Master Team Execution Manual

> **Internal SIH 2026 | PS70 only | 8-Day Sprint**
>
> **Purpose:** This is the team's master execution manual. The individual `PS70_Team_Task_Sheet_By_Person.md` tells each member **what** to do. This manual explains **how to execute it**, what the expected inputs/outputs are, what to hand off, how to test it, and how to recover when something breaks.

---

## 0. READ THIS FIRST

### 0.1 Current scope is PS70 only

**Active problem statement:**

> AI/ML-based system for identification, classification, and prediction of different tropical cyclone patterns using multi-source satellite data.

**Current product:** `CycloneWatch`

**Sprint:** 8 days

- **Days 1–4:** working proof of concept
- **Day 4:** mentor checkpoint
- **Days 5–8:** hardening, validation, polish, rehearsal
- **Day 8:** final demo

**PS59 is not part of this sprint.** Do not spend build time on Antarctic sea-ice, iceberg trajectory, or navigation routing.

### 0.2 What we are actually building

```text
MULTI-SOURCE SATELLITE DATA
        |
        v
DATA INGESTION + STANDARDIZATION
        |
        v
SPATIAL / CLASSIFICATION MODEL
        |
        +--> Cyclone centre
        +--> Structural pattern
        +--> Confidence
        |
        v
TEMPORAL MODEL
        |
        +--> Future centre T+12 / T+24
        +--> Future pattern state
        +--> Uncertainty
        |
        v
FASTAPI + POSTGIS
        |
        +--> classify
        +--> predict
        +--> replay
        +--> metrics
        |
        +--------------------------+
        |                          |
        v                          v
WEB DASHBOARD                  MOBILE APP
React + Leaflet                Status + Alerts
        |
        v
OBSERVE -> UNDERSTAND -> PREDICT -> UNCERTAINTY -> EVIDENCE
```

### 0.3 The positioning line

Memorize the idea, not just the sentence:

> **We are not replacing IMD. IMD uses complex NWP physics models. We are building a decision-support layer that automates the interpretation of raw satellite data to classify structural patterns and predict evolution, addressing MoES's acknowledged gaps in short-fuse event interpretation and uncertainty visualization.**

### 0.4 Non-negotiable principles

1. **Satellite-only input for the sprint.** Do not feed NWP outputs into the PS70 model.
2. **Real data beats fake sophistication.**
3. **A measured baseline beats an impressive-looking number.**
4. **No fabricated accuracy.**
5. **Every displayed prediction must have source imagery, timestamp, and model/confidence metadata.**
6. **Use stubs when another member would otherwise be blocked.**
7. **Historical replay is the credibility feature.**
8. **Freeze the models on Day 7.**
9. **Freeze API/UI/app features on Day 7.**
10. **Do not add new science on Day 8.**
11. **If blocked for more than ~30 minutes, tell Satyam and the relevant owner.**
12. **Do not silently change an API field, data shape, label, or coordinate convention.**

---

# 1. VERIFIED SCOPE AND TASK AUDIT

This section was checked against:

- `todo_LIST.pdf`
- `PS70_Team_Task_Sheet_By_Person.md`
- `PS70_Team_Brief_8Day_Sheet.md`
- `SIH2026_PS59_PS70_Master_Plan_v2.md`
- `SIH_2026_PS59_PS70_9_Day_Execution_Playbook(1).md`
- `SIH2026_PS59_PS70_Team_Playbook(2).md`
- `SIH_2026_PS59_PS70_Master_Research_Architecture(1).pdf`

### 1.1 Task verification

| Owner | Task from current 8-day sheet | Covered here? | Required handoff |
|---|---|---:|---|
| ML | PyTorch scaffold + dataloaders | Yes | Data contract + loader test |
| ML | Day-1 classification stub | Yes | Fixed JSON to Backend/Frontend |
| ML | CNN centre + pattern + confidence | Yes | Model artifact + inference function |
| ML | Temporal model T-12→T0 | Yes | Prediction function + schema |
| ML | Known limitations | Yes | One-paragraph note |
| ML | Classification improvement | Yes | Versioned experiment |
| ML | Confidence calibration | Yes | Calibrated confidence + uncertainty mapping |
| ML | Freeze models | Yes | Model manifest |
| Backend | FastAPI + PostgreSQL/PostGIS + Docker | Yes | Running API + DB |
| Backend | Satellite tile endpoint | Yes | Map-ready endpoint |
| Backend | `/api/ps70/classify` | Yes | Stable response contract |
| Backend | Store classification time-series | Yes | PostGIS rows |
| Backend | Forecast endpoint | Yes | Stable prediction contract |
| Backend | Uncertainty polygon | Yes | GeoJSON polygon |
| Backend | `/api/replay` | Yes | Offline historical replay |
| Backend | `/api/metrics` | Yes | Measured metrics |
| Backend | API freeze + stress test | Yes | Test report |
| App | Project skeleton | Yes | Running mobile shell |
| App | `/classify` integration | Yes | Classification screen |
| App | Prediction + alert display | Yes | Alert screen |
| App | Offline demo case | Yes | Bundled fixture |
| App | Device reliability | Yes | Demo-device checklist |
| App | Visual polish | Yes | Matched design tokens |
| Frontend | Design tokens | Yes | Token file |
| Frontend | React + Leaflet shell | Yes | Running map |
| Frontend | IR/Visible/WV layer toggles | Yes | Working layer controls |
| Frontend | Classification marker/card | Yes | Level-2 view |
| Frontend | Predicted track/timeline | Yes | Prediction view |
| Frontend | Historical replay | Yes | T-48h→T0 slider |
| Frontend | Level-3 evidence panel | Yes | Source-image click-through |
| Frontend | Day-6 visual polish | Yes | Final UI |
| Data | Satellite acquisition | Yes | Raw-data manifest |
| Data | NetCDF/GeoTIFF standardization | Yes | Normalized files |
| Data | Additional events | Yes | Expanded dataset |
| Data | Ground-truth imagery | Yes | Validation bundle |
| Data | MAE support | Yes | Evaluation table |
| Data | Confidence-calibration support | Yes | Calibration dataset |
| Data | Full backtest | Yes | Metrics file |
| Research | 2 historical events | Yes | Event manifest |
| Research | IBTrACS best tracks | Yes | Ground-truth CSV |
| Research | Pattern taxonomy | Yes | Label specification |
| Research | Ground-truth labels | Yes | Label table |
| Research | MoES/IMD gap analysis | Yes | Evidence notes |
| Research | Backtest support | Yes | Final metrics narrative |
| Research | Limitations + positioning | Yes | Slide-ready text |
| Research | Q&A sheet | Yes | Judge defense sheet |
| All | Daily status | Yes | One-line update |
| All | Day-4 checkpoint | Yes | Honest POC state |
| All | Day-8 rehearsal | Yes | Full-system rehearsal |

### 1.2 Two important clarifications

#### Clarification A: visible data

The current task sheet explicitly asks Data to acquire **IR + water vapour**, while the frontend contract includes **IR + Visible + Water Vapor** layer toggles.

Therefore:

- IR and water vapour are mandatory acquisition targets for the current task sheet.
- Visible is a required UI layer.
- If the selected satellite/event provides aligned visible data without delaying the sprint, include it.
- **Do not block the entire project waiting for a perfect visible-data pipeline.**
- Never show a "Visible" layer that silently displays another band.

#### Clarification B: uncertainty on Day 3 vs Day 6

Backend is asked to generate an uncertainty polygon on Day 3, while ML calibrates confidence on Day 6.

Therefore the intended sequence is:

```text
Day 3:
model confidence / provisional interval
        |
        v
backend geometry interface
        |
        v
uncertainty polygon works end-to-end

Day 6:
calibrated confidence
        |
        v
real uncertainty mapping
        |
        v
final uncertainty polygon
```

Do not pretend the Day-3 cone is scientifically calibrated if calibration has not happened yet.

---

# 2. TEAM CONTRACT

## 2.1 Roles

| Person | Role | Primary ownership |
|---|---|---|
| Satyam Srivastava | Backend + Team Lead | FastAPI, PostGIS, integration, API contract, coordination |
| Kavya Agarwal | Designer + Frontend | React, Leaflet, UI/UX, evidence/replay |
| Arshit Singh | Research | Taxonomy, events, IBTrACS, domain/Q&A |
| Aniket Tiwari | App Dev | Mobile status/alert app |
| Aditya Tyagi | ML | Classification + temporal prediction |
| Abhinav Pal | Data | Satellite acquisition + preprocessing + validation data |

## 2.2 Ownership rule

Ownership means:

> "You are responsible for making sure the output exists and is usable by the next person."

It does **not** mean:

> "You must do everything yourself."

If a dependency is broken, escalate early.

---

# 3. SHARED DATA CONTRACT

Before serious implementation, everyone should understand the same object.

## 3.1 Canonical satellite frame

Each frame should conceptually contain:

```json
{
  "event_id": "biparjoy_2023",
  "timestamp": "2023-06-14T12:00:00Z",
  "source": "SELECTED_PROVIDER",
  "channels": {
    "ir": "path/to/ir.tif",
    "water_vapor": "path/to/wv.tif",
    "visible": "path/to/visible.tif"
  },
  "crs": "EPSG:4326",
  "bbox": [min_lon, min_lat, max_lon, max_lat],
  "resolution": {
    "width": 512,
    "height": 512
  },
  "normalization": {
    "method": "dataset_channel_statistics"
  }
}
```

The exact source name depends on the dataset actually selected.

## 3.2 Canonical model input

Recommended logical shape:

```text
single frame:
[C, H, W]

sequence:
[T, C, H, W]
```

Where:

- `T` = number of time frames
- `C` = number of satellite channels
- `H, W` = standardized spatial dimensions

Do not silently switch to:

```text
[C, T, H, W]
```

without telling the ML/backend owners.

## 3.3 Coordinate convention

Use:

- latitude = north/south
- longitude = east/west
- longitude range: keep one project-wide convention
- timestamps: **UTC**
- GeoJSON coordinate order: **[longitude, latitude]**

This matters because map libraries and scientific arrays do not always use the same coordinate order.

---

# 4. REPOSITORY STRUCTURE

Use a simple monorepo unless the team has already committed to another structure.

```text
cyclonewatch/
│
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── data/
│   ├── raw/
│   ├── normalized/
│   ├── labels/
│   ├── ground_truth/
│   └── demo/
│
├── ml/
│   ├── notebooks/
│   ├── src/
│   │   ├── datasets/
│   │   ├── models/
│   │   ├── training/
│   │   ├── inference/
│   │   └── evaluation/
│   ├── checkpoints/
│   └── configs/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   ├── db/
│   │   └── schemas/
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── map/
│   │   ├── replay/
│   │   ├── evidence/
│   │   └── api/
│   └── public/
│
├── app/
│   └── ...
│
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── model_card.md
│   ├── limitations.md
│   └── metrics.md
│
└── scripts/
    ├── validate_data.py
    ├── build_demo.py
    └── run_backtest.py
```

---

# 5. DAY 1 — FOUNDATION

## Objective

At the end of Day 1:

```text
real historical event
        ↓
real satellite data
        ↓
normalized data
        ↓
map
        ↓
classification stub
        ↓
backend API
        ↓
frontend/app shells
```

Nothing has to be scientifically impressive yet.

It has to be **connected**.

---

## 5A. RESEARCH — DAY 1

### Task

1. Lock two historical cyclone events.
2. Pull IBTrACS best-track data.
3. Draft the pattern taxonomy.

### Step 1: choose events

Selection criteria:

- North Indian Ocean relevance
- good satellite coverage
- usable historical best-track data
- enough temporal frames for replay
- visually distinct storm structure
- preferably at least one well-known event such as Biparjoy

Do not select an event merely because its name is famous.

### Step 2: create event manifest

Create:

```text
data/labels/events.csv
```

Example:

```csv
event_id,name,year,basin,start_time,end_time,notes
event_001,Biparjoy,2023,NI,2023-06-06T00:00:00Z,2023-06-16T00:00:00Z,primary demo
event_002,<event>,<year>,NI,<start>,<end>,secondary demo
```

### Step 3: obtain IBTrACS

Use the official NOAA/NCEI IBTrACS source.

Required fields should include, at minimum:

```text
storm identifier
storm name
timestamp
latitude
longitude
basin
wind/intensity fields if used
```

For the North Indian Ocean, prefer the basin subset where practical.

### Step 4: normalize timestamps

Everything in the project is UTC.

Example:

```python
import pandas as pd

df["ISO_TIME"] = pd.to_datetime(
    df["ISO_TIME"],
    utc=True,
    errors="coerce"
)
```

### Step 5: produce a clean ground-truth file

```text
data/ground_truth/
    biparjoy_best_track.csv
    event_002_best_track.csv
```

Minimum schema:

```csv
event_id,timestamp,lat,lon
event_001,2023-06-06T00:00:00Z,....
```

### Step 6: draft pattern taxonomy

Start small.

Recommended initial labels:

```text
eye
banding
curved_band
shear_affected
disorganized
```

Do not invent ten classes because a neural network looks happier with a larger label list.

Each class must have:

1. name
2. visual definition
3. inclusion rule
4. exclusion rule
5. example frames
6. confidence/ambiguity note

Example:

```text
Class: shear_affected

Definition:
Cyclone circulation remains identifiable but convection is displaced
or asymmetric relative to the estimated centre.

Include:
- persistent asymmetric cloud structure
- displaced deep convection

Exclude:
- completely unorganized cloud field
```

### Day-1 Research deliverable

```text
events.csv
best-track CSVs
taxonomy.md
source_notes.md
```

### Done when

Another team member can answer:

> Which two storms are we using, where is their ground truth, and what exactly does each pattern label mean?

---

# 5B. DATA — DAY 1

## Task

Acquire raw satellite sequences and standardize them.

### Preferred acquisition order

1. Official Indian source where suitable, especially MOSDAC/INSAT.
2. Official/open international satellite archive if required.
3. Do not spend the entire day fighting an authentication system if an equivalent legitimate historical dataset is already available.

### MOSDAC workflow

The current MOSDAC Download API uses:

```text
MOSDAC account
    ↓
Download API client
    ↓
datasetId
    ↓
start/end time
    ↓
bounding box
    ↓
download
```

The current official manual requires Python 3, `requests`, MOSDAC credentials for downloading, and a dataset ID.

### Search before downloading

Do not download an entire satellite archive.

First determine:

- event dates
- geographic box
- satellite/product
- channel availability
- temporal cadence
- file size
- access requirements

### Data acquisition manifest

Every downloaded dataset gets a record:

```csv
file_id,event_id,source,satellite,product,channel,timestamp,crs,bbox,license_or_access_note,local_path
```

### File naming

Use deterministic names:

```text
<event>_<timestamp>_<channel>_<source>.tif
```

Example:

```text
biparjoy_2023-06-14T1200Z_ir_insat.tif
```

Avoid:

```text
final_final2_new.tif
```

The satellite gods do not reward this.

---

## Standardization pipeline

The target is:

```text
RAW FILE
  ↓
read metadata
  ↓
decode/calibrate if needed
  ↓
reproject
  ↓
crop common area
  ↓
align channels
  ↓
resample to common grid
  ↓
normalize
  ↓
save standardized array
  ↓
write metadata
```

### Use Xarray for multidimensional data

Conceptually:

```python
import xarray as xr

ds = xr.open_dataset(path)

print(ds.dims)
print(ds.data_vars)
print(ds.coords)
```

### Use Rasterio for raster files

```python
import rasterio

with rasterio.open(path) as src:
    arr = src.read(1)
    profile = src.profile
```

### Standard output

For a multi-channel frame, prefer one standardized representation:

```text
[event_id]/frames/<timestamp>.npz
```

or NetCDF if the team prefers a scientific container.

Example metadata:

```json
{
  "event_id": "biparjoy_2023",
  "timestamp": "2023-06-14T12:00:00Z",
  "channels": ["ir", "water_vapor"],
  "height": 256,
  "width": 256,
  "crs": "EPSG:4326"
}
```

### Critical preprocessing checks

For every frame:

- no unexpected NaN explosion
- correct geographic orientation
- correct timestamp
- correct CRS
- channel dimensions match
- no accidental transpose
- no all-zero image
- values within expected range
- storm region is actually inside crop

### Data validation script

Run:

```bash
python scripts/validate_data.py
```

It should report:

```text
files checked
missing channels
duplicate timestamps
bad dimensions
missing coordinates
NaN percentage
value ranges
```

### Day-1 Data deliverable

```text
raw/
normalized/
metadata.csv
validation_report.txt
```

### Done when

ML can load a real frame with one function call.

---

# 5C. ML — DAY 1

## Task 1: PyTorch environment

Recommended:

```bash
python -m venv .venv
```

Activate the environment and install the project's pinned dependencies.

At minimum:

```text
torch
torchvision
numpy
pandas
xarray
rasterio
opencv-python
scikit-learn
matplotlib
```

Do not install twenty packages because a blog did.

### Verify PyTorch

```python
import torch

print(torch.__version__)
print("CUDA:", torch.cuda.is_available())
```

If CUDA is unavailable, continue on CPU.

Do not burn half a day trying to make a GPU appear.

---

## Task 2: dataloader

Expected:

```python
sample = dataset[0]

print(sample["image"].shape)
print(sample["timestamp"])
print(sample["event_id"])
```

For a single frame:

```text
[C, H, W]
```

For temporal data:

```text
[T, C, H, W]
```

### Dataloader acceptance test

It must:

- open a real standardized file
- return tensor
- preserve timestamp
- preserve event ID
- return label if available
- reject corrupt files clearly

---

## Task 3: classification stub

Backend and Frontend must not wait for the model.

Create a fixed JSON fixture:

```json
{
  "event_id": "demo_event",
  "timestamp": "2023-06-14T12:00:00Z",
  "center": {
    "lat": 15.20,
    "lon": 68.40
  },
  "pattern": {
    "label": "banding",
    "confidence": 0.72
  },
  "model": {
    "name": "ps70-classifier-stub",
    "version": "0.1.0"
  }
}
```

The exact values are demo placeholders and must be visibly treated as such until real inference replaces them.

### Day-1 ML deliverable

```text
working environment
dataloader
one real frame loaded
classification stub JSON
```

### Done when

Backend can build the API without needing your trained model.

---

# 5D. BACKEND — DAY 1

## Task

Build:

- FastAPI
- PostgreSQL
- PostGIS
- Docker Compose
- basic satellite-serving endpoint
- shared API contract

### Docker architecture

```text
docker-compose
├── api
├── postgres + postgis
└── optional frontend dev server
```

Do not add Kubernetes.

### Basic FastAPI structure

```text
backend/app/
├── main.py
├── api/
│   ├── classify.py
│   ├── predict.py
│   ├── replay.py
│   └── metrics.py
├── schemas/
├── services/
└── db/
```

### Start API

```bash
uvicorn app.main:app --reload
```

### Health endpoint

Implement:

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### Database

Create at minimum:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

Core logical tables:

```text
events
satellite_frames
classifications
predictions
metrics
```

### Classification table concept

```text
classification_id
event_id
timestamp
lat
lon
pattern
confidence
model_name
model_version
source_frame_id
geometry
```

### Day-1 satellite endpoint

The exact endpoint may be:

```http
GET /api/ps70/frames/{frame_id}
```

or a tile/image endpoint chosen by Backend.

The important contract is:

```text
Frontend asks for frame
Backend returns deterministic source image
Frontend does not know where the file lives
```

### Day-1 API contract

Write it down in:

```text
docs/api_contract.md
```

Do not keep the contract inside everyone's head.

---

# 5E. FRONTEND — DAY 1

## Task

Build the shell quickly.

### Stack

```text
React
Leaflet
```

### Design tokens

Define:

```text
typography
spacing
border radius
map controls
card styles
status styles
confidence styles
```

The visual language should feel:

- scientific
- clean
- geospatial
- operational
- trustworthy

Avoid:

- neon cyberpunk
- dashboard-card explosion
- unnecessary animation
- generic AI imagery

### Shell layout

Recommended:

```text
+------------------------------------------------------+
| CycloneWatch | Event | Time | System Status         |
+--------------------------+---------------------------+
|                          |                           |
|                          |  Level 1 / Status        |
|        MAP               |  Level 2 / Confidence    |
|                          |                           |
|                          |  Timeline                |
+--------------------------+---------------------------+
| Evidence / Source / Timestamp / Model               |
+------------------------------------------------------+
```

### Layer controls

```text
[ IR ] [ Visible ] [ Water Vapor ]
```

Do not display a channel unless it is actually available.

### Done when

A real satellite frame can be seen on a map.

---

# 5F. APP — DAY 1

## Scope

The app is **not** a mobile copy of the dashboard.

Only:

```text
Status
Alerts
Prediction summary
```

### Screens

```text
Home
  ↓
Current cyclone status
  ↓
Alert list
  ↓
Prediction detail
```

Build static shells first.

### Done when

The app launches on the actual demo device.

---

# DAY 2 — CLASSIFICATION

## 6A. RESEARCH

### Ground-truth labels

For each selected frame:

```text
event_id
timestamp
center_lat
center_lon
pattern_label
label_source
label_confidence
notes
```

Do not call a label "ground truth" if it is merely someone's guess from one screenshot.

If labels are manually assigned, record that clearly.

### MoES/IMD gap notes

Keep claims evidence-based.

The project is positioned around:

- faster satellite interpretation
- structural pattern classification
- uncertainty visualization
- cross-source interpretation

Do not write:

> "IMD cannot predict cyclones."

Write:

> "CycloneWatch targets the satellite-interpretation and decision-support layer rather than replacing IMD's forecasting system."

---

# 6B. DATA

Continue standardization.

The highest priority is not "more files".

The priority is:

```text
more usable sequences
```

A clean 50-frame sequence is more valuable than 500 badly aligned files.

### Build temporal index

Create:

```csv
event_id,timestamp,frame_path,available_channels
```

Sort strictly by timestamp.

Detect gaps:

```python
df = df.sort_values(["event_id", "timestamp"])
df["delta"] = df.groupby("event_id")["timestamp"].diff()
print(df["delta"].value_counts())
```

---

# 6C. ML — CNN CLASSIFICATION

## Required outputs

The current task requires:

1. cyclone centre latitude/longitude
2. structural pattern category
3. confidence score

### Model shape

A practical prototype can use a CNN backbone with separate heads:

```text
Satellite image
      |
      v
CNN backbone
      |
      +----------+-----------+
      |          |           |
 centre head  class head  confidence
      |          |           |
    lat/lon    pattern      score
```

### Why multi-head?

Because centre estimation and pattern classification are related but not identical tasks.

### Training target

Centre:

```text
(lat, lon)
```

Pattern:

```text
class ID
```

Confidence:

Prefer deriving/calibrating confidence from model outputs rather than treating an arbitrary probability as truth.

### Baseline losses

Conceptually:

```text
total_loss =
    centre_loss
    + lambda * classification_loss
```

Use a documented weighting.

Do not spend Day 2 inventing a sophisticated loss function.

### Training loop

Track:

```text
train loss
validation loss
classification accuracy
per-class precision/recall
centre error
```

Do not only report training accuracy.

### Split rule

Do not randomly split adjacent frames from the same cyclone across train and validation if that causes temporal leakage.

Prefer event-level separation where possible:

```text
train events
validation events
test events
```

If the dataset is too small, clearly document the limitation.

### Model artifact

Save:

```text
model.pt
config.json
label_map.json
normalization.json
```

The model cannot be handed to Backend as a mysterious 400 MB blob with no instructions.

### Inference contract

Provide one function:

```python
result = predict_frame(frame)
```

Returning:

```python
{
    "center": {"lat": ..., "lon": ...},
    "pattern": {"label": ..., "confidence": ...},
    "model": {"name": ..., "version": ...}
}
```

---

# 6D. BACKEND — `/api/ps70/classify`

Endpoint:

```http
POST /api/ps70/classify
```

Request concept:

```json
{
  "event_id": "biparjoy_2023",
  "timestamp": "2023-06-14T12:00:00Z",
  "frame_id": "frame_001"
}
```

Response:

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
    "name": "ps70-classifier",
    "version": "0.2.0"
  }
}
```

### PostGIS storage

Store:

```text
Point(longitude latitude)
```

GeoJSON uses:

```text
[lon, lat]
```

### Acceptance test

```text
POST frame
    ↓
model inference
    ↓
JSON response
    ↓
database row
    ↓
GET/retrieve classification
```

---

# 6E. FRONTEND — CLASSIFICATION

Show:

### Level 1

```text
CYCLONE DETECTED
```

### Level 2

```text
Pattern: Curved Band
Confidence: 72%
Centre: 15.20°N, 68.40°E
Timestamp: 14 Jun 2023 12:00 UTC
```

### Map

Show:

- cyclone centre marker
- selected satellite layer
- timestamp
- source

Do not show ten unrelated widgets.

---

# 6F. APP — CLASSIFICATION

Connect to:

```http
/api/ps70/classify
```

Display:

```text
Cyclone status
Pattern
Confidence
Last updated
```

If the API fails, show an honest offline/demo state rather than fake live data.

---

# DAY 3 — TEMPORAL PREDICTION

## 7A. DATA

Prepare sequences.

Logical sample:

```text
T-12
T-9
T-6
T-3
T0
```

The exact cadence must match the actual dataset and be documented.

The task only fixes the prediction window conceptually as:

```text
T-12 → T0
```

Do not claim a specific frame cadence unless the dataset actually supports it.

### Sequence integrity test

For each sample:

```text
all required timestamps exist
same geographic grid
same channel order
same normalization
same dimensions
```

---

# 7B. ML — TEMPORAL MODEL

## Required output

From:

```text
T-12 → T0
```

predict:

```text
T+12 centre
T+24 centre
T+12 pattern
T+24 pattern
```

### Baseline architecture

The master architecture recommends a lightweight temporal model, with ConvLSTM-style sequencing in the team sheet.

A practical prototype:

```text
frame CNN encoder
      |
      v
temporal sequence
      |
      +----------+----------+
      |                     |
 track head             pattern head
      |                     |
 future centre         future state
```

A GRU-based temporal head is acceptable if it gives a faster stable baseline. Do not change architecture repeatedly during the sprint.

### Training target

For centre prediction:

```text
target_t+12 = best-track position at T+12
target_t+24 = best-track position at T+24
```

For pattern:

```text
target_t+12
target_t+24
```

only where labels are actually available.

### Baseline first

Before trying an advanced model, build a simple baseline.

For track prediction, a basic persistence baseline can be:

```text
future position = current position + recent average motion
```

Then compare the ML model against it.

If the ML model loses to the baseline, report that.

Do not hide it.

---

# 7C. BACKEND — PREDICTION

Endpoint:

```http
POST /api/ps70/predict
```

Request:

```json
{
  "event_id": "biparjoy_2023",
  "start_timestamp": "2023-06-14T00:00:00Z"
}
```

Response:

```json
{
  "event_id": "biparjoy_2023",
  "base_time": "2023-06-14T00:00:00Z",
  "predictions": [
    {
      "valid_time": "2023-06-14T12:00:00Z",
      "center": {"lat": 16.10, "lon": 67.80},
      "pattern": {"label": "eye", "confidence": 0.64}
    },
    {
      "valid_time": "2023-06-15T00:00:00Z",
      "center": {"lat": 17.20, "lon": 67.10},
      "pattern": {"label": "eye", "confidence": 0.59}
    }
  ],
  "uncertainty": {
    "status": "provisional",
    "geometry": {
      "type": "Polygon",
      "coordinates": []
    }
  },
  "model": {
    "name": "ps70-temporal",
    "version": "0.1.0"
  }
}
```

### Important

If uncertainty has not been calibrated yet, label it:

```text
provisional
```

Do not label a placeholder cone:

```text
95% confidence
```

unless that statistic has actually been calibrated and evaluated.

---

# 7D. UNCERTAINTY GEOMETRY

Conceptually:

```text
predicted centre
       +
forecast spread
       ↓
confidence region
       ↓
polygon / corridor
```

The geometry should be generated from the model's actual uncertainty representation.

### Prototype fallback

If the model initially provides coordinate-wise standard deviations:

```text
sigma_lat
sigma_lon
```

construct an approximate ellipse around the forecast point.

Then project that ellipse into the map coordinate system.

Document the assumption.

### Final Day-6 version

Use calibrated model uncertainty and evaluate:

```text
How often does the observed future centre fall inside
the claimed uncertainty region?
```

This is **uncertainty coverage**.

---

# 7E. FRONTEND — FUTURE TRACK

Show:

```text
observed track
    |
    +---- predicted track
              |
              +---- uncertainty corridor
```

Use different visual treatment for:

- observed
- predicted
- uncertainty

The viewer should understand the difference immediately.

---

# 7F. APP — PREDICTION

Show:

```text
Predicted movement
T+12
T+24

Alert status
Confidence
```

Do not attempt to reproduce the full map dashboard.

---

# DAY 4 — HISTORICAL REPLAY + MENTOR CHECKPOINT

## 8A. HISTORICAL REPLAY

This is the flagship credibility feature.

### User journey

```text
Choose historical cyclone
        ↓
rewind to T-48h
        ↓
show available observation
        ↓
run/store prediction
        ↓
move to T-36h
        ↓
compare prediction with actual
        ↓
T-24h
        ↓
T-12h
        ↓
T0
```

### Why this matters

It converts:

> "Here is what our model says."

into:

> "Here is what our model would have said before the outcome was known."

That is much stronger evidence.

---

## 8B. BACKEND — `/api/replay`

Endpoint:

```http
GET /api/replay/{event_id}
```

Response should contain enough information for the frontend to animate the historical state without making dozens of unpredictable external calls.

Example:

```json
{
  "event_id": "biparjoy_2023",
  "steps": [
    {
      "time": "2023-06-12T00:00:00Z",
      "observation_frame": "frame_001",
      "prediction": {},
      "actual": {}
    }
  ]
}
```

### Offline rule

The replay must work when:

```text
internet = OFF
```

after the demo environment is prepared.

This means:

- preloaded frames
- precomputed predictions if necessary
- cached API data
- local database

No live external API should be required for the final replay.

---

## 8C. FRONTEND — REPLAY UI

Slider:

```text
T-48h ---- T-36h ---- T-24h ---- T-12h ---- T0
```

At each point show:

```text
Prediction
Actual
Error
Source image
```

The user should be able to answer:

> "What did the model know at this moment?"

without asking the presenter.

---

## 8D. LEVEL-3 EVIDENCE PANEL

When a judge clicks a prediction:

```text
Prediction
    ↓
Evidence
    ├── source image
    ├── timestamp
    ├── channel
    ├── centre estimate
    ├── pattern
    ├── confidence
    └── model version
```

This directly supports the project's explainability rule.

---

## 8E. MAE CALCULATION

The current task explicitly requires the **exact Mean Absolute Error of predicted centre vs. IMD Best Track data**.

For geographic positions, do not average raw degree differences and call that kilometres.

Use a geodesic distance.

### Haversine distance

For predicted:

```text
(lat_p, lon_p)
```

and actual:

```text
(lat_a, lon_a)
```

calculate great-circle distance.

Python:

```python
from math import radians, sin, cos, asin, sqrt

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    return 2 * R * asin(sqrt(a))
```

Then:

```python
errors = [
    haversine_km(p_lat, p_lon, a_lat, a_lon)
    for p_lat, p_lon, a_lat, a_lon in pairs
]

mae_km = sum(errors) / len(errors)
```

### Evaluation table

Create:

```csv
event_id,base_time,horizon,pred_lat,pred_lon,actual_lat,actual_lon,error_km
```

Then summarize:

```text
MAE @ +12h
MAE @ +24h
number of forecasts
number of events
test period
baseline
```

### Never report only one number

Bad:

```text
Our model has 42 km MAE.
```

Better:

```text
On N held-out forecasts from X historical events,
the prototype's +12h centre-position MAE was Y km
and +24h MAE was Z km, compared with baseline B.
```

If no proper baseline exists, say so.

---

## 8F. DAY-4 MENTOR CHECKPOINT

Bring:

### Working

- satellite frame
- classification
- predicted track/pattern
- replay
- map
- evidence panel, even if rough
- actual measured error

### Documentation

- architecture
- data sources
- taxonomy
- model description
- limitations
- current metrics
- next steps

### Do not hide

- missing data
- failed experiments
- weak classes
- poor confidence calibration
- model limitations

The checkpoint is for feedback, not theatrical perfection.

---

# DAY 5 — FEEDBACK + MODEL IMPROVEMENT

## Research + Data

Expand beyond the two demo events.

Prioritize:

```text
event diversity
data quality
temporal coverage
label consistency
```

Do not simply add storms to make the dataset number look large.

## ML

Improve classification first.

Possible changes:

- more training data
- more epochs
- augmentation
- class balancing
- better crop
- learning-rate adjustment

Change one meaningful variable at a time when possible.

Record:

```text
experiment ID
change
training data
validation data
metric
result
decision
```

## Backend

Fix mentor-identified API problems.

Do not redesign the API because the route name feels boring.

## Frontend

Fix the exact confusion the mentor observed.

Examples:

- unclear legend
- unclear prediction/observation distinction
- confidence not understandable
- replay controls unclear

## App

Fix only the feedback relevant to the mobile scope.

---

# DAY 6 — UNCERTAINTY + EXPLAINABILITY

## 10A. ML CONFIDENCE CALIBRATION

A raw softmax probability is not automatically a calibrated confidence.

Goal:

```text
predicted confidence
        |
        v
meaningful probability / confidence estimate
```

Possible prototype methods include:

- temperature scaling
- validation-set calibration
- reliability diagram

### Reliability diagram

Group predictions into confidence bins:

```text
0.0–0.1
0.1–0.2
...
0.9–1.0
```

Compare:

```text
mean predicted confidence
vs.
actual correctness
```

If the model says 0.8 confidence, roughly 80% of those predictions should be correct for a well-calibrated classifier.

Do not claim calibration quality without measuring it.

---

## 10B. UNCERTAINTY COVERAGE

For a forecast region:

```text
forecast region
      |
      v
did actual future centre fall inside?
```

Compute:

```text
coverage =
inside_count / total_forecasts
```

Report the region definition too.

Example:

```text
90% uncertainty region
Observed centre coverage: 83%
```

Only say "90%" if the region is actually defined/calibrated at that level.

---

## 10C. BACKEND FINAL UNCERTAINTY

The backend should return:

```json
{
  "uncertainty": {
    "level": "calibrated",
    "coverage_target": 0.90,
    "geometry": {
      "type": "Polygon",
      "coordinates": []
    }
  }
}
```

Only include `coverage_target` after calibration.

---

## 10D. `/api/metrics`

Endpoint:

```http
GET /api/metrics?event_id=biparjoy_2023
```

Return metrics such as:

```json
{
  "dataset": {
    "events": 5,
    "forecasts": 120
  },
  "track": {
    "mae_km_t12": 54.2,
    "mae_km_t24": 91.8
  },
  "classification": {
    "accuracy": 0.81
  },
  "uncertainty": {
    "coverage": 0.86
  },
  "baseline": {
    "mae_km_t12": 61.0,
    "mae_km_t24": 110.2
  }
}
```

These are example shapes only. Use actual measured values.

---

## 10E. FRONTEND POLISH

Protect Day 6.

Polish:

- spacing
- typography
- map controls
- loading states
- error states
- evidence panel
- replay
- confidence presentation
- responsive layout

Do not add new scientific features.

---

# DAY 7 — FREEZE + VALIDATION

## 11A. MODEL FREEZE

After Day 7:

```text
NO NEW TRAINING CHANGES
```

Create:

```text
docs/model_manifest.json
```

Example:

```json
{
  "classifier": {
    "version": "1.0.0",
    "checkpoint": "classifier_v1.pt"
  },
  "temporal": {
    "version": "1.0.0",
    "checkpoint": "temporal_v1.pt"
  },
  "normalization": "normalization_v1.json",
  "labels": "label_map_v1.json"
}
```

---

## 11B. FULL BACKTEST

Run one reproducible command:

```bash
python scripts/run_backtest.py --config configs/final_backtest.yaml
```

Output:

```text
reports/
├── metrics.json
├── forecast_errors.csv
├── classification_report.csv
├── uncertainty_coverage.csv
└── plots/
```

### Minimum final report

```text
dataset
events
forecast count
train/test split
+12h MAE
+24h MAE
classification accuracy
per-class performance
uncertainty coverage
baseline comparison
limitations
```

---

## 11C. API FREEZE

Run:

```bash
pytest
```

Then test:

```text
health
classify
predict
replay
metrics
```

Stress test replay:

```text
event 1
event 2
event 3
...
```

No live internet.

---

## 11D. UI FREEZE

Only:

- bug fixes
- visual corrections
- demo reliability

No feature creep.

---

## 11E. DOCUMENTATION FREEZE

Final docs:

```text
README.md
docs/architecture.md
docs/data_dictionary.md
docs/model_card.md
docs/metrics.md
docs/limitations.md
docs/api_contract.md
docs/qna.md
```

---

# DAY 8 — REHEARSAL

## 12. FULL DEMO FLOW

The recommended flow:

```text
1. Open CycloneWatch
2. Select historical cyclone
3. Show raw satellite observation
4. Toggle IR / Visible / WV
5. Show detected centre
6. Show structural pattern
7. Show confidence
8. Move into historical replay
9. Show prediction
10. Show actual outcome
11. Show uncertainty
12. Open evidence panel
13. Show measured metric
14. Explain where it fits beside IMD
```

## 12.1 Three-minute version

```text
0:00–0:20
Problem

0:20–0:40
Product reveal

0:40–1:30
Observation → classification → prediction → uncertainty

1:30–2:10
Historical replay + evidence

2:10–2:35
Measured results

2:35–3:00
Positioning + impact
```

## 12.2 Recorded fallback

The recorded demo must show the exact same workflow.

Do not record a fantasy version of the product that the live build cannot reproduce.

---

# 13. ROLE-SPECIFIC FINAL CHECKLISTS

# 13A. ADITYA — ML

### Day 1
- [ ] PyTorch works
- [ ] Dataloader reads real data
- [ ] Stub JSON delivered

### Day 2
- [ ] CNN trained
- [ ] Centre output works
- [ ] Pattern output works
- [ ] Confidence output exists
- [ ] Model handed to Backend

### Day 3
- [ ] Sequence dataset works
- [ ] Temporal model predicts T+12/T+24
- [ ] Pattern evolution output works
- [ ] Model handed to Backend

### Day 4
- [ ] No new modelling
- [ ] Bugs fixed
- [ ] Limitations written

### Day 5
- [ ] Classification improvement tested

### Day 6
- [ ] Temporal improvement tested
- [ ] Confidence calibration measured

### Day 7
- [ ] Models frozen
- [ ] Model manifest created

### Day 8
- [ ] Can explain model architecture
- [ ] Can explain failure modes
- [ ] Can explain metrics

---

# 13B. SATYAM — BACKEND + LEAD

### Day 1
- [ ] Docker Compose works
- [ ] FastAPI works
- [ ] PostGIS works
- [ ] Health endpoint works
- [ ] API contract written
- [ ] Satellite endpoint works

### Day 2
- [ ] `/api/ps70/classify`
- [ ] PostGIS classification storage
- [ ] Frontend receives real response

### Day 3
- [ ] `/api/ps70/predict`
- [ ] uncertainty geometry interface
- [ ] Frontend receives prediction

### Day 4
- [ ] `/api/replay`
- [ ] offline replay
- [ ] mentor demo works

### Day 5
- [ ] mentor fixes complete

### Day 6
- [ ] final uncertainty geometry
- [ ] `/api/metrics`

### Day 7
- [ ] API frozen
- [ ] replay stress-tested
- [ ] no live internet dependency

### Day 8
- [ ] full-stack rehearsal
- [ ] fallback confirmed

### Leadership rule

Every evening send:

```text
DONE:
BLOCKED:
TOMORROW:
```

---

# 13C. KAVYA — DESIGN + FRONTEND

### Day 1
- [ ] design tokens
- [ ] React shell
- [ ] Leaflet map
- [ ] layer toggles

### Day 2
- [ ] centre marker
- [ ] pattern card
- [ ] confidence

### Day 3
- [ ] predicted track
- [ ] timeline

### Day 4
- [ ] replay slider
- [ ] evidence panel
- [ ] actual vs predicted

### Day 5
- [ ] mentor UI issues fixed

### Day 6
- [ ] full polish
- [ ] evidence panel complete

### Day 7
- [ ] UI frozen

### Day 8
- [ ] rehearsal with Backend

---

# 13D. ANIKET — APP

### Day 1
- [ ] project runs
- [ ] static screens
- [ ] API contract understood

### Day 2
- [ ] classify endpoint connected
- [ ] status visible

### Day 3
- [ ] prediction visible
- [ ] alert list
- [ ] offline fixture

### Day 4
- [ ] device-tested
- [ ] features frozen

### Day 5
- [ ] feedback fixes

### Day 6
- [ ] visual identity matched

### Day 7
- [ ] app frozen

### Day 8
- [ ] real-device rehearsal

---

# 13E. ABHINAV — DATA

### Day 1
- [ ] 2 event datasets acquired
- [ ] metadata captured
- [ ] standardized frames created

### Day 2
- [ ] more frames standardized
- [ ] temporal index complete

### Day 3
- [ ] validation imagery ready

### Day 4
- [ ] MAE data aligned with Research

### Day 5
- [ ] expanded event set
- [ ] data-quality issues fixed

### Day 6
- [ ] calibration support data ready

### Day 7
- [ ] final backtest executed
- [ ] metrics exported

### Day 8
- [ ] source provenance understood

---

# 13F. ARSHIT — RESEARCH

### Day 1
- [ ] two events locked
- [ ] IBTrACS downloaded
- [ ] taxonomy drafted

### Day 2
- [ ] labels finalized
- [ ] gap analysis started

### Day 3
- [ ] validation positions prepared

### Day 4
- [ ] MAE calculation supported
- [ ] documentation

### Day 5
- [ ] expanded event set

### Day 6
- [ ] limitations
- [ ] positioning slide

### Day 7
- [ ] final metrics narrative
- [ ] documentation
- [ ] PPT content

### Day 8
- [ ] Q&A defense sheet
- [ ] whole-system understanding

---

# 14. SHARED HANDOFF PROTOCOL

Every handoff must contain:

```text
OWNER:
OUTPUT:
LOCATION:
FORMAT:
VERSION:
HOW TO TEST:
KNOWN LIMITATION:
NEXT OWNER:
```

Example:

```text
OWNER: ML
OUTPUT: classifier
LOCATION: ml/checkpoints/classifier_v1.pt
FORMAT: PyTorch checkpoint
VERSION: 1.0.0
HOW TO TEST: python scripts/test_classifier.py
KNOWN LIMITATION: trained on 4 events
NEXT OWNER: Backend
```

---

# 15. GIT / VERSIONING RULE

Use small commits.

Examples:

```text
data: add Biparjoy normalized frames
ml: add classifier baseline
backend: add classify endpoint
frontend: add classification card
app: connect classify endpoint
research: add taxonomy v1
```

Avoid:

```text
final changes
final2
final_latest
final_latest_real
```

Tag major milestones:

```text
v0.1-day1
v0.2-day2
v0.3-day3
v0.4-day4-poc
v1.0-day7-freeze
v1.1-demo
```

---

# 16. DATA QUALITY CHECKLIST

Before any model training:

- [ ] source known
- [ ] event known
- [ ] timestamp known
- [ ] timezone UTC
- [ ] CRS known
- [ ] dimensions known
- [ ] channel known
- [ ] missing values checked
- [ ] geographic crop checked
- [ ] channel alignment checked
- [ ] normalization documented
- [ ] file hash or stable filename recorded

### Common silent failures

#### Failure: image is upside down

Check latitude coordinate direction.

#### Failure: longitude shifted

Check CRS and longitude convention.

#### Failure: channels do not align

Check projection, resolution, timestamp and resampling.

#### Failure: model learns timestamp/event instead of storm

Check event-level train/test split.

#### Failure: validation looks suspiciously perfect

Check leakage.

---

# 17. MODEL EVALUATION RULES

## Classification

Report:

```text
accuracy
macro F1
per-class precision
per-class recall
confusion matrix
```

Especially watch:

```text
shear-affected
disorganized
curved-band
```

because visually ambiguous classes may behave differently.

## Centre estimation

Report:

```text
MAE in km
```

and preferably:

```text
median error
P90 error
```

## Track prediction

Report separately:

```text
+12h error
+24h error
```

## Uncertainty

Report:

```text
coverage
region size
calibration status
```

Do not use the word "confidence" to mean five different things.

---

# 18. BASELINE COMPARISON

The project should have at least one simple baseline.

Possible track baseline:

```text
persistence / recent-motion extrapolation
```

Workflow:

```text
current centre
     +
recent motion vector
     ↓
baseline future centre
```

Then compare:

```text
baseline MAE
vs
ML MAE
```

If ML does not beat the baseline:

1. investigate
2. document
3. do not hide it

A transparent weak result is still a scientific result.

---

# 19. HISTORICAL REPLAY DATA MODEL

A replay record should contain:

```json
{
  "event_id": "biparjoy_2023",
  "analysis_time": "2023-06-13T00:00:00Z",
  "observation_frames": [],
  "prediction": {
    "t12": {},
    "t24": {}
  },
  "actual": {
    "t12": {},
    "t24": {}
  },
  "errors": {
    "t12_km": 0,
    "t24_km": 0
  }
}
```

This lets the frontend replay the experiment without rerunning the model during the demo.

---

# 20. EVIDENCE / PROVENANCE

Every prediction displayed on screen should be traceable through:

```text
Prediction
   ↓
model version
   ↓
input sequence
   ↓
source frames
   ↓
timestamps
   ↓
ground truth
```

Minimum provenance fields:

```text
source
satellite
product
channel
timestamp
frame ID
model version
data preprocessing version
```

This is one of the easiest ways to make the system feel scientifically serious without adding another giant model.

---

# 21. HUMAN-IN-THE-LOOP POSITIONING

The prototype is not autonomous authority.

Recommended conceptual flow:

```text
Satellite observation
        ↓
AI interpretation
        ↓
confidence + evidence
        ↓
analyst/user review
        ↓
decision
```

The evidence panel should support this.

If a judge asks:

> "What happens if the model is wrong?"

Answer:

> "We expose confidence and uncertainty, show the source evidence, and keep the human decision-maker in the loop. The prototype is a decision-support layer, not an autonomous authority."

---

# 22. WHAT WE ARE NOT BUILDING

Do not add these during the sprint:

- full national NWP
- new foundation weather model
- satellite ground station
- global high-resolution atmospheric simulation
- autonomous cyclone warning authority
- Kubernetes
- Kafka
- complex microservice mesh
- LLM as scientific prediction core
- ten different ML architectures
- unnecessary mobile features
- live-internet dependence for the demo

If someone proposes one of these on Day 6, the answer is:

> "Put it in the post-selection roadmap."

---

# 23. LOW-COST DEVELOPMENT SETUP

The research architecture intentionally favors:

```text
Laptop
  ↓
Python
  ↓
Docker Compose
  ↓
PostgreSQL/PostGIS
  ↓
local inference
```

For the demo:

```text
single machine
├── React
├── FastAPI
├── PostgreSQL/PostGIS
├── ML
└── cached demo data
```

Optional services should not delay the core.

### Principle

Use:

- open data
- open-source frameworks
- local inference
- cached demonstration datasets

Avoid paid infrastructure unless the team already has access and it materially reduces risk.

---

# 24. TROUBLESHOOTING TREE

## If ML is blocked by Data

Use:

```text
agreed standardized sample
```

and continue model plumbing.

Tell Data exactly what is missing.

## If Backend is blocked by ML

Use:

```text
stub JSON
```

and continue API + database + frontend integration.

## If Frontend is blocked by Backend

Use:

```text
mock API fixture
```

with the exact agreed response schema.

## If App is blocked by Backend

Use:

```text
local JSON fixture
```

until the API is ready.

## If satellite download fails

Do:

```text
1. check credentials/access
2. check dataset ID
3. check date range
4. check bounding box
5. check file availability
6. use an already-approved alternative source
```

Do not spend the entire sprint on one portal.

## If model accuracy is poor

Do:

```text
1. check labels
2. check leakage
3. check normalization
4. check centre labels
5. check crop
6. compare with baseline
7. simplify model if needed
```

Do not immediately add a transformer.

---

# 25. JUDGE Q&A

## "Why not just use IMD?"

> We are not replacing IMD. IMD has a mature forecasting system that combines NWP, statistical-dynamical guidance, satellite and other observations. CycloneWatch targets the interpretation layer: automatically reading multi-source satellite imagery, classifying structural patterns, predicting short-horizon evolution, and exposing uncertainty and evidence.

## "Where did your data come from?"

Answer with the exact provider and dataset used for the displayed example.

Never say:

> "Internet data."

Say:

> "This demo uses [provider/product], with [event], and the ground-truth track comes from [IBTrACS/IMD], with the exact source recorded in our provenance metadata."

## "Is your model accurate?"

Give:

```text
dataset
events
held-out protocol
metric
baseline
limitation
```

Do not give a naked percentage.

## "Why AI?"

> AI is useful for pattern recognition and systematic spatio-temporal prediction. We are not claiming that AI replaces the physics-based forecasting ecosystem.

## "Why not an LLM?"

> LLMs are not the appropriate scientific core for spatio-temporal satellite prediction. We use specialized vision and temporal models for the actual scientific task.

## "What makes this different?"

Use the strongest defensible combination:

```text
multi-source interpretation
+
historical replay
+
measured prediction
+
uncertainty
+
source evidence
```

## "Can it scale?"

> The prototype is deliberately simple. Ingestion, inference, storage, API and presentation are logically separated, so they can later be scaled independently. The prototype itself does not claim national operational deployment.

## "What if the model is wrong?"

> The system exposes confidence and uncertainty, shows source evidence, and keeps a human decision-maker in the loop.

---

# 26. PRESENTATION RULES

Use 8–10 slides.

Recommended:

1. Problem
2. Existing ecosystem + gap
3. Solution
4. Product
5. PS70 pipeline
6. Historical replay
7. Metrics
8. Explainability + uncertainty
9. Technology
10. Closing

### Never put on a slide

- fabricated accuracy
- unexplained charts
- fake real-time claims
- "replaces IMD"
- "production-ready"
- "98% accurate" without rigorous evidence
- screenshots of code as the main demo

---

# 27. FINAL DEMO CHECKLIST

## Data

- [ ] All demo frames local
- [ ] All source metadata available
- [ ] No missing critical frames
- [ ] Ground truth loaded

## Backend

- [ ] Docker starts
- [ ] PostGIS starts
- [ ] `/health`
- [ ] `/classify`
- [ ] `/predict`
- [ ] `/replay`
- [ ] `/metrics`
- [ ] no live internet required

## ML

- [ ] frozen model
- [ ] correct labels
- [ ] correct normalization
- [ ] model version documented

## Frontend

- [ ] map loads
- [ ] layers work
- [ ] centre appears
- [ ] pattern appears
- [ ] confidence appears
- [ ] prediction appears
- [ ] uncertainty appears
- [ ] replay works
- [ ] evidence works

## App

- [ ] actual device tested
- [ ] status works
- [ ] alerts work
- [ ] offline fallback works

## Presentation

- [ ] metrics slide uses final numbers
- [ ] limitations included
- [ ] data provenance included
- [ ] positioning line consistent
- [ ] Q&A sheet ready
- [ ] recorded fallback ready

---

# 28. THE FINAL 30-MINUTE PRE-DEMO PROTOCOL

Do not make code changes unless they are emergency fixes.

### T-30

Start the exact demo machine.

### T-25

Start Docker services.

### T-20

Open dashboard and app.

### T-15

Run the complete replay once.

### T-10

Verify metric values.

### T-5

Open the presentation.

### T-2

Stop touching the code.

### T-0

Demo.

---

# 29. SOURCE AND VERIFICATION NOTES

## Internal source hierarchy

For sprint execution:

1. **Current `PS70_Team_Task_Sheet_By_Person.md`** = task ownership and 8-day schedule.
2. **`PS70_Team_Brief_8Day_Sheet.md`** = PS70 scope, architecture, role rationale, checkpoint logic.
3. **Master Plan / Research Architecture** = benchmark systems, technology rationale, long-term architecture and positioning.
4. **Older 9-day / PS59 material** = background only where it does not conflict with the current PS70-only 8-day sprint.

## Official external sources checked for execution

### MOSDAC

The current MOSDAC Download API documentation states that the download workflow uses a dataset ID, time range and optional bounding box, with Python 3 and `requests`; downloading requires MOSDAC credentials. It also documents archived and near-real-time access and the current download client workflow.

Official references:

- [MOSDAC Download API Manual](https://mosdac.gov.in/downloadapi-manual)
- [MOSDAC Satellite Data Portal](https://mosdac.gov.in/catalog-app/satellite.php)
- [MOSDAC Data Access Policy](https://www.mosdac.gov.in/data-access-policy)

### IBTrACS

NOAA/NCEI's current IBTrACS documentation describes IBTrACS as a global best-track collection with CSV, NetCDF and shapefile access and a North Indian Ocean subset.

Official reference:

- [NOAA/NCEI IBTrACS](https://www.ncei.noaa.gov/products/international-best-track-archive)

### IMD / RSMC New Delhi

RSMC New Delhi maintains a best-track data section and describes its responsibility for North Indian Ocean cyclone monitoring, prediction and best-track preparation.

Official references:

- [RSMC New Delhi Best Track](https://rsmcnewdelhi.imd.gov.in/report.php?internal_menu=MzM)
- [RSMC New Delhi Best Track Documentation](https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2Fbestrack.pdf)

The team should still record the exact dataset/product used for every demo event.

---

# 30. WHAT "DONE" MEANS

The project is done when a person who did not build it can perform this sequence:

```text
Select cyclone
      ↓
See real satellite observation
      ↓
Understand detected centre
      ↓
Understand structural pattern
      ↓
See confidence
      ↓
Rewind historical time
      ↓
See what the model predicted
      ↓
Compare against actual
      ↓
See uncertainty
      ↓
Open evidence
      ↓
See measured metric
      ↓
Understand where CycloneWatch fits beside IMD
```

If that works reliably, the prototype has a coherent story.

If the model is imperfect but the measurement is honest, that is acceptable.

If the dashboard is beautiful but the data is fabricated, it is not.

If the model is clever but nobody can explain what it saw, it is not.

If the demo depends on venue Wi-Fi, it is not finished.

---

# 31. MASTER RULE

> **Build the smallest scientifically defensible PS70 system that can be demonstrated, measured, explained, and defended.**

The goal is not to pretend that six students rebuilt a national meteorological forecasting centre in eight days.

The goal is to demonstrate one credible slice of the larger system:

```text
REAL SATELLITE DATA
       ↓
AUTOMATED INTERPRETATION
       ↓
STRUCTURAL CLASSIFICATION
       ↓
SHORT-HORIZON EVOLUTION
       ↓
UNCERTAINTY
       ↓
EVIDENCE
       ↓
DECISION SUPPORT
```

That is CycloneWatch.
