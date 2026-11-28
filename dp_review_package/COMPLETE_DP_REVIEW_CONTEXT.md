# Complete Design Project Review Context (Consolidated Reference)

Use this single document as complete factual context for slide decks, research paper presentation, prototype demonstration, and viva Q&A. Every figure, file path, formula, and metric below was directly verified from the repository.

---

## 1. Project Identity & Current State
- **Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data
- **Study Area:** Bengaluru Urban District (`77.45°E–77.75°E`, `12.85°N–13.15°N`), **1,170** equal-area `1 km × 1 km` cells (`EPSG:6933`, IDs `g1000_{col}_{row}`).
- **Branch:** `upgrade/v8-operational-ai` (Frozen V7.2 baseline untouched; `171` automated tests passing).
- **Deployment:** Python 3.11 + SQLite WAL (`data/state/floodrisk_v8.db`) + `ThreadedHTTPServer` (`src/floodrisk/dashboard/server.py`) + Docker / Render (`render.yaml`, `Dockerfile`).
- **Safety Gates:** `public_dispatch_enabled = False`, ML status = `EXPERIMENTAL_UNVALIDATED` / `BLOCKED_EXPERIMENTAL_MODEL`.

## 2. Core Datasets Used
- **Static Terrain & Land Cover (1,170 cells):** SRTM GL1 30m DEM (`elevation_mean_m`: `755.54–944.55 m`, `elevation_std_m`: `1.50–18.62 m`) & ESA WorldCover 10m (`built_up`, `tree_cover`, `cropland`, `water` fractions) in `features_static_bengaluru.parquet`.
- **D8 Hydrology (1,170 cells):** Flow direction, accumulation (`km²`), `TWI = ln(a/tan b)`, `19` sinks in `phase6/hydrology/topographic_routing_static_features.parquet`.
- **Live 72h Weather:** Open-Meteo `ecmwf_ifs025` (`0.25°` ~27.8 km, 5 Bengaluru anchors snapping to 2 native nodes `[13.0, 77.5]` and `[13.0, 77.75]`), `1h–72h` cumulative & peak windows (`forecast_metrics.py`), SQLite WAL + `forecast_refresh_history`.
- **Historical NWP vs. Rain Gauges (Phase 6B):** NOAA GFS `0.25°` vs. **16 primary IMD/KSNDMC gauges** (`21` catalogued) across **256 pairs** (`2022-08-25` to `2022-09-09`): **Bias = `-10.88 mm`**, **MAE = `18.64 mm`**, **Pearson `r = 0.142`**, **Heavy-rain (`>=64.5 mm`) POD = `0.000`** (`0` hits, `23` misses).
- **Flood Evidence (Phase 6C):** `13` `VERIFIED_POSITIVE`, `7` `VERIFIED_NEGATIVE`, `1,150` `UNOBSERVED_DOMAIN_CELL` (`98.29%` unobserved). Legacy inventory: `21` records; Phase 6 inventory: `24` records.
- **Sentinel-1A SAR (Phase 6D/7C):** `5/13` (`38.5%`) true specular flood detection; urban canyons and lake conflation limit C-band radar in dense cities. Phase 2A.5 synthetic SAR is quarantined.

## 3. Scoring Formulas & Worked Example (`g1000_7489_1650`)
- **Static Susceptibility (`dynamic_risk.py`):** `0.50 * S_terrain + 0.50 * S_landcover` (manual MCDA weights).
  - For `g1000_7489_1650` (`elev=881.94m`, `std=1.9m`, `built_up=0.8582`, `tree=0.0476`, `crop=0.0454`): `S_terrain = 0.5894`, `S_landcover = 0.8747`, **`S_static = 0.7321`** (Rank `#12`).
- **Dynamic Prioritisation (`dynamic_risk.py`):** `0.35 * S_static + 0.30 * S_obs + 0.35 * S_fcst` (excludes flood labels to prevent circularity).
  - For `g1000_7489_1650` (`S_obs=0.1738`, `S_fcst=0.0738`): **`0.3342`** (`RESEARCH_PRIORITY_LOW`), `has_ground_flood_evidence = True`.
- **Live Forecast Risk Engine (`risk_engine.py`, `/api/risk/forecast`):** `0.35 * terrain + 0.20 * drainage(TWI, UPA) + 0.15 * landcover + 0.30 * forecast_rain` across `1h–72h`; returns `INSUFFICIENT_DATA` if stale/missing.

## 4. Experimental ML (`src/floodrisk/ml/`)
- **Dataset:** `data/phase8/flood_event_grid_dataset.parquet` (`9,360` rows; `48` labeled = `34` pos + `14` proxy-neg; `14` leakage-free features).
- **Models Compared:** Random Forest (`v8.0-exp-rf-20261127`, `n_estimators=100`, `max_depth=4`, `class_weight='balanced'`), XGBoost, HistGradientBoosting, Logistic Regression. No GridSearchCV used.
- **Random Forest Metrics:**
  - **5-Fold Spatial `GroupKFold`:** `ROC-AUC = 0.8382`, `PR-AUC = 0.9232`, `F1 = 0.8696`, `Precision = 0.8571`, `Recall = 0.8824`, `Brier = 0.1425`, `CM = {TN:9, FP:5, FN:4, TP:30}`.
  - **Temporal Holdout (`2023–2025`):** `0.3333` recall (`1/3` positives, `0` negative controls).

## 5. Prototype Pages & Demo Flow
- **Authority Dashboard (`/`):** Live Weather Bar, KPIs, **AUTOMATIC ALERT** button, **FLOOD ALERT CENTER** (4 Bengaluru zone cards + Real/Demo history), Leaflet 1,170-cell map, Cell Inspector + `1h–72h` timeline, and analytics tabs.
- **Civilian Safety Page (`/civilian-alert.html`):** Fixed public URL with predefined East Bengaluru demo scenario, Leaflet + OSM map, 4 zones, green demonstration destinations, OSRM indicative routing (with fallback), Copy/Share Link, and `tel:112` SOS.

## 6. Novelty Audit Summary
- **Implemented:** 3-state flood evidence classification, non-circular dynamic prioritisation, conditional priority tiers, NWP-vs-gauge reliability audit, spatial+temporal ML validation, stateful SQLite alert lifecycle, 5.5 km spatial clustering.
- **Partially Implemented:** Temporal escalation across horizons (`1h–72h` + run-to-run escalation, no explicit `d(risk)/dt`).
- **Proposed Only:** Evidence-aware dual-priority hotspot clustering; forecast-reliability-weighted risk fusion.

## 7. Package Files (`dp_review_package/`)
- `01_raw_sample_100.csv` .. `05_ml_evaluation_sample_100.csv` (100 real rows each; `openpyxl` not installed in `.venv` so `.xlsx` not generated)
- `PROJECT_TECHNICAL_AUDIT.md`, `DATASET_INVENTORY.md`, `DATA_DICTIONARY.md`, `PROCESSING_PIPELINE.md`, `ML_TRAINING_AND_EVALUATION.md`, `PROTOTYPE_PAGE_GUIDE.md`, `LIVE_DEMO_SCRIPT.md`, `NOVELTY_IMPLEMENTATION_AUDIT.md`, `VIVA_QUESTIONS_AND_ANSWERS.md`, `COMPLETE_DP_REVIEW_CONTEXT.md`.
