# CycloneWatch: Future Roadmap & Pending Work

*This document outlines the strategic improvements planned for CycloneWatch if selected for the next phase of the Smart India Hackathon. These are the key talking points for pitching the future of the project.*

---

## 1. Data Scaling: The MOSDAC Integration 🎯
Our current AI model is trained on NOAA GridSat-B1 imagery, which has a spatial resolution of **4 km/pixel**. This limits the model's ability to see critical micro-structures like early inner eyewall formation.

**The Plan:**
- Obtain formal research access to ISRO's **MOSDAC (Meteorological & Oceanographic Satellite Data Archival Centre)**.
- Train the next iteration of the model on **INSAT-3DR imagery**, which provides **1 km/pixel resolution**.
- **Expected Impact:** 16x more spatial detail per image will allow the model to drastically improve its centre-positioning accuracy (reducing MAE from ~255 km to <150 km) and detect Rapid Intensification (RI) signatures even earlier.

## 2. Advanced Temporal Forecasting (ConvLSTM / GRU) 🏗️
Currently, our T+12h and T+24h predictions use a persistence-based physical fallback (extrapolating current speed and direction).

**The Plan:**
- We have already staged a temporal sequence architecture (`ml/inference.py`).
- Once we scale the training dataset to include 50+ historical events, we will train a **Convolutional LSTM (ConvLSTM) or GRU** model.
- Instead of treating each satellite frame in isolation, this model will ingest the *sequence* of the last 4 frames (12 hours) to learn motion dynamics.
- **Expected Impact:** The model will learn to predict recurvature (storms changing direction) natively, driving T+24h forecast errors down to operational levels (< 100 km).

## 3. Dataset Expansion 📊
The current prototype is trained on 7 carefully selected gap cases (423 frames). While sufficient to prove the structural pattern-matching concept, it needs broader data to generalize to all anomalies.

**The Plan:**
- Download and process an additional **30–50 North Indian Ocean cyclones** (e.g., Yaas 2021, Mocha 2023, Gaja 2018).
- **Expected Impact:** A massive reduction in model bias and improved performance on rare tracks (e.g., extremely low-latitude formations).

## 4. Model Calibration & Uncertainty Confidence 📉
Currently, the model outputs a raw "Confidence %" (softmax probability) for its structural pattern prediction. 

**The Plan:**
- Apply **Temperature Scaling** on a validation set to calibrate these probabilities.
- **Expected Impact:** When the model says "80% confidence," it will statistically mean it is correct 80% of the time, making the output mathematically reliable for duty meteorologists.

## 5. Adding the Visible Light Channel 🛰️
Currently, the model relies on Infrared (IR) and Water Vapor (WV) channels because they are available 24/7 (including at night).

**The Plan:**
- Feed the **Visible spectrum channel** into the model during daytime hours.
- **Expected Impact:** Visible imagery provides incredibly sharp texture details of the cloud canopy (overshooting tops, gravity waves) which are strong leading indicators of rapid intensification.

## 6. Operational "First-Look" Alert System 🚨 (End Goal)
The ultimate goal is not a standalone dashboard, but integration into the actual meteorological workflow.

**The Plan:**
- Develop a webhook-based alert system.
- When the model processes a new live satellite image and detects a critical state change (e.g., `DISORGANIZED` → `CURVED BAND` at a low latitude), it immediately pings the duty meteorologist.
- **Expected Impact:** Closes the "Interpretation Gap." The AI serves as an automated, tireless sentry that directs human attention to the right storm at the exact moment structural danger appears.
