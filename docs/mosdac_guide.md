# MOSDAC Data Access & Ingestion Guide

This guide outlines the standard operating procedure for downloading, authenticating, and integrating INSAT-3DR satellite data from the Meteorological and Oceanographic Satellite Data Archival Centre (MOSDAC) into the CycloneWatch pipeline.

## 1. Prerequisites & Credentials

MOSDAC requires authenticated access to download raw HDF5 (`.h5`) satellite imagery.
1. Ensure your MOSDAC account is active and approved for data access.
2. In the `scripts/` directory, copy the `.env.example` file to create a new `.env` file:
   ```bash
   cp scripts/.env.example scripts/.env
   ```
3. Open `scripts/.env` and add your credentials:
   ```ini
   MOSDAC_USERNAME=your_actual_username
   MOSDAC_PASSWORD=your_actual_password
   ```

> [!WARNING]
> Never commit the `.env` file to version control. It is already included in `.gitignore` to prevent credential leaks.

## 2. Automated Download Pipeline

We have built an automated Python ingestion script (`download_insat.py`) that acts as a headless client. It programmatically logs in to MOSDAC using your credentials, searches the catalog for specific time bounds, and streams the HDF5 data chunks directly to the local disk.

### Running the Downloader
From the `scripts/` directory, execute the script with the target cyclone event name and date bounds:

```bash
python download_insat.py --event biparjoy_2023 --start 2023-06-13 --end 2023-06-16
```

**How it works under the hood:**
1. **Session Management**: Uses `requests.Session()` to grab the initial CSRF tokens from the MOSDAC login page.
2. **Authentication**: Posts your `.env` credentials to establish an authenticated cookie session.
3. **Catalog Query**: Queries the INSAT-3DR Imager (L1B/L1C) catalog for files matching the requested date range.
4. **Streaming**: Downloads the large HDF5 chunks into `data/raw/insat/`.

## 3. Standardization & ML Preparation

MOSDAC provides data in hierarchical HDF5 format, whereas our `ps70-classifier` model expects standardized `[C, H, W]` normalized NumPy tensors.

Once the `.h5` files are downloaded to the `data/raw/` directory, run the standardization script:

```bash
python standardize_data.py
```

**What this script does:**
1. Scans the raw directory for both `.nc` (NOAA GridSat) and `.h5` (MOSDAC INSAT) files.
2. Uses `h5py` to crack open the MOSDAC files.
3. Extracts the **Thermal Infrared (TIR1)** and **Water Vapor (MIR/WV)** data arrays.
4. Cleans `NaN` values and normalizes the pixel intensities between `0.0` and `1.0`.
5. Stacks them into a multi-channel tensor and saves them as highly compressed `.npz` files in `data/normalized/`.
6. Generates a strict `manifest.csv` logging the exact structural parameters and bounding boxes of every processed frame.

> [!TIP]
> If a MOSDAC HDF5 file is corrupted during download, the standardization script will safely reject it and flag it as `FAILED` in the manifest without crashing the entire batch process.

## 4. Manual Fallback

If the automated MOSDAC API changes its authentication mechanism (e.g., adding a manual CAPTCHA), you can fall back to manual downloads:
1. Log in via your browser at `mosdac.gov.in`.
2. Navigate to Data Access -> INSAT-3DR -> Imager.
3. Download the relevant `.h5` files and drop them manually into the `data/raw/insat/` directory.
4. Run `standardize_data.py` exactly as normal. The pipeline is designed to process the files regardless of how they arrived in the folder.
