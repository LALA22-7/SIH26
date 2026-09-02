# CycloneWatch — Known Limitations

> This document exists because a prototype with honest limitations is more credible than one that hides them.
> For the judge Q&A, cite this document. Do not make claims beyond what is measured here.

---

## Model limitations

### 1. Centre position error is high (255 km MAE)
The model was trained on 423 frames from 7 events. This is a small dataset by ML standards. The centre prediction is at the level of a simple persistence baseline — it knows roughly what region the cyclone is in, but not precisely where.

**What this means for the demo:** Centre position is shown with a large provisional uncertainty circle. This is honest. IMD's operational guidance at T+12h is ~100–150 km — we are not claiming to match that.

**How to improve:** More training data (more events). INSAT-3DR data at 1 km resolution. The architecture is sound — it is a data quantity problem, not a model architecture problem.

### 2. Pattern labels are algorithm-derived, not analyst-verified
The 5 structural pattern labels were assigned using IBTrACS wind speed thresholds, not by a meteorologist looking at actual satellite imagery. A human analyst might disagree with ~20% of our labels, especially at threshold boundaries.

**What this means for the demo:** Pattern classification is presented as a model output with confidence. The source satellite image is always shown (evidence panel). A judge can look at the image and verify.

### 3. No temporal model
The T+12 and T+24 predictions currently use a persistence + linear extrapolation approach — the model assumes the cyclone continues moving in the same direction at the same speed. A real temporal model (ConvLSTM, GRU) was not trained in this sprint due to time constraints.

**What this means for the demo:** Predictions are labeled "provisional". The uncertainty polygon is explicitly not a calibrated confidence region.

### 4. Two satellite channels only (IR + water vapour)
The model uses GridSat-B1 data which provides infrared and water vapour channels at 4 km resolution. Visible-light imagery and higher-resolution INSAT-3DR/MOSDAC data were not available in the sprint timeline.

### 5. Trained on 7 North Indian Ocean events
The model has only seen 7 storms. It cannot be expected to generalise well to unusual storms or Atlantic/Pacific cyclones. All 7 training events are North Indian Ocean cases.

### 6. Confidence scores not calibrated
The pattern classification outputs class probabilities but these have not been calibrated against a validation set using temperature scaling or isotonic regression. A raw softmax output of 0.8 does not mean "80% probability of being correct" — it just means the model is relatively more certain than for a 0.5 output.

---

## System limitations

### 7. Requires pre-downloaded satellite data
The demo uses pre-processed satellite frames downloaded from the NOAA GridSat-B1 archive. The system does not pull live satellite data — there is no direct integration with MOSDAC, EUMETSAT, or any real-time satellite feed in this prototype.

### 8. Offline operation only post-precompute
The historical replay works fully offline once `precompute_replay.py` has been run. The raw classification and prediction endpoints do call the ML model, so they require the model file to be present — but not the internet.

### 9. Single-machine deployment only
This prototype runs on a single machine (Docker Compose). It has not been stress-tested for concurrent users or deployed to any cloud infrastructure.

---

## What we are NOT claiming

- We are not claiming to replace IMD or any national meteorological service
- We are not claiming operational readiness
- We are not claiming our centre position error is better than IMD's NWP models
- We are not claiming real-time satellite data integration
- We are not claiming the pattern labels are equivalent to manual expert analysis

---

## What we ARE claiming

- Automated structural pattern classification with 78.3% accuracy on held-out data
- A working end-to-end pipeline: satellite data → ML inference → API → visualisation
- Historical replay demonstrating what the model would have said before the outcome was known
- Honest uncertainty quantification (provisional, not calibrated)
- Transparent evidence — every prediction links back to the source satellite frame
- A decision-support layer that could reduce analyst time for initial satellite interpretation
