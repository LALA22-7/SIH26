# Backend Explainer: The Engine of CycloneWatch

*This document explains the backend of CycloneWatch in simple terms so anyone — technical or not — can understand what it does and how it works.*

---

## What is the Backend?
If the **Frontend** (what you see on your screen) is the dashboard of a car, the **Backend** is the engine under the hood. It does not look pretty, but it does all the heavy lifting — storing data, running the AI models, answering questions from the dashboard, and keeping everything organized.

## How it Works (The Flow)

```
Satellite Images → ML Model → Backend API → Frontend Dashboard
```

When you click on a cyclone in the CycloneWatch dashboard:

1. **The Request:** Your browser asks the backend: "Give me all the data for Cyclone Biparjoy replay."
2. **The Database Lookup:** The backend looks in its digital filing cabinet (the database) and finds every pre-computed prediction, error metric, and classification already stored for that cyclone.
3. **The Response:** The backend packages all the data neatly (in a format called JSON) and sends it back to the frontend, which draws it on the map.

### Why Pre-compute?
Running the AI model on a satellite image in real-time takes a few seconds. For a smooth demo, we **pre-run** all the analysis in advance and save the answers to the database. When you drag the timeline slider, the backend just reads from its filing cabinet — no waiting for AI to think.

---

## The 6 Endpoints (The Menu)

Think of the backend as a restaurant. The frontend is the customer, and these are the "menu items" it can order:

| Endpoint | What it does |
|---|---|
| `GET /health` | "Is the kitchen open?" — confirms the backend is alive |
| `GET /api/replay/{cyclone_name}` | Returns the full replay steps for a historical cyclone |
| `GET /api/metrics` | Returns accuracy scores (how well did the AI do on this cyclone?) |
| `GET /api/ps70/classifications/{cyclone_name}` | Returns the AI's structural label for every observation |
| `POST /api/ps70/classify` | "Look at this new image and classify it" (real-time inference) |
| `GET /api/ps70/frames/{frame_id}` | Returns metadata about a specific satellite frame |

---

## The Database

The backend uses **SQLite** — a file-based database that requires zero installation. It stores:

- **Events:** The 7 historical cyclones (name, basin, dates)
- **SatelliteFrames:** Metadata about each satellite image (timestamp, file path, geographic bounding box)
- **Classifications:** The AI's structural pattern label for each frame (eye, banding, curved_band, etc.)
- **Predictions:** The AI's T+12h and T+24h position guesses
- **MetricRows:** The error between the AI's prediction and the actual best-track position (Haversine distance in km)

---

## Key Buzzwords Explained

- **API (Application Programming Interface):** Think of this as a waiter in a restaurant. The frontend (customer) places an order. The waiter (API) takes it to the kitchen (database + ML model) and brings the result back. The customer doesn't need to know how the kitchen works — just what to order and what format the food arrives in.
- **FastAPI:** The specific Python framework we used to build the backend. It is exceptionally fast (rivals Node.js) and automatically generates interactive documentation at `/docs` — you can test every endpoint in your browser without writing a single line of code.
- **SQLite:** A lightweight database stored as a single file (`cyclonewatch.db`). No server installation required, perfect for a hackathon prototype. In production, this would be swapped for PostgreSQL + PostGIS for geographic queries.
- **Uvicorn:** The server that actually runs FastAPI. Think of it as the building the restaurant is in.
- **Pydantic:** A data validation library. Every piece of data that goes into or comes out of the API is validated against a strict schema. If the ML model returns a confidence value of "banana" instead of a number, Pydantic will catch it and raise an error immediately.
- **Haversine Formula:** The mathematical formula to calculate the true distance between two GPS coordinates on a spherical Earth. We use this to measure how many kilometers off the AI's storm prediction was from the actual IBTrACS best-track position.
- **CORS (Cross-Origin Resource Sharing):** A browser security rule. It prevents a website at `site-A.com` from secretly reading data from `bank.com`. We configure CORS in the backend to explicitly allow the Vercel frontend URL to make requests.
- **Precomputation:** Analyzing satellite images with AI takes computing power. Instead of making users wait during a demo, we "precompute" (calculate in advance) all the historical data and save the answers to the database. Replay then just reads from storage.

---

## What Makes Our Backend Interesting

Most hackathon backends are simple "CRUD" apps — Create, Read, Update, Delete. Our backend has two additional technical layers:

1. **Spatial Awareness:** Every cyclone position is a GPS coordinate. The database understands geography — it can answer questions like "what storm was within 500 km of Mumbai on this date?" This is a capability that standard databases don't have.
2. **ML Adapter Pattern:** The backend doesn't directly import the ML model code. Instead, it uses an "adapter" layer (`ml_adapter.py`) that can automatically switch between a "stub mode" (returns realistic fake data when the model isn't available) and "real mode" (calls the actual PyTorch model). This lets the frontend team build and test before the ML model was ready.

---

## Summary
The backend is a fast, organized API server that bridges the complex AI models and raw satellite data to the visual dashboard. It pre-computes all AI analysis, stores it efficiently, and serves it on demand in milliseconds — making the real-time interactive demo possible.
