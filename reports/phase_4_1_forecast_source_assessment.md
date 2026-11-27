# Phase 4.1 — Numerical Weather Forecast Provider Assessment & Selection Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban (1,170 Cells, 1-km Grid)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Reporting Date:** 2026-11-05  

---

## 1. Executive Summary

A critical distinction in operational flood hydrology is the separation between:
1. **Weather Forecasts (Meteorological Forcing):** Numerical Weather Prediction (NWP) estimates of future atmospheric rainfall rate and accumulation (mm/hr, mm/day) issued at specific model run initialization times ($t_{\text{issue}}$).
2. **Flood Risk Forecasts (Hydrological Response):** Estimates of terrestrial surface water accumulation, underpass ponding, and drainage overwhelm resulting from the interaction of forecasted rainfall with static terrain depressions and impervious urban land cover.

This report evaluates four prospective NWP precipitation forecast providers for the Bengaluru study area, verifies licensing and programmatic accessibility, and selects the primary operational ingestion adapter for Phase 4.2.

---

## 2. Evaluation of Candidate Numerical Weather Prediction (NWP) Providers

| Candidate Provider | Underlying NWP Models | Native Resolution | Forecast Horizon & Step | Update Frequency | Access Protocol & Licensing | Assessment & Suitability |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **India Meteorological Department (IMD)** | IMD WRF (3 km regional) & GFS (12 km) | $3\text{ km} - 12\text{ km}$ | 72 hours (3-hourly) | 2 to 4 runs/day | Web bulletins / Mausam portal (No public open REST API) | **High Authority; Blocked by API Access.** Excellent national reference, but lacks open automated machine-readable streaming endpoints. |
| **Open-Meteo NWP Service** | ECMWF IFS ($9\text{ km}$), NOAA GFS ($13\text{ km}$), DWD ICON ($7\text{ km}$) | $7\text{ km} - 13\text{ km}$ | 72 hours to 16 days (Hourly) | 4 runs/day ($00, 06, 12, 18\text{Z}$) | Open Data (CC BY 4.0), Zero-key REST JSON API (`api.open-meteo.com`) | **SELECTED AS PRIMARY ADAPTER.** Validated in Python; delivers hourly precipitation depth (mm), probability, issue times, and lead times. |
| **NOAA NOMADS GFS** | NOAA GFS ($0.25^\circ$) | $\approx 25\text{ km}$ | 120 hours (3-hourly) | 4 runs/day | Public Open Data (GRIB2 HTTP/FTP) | **Viable Fallback.** Heavy GRIB2 parsing required; spatial resolution is coarse ($25\text{ km}$). |
| **ECMWF Open Data** | ECMWF Integrated Forecasting System (IFS) | $0.25^\circ - 0.4^\circ$ | 120 hours (3-hourly) | 2 runs/day | Open Data (GRIB2 via Python client) | **Viable Global Benchmark.** Coarser spatial resolution than regional Open-Meteo blended stream. |

---

## 3. Primary Selection: Open-Meteo NWP Ingestion Adapter

The **Open-Meteo NWP Service** is selected as the primary forecast ingestion engine for the platform:
- **Programmatic Accessibility:** Verified live HTTP REST connection returning structured JSON across the Bengaluru bounding box ($12.85^\circ - 13.15^\circ\text{N}, 77.45^\circ - 77.75^\circ\text{E}$).
- **Temporal Granularity:** 1-hour time steps across a 72-hour forecast horizon ($t + 1\text{h}$ to $t + 72\text{h}$).
- **Variables Retrieved:**
  - `precipitation` (hourly rainfall depth in mm)
  - `precipitation_probability` (0–100%)
  - `weather_code` (WMO meteorological classification)
- **Separation of Times:** The adapter explicitly records `forecast_issue_time` (e.g. `2026-11-05T06:00:00Z`) separately from `valid_time` (e.g. `2026-11-06T14:00:00Z`), enabling exact calculation of `lead_time_hours = valid_time - issue_time`.

---

## 4. Canonical Forecast Schema Definition

The forecast ingestion pipeline writes to the canonical schema:

```sql
CREATE TABLE forecast_rainfall_bengaluru (
    forecast_id VARCHAR PRIMARY KEY,
    provider VARCHAR NOT NULL,
    model_name VARCHAR NOT NULL,
    forecast_issue_time TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_time TIMESTAMP WITH TIME ZONE NOT NULL,
    lead_time_hours INT NOT NULL,
    grid_id VARCHAR NOT NULL,
    precipitation_value FLOAT NOT NULL,
    precipitation_unit VARCHAR NOT NULL,
    precipitation_depth_mm FLOAT NOT NULL,
    source_pixel_id VARCHAR NOT NULL,
    source_resolution VARCHAR NOT NULL,
    retrieval_time TIMESTAMP WITH TIME ZONE NOT NULL,
    provenance_status VARCHAR NOT NULL
);
```

