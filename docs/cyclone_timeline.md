# Training Data Timeline: The 7 Cyclones

This document breaks down the 7 historic events used to train the CycloneWatch model. Use this in the presentation deck to demonstrate the geographic and temporal diversity of the dataset and to put faces to the cyclones displayed on the dashboard.

---

## Dataset Overview

| Event | Year | Basin | Formation | Peak Intensity Class | Landfall | Peak Wind (kt) | Deaths | Economic Damage |
|---|---|---|---|---|---|---|---|---|
| **Phailin** | 2013 | Bay of Bengal | 4 Oct | Extremely Severe CS | Gopalpur, Odisha | 140 kt (259 km/h) | 45 | ~$4.26B |
| **Hudhud** | 2014 | Bay of Bengal | 7 Oct | Extremely Severe CS | Visakhapatnam, AP | 115 kt (213 km/h) | 124 | ~$3.40B |
| **Ockhi** | 2017 | Arabian Sea | 29 Nov | Very Severe CS | Dissipated at sea | 100 kt (185 km/h) | 218+ | ~$920M |
| **Fani** | 2019 | Bay of Bengal | 26 Apr | Extremely Severe CS | Puri, Odisha | 150 kt (278 km/h) | 89 | ~$8.10B |
| **Amphan** | 2020 | Bay of Bengal | 16 May | Super Cyclonic Storm | West Bengal/Bangladesh | 140 kt (259 km/h) | 128 | ~$13.7B |
| **Tauktae** | 2021 | Arabian Sea | 14 May | Extremely Severe CS | Saurashtra, Gujarat | 120 kt (222 km/h) | 174 | ~$2.10B |
| **Biparjoy** | 2023 | Arabian Sea | 6 Jun | Extremely Severe CS | Jakhau Port, Gujarat | 105 kt (194 km/h) | 17 | ~$120M |

---

## Why These 7 Events

### 1. Geographic Diversity
- **4 Bay of Bengal events** (Phailin, Hudhud, Fani, Amphan) — eastern coast of India and Bangladesh
- **3 Arabian Sea events** (Ockhi, Tauktae, Biparjoy) — western coast of India (Gujarat/Kerala)

This ensures the model has learned from both major North Indian Ocean cyclone basins and does not overfit to one basin's typical track patterns.

### 2. Temporal Diversity (2013–2023)
A 10-year span captures multiple phases of sea surface temperature variability in the Indian Ocean, ensuring the model isn't optimizing for a single weather regime year.

### 3. Intensity Diversity
The dataset spans the full intensity spectrum:
- Super Cyclonic Storm (Amphan — the strongest class IMD recognizes)
- Extremely Severe Cyclonic Storm (Phailin, Hudhud, Fani, Tauktae, Biparjoy)
- Very Severe Cyclonic Storm (Ockhi)

This means the model has seen `eye`, `banding`, `curved_band`, `shear_affected`, and `disorganized` patterns across a wide range of intensities.

### 4. Forecasting Difficulty Spectrum
- **Easy (for NWP):** Phailin, Fani — classic tracks, standard intensification
- **Moderate:** Hudhud, Amphan, Tauktae, Biparjoy — some unusual characteristics
- **Hard (for NWP):** Ockhi — anomalous formation, explosive RI, unusual track

---

## Individual Event Profiles

### Phailin (2013) — Bay of Bengal
The first Extremely Severe cyclone to strike India in 14 years. Landfall at Gopalpur, Odisha with devastating impact but relatively low deaths (45) due to the largest pre-cyclone evacuation in Indian history at the time (nearly 1 million people). Phailin triggered major improvements in India's disaster response framework.

**CycloneWatch context:** A textbook case of clear `banding` → `eye` evolution. The model learns the "classic" intensification signature from Phailin.

### Hudhud (2014) — Bay of Bengal
Struck Visakhapatnam (Vizag), Andhra Pradesh on 12 October with 185 km/h sustained winds. Caused severe damage to the port city and triggered unusually rapid intensification in the 24 hours before landfall — a pattern our model now recognizes as a characteristic of storms approaching warm, shallow coastal waters.

**CycloneWatch context:** Provides `banding` and `eye` training examples for Bay of Bengal near-landfall signatures.

### Ockhi (2017) — Arabian Sea ⚠️ KEY CASE
The primary motivating case for CycloneWatch. See the [full Ockhi analysis](ockhi_analysis.md) for a complete breakdown. In brief: anomalous low-latitude formation, explosive RI, 48-hour IMD advisory delay, 218+ fishermen killed.

**CycloneWatch context:** Provides `disorganized` → `curved_band` → `banding` → `eye` training examples for a low-latitude anomalous cyclone.

### Fani (2019) — Bay of Bengal ✅ IMD SUCCESS CASE
The most accurately forecast intense cyclone in Indian history. IMD predicted the Puri landfall within ~5 km at 72-hour lead time. 1.2 million people were evacuated. Despite extreme intensity (115 kt / 278 km/h), deaths were held to 89.

**CycloneWatch context:** Provides the best examples of a well-organized mature `eye` pattern and clean `shear_affected` signature during post-landfall weakening.

### Amphan (2020) — Bay of Bengal
The most powerful cyclone to form in the Bay of Bengal since 1999. Reached Super Cyclonic Storm status (the highest IMD classification) and made landfall in West Bengal. Caused catastrophic damage to Kolkata and the Sundarbans delta region.

**CycloneWatch context:** The only Super Cyclonic Storm in our dataset — provides training examples of the most organized, compact `eye` signatures possible.

### Tauktae (2021) — Arabian Sea
An Extremely Severe cyclone that struck the Gujarat coast with 185 km/h winds. Notably, it intensified very rapidly in the final 24 hours before landfall — from Severe CS to Extremely Severe CS — in a period when NWP ensemble models were still showing uncertainty.

**CycloneWatch context:** Critical RI case for the Arabian Sea. Provides `banding` → `eye` → `shear_affected` examples for rapidly intensifying west-coast storms.

### Biparjoy (2023) — Arabian Sea (Primary Demo Event)
Our primary demonstration cyclone. Formed on June 6, 2023, and remained active for 12+ days — one of the longest-lived Arabian Sea cyclones on record. Its slow movement gave us the largest single-event frame count (109 frames), making it the richest dataset for training and the best replay experience on the dashboard.

**CycloneWatch context:** The most time steps, the clearest structural progression. When judges watch the dashboard timeline for Biparjoy, they see a complete lifecycle from `disorganized` formation through `eye` peak to `shear_affected` dissipation.

---

## Dataset Composition Summary

| Metric | Value |
|---|---|
| Total events | 7 |
| Total frames | 423 |
| Date range | 2013–2023 (10 years) |
| Basin split | 4 Bay of Bengal, 3 Arabian Sea |
| Source | GridSat-B1 (NOAA) + IBTrACS (NOAA/WMO) |
| Frame interval | Every 3 hours during each storm's active period |
| Frame resolution | ~4 km/pixel (GridSat-B1 limitation) |
| Channels | Infrared (IR) + Water Vapour (WV) |

---

## What Is Not in the Dataset

| Cyclone | Reason for Exclusion |
|---|---|
| Vayu (2019) | Track data available but satellite frames not fully downloaded yet — considered for future expansion |
| Yaas (2021) | Similar to Amphan; prioritized more diverse events first |
| Mocha (2023) | Myanmar-focused track; outside current scope of Indian coastal impact analysis |

These represent natural expansion candidates for Phase 2 data collection.
