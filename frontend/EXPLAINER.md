# Frontend Explainer: The Face of CycloneWatch

*This document explains the Frontend of CycloneWatch in simple terms so anyone — technical or not — can understand what it does and how it works.*

---

## What is the Frontend?
The **Frontend** is everything you see and interact with on your screen. It is the visual dashboard, the maps, the buttons, and the panels. If the backend is the car engine, the frontend is the steering wheel, the speedometer, and the GPS display.

## How it Works
The frontend is a web application that runs inside your browser. It does not do any heavy math or AI predictions itself. Instead, it talks to the Backend via the internet, asks for the data, and presents it in a beautiful, understandable way.

### When you select a cyclone from the dropdown:
1. The frontend sends a request to the backend: "Give me all historical replay steps for Cyclone Biparjoy."
2. The backend retrieves the pre-computed ML predictions from its database and sends them back.
3. The frontend draws the storm's track as a glowing line on the interactive map.
4. The NASA GIBS satellite imagery for that specific date loads automatically — you are looking at real clouds from the actual day of the event.
5. The metrics panel populates with the AI model's classification (e.g., "EYE structure detected") and position error data.

### The Timeline Slider:
- Each dot on the timeline represents one 3-hour satellite observation during the storm's lifetime.
- Clicking any dot instantly updates the entire dashboard — the map, the cloud layer, the classification, and the prediction errors all sync together.
- You can scroll horizontally through the timeline because major cyclones like Biparjoy had over 80 observation steps across 10+ days.

---

## What You Are Actually Seeing on the Map

| Element | What it is |
|---|---|
| 🟡 Yellow line | The ML model's predicted track (where it thought the storm would go) |
| ⚪ White dots | Actual observed storm positions (from IBTrACS best-track data) |
| 🔵 Blue circle | Current active observation marker |
| ☁️ Cloud layer | Real NASA MODIS satellite imagery from that exact date |
| 🔴 Red area | Forecast uncertainty region |

---

## Live Monitoring Mode
When switched to LIVE mode, the dashboard connects to the **Open-Meteo API** (a free, real-time weather data provider) and pulls actual current measurements for wind, pressure, rainfall, sea surface temperature, and wave height for either the Bay of Bengal or Arabian Sea. This is 100% real data, updated every 60 minutes.

---

## Key Buzzwords Explained

- **SPA (Single Page Application):** Traditional websites reload the entire page every time you click. An SPA loads the framework once and only updates the specific pieces that change. This makes the dashboard feel instant and app-like.
- **React:** Facebook's open-source toolkit for building interactive UIs using reusable components. Every card, button, and panel on the CycloneWatch screen is one React "component."
- **Zustand:** A lightweight state manager. All the data (which cyclone is selected, what the ML model said, is the map playing) lives in one central "store" that every component can read from.
- **Leaflet:** The industry-standard JavaScript map library. It handles the interactive world map, tile loading, and rendering of lines and markers.
- **NASA GIBS:** NASA's Global Imagery Browse Services — a free API that provides historical satellite imagery by date. We use it to overlay real cloud data on the map matching the cyclone's timeline.
- **Tailwind CSS:** A utility-first CSS framework that lets us define the dark ocean color palette, glassmorphism effects, and responsive layout without writing raw CSS files.
- **GeoJSON:** The standard format for geographic shapes. When the AI predicts an uncertainty region for the storm, it returns a GeoJSON polygon that Leaflet draws on the map as a transparent colored area.
- **Vite:** The modern build tool that compiles the TypeScript/React code into a fast, optimized bundle for the browser.

---

## How the Dashboard Handles No-Internet Scenarios

The historical data (replay steps, ML predictions, classification labels) is **pre-computed and stored in the backend database**. Once the backend is running (locally or on Render), the historical archive works completely offline — the backend makes no external API calls during replay.

The live monitoring mode and NASA GIBS cloud imagery do require internet.

---

## Summary
The frontend translates massive, complex ML model outputs into a highly intuitive visual command center. It shows emergency responders not just a number on a screen, but the actual satellite image the AI was looking at, the pattern it detected, and exactly how far off its prediction was — making the AI's reasoning transparent and verifiable.
