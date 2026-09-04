# CycloneWatch Dashboard: Every Metric Explained

> This document is the definitive reference for every number, label, and indicator shown on the CycloneWatch dashboard — what it means, why it might be high or low, and how it can be improved. Designed for judges, non-technical stakeholders, and anyone demoing the system.

---

## HISTORICAL MODE: Classification Inference Panel

### Pattern Label
**Example values:** `EYE`, `BANDING`, `CURVED BAND`, `SHEAR AFFECTED`, `DISORGANIZED`

The AI's structural assessment of the cyclone in the current satellite frame. This is the primary output of the `ps70-classifier` model.

**Why does it say "DISORGANIZED" at the start of every cyclone?**
Every cyclone begins as a disorganized depression. The cloud structure is genuinely scattered — no spiral, no banding, no coherent centre. As you scrub the timeline forward, you will watch this label evolve in real time, mirroring the actual storm's lifecycle.

**Reference:** [Pattern Taxonomy](taxonomy.md) — full definitions with visual descriptions for each of the 5 labels.

---

### Confidence %
**Example values:** `87.4%`, `< 5.0%`, `43.2%`

The model's raw softmax probability for the predicted pattern class. Mathematically, it is the highest value across the 5 output neurons after the final softmax activation.

**Interpretation guide:**
| Confidence Range | What It Means |
|---|---|
| `> 80%` | High — strong, unambiguous structural signature in the satellite image |
| `40–80%` | Moderate — clear structure present but some ambiguity (e.g., transitioning between phases) |
| `< 20%` | Low — disorganized or transitioning state, model is uncertain |
| `< 5%` | Very low — shown as `< 5.0%` on the dashboard to avoid the appearance of "0%" being a bug |

**Important caveat:** The confidence percentages are **not calibrated**. A raw softmax output of `75%` does not statistically mean the model is correct 75% of the time. It only means the model is relatively more certain than if it output `30%`. Confidence calibration (via temperature scaling) is a planned next step — after calibration, `75%` would be a meaningful probabilistic statement.

**When the confidence is 0% or "< 5%":**
This is completely expected during early depression stages and late dissipation stages. The satellite image genuinely shows no clear pattern — the AI is honestly reporting its uncertainty, not malfunctioning.

---

### Center Lat / Center Lon
**Example:** `14.82°N`, `68.45°E`

The AI model's prediction of the cyclone's geographic center at this timestamp. Derived from the `fc_center` head of the CycloneCNN — a 2-neuron output layer that regresses directly to (latitude, longitude).

**How accurate is it?**
On average: **~255 km off** from the real IBTrACS best-track position. See the "Avg MAE" metrics below for the aggregated error for each event. Individual steps vary widely — some frames are within 50 km, others may be 500 km off, depending on how clear the cloud structure is in that particular image.

---

### Model
**Value:** `ps70-classifier`

The name and version of the ML model that produced this prediction. The `ps70` prefix refers to Problem Statement 70 — the SIH 2026 problem statement this project addresses.

---

### Frame ID
**Example:** `biparjoy_2023...` (truncated to 16 chars on display)

The internal database identifier for the satellite frame used to generate this classification. Each frame maps to a specific 3-hourly GridSat-B1 satellite observation. The full ID is visible in the `title` tooltip on hover.

---

### Timestamp
**Example:** `2023-06-10 12:00:00 UTC`

The UTC time of the satellite observation. All timestamps in CycloneWatch are in UTC (Coordinated Universal Time), which is 5 hours 30 minutes behind IST (Indian Standard Time).

---

## HISTORICAL MODE: Temporal Prediction Panel

### T+12 Forecast Error (km)
**Example values:** `120.4 km` (amber), `48.2 km` (white), `N/A`

The Haversine distance in kilometers between where the model predicted the cyclone centre would be **12 hours after the current frame's timestamp**, and where it actually was according to the IBTrACS best-track record.

**Color coding:**
- White: Error ≤ 100 km — good for a prototype
- Amber: Error > 100 km — expected at this stage
- `N/A`: No ground-truth position available for T+12 from this step (e.g., at the end of the event timeline)

**Why is T+12 sometimes higher than T+24?**
This seems counterintuitive, but it happens because the T+12 and T+24 predictions are independent — they don't feed into each other. If the model happens to make a correct spatial guess at the T+24 position but a poor one at T+12, the T+24 error will be lower. This is a sign that the current temporal model (which uses persistence + linear extrapolation) is not physically modeled properly. A trained ConvLSTM/GRU would eliminate this inconsistency.

**What does "Haversine" mean?**
It is the mathematically correct formula for measuring distance between two GPS coordinates on the surface of a sphere (the Earth). Unlike flat-Earth distance formulas, it accounts for the curvature of the Earth and gives accurate results even for distances of hundreds of kilometers.

---

### T+24 Forecast Error (km)
**Example values:** `234.5 km` (alert red), `150.2 km` (amber), `N/A`

Same as T+12 but measuring the prediction for **24 hours ahead**.

**Color coding:**
- White: ≤ 100 km
- Alert red: > 200 km — significant error, expected given current model maturity
- `N/A`: No ground-truth data available for T+24 from this step

**Why is T+24 typically higher than T+12?**
Forecasting further into the future is inherently less certain. Small errors in the starting position and velocity compound over 12 more hours. This is true for all forecasting systems — IMD's NWP models also have higher T+24 errors than T+12.

---

## HISTORICAL MODE: Event Evaluation Metrics Panel

### Avg MAE (T+12) — km
**Typical values:** `180–300 km`

The **Mean Absolute Error** averaged across all timesteps in the selected event, measuring T+12h prediction accuracy. This is the single most important performance metric for tracking quality.

#### Why is MAE High? (The Honest Breakdown)

Our T+12/T+24 MAE (~200–280 km depending on the event) is high for three compounding reasons:

**Reason 1: Tiny training dataset (most impactful)**
We trained on 423 satellite frames from 7 cyclones. State-of-the-art tropical cyclone prediction models are trained on tens of thousands of frames spanning decades. At 423 frames, the model does not have enough examples to learn nuanced position regression — it learns the general region of where cyclones are, but not precise centers.

**Reason 2: Coarse satellite resolution (4 km/pixel)**
GridSat-B1 images are blurry by modern standards. The storm's eye — which anchors the centre estimate — may span only 10–20 pixels in a 4 km/pixel image. Features that a meteorologist would use to refine the centre estimate (inner eyewall structure, feeder band geometry) are invisible at this resolution.

**Reason 3: Persistence-based temporal forecasting**
The current T+12/T+24 predictions are generated by **linear extrapolation** — the model takes the current position and velocity and projects them forward in a straight line. Real cyclones curve, accelerate, and decelerate unpredictably. A physics-informed or trained temporal model would account for this; our current one does not.

#### How Can MAE Be Improved?

| Improvement | Expected Impact | Effort |
|---|---|---|
| MOSDAC/INSAT-3DR data (1 km resolution) | T+12 MAE → ~150 km | High (pending data access) |
| 10x more training data (50+ events) | T+12 MAE → ~120–150 km | Medium (download + processing) |
| Trained ConvLSTM temporal model | T+24 MAE → ~100–130 km | Medium (architecture ready) |
| All three combined | T+24 MAE → <100 km (operational range) | Phase 2 roadmap |

**Context: Is 200–280 km "bad"?**
For comparison:
- Simple persistence baseline ("storm stays where it was"): ~200–300 km at T+12h
- IMD's operational NWP at T+12h: ~100–150 km
- Our model at T+12h: ~180–260 km

We are currently at the persistence baseline level — we know roughly where the storm is but don't add meaningful predictive signal beyond "it will be near where it was." The 78.3% pattern classification is the more impressive result for this prototype stage.

---

### Avg MAE (T+24) — km
**Typical values:** `240–400 km`

Same calculation as T+12 MAE but for the 24-hour forecast. Always higher than T+12 MAE because more time means more compounding error. The gap between T+12 and T+24 MAE is an indicator of how well the temporal extrapolation performs — a smaller gap would indicate the model is "catching up" with the storm's actual trajectory over time.

---

### Classification Accuracy — %
**Example values:** `78.3%`, `N/A`

The fraction of frames in this event where the model's pattern label matched the ground-truth label derived from IBTrACS wind speed rules.

**Why does it show "N/A" for some events?**
Classification accuracy requires ground-truth pattern labels. Labels are computed from IBTrACS wind speed thresholds at the time of training. If an event's labels were not fully joined to the prediction records in the database (due to timestamp mismatches or missing ground-truth CSV files), the accuracy field returns `null` and displays as `N/A`. This does not mean the model is not classifying — it means the automatic comparison against the answer key was not completed for that event.

**Is 78.3% good?**
Yes, it is strong for a prototype. A human meteorologist reviewing IR satellite images agrees with the IBTrACS-derived "correct answer" approximately 80% of the time (the labels themselves are not perfect — they are algorithmic, not hand-drawn). So our model is approaching human-level agreement on the same imperfect labels it was trained on.

---

### Sample Size — frames
**Example values:** `60`, `0`

The number of frames in this event that had valid ground-truth labels and were used to compute the Classification Accuracy and MAE values shown.

**If Sample Size shows `0`:** No ground-truth data was available for this event in the database. The replay and classification still work — only the accuracy comparison metric is unavailable.

---

## HISTORICAL MODE: Storm Identity Panel

### Peak Wind — km/h
**Example:** `185 km/h`

The maximum sustained 1-minute wind speed recorded during the cyclone's entire lifetime, from the IBTrACS historical record. This is the official peak intensity of the storm. Sourced from `cyclones.ts` static metadata.

**IMD Intensity Classification:**
| Wind Speed | IMD Classification |
|---|---|
| < 63 km/h | Depression / Deep Depression |
| 63–88 km/h | Cyclonic Storm |
| 89–117 km/h | Severe Cyclonic Storm |
| 118–167 km/h | Very Severe Cyclonic Storm |
| 168–221 km/h | Extremely Severe Cyclonic Storm |
| > 221 km/h | Super Cyclonic Storm |

---

### Min Pressure — hPa
**Example:** `958 hPa`

The minimum central pressure recorded during the storm's lifetime (IBTrACS). Pressure and wind speed are inversely related — the lower the pressure, the stronger the storm. Standard sea-level pressure is ~1013 hPa. A reading of 900 hPa indicates an extraordinarily intense storm.

---

### Landfall Time & Region
The official date/time (UTC) and geographic location where the cyclone's eye made landfall (crossed the coastline). Sourced from static historical records.

---

## LIVE MODE: Atmosphere Panel

All live mode data is sourced from [Open-Meteo](https://open-meteo.com) — a free, open-source meteorological API providing real-time observations derived from ECMWF and GFS model outputs.

### Wind Speed — km/h
Current surface wind speed at the selected basin's representative monitoring point (Bay of Bengal: ~13°N 82°E; Arabian Sea: ~16°N 68°E). Orange coloring indicates wind speed exceeds the BASELINES threshold (65 km/h — Cyclonic Storm threshold).

### Wind Direction — °
Meteorological wind direction in degrees from North (0° = North, 90° = East, 180° = South, 270° = West). This is the direction the wind is coming **from**, not going to.

### Pressure — hPa
Current sea-level pressure. Values below 1000 hPa in tropical basins indicate the presence of a low-pressure system. Values below 980 hPa are consistent with a developing cyclone.

### Humidity — %
Relative humidity at the monitoring point. High humidity (>80%) combined with warm SST (>28°C) indicates favorable thermodynamic conditions for cyclone development.

### 24h Rainfall — mm
Total precipitation accumulated over the past 24 hours at the monitoring point.

---

## LIVE MODE: Ocean Panel

### Sea Surface Temperature (SST) — °C
Current sea surface temperature. This is the single most critical environmental factor for tropical cyclone formation and intensification.

- **< 26°C:** Too cold — cyclone cannot sustain itself
- **26–28°C:** Marginally favorable
- **> 28°C:** Favorable for development
- **> 30°C:** Highly favorable — rapid intensification risk

The Indian Ocean SST peaks between April–June (Bay of Bengal) and October–December (Arabian Sea), which is why cyclone seasons coincide with these periods.

### Wave Height — m
Significant wave height — the average height of the highest one-third of waves at the monitoring point. Values above 4 m indicate rough sea conditions dangerous for fishing and shipping.

### Current Speed — m/s
Depth-averaged ocean surface current speed. Strong currents can influence cyclone track by advecting the warm water layer. At 1 m/s, a current is moving at ~3.6 km/h.

### Current Direction — °
Direction the ocean current is flowing **toward** (opposite convention from wind direction). 90° means the current is flowing toward the east.

---

## Quick Reference: What Each Metric Tells You

| Metric | Good Value | Concerning Value | What It Reveals |
|---|---|---|---|
| Pattern Label | EYE / BANDING | DISORGANIZED at late stage | Storm organization and danger phase |
| Confidence % | > 70% | < 20% | AI certainty — low is OK early in storm |
| T+12 Error | < 100 km | > 250 km | Per-step tracking precision |
| T+24 Error | < 200 km | > 400 km | Extrapolation skill |
| Avg MAE T+12 | — | — | Event-level average tracking error |
| Class. Accuracy | > 70% | N/A | AI pattern-matching quality for this event |
| SST | > 28°C | > 30°C (RI risk) | Ocean heat available for storm |
| Wind Speed | — | > 65 km/h | Cyclonic storm threshold reached |
| Pressure | > 1000 hPa | < 980 hPa | Cyclone development indicator |

---

*For deeper technical context: see [model_explained.md](model_explained.md) for architecture and training details, and [limitations.md](limitations.md) for an honest prototype assessment.*
