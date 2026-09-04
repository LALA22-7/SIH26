# Data Explainer: The Fuel of CycloneWatch

*This document explains the Data pipeline of CycloneWatch in simple terms so anyone — technical or not — can understand where our information comes from and how it is processed.*

---

## What is the Data Pipeline?
If the ML model is a student preparing for an exam, the Data Pipeline is the massive textbook they have to study from. A machine learning model is completely useless without high-quality historical data to learn from. The Data Pipeline downloads, cleans, and standardizes years of real weather history so the AI can understand it.

---

## Where Does the Data Come From?

### 1. Satellite Imagery: NOAA GridSat-B1
We download real satellite images from the **NOAA GridSat-B1 archive** — a free, publicly accessible dataset maintained by the National Oceanic and Atmospheric Administration (United States).

- **Resolution:** Each image covers the Indian Ocean at approximately 4 km per pixel.
- **Frequency:** One image every 3 hours, continuously, from 2000 to present.
- **Channels used:** Infrared (measures cloud top temperature) and Water Vapor (measures atmospheric moisture).

### 2. Ground Truth: IBTrACS Best-Track Data
To teach the AI, we need to know the "correct answer" for every satellite image. We use **IBTrACS (International Best Track Archive for Climate Stewardship)** — the global gold-standard historical record of every tropical cyclone.

IBTrACS gives us, for every cyclone at every 6-hour interval:
- Exact center latitude and longitude (GPS coordinates)
- Wind speed
- Minimum pressure

---

## How the Pipeline Works (Step by Step)

### Step 1: Download the Raw Satellite Files
`scripts/aws_downloader.py` connects to NOAA's AWS S3 bucket and downloads the NetCDF4 (.nc) satellite files for the time range of each cyclone.

### Step 2: Parse IBTrACS for Storm Positions
`scripts/split_ibtracs.py` reads the massive IBTrACS database and extracts only the rows relevant to our 7 target cyclones, saving them as per-event CSV files in `data/ground_truth/`.

### Step 3: Crop and Normalize Images
`scripts/standardize_data.py` takes each raw satellite file and:
1. Reads the infrared and water vapor channels
2. Crops the image to a bounding box centered on the known storm position
3. Scales all pixel values to the 0–1 range (normalization)
4. Saves the result as a `.npz` file (a compressed NumPy array — the format the AI understands)

### Step 4: Join Images with Ground Truth
`scripts/validate_and_join.py` matches each satellite frame (by timestamp) to the closest IBTrACS best-track record, producing the final `training_manifest.csv` — the master "answer key" that tells the model where the storm centre was at each image's timestamp.

---

## The Folder Structure

```
data/
├── raw/              ← Downloaded NetCDF4 satellite files (not committed to git — too large)
├── normalized/       ← Processed .npz tensors, one per storm frame
├── ground_truth/     ← IBTrACS CSV files per cyclone (official position data)
├── training_manifest.csv   ← Master file: frame path + timestamp + lat/lon + pattern label
└── metadata.csv            ← Summary of all cyclone metadata
```

---

## Key Buzzwords Explained

- **IBTrACS (International Best Track Archive for Climate Stewardship):** The world's most comprehensive historical record of tropical cyclones, maintained by NOAA, WMO, and other international agencies. It is the "answer key" we compare our AI predictions against.
- **GridSat-B1:** A historical satellite data product provided by NOAA. It harmonizes data from multiple geostationary satellites (including INSAT) into a consistent global grid of infrared imagery, making it easy to download and use without needing satellite-specific software.
- **NetCDF4 (.nc files):** The file format used by meteorologists worldwide for multi-dimensional scientific data. A single NetCDF4 file can contain global satellite data across hundreds of time steps, stored with geographic metadata. Our scripts parse these into simple 2D arrays.
- **Channels (IR / Water Vapour):** Satellites photograph the Earth across different wavelengths of light. The Infrared (IR) channel tells us how cold the cloud tops are — colder means higher clouds means more intense convection. The Water Vapor (WV) channel reveals moisture patterns and the storm's circulation even when clouds aren't visible.
- **.npz files (Tensors):** The AI cannot read JPEG images or weather data files directly. We convert everything into `.npz` files — compressed archives of pure number grids (NumPy arrays). The AI reads these grids of numbers directly.
- **Normalization:** Raw satellite data values are arbitrary numbers (e.g., brightness temperatures in Kelvin ranging from 200 to 300). Normalization scales all values to between 0 and 1. This prevents any single data channel from dominating the training because its numbers happen to be much larger.
- **Training Manifest:** A master spreadsheet (`training_manifest.csv`) that acts as the "index card" for every training example. Each row links a `.npz` file to its ground-truth storm position (lat/lon) and structural pattern label. The model reads this manifest to know what to learn from.

---

## Dataset at a Glance

| Cyclone | Year | Frames | Date Range | Source |
|---|---|---|---|---|
| Phailin | 2013 | 57 | Oct 4–14 | GridSat-B1 + IBTrACS |
| Hudhud | 2014 | 43 | Oct 7–14 | GridSat-B1 + IBTrACS |
| Ockhi | 2017 | 38 | Nov 29 – Dec 6 | GridSat-B1 + IBTrACS |
| Fani | 2019 | 71 | Apr 26 – May 4 | GridSat-B1 + IBTrACS |
| Amphan | 2020 | 56 | May 16–21 | GridSat-B1 + IBTrACS |
| Tauktae | 2021 | 49 | May 14–19 | GridSat-B1 + IBTrACS |
| Biparjoy | 2023 | 109 | Jun 6–17 | GridSat-B1 + IBTrACS |
| **Total** | | **423** | 2013–2023 | |

---

## What We Could Not Use (Future Plans)

The major limitation of our dataset is the 4 km resolution of GridSat-B1. The real INSAT-3DR satellite operated by ISRO provides **1 km resolution imagery**, which would give our model 16x more spatial detail per frame. MOSDAC (ISRO's data portal) provides access to this data, but requires a formal research access request, which is currently pending. This MOSDAC integration is the single highest-impact improvement identified for the next phase of CycloneWatch.

---

## Summary
The Data Pipeline does the unglamorous but critical work of downloading massive scientific files from NOAA's archives, aligning them with the official IBTrACS position records, standardizing them into uniform number grids, and generating the master training manifest that the AI learns from. Without this pipeline, the ML model would have nothing to study.
