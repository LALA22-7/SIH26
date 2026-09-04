# CycloneWatch: Hosting & Deployment Guide

This guide provides step-by-step instructions for deploying the CycloneWatch prototype to the internet for your SIH presentation. Read the entire guide before starting.

We split the deployment into two services:
1. **Frontend -> Vercel** (Free, instant, zero-config for React/Vite)
2. **Backend + ML -> Ngrok or Cloudflared** (Local tunnel running from your laptop for zero-cost demoing)

**Estimated total time: 10-15 minutes**

---

## Prerequisites

Before starting, make sure these work locally:
```bash
# Backend health check (from repo root)
cd backend
$env:DATABASE_URL="sqlite+aiosqlite:///cyclonewatch.db"
$env:PYTHONPATH="d:\PROJECTS\SIH26\backend;d:\PROJECTS\SIH26"
uvicorn app.main:app --host 127.0.0.1 --port 8001
# -> visit http://localhost:8001/health — should return {"status":"ok"}

# Frontend build check
cd frontend
npm run build
# -> Should complete with exit code 0, no TypeScript errors
```

If either of these fails locally, fix them first. Do not attempt deployment with a broken build.

---

## Step 1: Deploy the Backend (100% Free Hackathon Method)

Because our backend uses heavy Machine Learning models (PyTorch), it requires at least 1GB of RAM to run without crashing. **"Free Tier" cloud providers (like Render, Heroku, or HF Docker) either charge money for this much RAM or will crash instantly on their 512MB free tiers.**

For a Hackathon presentation, the most bulletproof, zero-cost method is to **run the backend on your own laptop** (where you have plenty of RAM) and expose it to the internet using a secure tunnel like Ngrok or Cloudflare. 

### Option A: Ngrok (Fastest Setup)
1. Install [Ngrok](https://ngrok.com/download) and create a free account to get your authtoken.
2. Run your backend locally:
   ```bash
   cd backend
   $env:DATABASE_URL="sqlite+aiosqlite:///cyclonewatch.db"
   $env:PYTHONPATH="d:\PROJECTS\SIH26\backend;d:\PROJECTS\SIH26"
   uvicorn app.main:app --host 127.0.0.1 --port 8001
   ```
3. Open a **new terminal** and run Ngrok to tunnel port 8001 to the internet:
   ```bash
   ngrok http 8001
   ```
4. Ngrok will give you a "Forwarding" URL (e.g., `https://a1b2c3d4.ngrok-free.app`).
5. This URL is your live backend API! As long as your laptop is awake, Vercel can reach your backend.

### Option B: Cloudflare Quick Tunnels (No Account Needed)
If you don't want to make an Ngrok account, Cloudflare offers a completely free tunnel.

1. Install `cloudflared`:
   ```bash
   npm install -g cloudflared
   ```
2. Run your backend locally (same as Step 2 in Option A).
3. In a **new terminal**, run the tunnel:
   ```bash
   cloudflared tunnel --url http://localhost:8001
   ```
4. Cloudflare will give you a URL ending in `trycloudflare.com` (e.g., `https://random-words.trycloudflare.com`). This is your live backend API.

---

## Step 2: Deploy the Frontend (Vercel)

### 2a. Push your latest code to GitHub
```bash
# From repo root
git add .
git commit -m "chore: final production build"
git push origin main
```

### 2b. Create a Vercel project
1. Go to [vercel.com](https://vercel.com) and log in with your GitHub account.
2. Click **"Add New" -> "Project"**.
3. Click **"Import"** next to your `SIH26` GitHub repository.

### 2c. Configure the project
In the deployment configuration screen:
- **Framework Preset:** Select **Vite**
- **Root Directory:** Click **Edit** and type `frontend` (this tells Vercel to build from the `frontend/` subfolder)
- **Build Command:** Leave default (`npm run build`) — do not change
- **Output Directory:** Leave default (`dist`) — do not change

### 2d. Set the environment variable
In the **Environment Variables** section (still on the same configuration page before first deploy):
- **Key:** `VITE_API_BASE_URL`
- **Value:** Your Ngrok or Cloudflare URL + `/api` (e.g., `https://a1b2c3d4.ngrok-free.app/api`)

### 2e. Deploy
Click **"Deploy"**. Vercel will:
1. Clone your repository
2. Run `npm install` and `npm run build` inside the `frontend/` folder
3. Publish the `dist/` output to a global CDN

**Expected time: ~2 minutes.**

When complete, Vercel gives you a live URL like:
```
https://cyclonewatch-abc123.vercel.app
```

---

## Step 3: Verify the Live Dashboard

1. Open your Vercel URL in your browser.
2. ✅ **Live Data:** The "Atmosphere" and "Ocean" panels should populate with Open-Meteo data immediately.
3. ✅ **Historical Mode:** Select a cyclone from the dropdown. The timeline should populate.
4. ✅ **Map:** The Esri satellite base layer should load; NASA GIBS cloud layer should overlay.
5. ✅ **Metrics panel:** Classification pattern and confidence should display.

If any step fails, check the backend terminal (if using Ngrok) or the **Browser DevTools Console** for frontend errors.

---

## Troubleshooting

### "Loading event data..." spinner never goes away
The frontend cannot reach the backend API.
- Check `VITE_API_BASE_URL` in Vercel environment variables (no trailing slash, starts with `https://`).
- Visit `https://your-backend-url/health` directly in a browser — if it fails, the backend is not running.
- Ensure your laptop didn't go to sleep and Ngrok/Cloudflared is still running.

### Build fails: "Cannot find module"
- Run `npm run build` locally first and fix all TypeScript errors before pushing.

### CORS error in browser console
- The frontend URL is not in the backend's CORS whitelist.
- For a demo, set `CORS_ORIGINS=*` in the backend code and restart the server.

### NASA GIBS cloud layer not showing
- This is a public API with rate limits. It may load slowly. Check the browser Network tab to see if GIBS tile requests are returning 200 or 429 (rate limited).
