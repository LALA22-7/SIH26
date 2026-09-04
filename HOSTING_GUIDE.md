# CycloneWatch: Hosting & Deployment Guide

This guide provides step-by-step instructions for deploying the CycloneWatch prototype to the internet for your SIH presentation. Read the entire guide before starting.

We split the deployment into two services:
1. **Frontend → Vercel** (Free, instant, zero-config for React/Vite)
2. **Backend + ML → Hugging Face Spaces** (Free Docker container with 16GB RAM) OR **Ngrok** (Local tunnel for zero-cost demoing)

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

## Step 2: Deploy the Backend (Free Alternatives)

Because our backend uses heavy Machine Learning models (PyTorch), it requires at least 1GB of RAM to run without crashing. Most "Free Tier" cloud providers (like Render or Heroku) only give you 512MB of RAM, which will crash instantly. 

Here are the two best 100% free ways to host the backend for your presentation:

### Option A: Render (Free Tier with PyTorch Optimization)
You *can* host on Render's 512MB Free Tier if we force PyTorch to use the lightweight CPU-only version. If we use the default PyTorch, it downloads 2GB of CUDA binaries and crashes Render instantly.

1. In your `backend/` folder, create a file named `requirements.txt` exactly like this:
   ```text
   --extra-index-url https://download.pytorch.org/whl/cpu
   fastapi>=0.111.0
   uvicorn[standard]>=0.30.1
   sqlalchemy[asyncio]>=2.0.0
   aiosqlite>=0.20.0
   pydantic>=2.7.0
   pydantic-settings>=2.3.0
   numpy>=1.26.0
   torch
   ```
2. Replace your `backend/Dockerfile` with the optimized one at the bottom of this guide.
3. Push to GitHub.
4. Go to [Render](https://render.com), create a New Web Service connected to your repo.
5. Set Root Directory to `backend` and Environment to `Docker`.
6. Set the `DATABASE_URL` environment variable to `sqlite+aiosqlite:///cyclonewatch.db`.
7. Set `CORS_ORIGINS=*`
8. Deploy! Render will build the lightweight image and it should run within 512MB RAM.

### Option B: Hugging Face Spaces (Best for always-on Cloud)
Hugging Face Spaces gives you a free Docker environment with 16GB of RAM and 2 vCPUs — perfect for PyTorch APIs.

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and create a free account.
2. Click **Create new Space**.
3. **Space name:** `cyclonewatch-api`
4. **License:** `MIT`
5. **Select the Space SDK:** Choose **Docker** (Blank).
6. **Space Hardware:** Free (2 vCPU, 16GB RAM).
7. Click **Create Space**.
8. Hugging Face provides instructions on how to clone this blank space. Clone it to your computer, then copy **everything** inside your `backend/` folder into that cloned repository.
9. Create a `Dockerfile` in that folder if you don't have one (see the reference at the bottom of this guide).
10. Commit and push back to Hugging Face.
11. Hugging Face will build the Docker container and give you a live URL (e.g., `https://yourusername-cyclonewatch-api.hf.space`).
12. *Note on CORS:* Make sure to update `CORS_ORIGINS=*` in your code before pushing, so Vercel can talk to it.

### Option B: Localhost + Ngrok (Most Reliable for Hackathon Demos)
Hackathon Wi-Fi is notoriously bad, and cloud servers can sometimes sleep. The most bulletproof, zero-cost method is to run the backend on your own laptop and expose it to the internet using Ngrok.

1. Install [Ngrok](https://ngrok.com/download) and create a free account to get your authtoken.
2. Run your backend locally:
   ```bash
   cd backend
   $env:DATABASE_URL="sqlite+aiosqlite:///cyclonewatch.db"
   $env:PYTHONPATH="d:\PROJECTS\SIH26\backend;d:\PROJECTS\SIH26"
   uvicorn app.main:app --host 127.0.0.1 --port 8001
   ```
3. Open a new terminal and run Ngrok to tunnel port 8001 to the internet:
   ```bash
   ngrok http 8001
   ```
4. Ngrok will give you a "Forwarding" URL (e.g., `https://a1b2c3d4.ngrok-free.app`).
5. This URL is your live backend API! As long as your laptop is awake, the internet can reach your backend.

## Step 3: Connect Frontend to Backend

3a. Update the Vercel environment variable
1. Go to your Vercel dashboard.
2. Select the `cyclonewatch` project.
3. Go to **Settings → Environment Variables**.
4. Update `VITE_API_BASE_URL` to your actual backend URL (either your Hugging Face Space URL or your Ngrok URL). Make sure to append `/api` to the end if your FastAPI routes require it.
   ```
   VITE_API_BASE_URL=https://your-chosen-backend-url/api
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

If any step fails, check the backend terminal (if using Ngrok) or the Hugging Face Spaces logs, and the **Browser DevTools Console** for frontend errors.

---

## Troubleshooting

### "Loading event data..." spinner never goes away
The frontend cannot reach the backend API.
- Check `VITE_API_BASE_URL` in Vercel environment variables (no trailing slash, starts with `https://`).
- Visit `https://your-backend-url/health` directly in a browser — if it fails, the backend is not running.
- If using Ngrok, ensure your laptop didn't go to sleep and Ngrok is still running.

### Build fails: "Cannot find module"
- Run `npm run build` locally first and fix all TypeScript errors before pushing.

### CORS error in browser console
- The frontend URL is not in the backend's CORS whitelist.
- If using Ngrok or Hugging Face, the easiest fix for a demo is to set `CORS_ORIGINS=*` in the backend code and restart the server/space.

### NASA GIBS cloud layer not showing
- This is a public API with rate limits. It may load slowly. Check the browser Network tab to see if GIBS tile requests are returning 200 or 429 (rate limited).

---

## Backend Dockerfile (Optimized for Free Tier)

If you are using Option A (Render Free Tier), replace your `backend/Dockerfile` with this exact code. It disables cache and forces a lightweight build:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set PYTHONPATH to include the parent directory for ml package
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run the server (1 worker to save RAM)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
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
