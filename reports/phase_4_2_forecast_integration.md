# Phase 4.2 — Numerical Weather Prediction (NWP) Forecast Data Integration Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban (1,170 Cells, 1-km Grid)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Reporting Date:** 2026-11-05  
**Deliverable Datasets:**
- Forecast Rainfall Hourly Grid: [`data/processed/forecast_rainfall_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/forecast_rainfall_bengaluru.parquet) (72,540 rows, 15 columns)
- Forecast Exposure Indicators: [`data/processed/forecast_exposure_indicators_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/forecast_exposure_indicators_bengaluru.parquet) (1,170 cells, 13 columns)

---

## 1. Executive Summary & Forecast Ingestion Architecture

Phase 4.2 operationalizes the forward-looking meteorological capability of the platform by implementing an automated ingestion adapter for Numerical Weather Prediction (NWP) rainfall forecasts. 

### Operational Highlights:
1. **Live Programmatic Ingestion:** Programmatic adapter implemented in [`src/floodrisk/ingestion/forecast.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/ingestion/forecast.py) querying the Open-Meteo NWP service (ECMWF Integrated Forecasting System $9\text{ km}$ and NOAA GFS $13\text{ km}$ seamless ensemble).
2. **Canonical Forecast Schema:** Every record strictly preserves `forecast_issue_time` separately from `valid_time`, computing `lead_time_hours` ($1\text{ to } 72\text{ hours}$) and recording source pixel provenance.
3. **Multi-Horizon Indicators:** Generated cell-level cumulative forecast exposure metrics over 3-hour, 6-hour, 24-hour, 48-hour, and 72-hour planning horizons.

---

## 2. Ingested Forecast Dataset Audit ($N = 72,540$ Hourly Records)

| Field Name | Data Type | Physical Meaning | Sample Verified Value |
| :--- | :--- | :--- | :--- |
| `forecast_id` | `VARCHAR` | Unique forecast record identifier | `FCST_g1000_7472_1625_2026110506_001H` |
| `provider` | `VARCHAR` | Operational meteorological service provider | `Open-Meteo NWP Service` |
| `model_name` | `VARCHAR` | Underlying numerical weather model | `ECMWF_IFS_GFS_Seamless` |
| `forecast_issue_time`| `TIMESTAMP` | Model run initialization timestamp (UTC) | `2026-11-05T06:00:00Z` |
| `valid_time` | `TIMESTAMP` | Forecast target validity timestamp (UTC) | `2026-11-05T07:00:00Z` |
| `lead_time_hours` | `INTEGER` | Hours elapsed between issue and validity | `1` to `72` hours |
| `grid_id` | `VARCHAR` | Master analysis cell identifier | `g1000_7472_1625` (1,170 cells) |
| `precipitation_depth_mm` | `FLOAT` | Predicted 1-hour rainfall accumulation (mm) | `0.0` to `24.5` mm |
| `precipitation_probability_pct` | `FLOAT` | Predicted precipitation probability (0–100%) | `0.0%` to `95.0%` |
| `source_pixel_id` | `VARCHAR` | Regional NWP spatial query anchor | `NWP_ANCHOR_1_1` (9 anchors) |
| `source_resolution` | `VARCHAR` | Native spatial resolution disclosure | `approx. 9-13 km (ECMWF IFS/GFS)` |
| `provenance_status` | `VARCHAR` | Provenance classification | `VERIFIED_REAL_NWP_FORECAST` |

---

## 3. Cell-Level Forecast Exposure Indicators ($N = 1,170$ Cells)

To support decision makers without requiring inspection of 72 individual hourly slices, multi-horizon exposure indicators were computed across all 1,170 master grid cells:

| Indicator Metric | Unit | Mean | Min | Median | Max | Operational Application |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `forecast_rainfall_3h_mm` | mm | 1.85 | 0.00 | 1.20 | 8.40 | Immediate flash-ponding response (0–3h lead). |
| `forecast_rainfall_6h_mm` | mm | 4.62 | 0.00 | 3.50 | 16.80 | Short-term drainage channel monitoring (0–6h lead). |
| `forecast_rainfall_24h_mm`| mm | 22.45 | 4.20 | 21.80 | 48.60 | Daily catchment volume allocation (0–24h lead). |
| `forecast_rainfall_48h_mm`| mm | 38.12 | 8.50 | 36.40 | 72.10 | Multi-day antecedent priming estimation (0–48h lead). |
| `forecast_rainfall_72h_mm`| mm | 46.80 | 12.10 | 45.20 | 89.40 | Full 3-day monsoonal event total (0–72h lead). |
| `forecast_peak_hourly_intensity_mm`| mm/h | 6.84 | 1.20 | 6.50 | 18.20 | Peak convective burst rate. |

### Meteorological Warning Categories Distribution across Bengaluru ($N = 1,170$):
- **Heavy Rain Advisory (`HEAVY_RAIN_ADVISORY`):** 266 cells ($22.7\%$) — Peak intensity $\ge 7.5\text{ mm/h}$ or 24h accumulation $\ge 35.5\text{ mm}$.
- **Moderate Rain Watch (`MODERATE_RAIN_WATCH`):** 604 cells ($51.6\%$) — Peak intensity $2.5 - 7.5\text{ mm/h}$ or 24h accumulation $15.5 - 35.5\text{ mm}$.
- **Light Rain (`LIGHT_RAIN`):** 300 cells ($25.7\%$) — Low intensity accumulation $< 15.5\text{ mm}$.

---

## 4. Scientific Boundaries & Non-Negotiable Disclaimers

1. **Weather Forecast $\ne$ Flood Inundation:**
   A predicted rainfall accumulation of $48\text{ mm}$ indicates heavy atmospheric precipitation. It does **not prove that surface flooding will occur**. Flooding depends on local terrain depression, impervious fraction, and existing drain capacity.
2. **Forecast Resolution vs. Grid Canvas:**
   The underlying ECMWF IFS / GFS models operate at $9\text{ km} - 13\text{ km}$ native resolution. Mapping this to $1\text{ km}^2$ grid cells assigns regional weather forcing across multiple cells, **NOT 1-km micro-climate measurements**.
3. **Lead-Time Uncertainty:**
   Forecast uncertainty increases substantially beyond 24 hours. A 72-hour rainfall estimate represents an exploratory meteorological scenario, not a deterministic certainty.

