# CycloneWatch: AI-Powered Tropical Cyclone Tracker

**Smart India Hackathon 2026 Submission (PS70)**  
*AI/ML-based system for identification, classification, and prediction of different tropical cyclone patterns using multi-source satellite data.*

### 🌐 Live Demo
- **Frontend Dashboard:** [https://sih-26-one.vercel.app/](https://sih-26-one.vercel.app/)
- **Backend API (Render):** [https://sih26-o6nv.onrender.com/health](https://sih26-o6nv.onrender.com/health)

---

## 🌪️ Project Overview
CycloneWatch is an end-to-end, AI-driven meteorological tracking system. Traditional Numerical Weather Prediction (NWP) physics models are highly accurate but notoriously slow to respond to Rapid Intensification (RI) events and anomalous low-latitude storm formations. 

CycloneWatch addresses this **interpretation gap**. By applying deep convolutional neural networks directly to infrared satellite imagery, we automate the structural classification of storms. Our model detects dangerous structural anomalies (like sudden "banding" or "eye" formations) hours before traditional physics models compute the danger, providing a vital early warning system.

## 📂 Repository Structure

This repository is organized into distinct, microservice-ready domains:

- **[`/backend`](backend/README.md):** The core FastAPI engine. Handles spatial database operations via PostGIS, serves the ML predictions to the frontend, and manages historical storm precomputations.
- **[`/ml`](ml/README.md):** The Artificial Intelligence pipeline. Contains the PyTorch code for our Convolutional Neural Network (CNN) and Gated Recurrent Unit (GRU) temporal sequence models.
- **[`/frontend`](frontend/README.md):** The React + Leaflet Single Page Application (SPA). The visual command center for live and historical storm tracking.
- **[`/data`](data/README.md):** The data ingestion pipeline. Scripts to download raw GridSat-B1 satellite imagery, parse IBTrACS best-track data, and normalize it into ML-ready tensors.
- **[`/docs`](docs/):** Research documents, including gap analyses of historical cyclones (like Ockhi and Fani), the pattern taxonomy, and our training timelines.

*(Note: For non-technical readers or judges, every directory contains an `EXPLAINER.md` file that translates the technical code into layman's terms.)*

## 🚀 Quick Start (Local Development)

### 1. Backend & ML (FastAPI Server)
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt

# Run the SQLite database seed and start the server
python -m scripts.seed_db
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:5173` to view the CycloneWatch dashboard.

## 📊 Current Metrics & Performance
- **Structural Pattern Classification:** ~78.3% accuracy across 5 distinct morphological classes.
- **Center Tracking (T+12h):** Mean Absolute Error (MAE) of ~234 km (Beating our 255 km persistence baseline).
- **Inference Speed:** ~12 milliseconds per satellite frame on CPU.

## 🔮 Future Roadmap (Scaling to Production)
Our current prototype is constrained by the 4km-resolution GridSat-B1 dataset. The immediate next step for CycloneWatch is unlocking research access to the **MOSDAC / INSAT-3DR** dataset from ISRO. 

Moving from 4km to 1km resolution will provide the ML model with 16x more spatial data per frame. Combined with our fully staged temporal sequence architecture (ConvLSTM), this will allow our MAE to drop below 100km, rivaling traditional physics models while maintaining our massive speed advantage.

**Read our full Pitch & Roadmap here:** [docs/FUTURE_IMPROVEMENTS.md](docs/FUTURE_IMPROVEMENTS.md)

For a deeper dive into the project's logic and architecture, please read the [Main Project Explainer](PROJECT_EXPLAINER.md).
