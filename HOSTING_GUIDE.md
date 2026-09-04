# CycloneWatch: Hosting & Deployment Guide

This guide provides step-by-step instructions for deploying the CycloneWatch prototype to the internet for your SIH presentation. Read the entire guide before starting.

We split the deployment into two services:
1. **Frontend → Vercel** (Free, instant, zero-config for React/Vite)
2. **Backend + ML → Render** (Docker container with SQLite database)

**Estimated total time: 20–30 minutes** if your repository is already clean and the build works locally.

---

## Prerequisites

Before starting, make sure these work locally:
```bash
# Backend health check (from repo root)
cd backend
$env:DATABASE_URL="sqlite+aiosqlite:///cyclonewatch.db"
$env:PYTHONPATH="d:\PROJECTS\SIH26\backend;d:\PROJECTS\SIH26"
uvicorn app.main:app --host 127.0.0.1 --port 8001
# → visit http://localhost:8001/health — should return {"status":"ok"}

# Frontend build check
cd frontend
npm run build
# → Should complete with exit code 0, no TypeScript errors
```

If either of these fails locally, fix them first. Do not attempt deployment with a broken build.

---

## Step 1: Deploy the Frontend (Vercel)

### 1a. Push your latest code to GitHub
```bash
# From repo root
git add .
git commit -m "chore: final production build"
git push origin main
```

### 1b. Create a Vercel project
1. Go to [vercel.com](https://vercel.com) and log in with your GitHub account.
2. Click **"Add New" → "Project"**.
3. Click **"Import"** next to your `SIH26` GitHub repository.

### 1c. Configure the project
In the deployment configuration screen:
- **Framework Preset:** Select **Vite**
- **Root Directory:** Click **Edit** and type `frontend` (this tells Vercel to build from the `frontend/` subfolder)
- **Build Command:** Leave default (`npm run build`) — do not change
- **Output Directory:** Leave default (`dist`) — do not change

### 1d. Set the environment variable
In the **Environment Variables** section (still on the same configuration page before first deploy):
- **Key:** `VITE_API_BASE_URL`
- **Value:** `https://cyclonewatch-backend.onrender.com/api`

> ⚠️ **Important:** You will update this value after Step 2 when you know your actual Render URL. For now, use a placeholder — you can redeploy in 1 click after.

### 1e. Deploy
Click **"Deploy"**. Vercel will:
1. Clone your repository
2. Run `npm install` and `npm run build` inside the `frontend/` folder
3. Publish the `dist/` output to a global CDN

**Expected time: ~2 minutes.**

When complete, Vercel gives you a live URL like:
```
https://cyclonewatch-abc123.vercel.app
```
**Save this URL.** You will need it for the backend CORS configuration.

---

## Step 2: Deploy the Backend (Render)

### 2a. Verify the Dockerfile exists
The backend must have a Dockerfile. Check:
```bash
ls backend/Dockerfile
```

If it does not exist, see the Dockerfile section at the bottom of this guide.

### 2b. Update CORS origins
Before deploying, add your Vercel URL to the backend CORS configuration.

In `backend/app/core/config.py` or `.env`, set:
```
CORS_ORIGINS=https://cyclonewatch-abc123.vercel.app
```

Or if using the wildcard for development/demo:
```
CORS_ORIGINS=*
```

> For SIH demo purposes, `CORS_ORIGINS=*` is acceptable. In production, lock this to your Vercel URL.

### 2c. Create a Render Web Service
1. Go to [render.com](https://render.com) and log in with GitHub.
2. Click **"New" → "Web Service"**.
3. Connect your `SIH26` repository.

### 2d. Configure Render
| Setting | Value |
|---|---|
| **Name** | `cyclonewatch-backend` |
| **Region** | Singapore (closest to India — lowest latency) |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Environment** | **Docker** ← Critical! |
| **Instance Type** | **Standard ($7/mo)** — Free tier has only 512MB RAM; PyTorch requires ≥1GB |

### 2e. Set environment variables on Render
In the **Environment Variables** section on Render:

| Key | Value |
|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///cyclonewatch.db` |
| `CORS_ORIGINS` | `https://your-vercel-url.vercel.app` |
| `ML_FORCE_STUB` | `false` |
| `DEBUG` | `false` |

### 2f. Deploy
Click **"Create Web Service"**. Render will:
1. Clone your repository
2. Build the Docker image (downloads Python dependencies including PyTorch — takes ~10 minutes on first build)
3. Run the container

**Expected first build time: 8–15 minutes.**

When complete, Render gives you a URL like:
```
https://cyclonewatch-backend.onrender.com
```

Test it:
```bash
curl https://cyclonewatch-backend.onrender.com/health
# Expected: {"status":"ok","version":"v1"}
```

---

## Step 3: Connect Frontend to Backend

### 3a. Update the Vercel environment variable
1. Go to your Vercel dashboard.
2. Select the `cyclonewatch` project.
3. Go to **Settings → Environment Variables**.
4. Update `VITE_API_BASE_URL` to your actual Render URL:
   ```
   VITE_API_BASE_URL=https://cyclonewatch-backend.onrender.com/api
   ```
5. Click **Save**.

### 3b. Redeploy the frontend
1. Go to the **Deployments** tab in Vercel.
2. Click the **three-dot menu** on the latest deployment.
3. Click **"Redeploy"**.

The frontend will rebuild with the correct backend URL baked in.

---

## Step 4: Verify End-to-End

Open your Vercel URL and:
1. ✅ The CycloneWatch intro animation should play.
2. ✅ **LIVE tab:** Real wind/pressure/SST data from Open-Meteo should load (takes ~2 seconds).
3. ✅ **HISTORICAL tab → Select BIPARJOY 2023:** The timeline should populate with all 80+ timesteps.
4. ✅ **Map:** The Esri satellite base layer should load; NASA GIBS cloud layer should overlay.
5. ✅ **Metrics panel:** Classification pattern and confidence should display.

If any step fails, check the **Render logs** for backend errors and the **Browser DevTools Console** for frontend errors.

---

## Troubleshooting

### "Loading event data..." spinner never goes away
The frontend cannot reach the backend API.
- Check `VITE_API_BASE_URL` in Vercel environment variables (no trailing slash, starts with `https://`).
- Visit `https://your-backend.onrender.com/health` directly in a browser — if it fails, the backend is not running.
- Check Render logs for Python errors.

### Render deploy fails with "Out of memory"
The Free Tier (512MB) is not enough for PyTorch.
- Upgrade to the **Standard instance ($7/month)** on Render.

### Build fails: "Cannot find module"
- Run `npm run build` locally first and fix all TypeScript errors before pushing.

### CORS error in browser console
- The frontend URL is not in the backend's CORS whitelist.
- Update `CORS_ORIGINS` in Render environment variables and redeploy the backend.

### NASA GIBS cloud layer not showing
- This is a public API with rate limits. It may load slowly. Check the browser Network tab to see if GIBS tile requests are returning 200 or 429 (rate limited).

---

## Backend Dockerfile (Reference)

If `backend/Dockerfile` does not exist, create it:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set PYTHONPATH to include the parent directory for ml package
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Then create `backend/requirements.txt` if it does not exist (or update it):
```
fastapi>=0.111.0
uvicorn[standard]>=0.30.1
sqlalchemy[asyncio]>=2.0.0
aiosqlite>=0.20.0
pydantic>=2.7.0
pydantic-settings>=2.3.0
numpy>=1.26.0
torch
```

---

## Post-Deployment Checklist

Before your SIH presentation:

- [ ] Backend `/health` returns `{"status":"ok"}`
- [ ] Frontend loads without console errors
- [ ] LIVE mode shows real-time data (not "UPDATING..." forever)
- [ ] Selecting BIPARJOY 2023 loads the timeline (80+ steps)
- [ ] The NASA GIBS cloud layer appears on the map
- [ ] The Metrics panel shows pattern and confidence values
- [ ] Evidence drawer opens with frame ID
- [ ] Other cyclones (OCKHI 2017, AMPHAN 2020) also load successfully

You are ready for the presentation! ✅
