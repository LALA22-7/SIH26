# CycloneWatch — Frontend Dashboard

React + TypeScript + Vite web application powering the CycloneWatch visual command center for PS70 — SIH 2026.

---

## What This Is

The CycloneWatch frontend is a **Single-Page Application (SPA)** that provides:

- **Live Monitoring Mode:** Real-time atmospheric and ocean data (wind speed, pressure, SST, wave height) fetched from Open-Meteo API for both Bay of Bengal and Arabian Sea basins.
- **Historical Archive Mode:** Full replay of 7 historical cyclones (2013–2023) with satellite imagery, ML-predicted tracks, and T+12h/T+24h forecast errors visualized on an interactive Leaflet map.
- **ML Evidence Panel:** Structural classification output from the `ps70-classifier` model — pattern label, confidence, frame ID, and the raw satellite image that generated the prediction.
- **Timeline Slider:** Scrollable, clickable timeline that steps through every 3-hourly observation for any selected cyclone.

---

## Folder Structure

```
frontend/
+-- src/
¦   +-- App.tsx                     # Root component: mode switching, layout, timeline auto-play
¦   +-- main.tsx                    # React entry point
¦   +-- index.css                   # Global CSS, design tokens, Tailwind utilities
¦   ¦
¦   +-- store/
¦   ¦   +-- useCycloneStore.ts      # Zustand global state — all API fetches live here
¦   ¦
¦   +-- data/
¦   ¦   +-- cyclones.ts             # Static cyclone metadata (names, dates, IMD gap notes)
¦   ¦
¦   +-- components/
¦   ¦   +-- IntroAnimation.tsx      # Boot-up animation shown on first load
¦   ¦   +-- TopNavigation.tsx       # Mode switcher (LIVE / HISTORICAL) + cyclone dropdown
¦   ¦   ¦
¦   ¦   +-- Dashboard/
¦   ¦       +-- LeafletMap.tsx      # Interactive map — base tiles + NASA GIBS clouds + track markers
¦   ¦       +-- SatellitePanel.tsx  # Wraps LeafletMap, handles layer toggles and map controls
¦   ¦       +-- MetricsPanel.tsx    # Right-side panel — live data or historical ML metrics
¦   ¦       +-- Timeline.tsx        # Scrollable timestep bar (historical mode only)
¦   ¦       +-- EvidenceDrawer.tsx  # Slide-out drawer showing raw satellite frame + classification
¦   ¦
¦   +-- assets/                     # Static assets (logo, icons)
¦
+-- public/                         # Static files served as-is
+-- dist/                           # Production build output (generated — do not commit)
+-- index.html
+-- vite.config.ts
+-- tailwind.config.js
+-- tsconfig.json
+-- package.json
```

---

## Quick Start

```bash
# Install dependencies
npm install

# Start development server (hot-reload)
npm run dev
# ? http://localhost:5173

# Type-check only
npx tsc --noEmit

# Production build
npm run build
```

---

## Environment Variables

Create a `.env.local` file at `frontend/` (never commit this):

```env
# Backend API root — no trailing slash
VITE_API_BASE_URL=http://localhost:8001/api
```

For production (Vercel), set `VITE_API_BASE_URL` in your Vercel project Environment Variables dashboard.

---

## API Contract

The frontend makes the following requests to the backend:

| Call | Endpoint | When |
|---|---|---|
| Fetch replay steps | `GET /api/replay/{event_id}` | On cyclone selection |
| Fetch ML metrics | `GET /api/metrics?event_id={event_id}` | On cyclone selection |
| Fetch classifications | `GET /api/ps70/classifications/{event_id}` | On cyclone selection |
| Live atmospheric data | Open-Meteo (external) | On LIVE mode |
| Live marine data | Open-Meteo Marine (external) | On LIVE mode |

All data fetching is centralized in `src/store/useCycloneStore.ts`.

---

## Map Layers

The map uses two tile providers stacked:

1. **Base Layer:** Esri World Imagery — high-resolution satellite terrain.
2. **Cloud Layer:** NASA GIBS MODIS Terra True Color — real satellite cloud imagery matched to the selected cyclone date. The URL includes the date dynamically from the observation timestamp, so you see the actual clouds from that day.

---

## Supported Cyclones

| ID | Name | Year | Basin |
|---|---|---|---|
| `biparjoy_2023` | BIPARJOY | 2023 | Arabian Sea |
| `amphan_2020` | AMPHAN | 2020 | Bay of Bengal |
| `fani_2019` | FANI | 2019 | Bay of Bengal |
| `tauktae_2021` | TAUKTAE | 2021 | Arabian Sea |
| `ockhi_2017` | OCKHI | 2017 | Arabian Sea |
| `hudhud_2014` | HUDHUD | 2014 | Bay of Bengal |
| `phailin_2013` | PHAILIN | 2013 | Bay of Bengal |

---

## Design System

The UI uses a custom dark ocean design system in `src/index.css`. Key tokens:

- `ocean-950/900/800/750` — dark background palette
- `text-text-primary/secondary/muted/faint` — text hierarchy
- `text-ir`, `text-wv`, `text-confidence`, `text-alert` — semantic meteorological colors
- `glass-card`, `glass-chrome` — glassmorphism utility classes

---

For further reading:
- [EXPLAINER.md](EXPLAINER.md) — Plain-English explanation for non-technical readers.
- [Main Project README](../README.md) — Full project overview.
