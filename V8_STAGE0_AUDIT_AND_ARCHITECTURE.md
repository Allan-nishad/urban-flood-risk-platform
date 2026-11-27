# URBAN FLOOD RISK PLATFORM — V8 OPERATIONAL AI UPGRADE: STAGE 0 REPORT

**Branch:** `upgrade/v8-operational-ai` (branched from `recovery/v7.3` at `7a6a97b`; `v7.2.0-FREEZE` at `1e63101` untouched)  
**Baseline Test Suite:** `129 passed, 0 failed, 0 skipped`  
**Audit Date:** 2026-11-27  

---

## 1. Verified Current Project Baseline

- **Git State:** `upgrade/v8-operational-ai` checked out cleanly from `recovery/v7.3` (`7a6a97b`). `v7.2.0-FREEZE` (`1e63101`) and `main` preserved untouched.
- **Test Suite:** `.venv\Scripts\python.exe -m pytest tests/ -q` → **`129 passed, 0 failed, 0 skipped`** (`109` v7.2 baseline + `7` data-integrity + `13` server/API/Playwright tests).
- **Spatial Domain:** `1,170` equal-area `1 km × 1 km` cells (`EPSG:6933`), `g1000_{col}_{row}`, spanning `30 km × 39 km` over Bengaluru Urban.
- **Current Scientific Baseline:**
  - Uncalibrated MCDA dynamic index: `S_dynamic = 0.35*S_static + 0.30*S_obs + 0.35*S_fcst_24h` (`dynamic_risk_intelligence_bengaluru.parquet`, range `[0.1243, 0.3500]`, `STALE` Phase 4.3 constant `12.5 mm` observed rain).
  - Ground-truth matrix: `13` `VERIFIED_POSITIVE` (`1.11%`), `7` `VERIFIED_NEGATIVE` (`0.60%`), `1,150` `UNOBSERVED_DOMAIN_CELL` (`98.29%`) — all from **one** episode (Aug 30–Sep 5, 2022).
  - NWP verification (`256` pairs): `MAE = 18.64 mm`, `RMSE = 33.19 mm`, `Bias = -10.88 mm`, `r = 0.1421`, heavy-rain ($\ge 64.5\text{ mm}$) `POD = 0.0` (`0/23` hits).
  - SAR audit: `5/13` (`38.5%`) true specular flood expansion (`4/13` lake-conflated, `3/13` urban-canyon missed, `1/13` double-bounce).

---

## 2. Complete Outstanding Blocker Matrix

| # | Issue | Current Status | Evidence / Root Cause |
|---|---|---|---|
| 1 | GFS 0.25° heavy-rain detection `POD = 0.0` (`0/23` hits) | **UNSOLVED** | `phase7_forecast_verification_metrics.parquet`: ~27.75 km grid smears convective Bengaluru storms. |
| 2 | Stale Phase 4.3 `12.5 mm` constant observed rainfall | **PARTIALLY_SOLVED** | Badged `STALE` in v7.3 (`server.py`, `index.html`), but no live ingestion pipeline replaces it yet. |
| 3 | `98.29%` (`1,150/1,170`) unobserved spatial grid | **UNSOLVED** | Only 13 positive + 7 negative-proxy cells from Aug–Sep 2022 exist. |
| 4 | Insufficient independent flood-positive evidence | **UNSOLVED** | `P6` (`24` records: `2022-09-05` & `2022-08-30`) and `P2/4` (`21` records) cover only 1 monsoon episode. |
| 5 | No validated supervised flood prediction ML model | **BLOCKED** | Blocked by single-episode 20-cell sample size; cannot perform temporal/event holdout without multi-event labels. |
| 6 | Coarse weather forecast resolution (27.75 km GFS) | **PARTIALLY_SOLVED** | Open-Meteo API (ECMWF IFS ~9 km / ICON / GFS seamless) is live-accessible (`HTTP 200`), not yet wired into live ingestion. |
| 7 | Unvalidated satellite flood detection (`38.5%` true specular) | **PARTIALLY_SOLVED** | Inflated `76.9%` KPI removed in v7.3; single-event 3-scene audit only; multi-event SAR change + permanent-water masking needed. |
| 8 | Absence of genuine operational alert lifecycle | **UNSOLVED** | No state machine (`Normal`/`Advisory`/`Watch`/`Warning`), persistence, hysteresis, ack/expiry, or stale-data suppression exists. |
| 9 | Missing automated data refresh, source health & prod controls | **UNSOLVED** | Dev `ThreadingMixIn` `HTTPServer` only; no scheduler, SQLite/DB persistence, retry/backoff, or provider health checks. |

---

## 3. Verified Real Data-Source Directory (Live-Probed 2026-11-27)

| Source | Access Method & Live Probe | Coverage / Res | Update Freq / History | License & Limitations | Operational Suitability |
|---|---|---|---|---|---|
| **Open-Meteo Forecast API** (`api.open-meteo.com/v1/forecast`) | REST JSON GET — **`HTTP 200` (Working)** | Global / Bengaluru; ~9 km ECMWF IFS + GFS/ICON seamless | Hourly updates; 7–16d forecast; UTC timestamps | CC-BY 4.0 (non-commercial free tier; rate-limited); not an official IMD warning | **SUITABLE** (Primary live/short-range NWP adapter) |
| **Open-Meteo Historical Archive** (`archive-api.open-meteo.com/v1/archive`) | REST JSON GET — **`HTTP 200` (Working)** | Global / Bengaluru; ERA5-Land ~9–11 km | Daily lag ~5d; hourly back to 1940 | CC-BY 4.0; reanalysis smears sub-km urban convective peaks | **SUITABLE** (Multi-event historical rainfall & antecedent moisture) |
| **NOAA GFS AWS Open Data** (`noaa-gfs-bdp-pds.s3.amazonaws.com`) | Public S3 HTTPS GRIB2 — **`HTTP 200` (Working)** | Global; 0.25° (~27.75 km) | 4 cycles/day (00/06/12/18Z); 2021–present | Public Domain (NOAA); coarse 27.75 km (`POD = 0.0` on heavy rain) | **SECONDARY** (Backup/ensemble context only) |
| **Copernicus CDSE Sentinel-1** (`catalogue.dataspace.copernicus.eu/odata/v1/Products`) | OData catalog **`HTTP 200`**; product download needs free OAuth2 token | Global / Bengaluru; 10 m IW GRDH | 6–12 day revisit; 2014–present | Copernicus Open License; C-band suffers double-bounce & canopy occlusion in urban canyons | **SUITABLE** (Post-event/co-event SAR detection with explicit `NO_VALID_OBSERVATION` outside overpass) |
| **NASA SRTM 30m & ESA WorldCover 10m** (already local) | Local GeoTIFFs — **Verified on disk** | Bengaluru 30 m / 10 m | Static (2000 / 2021) | NASA / ESA Open; WorldCover 2021 may lag 2022–2026 peri-urban construction | **SUITABLE** (Static terrain & imperviousness features) |
| **IMD Mausam** (`mausam.imd.gov.in`) | **`HTTP 200`** HTML portal (no open unauthenticated JSON API) | India / Bengaluru | Sub-daily | Restricted API (requires IP whitelisting / MoU) | **NOT OPERATIONAL** (Manual/future adapter if credentials granted) |
| **KSNDMC** (`www.ksndmc.org`) | **`SSL CERTIFICATE_VERIFY_FAILED`** | Karnataka / BBMP telemetric gauges | N/A | No open unauthenticated REST feed; TLS error on portal | **BLOCKED** (Cannot automate without official feed/API) |
| **CWC Flood Forecast** (`ffs.india-water.gov.in`) | **`HTTP 200`** HTML SPA (no open REST JSON API) | Major river basins | N/A | Monitors river basins, not Bengaluru urban stormwater pluvial drains | **NOT SUITABLE** (Pluvial urban domain) |

---

## 4. Flood-Event Dataset Acquisition Strategy

Because existing labels cover **only 1 monsoon episode** (Aug 30–Sep 5, 2022), a supervised ML model **cannot** be trained or temporally validated on the current 20 labeled cells alone. Strategy:
1. **Multi-Event Historical Expansion (2020–2025):** Compile curated, timestamped Bengaluru flood events across **at least 6–8 distinct monsoon episodes** (e.g., Aug–Sep 2022, Oct 2022, May 2023, Oct 2024, May 2025) from verifiable public municipal/media/field archives with explicit `event_id`, `event_date`, `location_name`, `grid_id`, `source_url`/`source_organisation`, and `spatial_uncertainty_m`.
2. **Verified Non-Flood / Dry-Event Controls:** Pair each flood episode with:
   - Monitored dry high-ground/functional-drainage control cells (`VERIFIED_NEGATIVE`), AND
   - Non-flood heavy-rain or dry-baseline dates at those same monitored stations (strictly **never** converting `1,150` unobserved cells into negative labels).
3. **Multi-Date Sentinel-1 SAR Expansion:** Query CDSE for all available Sentinel-1 IW GRDH passes intersecting Bengaluru flood episodes + dry baselines to compute permanent-water-masked $\Delta\gamma^0_{\text{VV}}$ anomalies.

---

## 5. ML Dataset Design & Labeling Strategy

- **Unit of Observation:** `(grid_id, event_id, prediction_timestamp_utc)` with `horizon_h` $\in \{6, 12, 24\}$.
- **Target Variable (`y_inundation`):** Binary verified inundation within `[prediction_timestamp_utc, prediction_timestamp_utc + horizon_h]` (`1` = `CONFIRMED_FLOOD`, `0` = `VERIFIED_NON_FLOOD`, `NULL` = `UNOBSERVED` / `UNCERTAIN` — excluded from supervised loss).
- **Mandatory Schema Columns:** `grid_id`, `event_id`, `prediction_timestamp_utc`, `horizon_h`, `rain_1h_mm`, `rain_3h_mm`, `rain_6h_mm`, `rain_24h_mm`, `api_7d_mm`, `fcst_rain_horizon_mm`, `fcst_peak_rate_mmh`, `elevation_mean_m`, `slope_deg`, `twi`, `flow_acc_km2`, `is_closed_sink`, `depression_depth_m`, `built_up_fraction`, `water_fraction`, `sar_delta_vv_db`, `sar_obs_state`, `y_inundation`, `label_source`, `label_confidence`, `observation_status`, `data_source`, `missing_flags`.
- **Strict Separation:** `CONFIRMED_FLOOD`, `VERIFIED_NON_FLOOD`, `UNCERTAIN`, `PROXY`, `SYNTHETIC`, and `UNOBSERVED` are stored in `observation_status` and never conflated.

---

## 6. Proposed Model Architecture & Baseline Comparisons

- **Baselines (Must Be Beaten):**
  1. **Rainfall-Threshold Baseline:** Predict flood when `fcst_rain_24h_mm >= 64.5` (or `35.5` mm).
  2. **v7.2 Static/Dynamic MCDA Baseline:** `S_dynamic = 0.35*S_static + 0.30*S_obs + 0.35*S_fcst_24h`.
- **Candidate Supervised / Hybrid Models (via existing `scikit-learn` & `xgboost`):**
  1. **Logistic Regression (L2-regularized)** — interpretable linear baseline + native probability calibration check.
  2. **Random Forest** — handles non-linear terrain $\times$ rainfall interactions.
  3. **HistGradientBoostingClassifier / XGBoost** — handles native `NaN` missing-data flags without zero-imputation.
- **Leakage-Resistant Validation:**
  - **Leave-One-Event-Out (LOEO) / Temporal Holdout:** Never split adjacent `grid_id`s from the same flood date across train and test.
  - **Metrics:** Precision, Recall, F1, PR-AUC, ROC-AUC, Confusion Matrix, FAR, Miss Rate, Brier Score / Reliability Curve (calibration), stratified by event, lead time, and zone.
  - **Qualification Gate:** A model is marked `EXPERIMENTAL_UNVALIDATED` and blocked from alerts unless it beats both baselines on out-of-event PR-AUC and calibrated Brier score.

---

## 7. Live-Data Architecture (`src/floodrisk/live/`)

- **Provider Adapters:** `OpenMeteoForecastAdapter` (hourly ECMWF/GFS/ICON seamless for Bengaluru grid anchors), `OpenMeteoArchiveAdapter`, `NoaaGfsAdapter` (fallback), `CdseSarCatalogAdapter`.
- **Resilience & Provenance:** Exponential backoff retries (3 attempts), rate-limit `429` handling, atomic SQLite + Parquet cache writes, UTC storage with `Asia/Kolkata` (IST) UI formatting, and strict freshness windows:
  - Forecast: `LIVE` ($\le 3\text{ h}$), `RECENT` ($\le 12\text{ h}$), `STALE` ($> 12\text{ h}$).
  - Observed Rain: `LIVE` ($\le 2\text{ h}$), `RECENT` ($\le 24\text{ h}$), `STALE` ($> 24\text{ h}$).
- **Stale-Data Blocking:** Inputs tagged `STALE` or `UNAVAILABLE` are automatically excluded from current inference and trigger shadow-alert suppression.

---

## 8. Flood-Detection Improvement Strategy (SAR)

- **Multi-Scene Baseline:** Compute per-cell dry-season baseline $\gamma^0_{\text{VV, baseline}}$ (median of $\ge 5$ dry-season Sentinel-1 scenes) and permanent water mask (ESA WorldCover class `80` + persistent dry-season water) to eliminate the `4/13` lake-conflation error discovered in Phase 7.
- **Urban Canyon & Double-Bounce Handling:** Flag high `built_up_fraction` ($> 0.70$) cells with positive $\Delta\gamma^0_{\text{VV}}$ separately from specular open-water drops, and explicitly output `DETECTED`, `NOT_DETECTED`, `UNCERTAIN`, `NO_VALID_OBSERVATION` (outside SAR overpass), or `STALE_OBSERVATION`.

---

## 9. Operational Risk & Alert Engine (`src/floodrisk/alerts/`)

- **Shadow-Mode State Machine:** `NORMAL` → `ADVISORY` → `WATCH` → `WARNING` persisted in SQLite (`data/state/floodrisk_v8.db`).
- **Controls:** Persistence (2 consecutive cycles to escalate), hysteresis (lower de-escalation threshold to prevent flapping), deduplication per `(grid_id, horizon_h)`, expiry TTL, human `acknowledge` / `review_status`, full audit log, and **automatic suppression** when inputs are `STALE`/`UNAVAILABLE` or the ML model is `EXPERIMENTAL_UNVALIDATED`.

---

## 10. Deployment & Operational-Readiness Roadmap

- Replace dev `HTTPServer` startup option with a production-capable WSGI/ASGI entrypoint (or hardened `ThreadingHTTPServer` + SQLite persistence + scheduled background refresh loop with clean shutdown), structured JSON logging, `/api/health` exposing per-provider status & DB connectivity, and `configs/` environment-variable secret management (`EARTHDATA_TOKEN`, `CDSE_CLIENT_ID`, `CDSE_CLIENT_SECRET` — never committed).

---

## 11. Ordered Implementation Tasks (v8 Stages)

| Stage | Scope | Dependencies | Acceptance Criteria |
|---|---|---|---|
| **Stage 1** | Live-Data Ingestion & SQLite Persistence (`OpenMeteoForecastAdapter`, provider health, freshness states, `/api/health` + `/api/sources`) | Stage 0 approval | Live Open-Meteo fetch stored in UTC, `LIVE`/`RECENT`/`STALE` enforced, retry/backoff & stale-blocking unit + live tests pass. |
| **Stage 2** | Multi-Event Flood Dataset Builder & SAR Multi-Scene Refinement | Stage 1 | Versioned multi-event ML dataset (no unobserved-as-negative, no synthetic inflation); SAR permanent-water conflation eliminated. |
| **Stage 3** | Reproducible ML Training, LOEO Validation & Inference Pipeline | Stage 2 | Models compared against thresholds + MCDA baseline; serialized model + metadata; calibrated or gated `EXPERIMENTAL_UNVALIDATED`. |
| **Stage 4** | Shadow-Mode Operational Alert Engine + Persistence | Stage 1 + 3 | Hysteresis, persistence, ack/expiry, audit log, and automatic suppression on `STALE`/unqualified model tested end-to-end. |
| **Stage 5** | Dashboard & API Integration + Full Playwright & Regression Suite | Stage 1–4 | UI displays live freshness, source health, model evaluation, horizons, SAR status, and alert history; all tests pass. |

---

## 12. Estimated Data, Storage & Computational Requirements

- **Local Free Disk Available:** **`161.00 GB`** free (of `475.79 GB`); **CPU:** `12` logical cores.
- **Open-Meteo Live & Archive JSON/Parquet:** `< 50 MB` total (lightweight REST JSON for 9–36 grid anchors).
- **Multi-Event Sentinel-1 SAR (if subset/AOI via CDSE):** `~2–5 GB` for 6–10 co-event/baseline subsets (`< 3%` of free disk).
- **SQLite Operational DB & Model Artifacts:** `< 100 MB`.
- **Compute:** Tabular ML training (Logistic Regression, Random Forest, XGBoost/HistGB on ~10k–50k cell-event rows) runs in **< 30 seconds** on 12 CPU cores (no GPU required).
