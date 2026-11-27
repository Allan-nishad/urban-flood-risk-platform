# Phase 4 — Master Technical Report: Operational Flood Risk Intelligence Platform

**Platform Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban Provisional Development Domain (1,170 Equal-Area Grid Cells in EPSG:6933)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Automated Tests:** 87 passed / 87 total (100% pass rate)  
**Cryptographic Manifest:** 33 / 33 datasets verified with SHA-256 (100% match rate)  
**Exit Decision:** **Decision B: Partial Operational Platform Validated (Supervised Flood Prediction Blocked)**

---

## 1. Executive Summary & Architectural Scope

Phase 4 represents the culminating engineering phase of the Urban Flood Risk Platform. In this phase, the project advanced from retrospective batch analysis and baseline exploratory modeling (Phases 1–3) into a fully operational, real-time dynamic risk surveillance platform.

The operational platform integrates authentic digital elevation mosaics (SRTM GL1 30m), high-resolution land-cover rasters (ESA WorldCover 10m), continuous Numerical Weather Prediction (NWP) forecasts from ECMWF IFS and GFS ensembles via Open-Meteo, a provenance-tracked historical flood incident inventory, an event monitoring engine, a cryptographic manifest engine, and an interactive web surveillance console.

Throughout this campaign, scientific honesty has been maintained as an absolute constraint:
1. **Four-Layer Strict Non-Conflation:** Static terrain susceptibility, observed historical rainfall exposure, forecast rainfall exposure, and observed ground flood evidence are strictly segregated across schema fields, preventing physical conflation.
2. **Quarantine of Simulated Synthetic Fixtures:** Synthetic Sentinel-1 SAR change rasters generated in Phase 2A.5 are permanently quarantined under `SYNTHETIC_TEST_ONLY_QUARANTINED` and strictly excluded from operational risk indices.
3. **Formal Exit Decision B:** Because authoritative flood depth/extent ground truth across non-incident cells is absent, supervised predictive flood models remain blocked. The platform operates as an exploratory dynamic prioritization and surveillance console, never claiming unverified flood probabilities.

```
+----------------------------------------------------------------------------------------------------+
|                                    OPERATIONAL SYSTEM ARCHITECTURE                                  |
+----------------------------------------------------------------------------------------------------+
                                                  |
           +--------------------------------------+--------------------------------------+
           |                                                                             |
+------------------------+                                                     +--------------------+
| DATA INGESTION ENGINE  |                                                     | CRYPTOGRAPHIC CORE |
| - Open-Meteo NWP       |                                                     | - SHA-256 Hasher   |
| - SRTM DEM Mosaics     |                                                     | - Lineage Tracker  |
| - ESA WorldCover 10m   |                                                     | - dataset_manifest |
+------------------------+                                                     +--------------------+
           |                                                                             |
           +--------------------------------------+--------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                       FOUR-LAYER DYNAMIC RISK INTELLIGENCE ENGINE (Phase 4.3)                      |
|                                                                                                    |
|  [Layer 1: Static Susceptibility]      [Layer 2: Observed Rainfall]    [Layer 3: Forecast NWP]     |
|   - SRTM Elevation Mean/Std             - Historical Monsoonal Depth    - 3h, 6h, 24h, 48h, 72h mm |
|   - WorldCover Built-up / Water         - API Decay Formulation         - WMO Advisory Category    |
|   - Multi-Criteria MCDA Index           - Antecedent Exposure Score     - Peak Intensity (mm/h)    |
|                                                                                                    |
|  [Layer 4: Ground Flood Evidence]   --> [Dynamic Risk Prioritization Index [0, 1] & Surveillance]  |
|   - 21 Provenance Incidents             - Multi-Criteria Composite Score (Uncalibrated)            |
|   - Uncertainty Buffers                 - Relative Ranking across 1,170 Cells (#1 to #1,170)       |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                             EVENT MONITORING SUBSYSTEM (Phase 4.4)                                 |
|  Tracks 6 Rainfall Episodes across State Machine: WATCH -> ACTIVE -> REPORTED -> UNDER_REVIEW -> CLOSED |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                         OPERATIONAL WEB DASHBOARD & REST API (Phase 4.5)                           |
|  - Standalone Zero-Dependency Python Server (src/floodrisk/dashboard/server.py)                     |
|  - Endpoints: /api/summary, /api/cells, /api/incidents, /api/episodes, /api/manifest, /api/health   |
|  - Interactive Leaflet Console: Thematic Layers, Uncertainty Circles, Dynamic Cell Inspector        |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Phase 4.1: Scientific Audit & Provenance Verification Synthesis

Phase 4.1 established a rigorous scientific baseline across all primary data foundations via seven comprehensive technical reports:

1. **NASA GPM IMERG Verification ([`phase_4_1_imerg_verification.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_4_1_imerg_verification.md)):**
   - Verified that IMERG half-hourly precipitation calibrated rate (`precipitationCal`, $\text{mm/h}$) cannot be treated as daily rainfall depth ($\text{mm/day}$) without explicit temporal integration.
   - Enforced the NASA Earthdata GES DISC credential gate for raw HDF5/NetCDF granules, preserving synthetic proxies for software integration while forbidding their use as verified observational ground truth.
2. **MERIT Hydro Verification ([`phase_4_1_merit_hydro_verification.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_4_1_merit_hydro_verification.md)):**
   - Corrected canonical tile identity to `n10e075_upa.tif`.
   - Identified the upstream accumulation gate requiring academic registration at the Yamazaki Hydrology Lab.
3. **Administrative Boundary Audit ([`phase_4_1_boundary_verification.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_4_1_boundary_verification.md)):**
   - Re-verified that the 1,170 grid domain ($77.45^\circ - 77.75^\circ\text{E}, 12.85^\circ - 13.15^\circ\text{N}$) is a provisional research bounding box.
   - Label remains explicitly `pending_authoritative_boundary` pending Survey of India / KGIS municipal boundary acquisition.
4. **Sentinel-1A SAR Verification ([`phase_4_1_sentinel1_verification.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_4_1_sentinel1_verification.md)):**
   - Documented the 24-day temporal baseline between the pre-flood scene (2022-08-12) and post-flood scene (2022-09-05).
   - Confirmed permanent quarantine (`SYNTHETIC_TEST_ONLY_QUARANTINED`) of simulated SAR rasters from the machine-learning feature matrix.
5. **Historical Flood Inventory Audit ([`phase_4_1_flood_inventory_audit.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_4_1_flood_inventory_audit.md)):**
   - Verified all 21 catalogued flood incidents with source attribution (KSNDMC, BBMP, media archives), spatial uncertainty radii ($250\text{ m} - 1000\text{ m}$), and strict separation of evidence categories.
6. **Forecast Source Assessment ([`phase_4_1_forecast_source_assessment.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_4_1_forecast_source_assessment.md)):**
   - Evaluated IMD GFS ($12\text{ km}$), ECMWF IFS ($9\text{ km}$), and Open-Meteo NWP APIs. Selected Open-Meteo ECMWF/GFS seamless service for open programmatic continuous forecasting.
7. **Consolidated Readiness Assessment ([`phase_4_1_data_acquisition_and_readiness.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_4_1_data_acquisition_and_readiness.md)):**
   - Formally established the roadmap for Phase 4 operational execution under Decision B constraints.

---

## 3. Phase 4.2: Forecast Ingestion & Multi-Horizon Indicators

### 3.1 Ingestion Pipeline (`src/floodrisk/ingestion/forecast.py`)
- **API Connection:** Direct REST interface with the Open-Meteo NWP service, requesting the seamless blend of ECMWF IFS ($9\text{ km}$) and GFS ($13\text{ km}$) models.
- **Decoupled Issue and Valid Times:** Every record maintains an immutable `forecast_issue_time` (e.g., `2026-11-05T00:00:00Z`) alongside its `valid_time` and `lead_time_hours` ($0$ to $72\text{ h}$). This decoupling guarantees zero forward-looking leakage.
- **Deliverable Dataset:** [`data/processed/forecast_rainfall_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/forecast_rainfall_bengaluru.parquet) (72,540 rows, SHA-256: `074e0bf03b9b940989b538e1f579e0bebe7f73907c1e550e181467406a6ea43a`).

### 3.2 Multi-Horizon Exposure Indicators
To support multi-tier operational decision-making, precipitation accumulations were computed across 5 operational horizons for each of the 1,170 cells:
- **3-Hour Accumulation ($R_{3\text{h}}$):** Flash-flood short-burst indicator (range: $0.0 - 4.8\text{ mm}$).
- **6-Hour Accumulation ($R_{6\text{h}}$):** Rapid-onset drainage saturation indicator (range: $0.0 - 12.2\text{ mm}$).
- **24-Hour Accumulation ($R_{24\text{h}}$):** Primary WMO daily exposure indicator (range: $11.4 - 68.2\text{ mm}$).
- **48-Hour Accumulation ($R_{48\text{h}}$):** Cumulative soil saturation indicator (range: $19.2 - 92.4\text{ mm}$).
- **72-Hour Accumulation ($R_{72\text{h}}$):** Extended synoptic episode depth (range: $24.8 - 110.4\text{ mm}$).
- **Peak Hourly Intensity ($I_{\max}$):** Maximum convective rain rate within the 72h window (range: $2.4 - 14.6\text{ mm/h}$).

### 3.3 WMO Alert Threshold Categorization
Grid cells are automatically classified based on their 24-hour forecasted precipitation depth:
- **`HEAVY_RAIN_ADVISORY` ($\ge 64.5\text{ mm / 24h}$):** 266 cells ($22.7\%$ of domain).
- **`MODERATE_RAIN_WATCH` ($15.6 - 64.4\text{ mm / 24h}$):** 604 cells ($51.6\%$ of domain).
- **`LIGHT_RAIN` ($< 15.6\text{ mm / 24h}$):** 300 cells ($25.6\%$ of domain).
- **Deliverable Dataset:** [`data/processed/forecast_exposure_indicators_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/forecast_exposure_indicators_bengaluru.parquet) (1,170 rows, SHA-256: `4c7ddfd6bc1c0b39678e2195f0376e737c0245a0b76e1919427ce7a3aaee42ad`).

---

## 4. Phase 4.3: Dynamic Risk Intelligence Engine

### 4.1 Four-Layer Separation Invariant
In [`src/floodrisk/processing/dynamic_risk.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/dynamic_risk.py), the four fundamental sources of flood intelligence are strictly separated into dedicated schema namespaces:

| Layer | Information Source | Feature Columns | Physical Interpretation |
| :--- | :--- | :--- | :--- |
| **Layer 1** | Static Physical Susceptibility | `elevation_mean_m`, `elevation_std_m`, `built_up_fraction`, `water_fraction`, `static_susceptibility_score`, `static_susceptibility_rank` | Terrain low-lyingness and surface impermeability (MCDA index). |
| **Layer 2** | Observed Monsoonal Exposure | `observed_rainfall_24h_mm`, `observed_api_decay_mm`, `observed_rainfall_exposure_score` | Historical precipitation volume and antecedent soil priming. |
| **Layer 3** | Forecast NWP Exposure | `forecast_rainfall_3h_mm`, `forecast_rainfall_24h_mm`, `forecast_rainfall_72h_mm`, `forecast_peak_hourly_intensity_mm`, `forecast_exposure_score_24h`, `forecast_intensity_category` | Atmospheric precipitation hazard over upcoming 72 hours. |
| **Layer 4** | Ground Flood Evidence | `has_ground_flood_evidence`, `historical_incident_count`, `historical_incident_categories` | Direct empirical validation of ground inundation / waterlogging. |

### 4.2 Dynamic Composite Prioritization Index
To assist emergency planners in ranking surveillance resources, an uncalibrated composite prioritization index $S_{\text{dynamic}} \in [0, 1]$ is evaluated:

$$S_{\text{dynamic}} = 0.35 \cdot S_{\text{static}} + 0.25 \cdot S_{\text{obs}} + 0.30 \cdot S_{\text{fcst\_24h}} + 0.10 \cdot \mathbb{I}_{\text{evidence}}$$

where:
- $S_{\text{static}}$ is the min-max normalized static terrain and land-cover susceptibility score.
- $S_{\text{obs}}$ is the normalized historical monsoonal rainfall exposure score.
- $S_{\text{fcst\_24h}}$ is the normalized 24-hour NWP forecast rainfall score.
- $\mathbb{I}_{\text{evidence}} \in \{0, 1\}$ is an indicator for documented historical flood occurrence.

**Scientific Disclaimer Embedded in Dataset:**
> *"The dynamic risk prioritization score is an exploratory, uncalibrated prioritization ranking [0, 1] for surveillance and resource allocation. It is NOT a calibrated statistical flood probability, hydrodynamic inundation depth, or certified hazard forecast."*

- **Deliverable Dataset:** [`data/processed/dynamic_risk_intelligence_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/dynamic_risk_intelligence_bengaluru.parquet) (1,170 rows, 33 columns, SHA-256: `44eeae3fae2316e115049980590c68ea728a49c9339798031d234a65b93fb6ec`).

---

## 5. Phase 4.4: Flood-Event Monitoring Subsystem

The event monitoring engine ([`src/floodrisk/processing/monitoring.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/monitoring.py)) tracks discrete precipitation episodes through a finite state machine:

$$\text{WATCH} \longrightarrow \text{ACTIVE\_RAINFALL\_EVENT} \longrightarrow \text{FLOOD\_EVIDENCE\_REPORTED} \longrightarrow \text{UNDER\_REVIEW} \longrightarrow \text{CLOSED}$$

### Summary of Monitored Episodes

| Episode ID | Episode Name | Time Period | Peak Date | Peak Rain | Incidents | Lifecycle State | Hazard Classification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `EP-2022-08-W1` | Pre-Monsoon Soil Priming | 2022-08-01 - 2022-08-05 | 2022-08-02 | $48.2\text{ mm}$ | 0 | `CLOSED` | Moderate Convective Priming |
| `EP-2022-08-STORM1` | Intense Convective Storm | 2022-08-29 - 2022-08-31 | 2022-08-30 | $131.4\text{ mm}$ | 8 | `CLOSED` | Severe Localized Inundation |
| `EP-2022-09-INTER` | Inter-Storm Saturation | 2022-09-01 - 2022-09-03 | 2022-09-02 | $32.6\text{ mm}$ | 0 | `CLOSED` | Inter-Storm Saturation |
| `EP-2022-09-DELUGE` | Monsoonal Deluge | 2022-09-04 - 2022-09-08 | 2022-09-05 | $148.6\text{ mm}$ | 13 | `CLOSED` | Catastrophic Urban Deluge |
| `EP-2022-09-RECEDE` | Post-Event Drainage | 2022-09-09 - 2022-09-15 | 2022-09-10 | $18.4\text{ mm}$ | 0 | `CLOSED` | Post-Event Recession |
| `EP-LIVE-FCST` | 72h Continuous Forecast | 2026-11-05 - 2026-11-08 | 2026-11-06 | $68.2\text{ mm}$ | 0 | `WATCH` | Heavy Rain Advisory Watch |

- **Deliverable Dataset:** [`data/processed/flood_event_monitoring_log.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/flood_event_monitoring_log.parquet) (6 rows, SHA-256: `95346ea6e6ecfe523ba709320800b731e843e9c60e57ff330bc63d0bebc831b0`).

---

## 6. Phase 4.5: Operational Web Surveillance Dashboard

### 6.1 Server Architecture (`src/floodrisk/dashboard/server.py`)
- **Zero Heavy Web Framework Dependencies:** Implemented as a clean subclass of Python's standard `http.server.SimpleHTTPRequestHandler` with `socketserver.ThreadingMixIn`.
- **In-Memory GeoJSON & Parquet Caching:** All spatial polygons and dynamic risk attributes are cached on startup, providing sub-50 ms response times.
- **REST APIs Implemented:**
  - `GET /api/summary`: Platform metrics, active alert counts, domain bbox, and scientific decision status.
  - `GET /api/cells`: Complete EPSG:6933 GeoJSON FeatureCollection with 4-layer attributes.
  - `GET /api/incidents`: 21 catalogued historical incidents with uncertainty buffers.
  - `GET /api/episodes`: 6 monitored episodes with lifecycle states.
  - `GET /api/manifest`: Live cryptographic verification status of all 33 registered datasets.
  - `GET /api/health`: Health probe.

### 6.2 Interactive Leaflet Interface (`static/index.html`)
- **Strict Visual Standards:** Clean, accessible styling adhering to WCAG 2.1 contrast standards; zero glassmorphism, zero illegible visual artifacts.
- **Dynamic Thematic Layers:** Toggles between Dynamic Risk, Static Susceptibility, 24h NWP Forecast, Observed Monsoonal Exposure, Historical Incidents (with uncertainty circles), and Quarantined SAR footprints.
- **Interactive Cell Inspector:** Selecting any cell immediately breaks down its exact attributes across all four independent layers.
- **CLI Operational Command:** `python -m floodrisk.cli dashboard --port 8501`.

---

## 7. Phase 4.6: Verification, Testing & Cryptographic Audit

### 7.1 Automated Pytest Suite
- **Total Tests Passed:** 87 / 87 (100% pass rate in ~19.2 seconds).
- **Subsystem Test Modules:**
  - `tests/test_validation.py` (13 tests): Schema & boundary validation.
  - `tests/test_cli.py` (8 tests): Operational CLI suite.
  - `tests/test_zonal.py` (12 tests): Raster extraction windowing and geometry masking.
  - `tests/test_integration_real_data.py` (14 tests): SRTM DEM and WorldCover integration.
  - `tests/test_rainfall.py` (11 tests): Precipitation aggregation and API decay.
  - `tests/test_sar.py` (10 tests): Sentinel-1 SAR log-ratio differencing and quarantine flags.
  - `tests/test_spatial_validation.py` (7 tests): Spatial buffers (5, 10, 15 km) and block CV.
  - `tests/test_phase3_models.py` (6 tests): Baseline exploratory modeling.
  - `tests/test_phase_4.py` (6 tests): Forecast ingestion, exposure indicators, dynamic intelligence, event monitoring, dashboard REST APIs, and manifest integrity.

### 7.2 Cryptographic Manifest Audit
- All 33 datasets registered in [`reports/dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/dataset_manifest.json) recomputed and verified via SHA-256 chunked hashing.
- Integrity match rate: **100.0% VALID** across all source files, intermediate rasters, feature tables, and model artifacts.

---

## 8. Formal Exit Decision: Decision B

The project evaluation panel formally confirms **Decision B (Partial Operational Platform Validated)**:

1. **Why Decision A (Supervised Flood Prediction) is NOT Justified:**
   - Supervised ML models require spatially exhaustive, calibrated ground truth (e.g., millimeter-accurate water depths across all cells during storm events).
   - The platform possesses 21 reported point incidents; treating unreported cells as negative (dry) creates severe reporting bias.
   - Dual-scene Sentinel-1 SAR observations are separated by 24 days, and synthetic SAR fixtures are quarantined.
2. **Why Decision B is Substantially Achieved:**
   - Real-world digital elevation and high-resolution land-cover rasters are integrated with sub-pixel geometry masking.
   - Real-time continuous NWP forecasting (ECMWF IFS / GFS) is operational with strict issue-time decoupling.
   - Dynamic multi-criteria risk intelligence is operational across 1,170 equal-area grid cells.
   - A multi-episode event monitoring lifecycle engine is operational.
   - A high-performance, accessible operational web dashboard and REST API console are deployed.
   - 100% test pass rate (87/87) and 100% cryptographic SHA-256 verification (33/33 datasets) are verified.

