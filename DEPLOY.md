# Beginner Deployment Guide

This guide explains how to run and deploy the **Bengaluru Urban Flood Risk Intelligence Platform** from scratch after cloning from GitHub.

> **Important Scope Notice:** This is a **private research decision-support platform** (`public_dispatch_enabled = false`, `BLOCKED_EXPERIMENTAL_MODEL`). It is not an official government emergency warning system.

---

## Option 1 — Deploy on Render (Easiest for Your Friend)

Render automatically handles HTTPS, domain (`https://<app-name>.onrender.com`), and Docker builds.

### Step 1: Connect GitHub Repo
1. Log in to [Render](https://render.com) and click **New + → Blueprint** (or **New + → Web Service**).
2. Connect your GitHub account and select this repository (`branch: upgrade/v8-operational-ai`).
   - If using **Blueprint**, Render reads `render.yaml` automatically and configures everything (including generating `FLOODRISK_ADMIN_TOKEN` and setting Health Check Path to `/api/ready`).
   - If creating a **Web Service** manually:
     - **Runtime:** `Docker`
     - **Branch:** `upgrade/v8-operational-ai`
     - **Health Check Path:** `/api/ready`
     - **Environment Variables:**
       - `FLOODRISK_ADMIN_TOKEN` = *(any strong secret password)*
       - `FLOODRISK_ALLOWED_ORIGIN` = `https://<your-render-app>.onrender.com`
       - `FLOODRISK_REFRESH_INTERVAL_S` = `1800`

### Step 2: Optional Persistent Storage (Paid Starter+ Plan)
- On Render's **Starter** plan or higher, add a **Disk** mounted at `/app/data/state` (`1 GB`) so SQLite alert history and backups survive redeploys.
- On Render's **Free** tier, it still runs and fetches live Open-Meteo forecasts automatically on startup, but SQLite state resets whenever the free container spins down or redeploys.

### Step 3: Verify Live URL
Open `https://<your-render-app>.onrender.com` and check `/api/health` and `/api/ready`.

---

## Option 2 — Deploy with Docker (VPS / Self-Hosted)

### Prerequisites on the Server
- **Git**
- **Docker** and **Docker Compose** (`docker compose version`)

### Step 1: Clone the Repository
```bash
git clone -b upgrade/v8-operational-ai https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### Step 2: Create `.env` Configuration
```bash
cp .env.example .env
```
Generate a strong random admin token:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```
Open `.env` and set your token and domain:
```env
FLOODRISK_ADMIN_TOKEN=paste-your-generated-token-here
FLOODRISK_ALLOWED_ORIGIN=https://your-domain.com
FLOODRISK_REFRESH_INTERVAL_S=1800
FLOODRISK_LOG_LEVEL=INFO
```

### Step 3: Start the Application
```bash
docker compose up -d --build
```
Check that it is healthy (wait ~15 seconds):
```bash
curl http://127.0.0.1:8501/api/ready
curl http://127.0.0.1:8501/api/health
```
You should see `"ready": true` and `"grid_cells_loaded": 1170`.

### Step 4: Put HTTPS in Front (Caddy — Easiest)
Install Caddy on your VPS, then add this to `/etc/caddy/Caddyfile`:
```caddy
your-domain.com {
    reverse_proxy 127.0.0.1:8501
}
```
Reload Caddy:
```bash
sudo systemctl reload caddy
```
Your dashboard is now live at `https://your-domain.com`.

### Useful Docker Commands
- View logs: `docker compose logs -f`
- Restart: `docker compose restart`
- Stop: `docker compose down` (SQLite data is safely preserved in the `floodrisk_state` volume)

---

## Option 2 — Run Locally Without Docker (Python 3.11+)

```bash
python3 -m venv .venv
source .venv/bin/activate        # On Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
export PYTHONPATH=src            # On Windows PowerShell: $env:PYTHONPATH="src"
python -m floodrisk.dashboard.server --host 127.0.0.1 --port 8501
```
Open `http://127.0.0.1:8501` in your browser.

---

## Using Admin Actions in the Dashboard
In the **Alert Candidates** tab, paste your `FLOODRISK_ADMIN_TOKEN` into the **Admin token** box before clicking **Re-evaluate Now**, **Acknowledge**, or **Resolve**.
