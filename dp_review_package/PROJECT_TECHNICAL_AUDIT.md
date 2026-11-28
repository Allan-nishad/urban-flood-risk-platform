# Project Technical Audit — Design Project Review

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Repository:** `urban-flood-risk-platform`  
**Branch:** `upgrade/v8-operational-ai`  
**Audit Scope:** Read-only inspection of codebase, datasets, SQLite state, ML artifacts, and dashboard UI. No application logic, weights, datasets, or database were modified.

---

## 1. Complete Project Overview

### Plain-Language Summary
Urban flooding in Bengaluru happens when heavy rain falls on low-lying, heavily paved neighbourhoods with poor drainage. Conventional flood monitoring only reacts after waterlogging is reported or relies on coarse city-wide weather bulletins. This prototype combines **satellite terrain and land-cover maps**, **live 72-hour weather forecasts**, **historical flood records**, and **an interactive web dashboard** to highlight which 1 km² zones of Bengaluru face higher flood-risk priority—plus a **public-facing citizen safety page** with indicative routing and a `112` SOS button.

### Technical Details
- **Study Area:** Bengaluru Urban District, India (`bbox_wgs84`: `77.45°E–77.75°E`, `12.85°N–13.15°N`), **1,170** equal-area `1 km × 1 km` grid cells in `EPSG:6933`.
- **Technology Stack:** Python 3.11+, `pandas`, `numpy`, `pyarrow`, `geopandas`, `shapely`, `rasterio`, `pyproj`, `scikit-learn`, `xgboost`, `joblib`, `pydantic`, `click`, `sqlite3` (WAL mode), `http.server.ThreadedHTTPServer`, HTML/CSS/JS, **Leaflet.js + OpenStreetMap**, **OSRM** (public routing), **Docker / Render**.
- **Implemented vs. Experimental vs. Proposed:**
  - **Implemented & Operational:** Equal-area 1 km grid, SRTM/WorldCover/D8 static susceptibility & hydrology features, live Open-Meteo ECMWF IFS (`ecmwf_ifs025`) 0–72h ingestion, `1h–72h` rainfall windows, SQLite WAL persistence & online backups, rule-based `OperationalAlertEngine`, 5.5 km spatial alert clustering, REST API (`server.py`), Authority Dashboard (`/`), Flood Alert Center (4 Bengaluru zones + Demo Mode), Civilian Safety Page (`/civilian-alert.html`).
  - **Experimental (Non-Operational):** Random Forest & candidate ML classifiers (`src/floodrisk/ml/train.py`, `infer.py`) trained on 48 historical records (`EXPERIMENTAL_UNVALIDATED`, `BLOCKED_EXPERIMENTAL_MODEL`).
  - **Unavailable / External Dependency:** Live KSNDMC/IMD ground rain-gauge telemetry (`UNAVAILABLE`; public portal SSL/IP-whitelist restrictions).
  - **What the Prototype Can and Cannot Predict:** It **can** compute relative terrain+drainage+forecast risk-prioritisation indices (`[0, 1]`) and trigger provisional rule-based candidate alerts. It **cannot** predict calibrated street-level flood depth or flood probability, and `public_dispatch_enabled` is permanently `false`.

---

## 3. Grid Generation and Geospatial Processing

### Plain-Language Summary
We divided Bengaluru Urban into **1,170 equal-area squares** (`1 km × 1 km` each) so every cell represents the same ground area (`1 km²`). Each square gets a permanent ID (like `g1000_7489_1650`) and stores its average elevation, slope, paved area, drainage wetness, rainfall, and past flood reports.

### Technical Details
- **Coordinate Reference Systems:**
  - Storage/Display: `EPSG:4326` (WGS84 lat/lon).
  - Analysis/Grid: `EPSG:6933` (WGS84 / NSIDC EASE-Grid 2.0 Global, equal-area cylindrical projection) via `src/floodrisk/spatial/grid.py` and `crs.py`.
- **Grid Cell Identification:** `g{cell_size_m}_{col}_{row}` where `col = floor(x_6933 / 1000)` and `row = floor(y_6933 / 1000)`. Total cells = `1,170` (`~1,170 km²`).
- **Spatial Association Methods:**
  - **SRTM DEM (30m) & ESA WorldCover (10m):** Zonal statistics aggregated to each 1 km cell (`src/floodrisk/processing/zonal.py`).
  - **D8 Hydrology:** Deterministic O'Callaghan & Mark (1984) flow direction, upstream contributing area (`km²`), and `TWI = ln(a / tan(beta))` (`data/processed/phase6/hydrology/topographic_routing_static_features.parquet`).
  - **Flood Incidents:** Spatial join (point-in-polygon / nearest cell) with recorded spatial uncertainty radius (`spatial_uncertainty_m`).
  - **Coarse Weather Data (0.25° ~27.8 km):** Nearest-anchor assignment (`assign_cell_to_forecast_zone` in `src/floodrisk/alerts/spatial.py`) using `NEAREST_SECTOR_ANCHOR_NO_INTERPOLATION` within `25.0 km` across 5 Bengaluru sector anchors (which snap to **2 distinct native ECMWF IFS 0.25° nodes**: `[13.0, 77.5]` and `[13.0, 77.75]`). No artificial spatial downscaling is fabricated.
- **Worked Real Grid Cell:** `g1000_7489_1650` (`col_idx=7489`, `row_idx=1650`, `13.0472°N, 77.6224°E`, `elevation_mean_m=881.94 m`, `elevation_std_m=1.9 m`, `built_up_fraction=0.8582`, `has_ground_flood_evidence=True`).

---

## 6. Static Susceptibility Assessment (`src/floodrisk/processing/dynamic_risk.py`)

### Plain-Language Summary
Static susceptibility measures how flood-prone a cell is based purely on its **permanent physical geography** (low elevation, flat slope, and heavy concrete/built-up cover vs. trees/cropland), regardless of today's weather.

### Exact Formula & Manually Selected Weights
All weights are **manually selected domain/MCDA weights** (not machine-learning-optimised):
1. **Terrain Susceptibility (`baseline_terrain_susceptibility`):**
   - `e_norm = (elevation_mean_m - 755.5400) / (944.5500 - 755.5400)`
   - `std_norm = (elevation_std_m - 1.5000) / (18.6200 - 1.5000)`
   - `S_terrain = clip(0.60 * (1 - e_norm) + 0.40 * (1 - std_norm), 0, 1)`
2. **Land-Cover Runoff (`baseline_landcover_runoff`):**
   - `lc_raw = 0.75 * built_up + 0.25 * water - 0.20 * (tree_cover + cropland)`
   - `S_landcover = clip((lc_raw - (-0.184795)) / (0.741060 - (-0.184795)), 0, 1)`
3. **Static Susceptibility Score:**
   - `S_static = clip(0.50 * S_terrain + 0.50 * S_landcover, 0, 1)`

### Manual Calculation for `g1000_7489_1650`
- `e_norm = (881.94 - 755.54) / (944.55 - 755.54) = 126.40 / 189.01 = 0.66875`
- `std_norm = (1.90 - 1.50) / (18.62 - 1.50) = 0.40 / 17.12 = 0.02336`
- `S_terrain = 0.60 * (1 - 0.66875) + 0.40 * (1 - 0.02336) = 0.19875 + 0.39066 = 0.58941` (stored: `0.589406`)
- `lc_raw = 0.75 * 0.8582 + 0.25 * 0.0 - 0.20 * (0.0476 + 0.0454) = 0.64365 - 0.01860 = 0.62505`
- `S_landcover = (0.62505 - (-0.184795)) / (0.741060 - (-0.184795)) = 0.809845 / 0.925855 = 0.87470` (stored: `0.874700`)
- **`S_static = 0.50 * 0.58941 + 0.50 * 0.87470 = 0.73205`** (Rank `#12 / 1,170`).

---

## 7. Dynamic Flood-Risk Prioritisation

Two complementary dynamic scoring paths exist in the repository:
1. **Batch Phase 4.3 Baseline (`src/floodrisk/processing/dynamic_risk.py` -> `dynamic_risk_intelligence_bengaluru.parquet`):**
   - `S_obs = 0.55 * clip(obs_24h / 100, 0, 1) + 0.45 * clip(api_7d / 150, 0, 1)`
     For `g1000_7489_1650`: `0.55 * (12.5/100) + 0.45 * (35.0/150) = 0.06875 + 0.10500 = 0.17375` (stored: `0.1738`).
   - `S_fcst = 0.0738` (for `forecast_rainfall_24h_mm = 4.8 mm`, `LIGHT_RAINFALL_CATEGORY`).
   - **`dynamic_risk_prioritization_score = 0.35 * S_static + 0.30 * S_obs + 0.35 * S_fcst`**
     `= 0.35 * 0.73205 + 0.30 * 0.1738 + 0.35 * 0.0738 = 0.25622 + 0.05214 + 0.02583 = 0.33419`** (stored: `0.334188`, Rank `#12`, `RESEARCH_PRIORITY_LOW`).
   - **Monitoring Tiers:** `>=0.70` `RESEARCH_PRIORITY_VERY_HIGH`, `>=0.50` `HIGH`, `>=0.35` `MODERATE`, `<0.35` `LOW`.
2. **Live V8 Forecast-Driven Risk Engine (`src/floodrisk/alerts/risk_engine.py`, `/api/risk/forecast`):**
   - Combines `0.35 * terrain_factor + 0.20 * drainage_factor(TWI, UPA) + 0.15 * landcover_factor + 0.30 * forecast_rain_factor` across horizons `1, 3, 6, 12, 24, 48, 72`h (`LOW`, `ELEVATED`, `MODERATE`, `HIGH`, `CRITICAL`, or `INSUFFICIENT_DATA` if stale/missing/out-of-coverage).
- **Circularity Prevention:** Historical flood incident labels are **deliberately excluded** from both formulas (`dynamic_risk.py` lines 104–105). The output is an **uncalibrated exploratory screening/prioritisation index**, **not** a flood probability.

---

## 11. Weather Forecast Reliability Evaluation (`Phase 6B` / `Phase 7B`)

- **Source Files:** `data/processed/phase6/ground_rainfall/gfs_vs_gauge_validation_metrics.parquet` & `rain_gauge_station_registry.parquet`, `data/processed/phase7/nwp/phase7_forecast_error_registry.parquet`.
- **Verified Metrics (exact values from parquet):**
  - **Stations:** `21` total catalogued (`IMD`, `KSNDMC`, `CPCB`), **`16` primary hydrological rain gauges** used in validation.
  - **Period & Sample Size:** `2022-08-25` to `2022-09-09`, **`256` matched station-date pairs** (16 stations × 16 days).
  - **Mean Bias (`forecast - observed`):** **`-10.875 mm`** (`-10.88 mm`).
  - **MAE (`|error|`):** **`18.64 mm`**.
  - **Pearson Correlation (`r`):** **`0.1421`** (`0.142`).
  - **Heavy-Rain Threshold (`>= 64.5 mm`):** `hits = 0`, `misses = 23`, `false_alarms = 0`, **`POD = 0.0000`**.
- **Interpretation:** Coarse 0.25° (~27.8 km) GFS grid cells average convective storms over a ~770 km² footprint, severely underestimating intense local rainfall peaks (`-10.88 mm` bias, `0.000` POD at 64.5 mm). Currently, forecast reliability **does not** dynamically re-weight runtime scores or alerts (reliability-weighted fusion is a proposed future enhancement).

---

## 12. Flood Evidence Classification

- **3-State Classification (`data/processed/phase6/flood_evidence/flood_validation_ground_truth_matrix.parquet`):**
  - `VERIFIED_POSITIVE`: **`13` cells** (confirmed standing water / BBMP & field records).
  - `VERIFIED_NEGATIVE`: **`7` cells** (monitored high-ground/campus/park dry control sites).
  - `UNOBSERVED_DOMAIN_CELL`: **`1,150` cells** (**98.29%** of domain).
- **Rule:** Missing flood report ≠ dry (`UNOBSERVED` cells are **never** converted to negative `0` labels in ML training or false-alarm calculations). Visible in the Dashboard under `Multi-Source Intelligence` & `Scientific Validation` tabs.

---

## 13. Alert Management and Spatial Clustering (`src/floodrisk/alerts/`)

- **Rule Thresholds (`rules.py` `AlertRuleConfig`):** Provisional thresholds (`15.6`, `35.0`, `64.5 mm / 24h`, `15.0 mm/h` peak) combined with static susceptibility (`0.45`, `0.60`). Skips generation if forecast freshness is not `LIVE`/`RECENT`.
- **Lifecycle (`engine.py`, `storage.py`):** `ACTIVE` → `ACKNOWLEDGED` → `RESOLVED` / `EXPIRED`, persisted in SQLite (`alerts`, `alert_audit_log`, `alert_evaluation_runs`) with one open alert per `grid_id` (escalation/de-escalation updates in place) and a `120-minute` cooldown after resolution/expiration.
- **Spatial Clustering (`clustering.py`):** Groups open alerts deterministically by `(forecast_zone_id, ~5.5 km spatial tile)` (`0.05°` grid). Clustering uses open alert severity and coordinates—it does **not** implement evidence-aware dual-priority hotspot clustering (which remains proposed).

---

## 17. System Architecture and Complete Working Process

```text
Open-Meteo (ECMWF IFS 0.25°, 5 anchors, 0-72h) ──▶ LiveWeatherRefresher (30m schedule, 3 retries)
                                                          │
SRTM 30m + WorldCover 10m + D8 Hydrology + Incidents      ▼
        │                                          SQLite WAL (floodrisk_v8.db)
        ▼                                                 │
Static Susceptibility & Risk Engine ◀─────────────────────┘
        │                                                 │
        ├──────────────────▶ OperationalAlertEngine ──────┤
        │                                                 ▼
        └──────────────────▶ ThreadedHTTPServer (REST API + Gzip + Auth)
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
     Authority Dashboard (/)               Civilian Safety Page (/civilian-alert.html)

Separate Experimental Branch:
Stage 2 Event-Grid Dataset (48 labeled rows) ──▶ Random Forest (train.py / infer.py) ──▶ /api/ml/experimental (Advisory Only)
```
