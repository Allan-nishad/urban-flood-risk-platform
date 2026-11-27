# Bengaluru Urban Flood Risk Intelligence Platform

**AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CRS EPSG:6933](https://img.shields.io/badge/CRS-EPSG%3A6933-green.svg)](https://epsg.io/6933)
[![Tests: 171 Passing](https://img.shields.io/badge/tests-171%20passing-brightgreen.svg)](#testing)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An operational research platform for **Bengaluru Urban District** (`1,170` equal-area `1 km × 1 km` grid cells) combining **live 72-hour weather forecasts**, **satellite terrain and drainage analysis**, an **interactive flood-risk dashboard**, and a **public-facing civilian safety page**.

> **Scope Notice:** This is a **research decision-support platform** (`public_dispatch_enabled = false`, `EXPERIMENTAL_UNVALIDATED`). For official public emergency warnings in Bengaluru, always follow **IMD**, **KSNDMC**, and **BBMP**.

---

## Key Features

- **Live 72-Hour Weather Forecasting:** Fetches hourly **ECMWF IFS (`ecmwf_ifs025`)** forecasts via Open-Meteo across 5 Bengaluru sector anchors, computing cumulative and peak rainfall across **1h, 3h, 6h, 12h, 24h, 48h, and 72h** windows with SQLite WAL persistence and refresh history.
- **Terrain, Drainage & Flood-Risk Engine:** Integrates **SRTM 30m elevation**, **D8 flow accumulation & Topographic Wetness Index (TWI)**, **ESA WorldCover 10m** built-up/water/vegetation fractions, and historical flood evidence into a reproducible risk-prioritisation index.
- **Flood Alert Center & Automatic Alert:**
  - **4 Bengaluru Zone Cards:** North, South, East, and West Bengaluru.
  - **Real-Data Evaluation:** Evaluates live Open-Meteo forecasts against provisional rainfall & terrain thresholds.
  - **Controlled Demonstration Mode (`DEMO MODE`):** Simulates zone-level rainfall scenarios (`10`, `20`, `35`, `50` mm/h) with instant danger popups, map highlighting, alert acknowledgement/resolution, and browser-local history.
- **Civilian Safety Page (`/civilian-alert.html`):**
  - Responsive, standalone citizen-facing alert page with **Leaflet + OpenStreetMap** zone highlighting, **suggested demonstration destinations**, indicative **OSRM** routing (with graceful offline fallback), **Copy / Share Link**, and an **India 112 SOS** dialler button (`tel:112`).
- **Experimental ML Benchmark:** Random Forest model trained on 48 historical flood/control records with spatial-block cross-validation and feature importance explanations (retained strictly as supporting research context).

---

## Quick Start

### 1. Run Locally (Python 3.11+)
```powershell
git clone -b upgrade/v8-operational-ai https://github.com/Allan-nishad/urban-flood-risk-platform.git
cd urban-flood-risk-platform

python -m venv .venv
.venv\Scripts\Activate.ps1       # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
$env:PYTHONPATH="src"            # Linux/macOS: export PYTHONPATH=src

python -m floodrisk.dashboard.server --host 127.0.0.1 --port 8501
```
Open:
- **Authority Dashboard:** `http://127.0.0.1:8501/`
- **Civilian Safety Page:** `http://127.0.0.1:8501/civilian-alert.html`

### 2. Deploy Online (Render / Docker)
See **[DEPLOY.md](DEPLOY.md)** for step-by-step instructions:
- **Render (One-Click Blueprint):** Connect this repo in Render (**New + → Blueprint**). `render.yaml` and `Dockerfile` automatically configure `$PORT`, `/api/ready` health checks, and `FLOODRISK_ADMIN_TOKEN`.
- **Docker Compose (VPS):**
  ```bash
  cp .env.example .env           # Set FLOODRISK_ADMIN_TOKEN
  docker compose up -d --build
  ```

---

## Data Sources & Methodology

| Layer | Dataset / Provider | Resolution / Coverage | Role |
| :--- | :--- | :--- | :--- |
| **Weather Forecast** | Open-Meteo (`ecmwf_ifs025`) | 0.25° (~27.8 km), 5 Bengaluru anchors | Live 0–72h rainfall outlook |
| **Elevation & Drainage** | SRTM GL1 DEM + D8 Flow Routing | 30m DEM aggregated to 1 km grid | Elevation, slope, TWI, catchment area |
| **Land Cover** | ESA WorldCover (2021) | 10m aggregated to 1 km grid | Built-up, water, tree, cropland fractions |
| **Rain Gauges** | IMD & KSNDMC (21 stations) | Historical validation archive | Forecast-vs-gauge accuracy benchmarking |
| **Satellite Radar** | Copernicus Sentinel-1A GRD | 2022 monsoon acquisition | Post-event water-detection cross-validation |
| **Flood Evidence** | BBMP / News / Field Records | 21 legacy + 24 Phase 6 records | Non-circular historical reference layer |

For architecture diagrams and detailed methodology, see [docs/V8_ARCHITECTURE_AND_DATAFLOW.md](docs/V8_ARCHITECTURE_AND_DATAFLOW.md) and [docs/reports/](docs/reports/).

---

## Key REST Endpoints

| Endpoint | Description |
| :--- | :--- |
| `GET /` & `GET /civilian-alert.html` | Authority dashboard & public-facing civilian safety page |
| `GET /api/health` & `GET /api/ready` | Service health, SQLite WAL status, and readiness probe |
| `GET /api/weather/forecast` & `/api/weather/history` | Live 72h forecast, `1h–72h` rainfall windows, & refresh log |
| `GET /api/risk/forecast?horizon=24` | Grid-level & per-cell (`?grid_id=...`) 1h–72h risk timeline |
| `GET /api/alerts` & `/api/alerts/clusters` | Candidate alerts & 5.5 km spatial clusters |
| `GET /api/spatial/coverage` | Anchor-to-cell coverage & native 0.25° node audit |
| `GET /api/ml/experimental` | Experimental Random Forest metrics & explanations |
| `POST /api/alerts/evaluate` | Trigger real-data alert evaluation (token-protected) |

---

## Project Structure

```text
urban-flood-risk-platform/
├── configs/                # Study-area YAML configs (Bengaluru, Mysuru) & schemas
├── data/
│   ├── processed/          # Ready-to-serve 1,170-cell grids, hydrology & validation datasets
│   └── state/              # Runtime SQLite WAL database & backups (gitignored)
├── docs/
│   ├── V8_ARCHITECTURE_AND_DATAFLOW.md
│   └── reports/            # Stage 0–5 & final audit reports
├── models/v8_experimental/ # Serialized experimental Random Forest model & metadata
├── reports/                # SHA-256 dataset manifests & Phase 7 audit outputs
├── src/floodrisk/
│   ├── alerts/             # Alert engine, rules, spatial assignment, clustering, risk engine
│   ├── dashboard/          # HTTP server (gzip, auth, security headers) & static UI
│   ├── live/               # Open-Meteo adapter, 72h window metrics, scheduler, SQLite store
│   ├── ml/                 # Experimental ML feature prep, training & gated inference
│   ├── processing/         # Terrain, land cover, rainfall, hydrology & SAR processing
│   └── spatial/            # EPSG:6933 equal-area grid & boundary handling
├── tests/                  # Automated pytest & Playwright test suite
├── DEPLOY.md               # Beginner deployment guide (Render, Docker, Local)
├── Dockerfile
├── docker-compose.yml
├── render.yaml
└── requirements.txt
```

---

## Testing

Run the full automated suite (unit, API, security, SQLite persistence, and Playwright end-to-end UI tests):

```powershell
.venv\Scripts\python.exe -m pytest tests/ -q -W ignore
```

**Latest Verified Run:** `171 passed, 0 failed`.
