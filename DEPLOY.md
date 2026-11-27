# Beginner Deployment Guide

This guide explains how to run and deploy the **Bengaluru Urban Flood Risk Intelligence Platform** from scratch after cloning from GitHub.

> **Important Scope Notice:** This is a **private research decision-support platform** (`public_dispatch_enabled = false`, `BLOCKED_EXPERIMENTAL_MODEL`). It is not an official government emergency warning system.

---

## Option 1 — Deploy with Docker (Recommended for Hosting / VPS)

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
