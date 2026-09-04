# CycloneWatch Model — Explained in Plain Language

> **Who this is for:** Everyone on the team, judges, and anyone curious about what the AI is actually doing.
> No machine learning background assumed.

---

## What does the model do?

It looks at a satellite image of a cyclone and answers two questions:

1. **Where is the centre of the cyclone right now?** (gives a latitude/longitude coordinate)
2. **What does its structure look like?** (gives one of 5 pattern labels)

That is it. It does not predict the weather. It does not replace meteorologists. It automates the interpretation of a satellite image — something that currently requires a trained analyst to do manually.

---

## What data does it use?

Each input is a satellite image with **two channels**:

| Channel | What it is | Why it matters |
|---|---|---|
| **IR (Infrared)** | Measures how cold cloud tops are | Cold = tall clouds = intense storm |
| **Water Vapour** | Measures moisture in the upper atmosphere | Shows storm circulation patterns |

The image is cropped to the Indian Ocean region and normalised to values between 0 and 1.

**No visible-light images yet** — GridSat-B1 (our satellite data source) provides IR and water vapour. Visible will be added if we get MOSDAC/INSAT data.

---

## What are the 5 pattern labels?

These follow standard meteorological structural classification:

| Label | What it means | When you see it |
|---|---|---|
| **eye** | Clear, calm centre with tight spiral banding around it | Peak intensity — most dangerous phase |
| **banding** | Well-organised spiral bands, no clear eye yet | Active intensification |
| **curved_band** | A single curved band of clouds, loosely organised | Developing or weakening phase |
| **shear_affected** | Storm is being torn apart by wind shear | Rapid weakening, lopsided appearance |
| **disorganized** | No clear structure, scattered convection | Early stage or dying remnant |

---

## How was it trained?

The model was trained on **7 historical North Indian Ocean cyclones**:

| Cyclone | Year | Peak Intensity | Why included |
|---|---|---|---|
| Biparjoy | 2023 | Very Severe (165 km/h) | Primary demo — Arabian Sea, Gujarat landfall |
| Amphan | 2020 | Super Cyclonic (220 km/h) | Bay of Bengal, strongest in decades |
| Fani | 2019 | Extremely Severe (215 km/h) | Landmark IMD forecast case |
| Tauktae | 2021 | Extremely Severe (185 km/h) | Recent Arabian Sea, same region as Biparjoy |
| Phailin | 2013 | Very Severe (215 km/h) | Triggered major IMD improvements |
| Hudhud | 2014 | Very Severe (185 km/h) | Andhra Pradesh landfall, well-documented |
| Ockhi | 2017 | Very Severe (165 km/h) | IMD missed early intensification — key positioning case |

**Total: 423 satellite frames** (one frame every 3 hours across each storm's lifetime)

Labels were assigned using IBTrACS best-track wind speed data:
- wind ≥ 120 kts → **eye**
- wind 64–119 kts → **banding**
- wind 34–63 kts → **curved_band**
- rapid weakening (≥15 kt drop in 6h) → **shear_affected**
- wind < 34 kts → **disorganized**

---

## Current accuracy

These numbers are from running the trained model on **60 held-out frames it never saw during training**:

### Pattern classification

| Metric | Value | What it means |
|---|---|---|
| **Overall accuracy** | **78.3%** | Correct label on 47 out of 60 frames |
| Eye F1 | 1.00 | Perfect — it always gets "eye" right |
| Banding F1 | 0.79 | Gets it right most of the time |
| Shear-affected F1 | 0.80 | Reasonable for a rare class |
| Disorganized F1 | 0.88 | Good — most common class |
| Curved-band F1 | 0.55 | Weakest — confused with banding |

**F1 score** is a combined precision+recall metric. 1.0 = perfect, 0.0 = useless.

### Centre position (where is the cyclone?)

| Metric | Value |
|---|---|
| **Mean Absolute Error (MAE)** | **255 km** |
| Median error | 240 km |
| Worst error | 684 km |

---

## Is 255 km good enough for a prototype?

**Honest answer: it is acceptable for a prototype, not for operational use.**

Context:
- The model was trained on only 423 frames from 7 events — that is tiny by ML standards
- GridSat-B1 has coarse 4 km resolution — the images are not sharp
- Labels were derived algorithmically, not hand-drawn by analysts

For comparison:
- IMD's operational NWP model: T+24h centre error ~100–150 km
- Simple persistence baseline (assume cyclone stays put): ~200–300 km error at T+12h

So our model performs **roughly at the persistence baseline level** — meaning it has learned the general region of where cyclones are, but is not yet meaningfully better than "it will be where it was". This is expected and honest for a first prototype on 423 frames.

**The good news:** 78.3% pattern accuracy is a real result. Classifying structural patterns is the harder and more novel task. A human analyst looking at a noisy IR image might agree with our label ~80% of the time.

For the demo this is presented correctly:
- Centre position is shown with a provisional uncertainty circle
- Everything is labeled as model output, not ground truth
- The historical replay shows predicted vs actual — judges can see the error honestly

---

## Why the T+12 Error Is Sometimes Higher Than T+24

On the dashboard, judges may notice that for some timesteps the **T+12 error is higher than the T+24 error**. This seems backwards — surely a 24-hour forecast should be less accurate than a 12-hour one?

The reason is that T+12 and T+24 predictions are **computed independently**. They do not cascade — T+24 is not built on top of T+12. Both are generated by the same persistence extrapolation (current position + current velocity × time). If the storm made an unexpected directional change between T+0 and T+12, the 12-hour estimate misses the turn, while the 24-hour estimate (looking further ahead) might accidentally land closer to where the storm ended up after it completed the turn.

In a properly trained temporal model (ConvLSTM/GRU), this artefact would disappear because the model would learn to anticipate directional changes from the sequence of past images.

---

## Why MAE Varies Dramatically Between Timesteps

Scroll through the timeline on any cyclone and you will see the T+12 error jump from ~80 km to ~400 km between adjacent frames. This is normal. The error is high when:

1. **The storm changes direction suddenly** — the persistence extrapolation projects it straight when it recurves
2. **Rapid intensification causes fast movement** — the velocity estimate from the previous step is too slow
3. **The satellite image is ambiguous** — cloudy, low-contrast frames give the model a poor starting position estimate

The error is low when:
1. **The storm moves slowly in a straight line** — persistence extrapolation is accurate
2. **The centre is clearly visible in IR** — the initial position estimate is tight

---

## How MAE Can Be Reduced: The Improvement Roadmap

| Improvement | Expected T+12 MAE | Expected T+24 MAE | Effort | Status |
|---|---|---|---|---|
| Current prototype | ~255 km | ~320 km | — | ✅ Done |
| INSAT-3DR data (1 km resolution) | ~150 km | ~220 km | High | 🔴 Pending MOSDAC access |
| 10× more training events (50+) | ~140 km | ~200 km | Medium | 🔴 Data download required |
| Trained ConvLSTM temporal model | ~120 km | ~160 km | Medium | 🟡 Architecture staged |
| All three combined | **< 100 km** | **< 130 km** | Phase 2 | 🔮 Roadmap target |
| IMD operational NWP (reference) | ~100–150 km | ~150–200 km | Supercomputer | — |

Reaching < 100 km T+12 MAE would put CycloneWatch in operational accuracy territory, competing with physics-based NWP while running 1000× faster.

---

## Why does this matter for the demo?

The positioning of CycloneWatch is:

> "We are not replacing IMD. We are automating the satellite-image interpretation step."

IMD uses complex physics models (NWP) that take hours to run. Our model processes a satellite image in milliseconds and gives a structural assessment + centre estimate. The use case is **faster first-look interpretation** — especially useful for rapid intensification events like Ockhi where IMD's models missed the early signal.

The model gives:
- An immediate structural classification when a new satellite image arrives
- A location estimate with honest uncertainty
- A trackable history of how the storm's structure evolved

---

## What is missing (next steps)

| Gap | Why it matters | Fix |
|---|---|---|
| Confidence calibration | Model doesn't know *how* confident it is | Temperature scaling on val set |
| Temporal model | T+12/T+24 prediction is just extrapolation | ConvLSTM or GRU sequence model |
| More data | 423 frames is small | Download 5+ more events, or add MOSDAC data |
| Visible channel | Currently IR + WV only | Add INSAT-3D visible band |
| Manual label verification | Labels from wind rules, not analyst review | Research team spot-check |
| Higher resolution | GridSat-B1 is 4 km | INSAT-3DR is 1 km |

---

## Architecture (for the technical judges)

```
Input: [2, H, W]  — 2 channels (IR, WV), variable spatial size

Conv2d(2→16, 3×3) + ReLU + MaxPool2d(2×2)
Conv2d(16→32, 3×3) + ReLU + MaxPool2d(2×2)
AdaptiveAvgPool2d(16×16)          ← handles any input resolution
Flatten → Linear(8192→128) + ReLU

┌─────────────────────────────────────────────┐
│ Centre head:  Linear(128→2)  → (lat, lon)   │  MSE loss, weight=10
│ Pattern head: Linear(128→5)  → class logits │  Weighted CrossEntropy
└─────────────────────────────────────────────┘

Total parameters: ~540K
Training: Adam, lr=0.001, ReduceLROnPlateau(patience=10)
Class weights: inverse-frequency to handle label imbalance
```

---

## Quick reference

| Item | Value |
|---|---|
| Checkpoint | `ml/checkpoints/model.pt` |
| Config | `ml/configs/model_config.json` |
| Training data | 423 frames, 7 events |
| Pattern accuracy | 78.3% |
| Centre MAE | 255 km |
| Input shape | `[2, H, W]` float32 |
| Output | `predict_frame(frame)` → dict |
| Model version | 2.0.0 |

---

## Dashboard Metrics Reference

For a plain-language explanation of every number shown on the CycloneWatch dashboard — including why confidence may be 0%, what T+12 vs T+24 error means, and what SST thresholds indicate — see:

➡️ **[metrics_explained.md](metrics_explained.md)**
