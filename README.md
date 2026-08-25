# SIH 2026 · PS59 + PS70 — Master Plan v2
### Internal-SIH Edition: Benchmarks → MoES Gaps → 9-Day Build → Post-Selection Roadmap
**Sponsoring ministry: Ministry of Earth Sciences (MoES)**

---

## How This Version Is Different

The first playbook covered *what to build and why*. This version answers a sharper question: **how do we win an internal selection in 9 days, where judges are scanning many teams and deciding fast on impression, not on production completeness?**

The governing rule for everything below:

> **We are not building a feature-complete system. We are building the smallest scientifically defensible slice that makes a judge believe the full system is real, is credible, and is worth funding further.**

That means: a genuinely beautiful dashboard, real (not fabricated) data, one flawless vertical slice, honest measured numbers, and a tight 8–10 slide story — over a sprawling half-working feature list. A simpler model with real validation beats a fancier model with none.

---

## PART A — What the Top Global Systems Actually Do (Condensed Benchmark)

Judges will probe "why not just use X." Know each system's real shape — pipeline + failure point — not just its name.

| System | Core workflow | Where it actually breaks | What we copy |
|---|---|---|---|
| **DMI / Copernicus (iceberg baseline)** | SAR → CFAR adaptive detection → post-processing → published positions | Detection-only — no drift prediction or route-relative risk | CFAR as our scientific detection baseline, not a black-box CNN |
| **USNIC** | Weekly analyst-driven SAR/IR/visible review, quadrant naming | Weekly cadence, size-threshold cutoff, heavy manual review | Confirms real-time automation + lower size threshold is a genuine open gap |
| **NOAA HAFS** | Assimilation → high-res nested physics → cyclone-specific coupling → forecaster | National-scale, decades of tuning — not reproducible by any team in 9 days | Pipeline *shape* only: assimilation → physics → human forecaster |
| **ECMWF IFS / AIFS** | Physics NWP (IFS) running alongside an operational AI forecasting engine (AIFS) | AI alone isn't trusted as sole authority — always paired with the physics model for validation | Confirms: AI forecasts, physics/ensembles validate — never AI alone |
| **ECMWF 2026 error-correction pattern** | ML learns a *correction* on top of an existing AIFS forecast, not a new model | Only as good as the base forecast being corrected | **The single most copyable pattern** — improve a proven output, don't rebuild the engine |
| **JMA Himawari / EUMETSAT** | Continuous multi-band geostationary observation | Observation-only, no decision layer | Treat purely as a raw data source to fuse |
| **IMD** | Synthesizes multiple NWP models + statistical-dynamical intensity guidance + synoptic/satellite input | Detailed in Part B | Our system feeds IMD's process — it does not compete with it |

**The one-line takeaway to repeat in every judge conversation:** *every* top system is a physics/observation pipeline with an AI correction layer and a human decision point — never a single end-to-end black box. That's our template.

---

## PART B — MoES / IMD: What It Does Well, What It Actually Lacks

Don't oversell ("India has nothing") or undersell ("MoES already solved this"). Use the accurate picture.

### Genuinely strong
- 150-year operational institution, own supercomputers, radar network, INSAT satellites.
- Measurable cyclone-tracking wins (e.g., Cyclone Biparjoy) credited with saving lives via lead-time warning.
- Stated ~40% forecast-accuracy improvement over the preceding five years, with a formal near-zero-error-by-2047 target.
- NCPOR already runs Antarctic sea-ice advisory work — the domain capability behind PS59 already exists in India.
- Active radar expansion (35 → a targeted 68 Doppler radars) and usable data products (IMDAA reanalysis, NCMRWF).

### Documented, publicly acknowledged gaps — this is where we position
1. **Short-fuse, small-scale events remain the weak point** — cloudbursts and hyper-local severe weather, even as broad forecasting improves.
2. **Observation density is thin relative to India's size** — real gaps between AWS/radiosonde/radar points, especially aerosols, soil moisture, maritime conditions.
3. **Downscaling to the last mile is unsolved** — block-level to panchayat-level actionable advisories is an acknowledged open problem, not a solved one.
4. **Institutional fragmentation** — e.g., flood warning depends on IMD rainfall forecasts feeding into CWC's separate, more dated hydrological methods.
5. **Human capital bottleneck** — a documented shortage of modelers/atmospheric scientists willing to join IMD/NCMRWF over private-sector roles.
6. **Trust gap at the hyperlocal level** — reported real-world disputes over forecast accuracy at the farmer/local level even when the model was directionally right.

### The positioning line for every slide and every judge answer
> "We are not replacing IMD or MoES. We integrate what already exists, automate what is repetitive, model what is genuinely difficult, and expose uncertainty — targeting exactly the gaps MoES itself has acknowledged: short-fuse detection, cross-agency fusion, and decision-ready last-mile output."

---

## PART C — Product Identity & Architecture

**One platform, two engines, one shared UI.**

```
                 ENVIRONMENTAL INTELLIGENCE PLATFORM
                              │
              ┌───────────────┴───────────────┐
          PS59 ENGINE                     PS70 ENGINE
         "PolarWatch"                   "CycloneWatch"
     Detect → Track → Predict       Detect → Track → Predict
     → Uncertainty → Route Risk     → Uncertainty → Hazard Risk
              └───────────────┬───────────────┘
                          SHARED UI
                    Decision Support Layer
```

Shared: ingestion, preprocessing, storage, APIs, uncertainty visualization, evidence/provenance, risk presentation, alerts.
Domain-specific: everything scientific inside each engine.

**Visual identity:** scientific, modern, trustworthy, geospatial, operational, clean. Avoid neon gradients, crowded dashboards, generic AI stock imagery, and unnecessary animation.

### Judge comprehension model (design every screen around this)

```
OBSERVE → UNDERSTAND → PREDICT → UNCERTAINTY → RISK → DECIDE
```

Three layers of depth on the same screen:
- **Level 1 (non-specialist):** "🔴 HIGH NAVIGATION RISK — predicted trajectory intersects the selected route."
- **Level 2 (technical):** confidence, predicted position, forecast spread, data age, model version.
- **Level 3 (evidence):** source imagery, timestamp, detection mask, historical observations, environmental forcing, model comparison.

---

## PART D — Tech Stack (Locked)

| Layer | Choice | Fallback |
|---|---|---|
| Backend | Python + FastAPI | Flask if the team already knows it well |
| AI/ML | PyTorch (CNN + GRU/lightweight temporal) | scikit-learn for statistical baselines |
| Scientific computing | NumPy, SciPy, Xarray | — |
| Remote sensing | Rasterio, GDAL, OpenCV | — |
| Geospatial | GeoPandas, PostGIS, Leaflet | — |
| Database | PostgreSQL + PostGIS | — |
| Frontend | React + Leaflet | — |
| Infra | Docker + Docker Compose | — |
| Optional (don't let these delay the core) | Redis, Celery, MinIO/S3, Flutter | — |

**Explicitly out of scope for the prototype:** full national NWP, a foundation weather model from scratch, satellite ground station, global high-res simulation, autonomous ship navigation, Kubernetes/Kafka/service mesh, a large LLM as the scientific core.

---

## PART E — The 9-Day Internal-SIH Sprint

### Priority order when time runs out
```
1. Real data              6. Explainability/evidence
2. Working baseline       7. Presentation
3. Accurate evaluation    8. Reliability/fallback
4. End-to-end slice       9. Mobile
5. Beautiful dashboard   10. Advanced ML
```
A simpler model with real data and honest limitations beats a fancier model with none.

### Team of six (function-based, not degree-based)

| Member | Owns |
|---|---|
| 1 — Research / Domain / Q&A | Scientific understanding, source register, dataset documentation, MoES/IMD gap analysis, judge Q&A prep, stated limitations |
| 2 — Data Engineering | Dataset acquisition, preprocessing, APIs, normalization, DB ingestion, data freshness, caching |
| 3 — PS59 ML | SAR preprocessing, CFAR, iceberg detection, tracking, evaluation |
| 4 — Prediction / PS70 ML | PS59 drift prediction + uncertainty, PS70 detection, cyclone tracking, temporal prediction, model evaluation |
| 5 — Backend + Integration | FastAPI, PostGIS, model-serving APIs, risk engine, integration, deployment |
| 6 — Frontend + Product + Presentation | React/Leaflet dashboard, UX, evidence panel, presentation deck, demo flow, visual polish |

*If only 5 people: merge Research↔Data, or Prediction↔Backend, based on actual skill.*

### Day-by-day plan

| Day | Focus | Exit condition |
|---|---|---|
| **1 — Foundation** | Repo, React shell, FastAPI shell, PostGIS, Leaflet, first dataset, first map layer, UI design system | One real dataset visible in the running app |
| **2 — PS59 Detection** | SAR ingestion, preprocessing, CFAR, candidate detections, map markers | Real SAR scene → detected iceberg candidates → map |
| **3 — PS59 Tracking** | Multi-frame association, track history, velocity, confidence | Real observations → continuous track |
| **4 — PS59 Prediction** | Baseline drift model, environmental forcing, ML residual, uncertainty corridor | Current position → future trajectory + uncertainty |
| **5 — PS59 Risk** | Route input, route-relative risk, alternative route, evidence panel | Prediction → risk → recommendation (flagship slice complete) |
| **6 — PS70** | Historical satellite sequence, cyclone detection, centre estimation, track reconstruction, future-track baseline | Historical event → detected cyclone → track → prediction |
| **7 — Validation (mandatory)** | Backtests: detection/tracking/prediction metrics, uncertainty coverage, baseline comparison, charts | Every scientific claim has a measured number behind it |
| **8 — Polish** | Typography, spacing, map, loading/error states, evidence cards, timeline, replay, responsiveness — **no new science** | A non-specialist judge understands the product in 10 seconds |
| **9 — Demo + PPT + Q&A** | 10 full rehearsals, live demo + recorded fallback, PPT, architecture slide, metrics slide, Q&A sheet, offline demo | Team can run the full demo from a cold start with zero confusion |

### The flagship feature: Historical Replay
Judge picks a real past event → system rewinds to T-48h/T-36h/T-24h/T-12h → shows what it would have predicted at each point → compares predicted vs. actually-observed. This turns the demo from a simulation into a measurable experiment, and it's the single highest-value feature for credibility per hour of build effort.

### Accuracy rules (non-negotiable)
Never say "98% accurate," "real-time" (unless genuinely real-time), "operational," "production-ready," "autonomous," or "replaces IMD" unless the evidence supports it.
Prefer: *prototype, backtested, held-out evaluation, mean prediction error, uncertainty coverage, demonstration, decision-support layer.* Scientific honesty reads as more credible to judges than inflated claims — this is a genuine competitive advantage, not just an ethics footnote.

### Presentation structure (8–10 slides)
1. Problem — one visual, one sentence
2. Existing gap — "data exists, forecasts exist, models exist, BUT information is fragmented → interpretation → decision" (don't attack IMD)
3. Solution — Observe → Understand → Predict → Uncertainty → Risk → Decide
4. Product — large dashboard screenshot, minimal text
5. PS59 pipeline with actual output shown
6. PS70 pipeline with actual output shown
7. Accuracy — real measured numbers; if no baseline comparison exists, label clearly as "prototype backtest," never fabricate a competitor comparison
8. Impact — Safer Navigation / Faster Interpretation / Actionable Warnings
9. Technology — only now show the stack
10. Closing — "We don't replace the existing ecosystem. We make its information more actionable." + Existing Data + AI + Physics + Uncertainty → Actionable Intelligence

### 3-minute demo script
- 0:00–0:20 Problem statement in one line
- 0:20–0:40 "This is our Environmental Intelligence Platform" + dashboard reveal
- 0:40–1:30 PS59: real scene → detection → track → prediction → uncertainty → route → risk → recommendation
- 1:30–2:10 PS70: cyclone → track → prediction → uncertainty → hazard
- 2:10–2:35 Real measured accuracy numbers
- 2:35–3:00 Close on the positioning line above

### Judge Q&A defense sheet
- *"Why not just use IMD?"* → "We're not replacing IMD — we're a decision-support layer that consumes existing observations/forecasts and turns them into role-specific, uncertainty-aware output."
- *"Where's your data from?"* → Name the exact provider and dataset every time. Never say "we generated it" unless it's clearly synthetic.
- *"Is the prediction accurate?"* → Show metric, dataset, test period, baseline, and stated limitation together.
- *"Why AI?"* → "AI is used where pattern recognition or systematic correction helps. Known physical dynamics stay represented by physics/statistical models."
- *"Why not an LLM?"* → "Not the appropriate scientific core for spatio-temporal environmental prediction — we use specialized models for the scientific task."
- *"Can this scale?"* → "The prototype is a simple monolith, but ingestion/inference/risk/presentation are logically separated so they can scale independently later." (See Part F.)
- *"What if the model is wrong?"* → "We expose confidence and uncertainty, show source evidence, and keep a human decision-maker in the loop."

### What success looks like on Day 9
Not two massive systems. **One excellent platform**, with **one flawless PS59 vertical slice** and **one credible PS70 proof-of-concept**, backed by real data, measured results, clean UX, explainability, a clear architecture story, and a rehearsed, reliable demo.

---

## PART F — The Full-Build Roadmap: If We Get Selected

The 9-day build is deliberately a *demonstration*, not a product. If the team advances past internal selection toward the grand finale or a real pilot, here is the phased path from prototype to something genuinely deployable — this is also the answer to "can this scale?" if a judge pushes further.

### Phase 1 (Weeks 1–4 post-selection) — Harden the Prototype
- Replace hackathon-grade backtesting with a proper held-out evaluation protocol across more historical events.
- Move detection/tracking models from "good enough to demo" to versioned, reproducible training pipelines (data versioning, experiment tracking).
- Add automated regression tests for the risk engine so a code change can't silently break a risk score.
- Expand the historical-replay library beyond the 1–2 events used in the demo.

### Phase 2 (Months 2–3) — Real Data Partnerships
- Formal outreach to MOSDAC, NCPOR, and INCOIS for documented API access rather than best-effort public scraping.
- Build a proper ingestion connector layer (per Part C/D) that can absorb a new data provider without a rewrite.
- Add data-quality monitoring and provenance logging as first-class features, not an afterthought.

### Phase 3 (Months 3–5) — Model Maturity
- Move PS59 drift prediction and PS70 track/intensity prediction from single-shot models to properly validated ensembles with calibrated uncertainty (this is where the "uncertainty coverage" metric from the demo becomes an operational SLA, not a slide).
- Introduce the human-in-the-loop review workflow fully: analyst accept/correct/reject feedback loop feeding back into model evaluation, not just UI polish.
- Only now consider the "advanced ML" items deliberately deferred during the 9-day sprint (e.g., a lightweight temporal transformer upgrade path for PS70, CNN refinement for PS59 false-positive reduction).

### Phase 4 (Months 4–6) — Infrastructure That Justifies Itself
- Only introduce the infrastructure explicitly avoided during the prototype (containers-as-a-service, managed queues, horizontal scaling) once real usage numbers justify it — not by default.
- Separate the shared platform (ingestion, storage, risk, UI) from the domain engines (PS59/PS70) as independently deployable services, matching the "logically separated" answer given to judges.
- Build the Flutter mobile alert app with genuine offline/low-bandwidth support — directly relevant for polar/maritime users (PS59) and rural/coastal alert recipients (PS70).

### Phase 5 (Months 6+) — Pilot & Institutional Fit
- Seek a defined pilot partner (e.g., a research-station logistics team for PS59, or a state disaster-management cell for PS70) rather than claiming national deployment.
- Formalize the "decision-support layer, not a replacement" positioning into an actual integration spec — how would this sit alongside IMD/NCPOR workflows rather than in front of them.
- Build the compliance/reliability case: uptime targets, audit logs for every risk recommendation, a documented model-update process — the things a real institution would ask for before trusting an alert feed.

**The throughline from Day 1 to Phase 5 is the same discipline used in the 9-day sprint:** never claim more certainty, scale, or completeness than the evidence supports. That discipline is what got the prototype through selection, and it's what a real institution would actually want from a decision-support system.

---

## Source Register

Carried forward from the original architecture document (DMI/Copernicus CFAR methodology, NOAA HAFS, ECMWF AIFS and its 2026 error-correction pattern, IMD RSMC New Delhi cyclone-warning SOP, MOSDAC infrastructure, USNIC), the prior playbook's MoES/IMD gap research (IMD's 150th-anniversary vision document, officials' acknowledgment of small-scale/cloudburst forecasting difficulty, IMD–CWC integration gaps, observation-density and staffing constraints, reported hyperlocal trust disputes), and this session's 9-day execution structure as drafted by the team.

*Reminder: verify exact PS59/PS70 statement wording against the live sih.gov.in portal before finalizing the deck — some third-party trackers currently show only partial statement text.*
