# CycloneWatch — Pending Work Tracker

> **Last updated:** 2026-09-01 → updated 2026-09-02 after ML repo integration  
> **Sprint:** SIH 2026 PS70 — 8-Day  
> **Lead:** Satyam Srivastava  
>
> This file tracks every piece of work that is not yet done across all teams.  
> Update it when a task is completed. Do not delete rows — change status to ✅ Done.

---

## Status Key

| Symbol | Meaning |
|---|---|
| 🔴 Blocked | Cannot start — waiting on another team's deliverable |
| 🟡 In Progress | Someone is actively working on it |
| 🟢 Ready | Can be started right now, no blocker |
| ✅ Done | Complete and merged |

---

## Backend (Satyam)

| # | Task | Status | Blocked on | Notes |
|---|---|---|---|---|
| B1 | FastAPI + PostGIS + Docker setup | ✅ Done | — | 93/93 tests passing |
| B2 | All 6 API endpoints | ✅ Done | — | classify, predict, replay, metrics, frames, health |
| B3 | ML adapter (stub + real switchover) | ✅ Done | — | Auto-detects ml.inference, falls back to stub |
| B4 | Seed script + precompute replay script | ✅ Done | — | scripts/seed_db.py, scripts/precompute_replay.py |
| B5 | Wire calibrated uncertainty | 🔴 Blocked | ML Day-6 calibration | ~1h work once ML delivers real sigma values |
| B6 | Load Research ground-truth labels | 🔴 Blocked | Research label CSV | ~1h — run scripts/load_ground_truth.py once CSV arrives |
| B7 | Register real satellite frames in DB | 🟢 Ready | — | data/normalized/ now committed (122 frames). Update seed_db.py with real npz paths, ~1h |
| B8 | Satellite XYZ tile serving (if needed) | 🔴 Blocked | Frontend confirms Leaflet format | ~2-3h only if raw GeoTIFF won't work in Leaflet |
| B9 | Second event (Amphan) support | 🟢 Ready | — | Amphan frames in data/normalized/. Register in DB, ~30 min |
| B10 | Baseline MAE wiring in /api/metrics | 🔴 Blocked | ML persistence baseline numbers | ~30 min once ML provides baseline MAE values |
| B11 | scripts/load_ground_truth.py | 🟢 Ready | — | Small script to load Research label CSV into metrics table |
| B12 | Day-7 API freeze + stress test | 🔴 Blocked | All other teams done | Full stress test + git tag v1.0-day7-freeze |

---

## ML (Aditya)

| # | Task | Status | Blocked on | Notes |
|---|---|---|---|---|
| M1 | PyTorch environment + dataloader | ✅ Done | — | ml/src/dataset.py committed, CycloneDataset loads real npz frames |
| M2 | Day-1 classification stub JSON | ✅ Done | — | Backend stub active; ml/inference.py also functional in stub fallback |
| M3 | CNN classification model (centre + pattern + confidence) | 🟡 In Progress | — | Centre head trained ✅ — model.pt committed. Pattern + confidence heads pending Research labels |
| M4 | Temporal prediction model T+12/T+24 | 🟡 In Progress | M3 | Provisional persistence fallback active in inference.py. Real temporal model still needed |
| M5 | **Deliver ml/inference.py** | 🟡 In Progress | M3 pattern head | ml/inference.py committed ✅. predict_frame() + predict_sequence() both working. Pattern returns "unlabeled" until retrained |
| M6 | Confidence calibration (Day 6) | 🔴 Blocked | M3 pattern head trained | Provide real sigma_lat, sigma_lon + flip predict_confidence=True |
| M7 | Baseline persistence model + MAE | 🟡 In Progress | — | predict_sequence() uses persistence fallback — this IS the baseline. Measure its MAE via /api/metrics |
| M8 | Known limitations document | 🟢 Ready | — | ml/README.md has known limitations section. Expand into docs/limitations.md |
| M9 | Model manifest (freeze Day 7) | 🟢 Ready | — | ml/configs/model_config.json created. Finalise on Day 7 |
| M10 | Freeze models | 🔴 Blocked | Day 7 | No training changes after this point |

**ML contract status: ✅ DONE**
```
ml/inference.py is committed and exports:
  predict_frame(frame: np.ndarray)     # shape [C, H, W]  ← WORKING
  predict_sequence(seq: np.ndarray)    # shape [T, C, H, W] ← WORKING (provisional)

Current centre prediction: REAL (model.pt loaded)
Current pattern: "unlabeled" until retrained with Research labels
Current temporal: persistence fallback — replace with real model on Day 3
```

---

## Data (Abhinav)

| # | Task | Status | Blocked on | Notes |
|---|---|---|---|---|
| D1 | IBTrACS NI raw CSV | ✅ Done | — | data/ground_truth/ibtracs.NI.list.v04r00.csv committed |
| D2 | split_ibtracs.py — per-event best-track CSVs | ✅ Done | — | biparjoy_2023_best_track.csv + amphan_2020_best_track.csv generated |
| D3 | aws_downloader.py — GridSat-B1 download | ✅ Done | — | scripts/aws_downloader.py committed, run locally |
| D4 | standardize_data.py — NetCDF → [C,H,W] npz | ✅ Done | D3 | scripts/standardize_data.py committed |
| D5 | validate_and_join.py — ground-truth join | ✅ Done | D4, D2 | scripts/validate_and_join.py committed |
| D6 | **Download Biparjoy satellite data** | ✅ Done | — | 88 frames in data/normalized/biparjoy_2023/frames/ (GridSat-B1, IR+WV) |
| D7 | **Run standardize_data.py → normalized npz frames** | ✅ Done | — | 122 total frames committed (biparjoy: 88, amphan: 34), shape [2,H,W] |
| D8 | Register real frames in backend DB | 🟢 Ready | — | Frames exist. Update backend/scripts/seed_db.py with real npz paths, coordinate with Satyam |
| D9 | Download Amphan satellite data | ✅ Done | — | 34 frames in data/normalized/amphan_2020/frames/ |
| D10 | Expanded event set (beyond Biparjoy + Amphan) | 🔴 Blocked | D6-D7 complete first | ✅ Primary events done. Expand only if time permits after Day-4 checkpoint |
| D11 | Validation report | ✅ Done | — | data/training_manifest.csv committed (122 rows, all PASS, centre positions joined) |
| D12 | Ground-truth visible data (if available) | 🟢 Ready | — | Include if aligned visible channel exists; never show wrong band as visible |

---

## Research (Arshit)

| # | Task | Status | Blocked on | Notes |
|---|---|---|---|---|
| R1 | Lock 2 historical events (Biparjoy + Amphan) | ✅ Done | — | events.csv, IBTrACS pulled |
| R2 | IBTrACS best-track data | ✅ Done | — | Per-event CSVs generated |
| R3 | Pattern taxonomy draft | 🟡 In Progress | — | Labels: eye, banding, curved_band, shear_affected, disorganized |
| R4 | **Finalise + lock pattern label set** | 🟢 Ready | R3 | MUST be done before ML trains. Labels are frozen in backend DB. |
| R5 | Ground-truth manual labels CSV | 🔴 Blocked | R4 locked, Data frames available | Format: event_id, frame_id, ground_truth_label |
| R6 | MoES/IMD gap analysis notes | 🟡 In Progress | — | Evidence-based only — no fabricated claims |
| R7 | Limitations + positioning slide text | 🔴 Blocked | Day 5 | One paragraph per the master README |
| R8 | Final metrics narrative | 🔴 Blocked | Backend metrics populated | Needs real MAE numbers from /api/metrics |
| R9 | Q&A defence sheet | 🔴 Blocked | Day 7 | Use judge Q&A section in master README as starting point |
| R10 | Cyclone dossier (Biparjoy + Amphan) | ✅ Done | — | docs/cyclone_dossier.html committed |

**Label set currently in backend (locked until further notice):**
```
eye | banding | curved_band | shear_affected | disorganized
```
Any change requires coordinating with Satyam for a DB migration.

---

## Frontend (Kavya)

| # | Task | Status | Blocked on | Notes |
|---|---|---|---|---|
| F1 | Design tokens | 🟡 In Progress | — | docs/cyclone_console_shell.html is the reference shell |
| F2 | React + Leaflet shell | 🟡 In Progress | — | Start calling backend API now — stub responses are live |
| F3 | IR / Visible / WV layer toggles | 🟡 In Progress | F2 | Do not show a channel that has no real data |
| F4 | Classification marker + pattern card | 🔴 Blocked | F2, Backend running | POST /api/ps70/classify → render centre marker |
| F5 | Predicted track + timeline | 🔴 Blocked | F4 | POST /api/ps70/predict → render T+12/T+24 + uncertainty cone |
| F6 | Historical replay slider | 🔴 Blocked | F5, precompute_replay run | GET /api/replay/{event_id} → slider T-48h → T0 |
| F7 | Level-3 evidence panel | 🔴 Blocked | F6 | Click prediction → show source image + model metadata |
| F8 | Metrics display | 🔴 Blocked | Backend metrics populated | GET /api/metrics → MAE + accuracy panel |
| F9 | Confirm Leaflet tile format with Satyam | 🟢 Ready | — | Raw GeoTIFF via ?format=image OR request XYZ tile endpoint — decide by Day 3 |
| F10 | Day-6 visual polish | 🔴 Blocked | F7 complete | Spacing, typography, loading states, error states |
| F11 | UI freeze | 🔴 Blocked | Day 7 | Bug fixes only after this |

---

## App Dev (Aniket)

| # | Task | Status | Blocked on | Notes |
|---|---|---|---|---|
| A1 | Project skeleton (runs on demo device) | 🟡 In Progress | — | |
| A2 | Static screen shells | 🟡 In Progress | — | Home, Status, Alert, Prediction |
| A3 | /classify endpoint integration | 🔴 Blocked | A1, Backend running | GET /api/ps70/classifications/biparjoy_2023 → last item = current status |
| A4 | Prediction + alert display | 🔴 Blocked | A3 | POST /api/ps70/predict → T+12/T+24 |
| A5 | Offline fixture bundle | 🟢 Ready | — | Save API responses as JSON fixtures now — works with stub data |
| A6 | Offline fallback toggle | 🔴 Blocked | A3, A4 | If API unreachable → serve from fixture files |
| A7 | Tested on actual demo device | 🔴 Blocked | A3-A6 | Must test on the real device, not just emulator |
| A8 | Visual identity matched to design tokens | 🔴 Blocked | F1 tokens finalised | Coordinate with Kavya |
| A9 | App freeze | 🔴 Blocked | Day 7 | |

---

## Cross-Team / Integration

| # | Task | Status | Blocked on | Notes |
|---|---|---|---|---|
| X1 | Run precompute_replay.py with real data | 🟡 In Progress | R5 (ground-truth labels) | M5 ✅ D7 ✅ — only blocked on Research label CSV now. Run once R5 arrives |
| X2 | Verify /api/metrics shows real numbers | 🔴 Blocked | X1 | mae_km_t12/t24 must be non-null floats |
| X3 | Full offline demo test (internet off) | 🔴 Blocked | X1, F6, A5 | Disable WiFi, verify every endpoint responds |
| X4 | Day-4 mentor checkpoint demo | 🔴 Blocked | Day 4 | Bring: satellite frame, classification, prediction, replay, evidence panel, measured error |
| X5 | Full backtest (run_backtest.py) | 🔴 Blocked | M9 frozen | python scripts/run_backtest.py |
| X6 | Final documentation freeze | 🔴 Blocked | Day 7 | README, api_contract, model_card, limitations, metrics, Q&A |
| X7 | Day-8 full rehearsal | 🔴 Blocked | Day 8 | Complete demo flow, recorded fallback ready |
| X8 | Tag release v1.0-day7-freeze | 🔴 Blocked | All frozen | git tag v1.0-day7-freeze && git push origin v1.0-day7-freeze |

---

## Immediate Actions (Do These Today)

| Priority | Who | Action |
|---|---|---|
| 🔥 1 | Arshit (Research) | **Finalise + send pattern label CSV** — this is now the single biggest blocker. ML cannot train pattern head, backend accuracy metric stays null, precompute_replay produces no labels without it |
| 🔥 2 | Satyam (Backend) | **Register real frames in DB** — run `python -m scripts.seed_db --reset` after updating seed_db.py with real npz paths from data/normalized/ |
| 🔥 3 | Satyam (Backend) | **Create scripts/load_ground_truth.py** — small script ready to run the moment Research delivers labels |
| 🔥 4 | Kavya (Frontend) | **Confirm Leaflet tile format** — raw GeoTIFF or XYZ tiles? Decide by Day 3 or the tile endpoint can't be built in time |
| 🔥 5 | Aditya (ML) | **Retrain with pattern labels** the moment Research delivers the CSV — set PREDICT_PATTERN=True and run `python -m ml.src.train` |
| 🔥 6 | Aniket (App) | **Save stub API responses as offline fixtures** — backend API is live right now, do this today |

---

## What Is Frozen (Do Not Change)

These are locked. Any change requires a DB migration + team-wide announcement:

| Item | Frozen value |
|---|---|
| Pattern labels | `eye`, `banding`, `curved_band`, `shear_affected`, `disorganized` |
| ML input shape (single frame) | `[C, H, W]` float32 |
| ML input shape (sequence) | `[T, C, H, W]` float32 |
| GeoJSON coordinate order | `[longitude, latitude]` |
| All timestamps | UTC ISO 8601 with Z |
| Uncertainty before calibration | `"provisional"` — never claim a % |
| Replay endpoint | Reads DB only — never calls ML |
| API base paths | `/api/ps70/`, `/api/replay/`, `/api/metrics` |
| Backend test count | 93 minimum — must not regress |

---

## Sprint Timeline Reference

| Day | Focus | Key deliverable |
|---|---|---|
| 1 | Foundation | Connected pipeline: satellite → classification → map |
| 2 | Classification | CNN model + /classify endpoint live |
| 3 | Prediction | Temporal model + /predict + uncertainty polygon |
| **4** | **Replay + checkpoint** | **/api/replay live + mentor demo** |
| 5 | Feedback | Fix mentor-identified issues |
| 6 | Uncertainty + polish | Calibrated confidence + UI polish + /api/metrics |
| **7** | **Freeze** | **All features frozen, stress test, tag release** |
| **8** | **Demo** | **Rehearsal, fallback verified, present** |
