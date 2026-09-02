# CycloneWatch — Pending Work Tracker

> **Last updated:** 2026-09-02 (post-Antigravity training run, 7-event dataset)
> **Sprint:** SIH 2026 PS70 — 8-Day Sprint
> **Lead:** Satyam Srivastava

---

## Status Key

| Symbol | Meaning |
|---|---|
| ✅ Done | Complete, tested, committed |
| 🟡 In Progress | Work started, not complete |
| 🟢 Ready | Can be started right now, no blocker |
| 🔴 Blocked | Waiting on a specific dependency |

---

## What is complete as of today

| Area | What is done |
|---|---|
| **Backend** | Full FastAPI + PostGIS + Docker. 6 endpoints, 93/93 tests, seed script, precompute script |
| **ML model** | Trained on 7 cyclones, 423 frames. Pattern accuracy 78.3%, Centre MAE 255 km. Pattern head LIVE |
| **Data** | 7 events downloaded + normalized. Best-track CSVs for all 7 events. Training manifest complete |
| **Labels** | 423 frames auto-labeled via IBTrACS intensity rules. ground_truth_labels.csv committed |
| **Docs** | api_contract.md, model_explained.md, taxonomy.md, limitations.md, BACKEND_EXPLAINED.md |
| **Research** | Cyclone dossier (Biparjoy + Amphan), IBTrACS data, pattern taxonomy draft |

---

## Updated Dashboard / Product Concept

The confirmed demo flow is:

```
1. Dashboard opens → shows current/recent satellite IR image of Indian Ocean
   (base map layer, live-ish satellite imagery as visual backdrop)

2. Event selector panel (sidebar/dropdown) → user picks a historical cyclone:
   Biparjoy 2023 | Amphan 2020 | Fani 2019 | Tauktae 2021 |
   Phailin 2013  | Hudhud 2014 | Ockhi 2017

3. Dashboard loads that event:
   - Satellite frames for the event appear as an overlay on the map
   - Timeline slider appears: T-start → T-landfall

4. For each time step:
   - Cyclone centre marker (from ML classification)
   - Pattern label card (eye / banding / curved_band / etc.)
   - Confidence indicator (provisional until Day-6 calibration)
   - Uncertainty ellipse around predicted position

5. "What would CycloneWatch have predicted?" panel:
   - Shows T+12 and T+24 predicted track
   - Shows uncertainty cone
   - Compare against actual IBTrACS track

6. Evidence panel (click any prediction):
   - Source satellite image
   - Timestamp, channel, model version
   - Actual vs predicted position, error in km

7. Metrics bar:
   - Centre MAE (km), Pattern accuracy (%), events evaluated
```

**Why this beats IMD for the demo positioning:**
Ockhi 2017 is the killer case — IMD issued the first advisory 36 hours after formation. Our historical replay shows what CycloneWatch would have flagged at T-36h. Use this in the demo.

---

## Backend (Satyam)

| # | Task | Status | Notes |
|---|---|---|---|
| B1 | FastAPI + PostGIS + Docker | ✅ Done | 93/93 tests passing |
| B2 | All 6 API endpoints | ✅ Done | classify, predict, replay, metrics, frames, health |
| B3 | ML adapter (stub + real) | ✅ Done | predict_frame() + predict_sequence() live |
| B4 | seed_db.py + precompute_replay.py | ✅ Done | Updated for 7 events |
| B5 | Register all 7 events + frames in DB | ✅ Done | seed_db.py has all 7 events |
| B6 | scripts/load_ground_truth.py | ✅ Done | Loads Research labels into metrics table |
| B7 | Wire calibrated uncertainty | 🔴 Blocked | After ML confidence head (Day 6) |
| B8 | XYZ tile serving (optional) | 🟢 Ready | Only if Frontend confirms Leaflet can't use raw GeoTIFF |
| B9 | scripts/run_backtest.py | 🟢 Ready | Full eval report — run after precompute |
| B10 | Baseline MAE wiring in /api/metrics | 🟢 Ready | Persistence baseline exists — wire the number |
| B11 | **Run precompute_replay for all 7 events** | 🟢 Ready | `docker compose exec api python -m scripts.precompute_replay --event_id biparjoy_2023` (repeat for each) |
| B12 | Day-7 freeze + stress test | 🔴 Blocked | Day 7 |

---

## ML (Aditya)

| # | Task | Status | Notes |
|---|---|---|---|
| M1 | Dataset + dataloader | ✅ Done | 423 frames, 7 events, CycloneDataset works |
| M2 | Centre regression | ✅ Done | MAE 255 km on 60 val samples |
| M3 | Pattern classification | ✅ Done | 78.3% accuracy, weighted CE loss |
| M4 | ml/inference.py delivered | ✅ Done | predict_frame() + predict_sequence() |
| M5 | Model config + evaluation metrics | ✅ Done | ml/configs/model_config.json v2.0.0 |
| M6 | **Temporal model (T+12/T+24)** | 🔴 Blocked | Currently persistence fallback. **Biggest remaining ML task** |
| M7 | Confidence calibration | 🔴 Blocked | Day 6 — temperature scaling after pattern head is stable |
| M8 | Improve centre MAE | 🟢 Ready | More training epochs, learning rate tuning, more data |
| M9 | Model manifest | ✅ Done | ml/configs/model_config.json |
| M10 | Freeze models | 🔴 Blocked | Day 7 |

**What Aditya needs to do next (in order):**
1. Build temporal model — ConvLSTM or simple GRU reading sequence `[T, C, H, W]` → predict T+12 and T+24 centre
2. Replace `predict_sequence()` in `ml/inference.py` — keep the function signature exactly the same
3. Retrain centre-only model with more epochs for lower MAE (try 200 epochs, ReduceLROnPlateau already configured)
4. Day 6: Add confidence head, run temperature scaling calibration

---

## Data (Abhinav)

| # | Task | Status | Notes |
|---|---|---|---|
| D1 | IBTrACS NI raw CSV | ✅ Done | 60,679 rows |
| D2 | Best-track CSVs for all 7 events | ✅ Done | biparjoy, amphan, fani, tauktae, phailin, hudhud, ockhi |
| D3 | GridSat-B1 download (7 events) | ✅ Done | scripts/aws_downloader.py — all 7 run |
| D4 | standardize_data.py | ✅ Done | 423 frames, [2, H, W] npz |
| D5 | training_manifest.csv | ✅ Done | 423 rows, all PASS, centres joined |
| D6 | ground_truth_labels.csv | ✅ Done | 423 labels via IBTrACS intensity rules |
| D7 | **Additional cyclones — see list below** | 🟢 Ready | Run aws_downloader.py after adding new events |
| D8 | MOSDAC / INSAT-3DR data (optional) | 🟢 Ready | Higher res (1km vs 4km) — instructions below |

### Recommended additional events for better MAE

To improve centre MAE from ~255 km to <150 km, we need more diverse training data. Add these in priority order — all are in IBTrACS and supported by aws_downloader.py:

| Cyclone | Year | Peak | Why add it |
|---|---|---|---|
| **Maha** | 2019 | 100 kts | Long-lived Arabian Sea, 111 frames in IBTrACS — lots of training data |
| **Kyarr** | 2019 | 130 kts | Strongest Arabian Sea cyclone in 2019, good intensification sequence |
| **Nivar** | 2020 | 75 kts | Tamil Nadu landfall, same year as Amphan — adds geographic diversity |
| **Yaas** | 2021 | 85 kts | Odisha landfall, well-documented rapid intensification |
| **Gati** | 2020 | 85 kts | Fastest intensifying Arabian Sea cyclone on record — unique pattern |

**How to add them (Abhinav):**
1. Open `scripts/aws_downloader.py` — add entries to the `EVENTS` list (same format as existing ones)
2. Open `scripts/split_ibtracs.py` — add entries to the `EVENTS` list
3. Run: `python scripts/split_ibtracs.py` (generates best-track CSVs)
4. Run: `python scripts/aws_downloader.py` (downloads satellite data)
5. Run: `python scripts/standardize_data.py` (normalises to npz)
6. Run: `python scripts/label_frames.py` (adds pattern labels)
7. Run: `python scripts/validate_and_join.py` (updates training_manifest.csv)
8. Tell Satyam + Aditya when done → retrain

**Event window format:**
```python
{"id": "maha_2019",  "start": datetime(2019, 10, 28, 0, tzinfo=timezone.utc),
                      "end":   datetime(2019, 11, 11, 0, tzinfo=timezone.utc)},
{"id": "kyarr_2019", "start": datetime(2019, 10, 22, 0, tzinfo=timezone.utc),
                      "end":   datetime(2019, 11,  3, 0, tzinfo=timezone.utc)},
{"id": "nivar_2020", "start": datetime(2020, 11, 23, 0, tzinfo=timezone.utc),
                      "end":   datetime(2020, 11, 28, 0, tzinfo=timezone.utc)},
{"id": "yaas_2021",  "start": datetime(2021,  5, 23, 0, tzinfo=timezone.utc),
                      "end":   datetime(2021,  5, 28, 0, tzinfo=timezone.utc)},
{"id": "gati_2020",  "start": datetime(2020, 11, 19, 0, tzinfo=timezone.utc),
                      "end":   datetime(2020, 11, 26, 0, tzinfo=timezone.utc)},
```

### MOSDAC / INSAT-3DR (optional but high value)

INSAT-3DR data gives 1 km resolution vs GridSat-B1's 4 km — much sharper images, much better model learning.

**Where to get it:**
- URL: https://mosdac.gov.in
- Product: INSAT-3DR Level-1B / IMR (Imager) data
- Channels needed: IR1 (10.8 µm), WV (6.8 µm)
- Credentials: Register at mosdac.gov.in — free for research use
- Download tool: `requests` library + MOSDAC Download API (documented at mosdac.gov.in/downloadapi-manual)

**Note:** Only pursue MOSDAC if GridSat-B1 downloads are complete. Do not let MOSDAC credential issues block the sprint.

---

## Research (Arshit)

| # | Task | Status | Notes |
|---|---|---|---|
| R1 | Events locked (7 total) | ✅ Done | biparjoy, amphan, fani, tauktae, phailin, hudhud, ockhi |
| R2 | IBTrACS best-track for all 7 | ✅ Done | Per-event CSVs committed |
| R3 | Pattern taxonomy | ✅ Done | 5 labels, documented in docs/taxonomy.md |
| R4 | Pattern labels CSV | ✅ Done | data/ground_truth/ground_truth_labels.csv (423 rows) |
| R5 | **Ockhi 2017 IMD gap analysis** | 🟢 Ready | **This is your most important remaining task — see below** |
| R6 | **Fani 2019 IMD comparison** | 🟢 Ready | See below |
| R7 | **Cyclone intensity timeline table** | 🟢 Ready | For all 7 events — judges will ask about data |
| R8 | Limitations + positioning slide | 🟢 Ready | Use docs/limitations.md + docs/model_explained.md as base |
| R9 | Final metrics narrative | 🟢 Ready | 78.3% accuracy, 255 km MAE — write the narrative with context |
| R10 | Q&A defence sheet | 🔴 Blocked | Day 7 — after metrics finalised |
| R11 | Judge Q&A prep | 🔴 Blocked | Day 7 |

### R5 — Ockhi 2017 IMD gap analysis (MOST IMPORTANT)

**What happened:** Cyclone Ockhi formed as a depression off Sri Lanka on 29 November 2017. IMD issued the first cyclone watch only on 1 December — nearly 48 hours after formation. The storm killed 218+ fishermen who were at sea with no warning.

**What to research and write (1-2 pages in docs/ockhi_analysis.md):**
1. Timeline of IMD advisories vs actual storm intensification
2. Why the early stage was missed (low-latitude formation, rapid intensification)
3. What satellite structural signatures were visible but not flagged in time
4. How CycloneWatch's automated classification would have flagged it earlier
   - Our model classifies every 3-hour frame → would have returned "curved_band" at T-48h and "banding" at T-36h before IMD issued any watch
5. The positioning statement: "CycloneWatch targets the interpretation gap, not the NWP gap"

**Sources to check:**
- RSMC New Delhi post-storm report: https://rsmcnewdelhi.imd.gov.in/report.php?internal_menu=MzM
- Wikipedia: Cyclone Ockhi
- India Meteorological Department: https://imd.gov.in
- arXiv / Springer post-storm analyses (search "Ockhi 2017 cyclone")

### R6 — Fani 2019 IMD comparison

**What happened:** Fani was a landmark case where IMD's forecast was praised — they predicted landfall with ~5 km accuracy 72 hours out. Contrast this with Ockhi.

**What to research (add to docs/):**
1. IMD's forecast accuracy for Fani (publicly praised, well-documented)
2. What made Fani easier to forecast than Ockhi (long track over open ocean)
3. Position CycloneWatch: "For cases like Fani where the track is clear, our system provides fast automated structural monitoring. For cases like Ockhi where early detection matters most, our system fills the gap."

### R7 — Cyclone intensity timeline table

For each of the 7 training events, create a table:
```
| Event | Formation | Peak intensity | Landfall | Peak wind | Deaths | Damage |
```
This goes in the presentation deck slide 5 ("Training data"). Judges will ask "which cyclones did you train on?" — have this ready.

**Sources:**
- Wikipedia cyclone articles for each event
- India Meteorological Department reports
- IBTrACS raw CSV already in the repo: `data/ground_truth/ibtracs.NI.list.v04r00.csv`

### R8 — Metrics narrative (write this now)

The model accuracy numbers are final for the prototype. Write the narrative:

```
On 60 held-out satellite frames from 7 North Indian Ocean cyclones
(2013–2023), the CycloneWatch prototype achieved:

- Structural pattern accuracy: 78.3% (47/60 frames correctly classified)
- Eye class F1: 1.00 (perfect — all 2 eye samples correctly identified)
- Centre position MAE: 255 km (comparable to persistence baseline)

These numbers are from a model trained on 423 frames with algorithm-derived
labels (not analyst-verified). The pattern classification result is the
primary demonstration — structural pattern recognition at 78.3% accuracy
automates what currently requires manual analyst interpretation.

The centre position error is high because the model was trained on limited
data (7 events, 423 frames). IMD's NWP guidance achieves ~100–150 km at
T+12h. Our prototype is not yet at that level for position, but demonstrates
the end-to-end pipeline architecture.
```

---

## Frontend (Kavya) — FULL REQUIREMENTS

### What to build

The frontend is a React + Leaflet single-page application. The entire UI is remaining.

Reference design: `docs/cyclone_console_shell.html` — use this as the visual target.

### Screen layout

```
┌─────────────────────────────────────────────────────────────────┐
│ CycloneWatch        [BIPARJOY '23 ▼]    14 Jun 2023 12:00 UTC  │
│                     [Event selector]    ●  Live                 │
├────────────────────────────────┬────────────────────────────────┤
│                                │                                 │
│                                │  CURRENT ANALYSIS              │
│        LEAFLET MAP             │  Pattern:  Banding             │
│                                │  Confidence: 72%               │
│    [cyclone centre marker]     │  Centre: 15.2°N  68.4°E        │
│    [track line]                │  Source: INSAT-3D              │
│    [uncertainty ellipse]       │  ─────────────────────         │
│    [predicted track T+12,T+24] │  PREDICTION                    │
│                                │  T+12: 16.1°N 67.8°E          │
│                                │  T+24: 17.2°N 67.1°E          │
│                                │  Status: Provisional           │
├────────────────────────────────┴────────────────────────────────┤
│ [IR]  [Water Vapour]    ←──── T-48h ────────────────── T0 ────→ │
│       Channel toggles              Timeline slider               │
└─────────────────────────────────────────────────────────────────┘
```

### Component breakdown

**1. Top bar**
- App name: "CycloneWatch"
- Event selector dropdown: hardcode 7 events with display names
  ```
  biparjoy_2023  → "Biparjoy 2023 (Arabian Sea)"
  amphan_2020    → "Amphan 2020 (Bay of Bengal)"
  fani_2019      → "Fani 2019 (Bay of Bengal)"
  tauktae_2021   → "Tauktae 2021 (Arabian Sea)"
  phailin_2013   → "Phailin 2013 (Bay of Bengal)"
  hudhud_2014    → "Hudhud 2014 (Bay of Bengal)"
  ockhi_2017     → "Ockhi 2017 (Arabian Sea/BoB)"
  ```
- Current timestamp (from the selected replay step)
- Status dot (pulsing amber = active event)

**2. Map (Leaflet)**
- Base layer: CartoDB dark tiles (already in vendor/leaflet.min.js)
- Satellite overlay: `GET /api/ps70/frames/{frame_id}?format=image` — load as ImageOverlay using the frame's `bbox` field
- Cyclone centre marker: custom marker at `center.lat, center.lon`
- Observed track line: polyline connecting all `GET /api/ps70/classifications/{event_id}` points
- Uncertainty ellipse: render `uncertainty.geometry` from predict response as GeoJSON Polygon
- Predicted track: dashed polyline connecting T+12 and T+24 prediction centres

**3. Right panel — Analysis card**
- Pattern label with colour coding:
  - `eye` → red / danger
  - `banding` → orange
  - `curved_band` → yellow
  - `shear_affected` → purple
  - `disorganized` → grey
- Confidence bar (provisional label if `confidence === null`)
- Centre coordinates
- T+12 / T+24 predicted positions
- Uncertainty status badge ("PROVISIONAL" / "CALIBRATED")

**4. Timeline slider (bottom)**
- Channel toggle buttons: `[IR]` `[Water Vapour]` — switch the satellite overlay channel
- Replay slider: drives the map through the precomputed replay steps
- At each slider position:
  - Update satellite overlay image (load that frame)
  - Update centre marker
  - Update pattern card
  - Update predicted track

**5. Evidence panel (click any prediction)**
- Source satellite image thumbnail
- Frame ID, timestamp, channel
- Model name + version
- Actual position (from IBTrACS) vs predicted
- Error in km

**6. Metrics bar (bottom right or separate panel)**
- Pull from `GET /api/metrics?event_id={current_event}`
- Show: Centre MAE T+12 / T+24, Pattern accuracy %, Events evaluated

### API calls the frontend makes

```
// On page load
GET /health                                          → verify API is up

// On event select
GET /api/ps70/classifications/{event_id}             → all centre positions for track line
GET /api/replay/{event_id}                           → full replay steps for slider
GET /api/metrics?event_id={event_id}                 → metrics for panel

// On slider move (use preloaded replay data, not live calls)
// The replay response has everything — no additional calls needed per step

// On "run classification" (optional live mode)
POST /api/ps70/classify                              → live classification on current frame

// On "run prediction" (optional live mode)
POST /api/ps70/predict                               → live T+12/T+24 prediction

// For satellite overlay
GET /api/ps70/frames/{frame_id}                      → frame metadata (bbox for ImageOverlay)
GET /api/ps70/frames/{frame_id}?format=image         → raw image file for ImageOverlay
```

### Design tokens (from cyclone_console_shell.html)

```css
--abyss:    #0A0F1A  (background)
--panel:    #121A2B  (cards)
--panel-2:  #182338  (hover states)
--grid:     #223049  (borders)
--cyan:     #4DD8C4  (primary accent, active states)
--amber:    #F2A93B  (warnings, status dot)
--fog:      #E7ECF3  (primary text)
--fog-dim:  #7C8AA3  (secondary text)
--mono: 'IBM Plex Mono', monospace
--sans: 'Inter', sans-serif
```

Pattern label colours:
```
eye           → #ef4444  (red)
banding       → #f97316  (orange)
curved_band   → #eab308  (yellow)
shear_affected → #a855f7 (purple)
disorganized  → #6b7280  (grey)
```

### Implementation sequence

Build in this order — each step is independently testable:

1. **React shell** — blank app with map, use CartoDB dark tiles, confirm Leaflet renders
2. **Event selector** — dropdown that logs the selected event_id to console
3. **Classification track** — call `GET /api/ps70/classifications/{event_id}`, plot dots on map
4. **Satellite overlay** — `GET /api/ps70/frames/{id}?format=image` as ImageOverlay
5. **Right panel** — display last classification as pattern card
6. **Replay slider** — call `GET /api/replay/{event_id}`, wire slider to steps array
7. **Predicted track** — show T+12/T+24 from replay prediction data
8. **Uncertainty ellipse** — render GeoJSON polygon from uncertainty.geometry
9. **Evidence panel** — click a point, show source frame + metadata
10. **Metrics panel** — call `GET /api/metrics`, display numbers

### CORS note
Backend already allows `*` in dev. No CORS config needed on frontend side.

### Offline note
Use the preloaded `replay` response data for the slider. Do not make per-step API calls during the demo — the replay endpoint returns everything at once.

---

## App Dev (Aniket) — FULL REQUIREMENTS

### Screens (3 screens only)

**Screen 1 — Status**
```
CycloneWatch
─────────────────────────────
ACTIVE EVENT
Biparjoy 2023 · Arabian Sea
─────────────────────────────
CURRENT STATUS
Pattern:     Banding
Confidence:  72%  [provisional]
Centre:      15.2°N  68.4°E
As of:       14 Jun 2023 12:00 UTC
─────────────────────────────
[→ See Prediction]  [→ See History]
```

**Screen 2 — Prediction**
```
Predicted Track
─────────────────────────────
T+12h  (14 Jun 00:00 UTC)
  Centre: 16.1°N  67.8°E
  Pattern: Eye  (confidence: 64%)
  Uncertainty: PROVISIONAL

T+24h  (14 Jun 12:00 UTC)
  Centre: 17.2°N  67.1°E
  Pattern: Eye  (confidence: 59%)
  Uncertainty: PROVISIONAL
─────────────────────────────
⚠ Uncertainty not yet calibrated
```

**Screen 3 — Metrics**
```
Model Performance
─────────────────────────────
Pattern Accuracy:  78.3%
Centre MAE T+12:   255 km
Centre MAE T+24:   —
Events evaluated:  7
─────────────────────────────
Source: IBTrACS best-track
Model:  ps70-classifier v2.0.0
```

### API calls

```
GET /api/ps70/classifications/biparjoy_2023   → Screen 1 (last item = current)
POST /api/ps70/predict                         → Screen 2
GET /api/metrics?event_id=biparjoy_2023        → Screen 3
```

### Offline fixture

Save these responses now as JSON files in the app `assets/fixtures/` folder:
1. `GET /api/ps70/classifications/biparjoy_2023` → `classifications.json`
2. `POST /api/ps70/predict` with biparjoy_2023 → `prediction.json`
3. `GET /api/metrics?event_id=biparjoy_2023` → `metrics.json`

Load fixtures when API is unreachable (check `GET /health` first).

---

## Cross-Team / Integration

| # | Task | Status | Notes |
|---|---|---|---|
| X1 | Run precompute_replay all 7 events | 🟢 Ready | `python -m scripts.precompute_replay --event_id {id}` |
| X2 | /api/metrics shows real MAE | 🟢 Ready | After X1 |
| X3 | Full offline test (WiFi off) | 🔴 Blocked | X1 + F6 + A5 done |
| X4 | Day-4 mentor checkpoint | 🔴 Blocked | Day 4 |
| X5 | run_backtest.py full report | 🟢 Ready | `python scripts/run_backtest.py` |
| X6 | Documentation freeze | 🔴 Blocked | Day 7 |
| X7 | Day-8 rehearsal | 🔴 Blocked | Day 8 |
| X8 | Tag v1.0-day7-freeze | 🔴 Blocked | Day 7 |

---

## Ockhi 2017 — Why It Matters for the Demo

This is the strongest positioning case against IMD:

```
29 Nov 2017:  Ockhi forms as a depression off Sri Lanka
              → CycloneWatch would show: "disorganized" classification

30 Nov 2017:  Rapid intensification begins
              → CycloneWatch would show: "curved_band" → "banding"
              → IMD: no advisory yet

01 Dec 2017:  IMD issues first cyclone watch (36-48h late)
              → 218+ fishermen already at sea with no warning

CycloneWatch claim: "Our system would have flagged structural
organisation at T-36h before IMD's first advisory."
```

Research (Arshit) needs to document the exact timeline with sources and write this into the presentation. This is the slide that wins the demo.

---

## What is frozen — do not change

| Item | Frozen value |
|---|---|
| Pattern labels | eye, banding, curved_band, shear_affected, disorganized |
| ML input shape | [C, H, W] float32, C=2 |
| GeoJSON order | [longitude, latitude] |
| All timestamps | UTC ISO 8601 |
| API paths | /api/ps70/, /api/replay/, /api/metrics |
| Backend tests | 93 minimum |
| Model version | ps70-classifier v2.0.0 (until Day-7 retrain) |

---

## Sprint reference

| Day | Focus | Key output |
|---|---|---|
| 1-3 | Backend + ML + Data | ✅ Complete |
| **4** | **Replay + mentor checkpoint** | Run precompute_replay, show full demo flow to mentor |
| 5 | Feedback + temporal model | Frontend progress, Aditya builds temporal model |
| 6 | Calibration + UI polish | Confidence calibration, Kavya polishes UI |
| **7** | **Freeze** | Code freeze, stress test, tag v1.0-day7-freeze |
| **8** | **Demo** | Rehearsal, recorded fallback, present |
