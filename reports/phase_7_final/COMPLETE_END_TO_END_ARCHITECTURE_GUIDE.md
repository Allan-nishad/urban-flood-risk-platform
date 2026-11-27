# Complete End-to-End Project Summary & Architecture Guide

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Repository:** `urban-flood-risk-platform`  
**Study Domain:** Bengaluru Urban District, Karnataka, India (1,170 km² Domain, EPSG:6933 Equal-Area 1-km Grid)  
**Final Release Baseline:** `v7.2.0-FREEZE`  
**Formal Acceptance Decision:** `FINAL_PROJECT_ACCEPTED_WITH_DOCUMENTED_LIMITATIONS`  
**Supervised Machine Learning Status:** `CURRENTLY_BLOCKED_BY_INSUFFICIENT_REPRESENTATIVE_INDEPENDENT_EVIDENCE`  
**Date of Audit & Reconciliation:** November 2026  

---

## 1. Executive Summary & Research Mandate

This guide serves as the definitive academic and technical reference for the **Urban Flood Risk Platform**. The project was undertaken to establish whether numerical weather prediction, satellite synthetic aperture radar (SAR), and physical hydrological modeling can reliably support early detection and predictive forecasting of urban flood risks in Bengaluru, India.

Rather than publishing artificially inflated machine learning metrics trained on incomplete observations, the project conducted a repository-grounded empirical audit across four physical tiers:
1. **Numerical Weather Prediction (Track A):** Evaluated genuine NOAA Global Forecast System (GFS 0.25°) GRIB2 forecasts against ground rain gauges across the August–September 2022 deluges ($N=256$). The evaluated product exhibited poor heavy-rain detection in this sample ($\text{POD} = 0.00$ at $\ge 64.5\text{ mm/day}$), with an $\text{MAE} = 18.64\text{ mm}$, $\text{RMSE} = 33.19\text{ mm}$, $\text{Mean Bias} = -10.88\text{ mm}$, and Pearson $r = 0.142$ (date-clustered 95% CI $[-0.07, +0.50]$).
2. **Satellite Remote Sensing (Track B):** Evaluated Copernicus Sentinel-1 C-band SAR observations over verified ground flood sites. Cautious scattering deconstruction demonstrated that only $38.5\%$ ($5/13$) of positive flood cells exhibited candidate specular water-expansion signals, while $30.8\%$ ($4/13$) were confounded by permanent lake basins, $7.7\%$ ($1/13$) produced double-bounce anomalies, and $23.1\%$ ($3/13$) experienced poor observability or radar shadow in dense urban canyons.
3. **Physical Hydrology & Topography (Track C):** Implemented deterministic D8 single-flow routing, SAGA Topographic Wetness Index (TWI), and 2D depression filling on 30m SRTM DEM data. The analysis identified 19 DEM-derived depressions/sinks (maximum computed depression depth: 4.85 m in Phase 6, 6.17 m in Phase 7 unconditioned DEM). Hydrological Inundation Potential Index (HIPI) evaluation against reference cells ($N=20$) yielded an $\text{ROC-AUC} = 0.560$ (Hanley–McNeil 95% CI $[0.303, 0.817]$), demonstrating that macro-topography alone cannot resolve sub-grid roadside walls and culverts.
4. **Machine Learning Governance:** Because $98.29\%$ ($1,150/1,170\text{ cells}$) of the urban domain is unobserved and verified flood reports are concentrated in narrow geographic clusters, supervised machine learning flood prediction is **strictly BLOCKED** under the governance status `CURRENTLY_BLOCKED_BY_INSUFFICIENT_REPRESENTATIVE_INDEPENDENT_EVIDENCE`.

The platform software is fully implemented, verified, and locked under release candidate `v7.2.0-FREEZE`, with 109 automated tests passing and 19 active REST API endpoints.

---

## 2. Reconciled Data Inventory & Manifest Audit

Every dataset in the repository has been audited directly against physical files on disk.

### 2.1 Physical Storage Accounting
* **Total Physical Files in `data/`:** **426 files**
* **Total Physical Size of `data/`:** **543,465,210 bytes** (which equals **543.47 MB** decimal [$10^6$ bytes] or **518.29 MiB** binary [$1024^2$ bytes]).

```
data/
├── raw/         : 356 files | 521,325,158 bytes (521.33 MB / 497.17 MiB)
│   ├── phase6/nwp/   : 340 files (170 GRIB2 + 170 IDX) | 152.79 MB
│   ├── weather/      :   3 files (Historical Sentinel-1 TIFFs) | 141.37 MB
│   ├── land_cover/   :   2 files (ESA WorldCover 10m GeoTIFF) | 127.65 MB
│   ├── elevation/    :   7 files (SRTM 30m HGT, ZIP, GeoTIFF) |  99.51 MB
│   └── placeholders  :   4 files (flood_events, hydrology, rainfall, terrain) | 4 bytes
├── processed/   :  67 files |  22,140,049 bytes ( 22.14 MB /  21.11 MiB)
│   ├── core/phase3/5 :  24 files (Grid GeoJSON/GPKG, baselines, indicator parquets)
│   ├── phase6/       :  18 files (NWP archive, gauges, flood matrix, SAR, hydrology)
│   └── phase7/       :   5 files (Error registry, verification, SAR, hydrology parquets)
├── interim/     :   1 file  |          1 byte  (Placeholder .gitkeep)
└── external/    :   2 files |          2 bytes (Placeholder .gitkeep)
```

### 2.2 Multi-Manifest Accounting & Bit-for-Bit Verification
Across the project's historical phases, datasets were catalogued in six manifest ledgers:

| Manifest File | Phase / Milestone Scope | Declared Entries |
|---|---|:---:|
| `reports/dataset_manifest.json` | Phase 1–4 Core Baseline Manifest | 33 entries |
| `reports/phase_5_dataset_manifest.json` | Phase 5 Initial Evaluation Manifest | 8 entries |
| `reports/phase_5_final_dataset_manifest.json` | Phase 5 Final Acceptance Manifest | 8 entries |
| `reports/phase_5_2/phase_5_2_dataset_manifest.json` | Phase 5.2 Closure Audit Manifest | 3 entries |
| `reports/phase_6/phase_6_master_manifest.json` | Phase 6 Authentic Baseline Manifest | 16 entries |
| `reports/phase_7_manifests/phase_7_final_manifest.json` | Phase 7 Final Comprehensive Master Ledger | 73 entries |
| **Total Manifest Declarations (Across 6 files)** | | **141 declarations** |

#### Reconciliation of Manifest Declarations:
* **Unique Dataset IDs Across All Manifests:** **81 unique IDs**
* **Unique Physical File Paths Referenced:** **102 unique file paths**
* **Duplicate Dataset IDs Across Manifests:** **60 IDs** (resulting from progressive phase baselines re-declaring frozen datasets)
* **Duplicate File Paths Across Manifests:** **39 paths**
* **Checksum Verification Status:** **102 out of 102 unique physical files exist on disk and match their recorded SHA-256 hashes bit-for-bit (0 mismatches, 0 missing).**
* **Consolidated Master Manifest (`phase_7_final_manifest.json`):** Tracks **73 registered datasets** (68 baseline datasets + 5 Phase 7 research datasets), with all 73 verified bit-for-bit.

---

## 3. Meteorological Architecture (Track A)

### 3.1 GFS Forecast Ingestion & Grid Extraction
* **Data Source:** Genuine NOAA NCEP Global Forecast System (GFS 0.25°) archived GRIB2 byte slices retrieved from AWS Open Data (`noaa-gfs-bdp-pds`).
* **Temporal Scope:** August 25, 2022 to September 10, 2022 (covering the peak monsoon cloudbursts).
* **Forecast Cycles:** 00:00 UTC and 12:00 UTC cycles across 17 calendar days (34 cycles).
* **Lead Times & Accumulation:** Forecast horizons of $T+6\text{h}$, $T+12\text{h}$, $T+24\text{h}$, $T+48\text{h}$, and $T+72\text{h}$. Precipitation parameter: `APCP` (Accumulated Precipitation in kg/m², equivalent to mm).
* **Raw Archive Slices:** 170 downloaded `.grib2` byte slices and 170 `.idx` index files.
* **ecCodes Ingestion:** 340 GRIB2 messages decoded.

### 3.2 Native Grid Resolution vs Analytical Grid
* **Native Grid Scale:** GFS operates on a native global spherical grid of $0.25^\circ \times 0.25^\circ$ ($\approx 27.75\text{ km}$ spatial resolution over Bengaluru).
* **Domain Grid Nodes:** **Exactly 6 native GFS grid nodes** cover the entire 1,170 km² Bengaluru study domain:
  1. $(12.75^\circ\text{N}, 77.50^\circ\text{E})$
  2. $(13.00^\circ\text{N}, 77.50^\circ\text{E})$
  3. $(13.25^\circ\text{N}, 77.50^\circ\text{E})$
  4. $(12.75^\circ\text{N}, 77.75^\circ\text{E})$
  5. $(13.00^\circ\text{N}, 77.75^\circ\text{E})$
  6. $(13.25^\circ\text{N}, 77.75^\circ\text{E})$
* **Analytical Grid Mapping Method:** In `scripts/phase6/acquire_nwp.py`, mapping from native GFS coordinates to the 1,170 1-km equal-area cells (EPSG:6933) is implemented via **nearest-node selection** (`mapping_method: "nearest_native_0p25"` based on Haversine distance between cell centroids and native nodes). It does **not** use bilinear interpolation.
* **Mapped Forecast Archive:** 198,900 cell forecast records ($1,170\text{ cells} \times 34\text{ cycles} \times 5\text{ lead times}$).

### 3.3 Ground Rainfall Network & Observation Reconciliation
* **Nominal Station Registry:** 21 stations recorded in `rain_gauge_station_registry.parquet`.
* **Station Categorization:**
  * **16 Primary Hydrological Stations (`is_primary_hydrological_gauge: True`):**
    * 3 IMD Observatory Stations: Bengaluru City (43295), HAL Airport (43296), KIA Devanahalli.
    * 13 KSNDMC Telemetric Rain Gauges: Mahadevapura, Doddaneckkundi, Bellandur, Marathahalli, Whitefield, Varthur, BTM Layout, Koramangala, Vidyapeetha, Kengeri, Yelahanka, Hebbal, Peenya.
  * **5 Excluded Air-Quality Stations (`is_primary_hydrological_gauge: False`):**
    * CPCB Continuous Ambient Air Quality Monitoring (CAAQM) stations (BTM, BWSSB, Railway, Peenya, Saneguru) excluded from hydrological rainfall evaluation due to lack of validated tipping-bucket rainfall sensors.
* **Primary Observations Count:** **272 daily 24-hour rainfall observations** ($16\text{ stations} \times 17\text{ observation days}$).
* **Matched Forecast-Observation Pairs:** **256 paired records** compiled in `phase7_forecast_error_registry.parquet` (matched at 24-hour lead time across valid cycle alignments).

### 3.4 Audited Forecast Verification Results
Verification metrics evaluated across the 256 paired records (using the standard **$\text{Forecast} - \text{Observation}$** error convention):
* **Mean Forecast Rainfall:** $13.14\text{ mm}$
* **Mean Observed Rainfall:** $24.02\text{ mm}$
* **Mean Bias ($\text{Forecast} - \text{Observed}$):** **$-10.88\text{ mm}$** (systematic under-forecasting of storm rainfall)
* **Mean Absolute Error (MAE):** **$18.64\text{ mm}$**
* **Root Mean Square Error (RMSE):** **$33.19\text{ mm}$**
* **Pearson Correlation Coefficient ($r$):** **$0.142$**
* **Categorical Contingency at IMD Heavy Rain Threshold ($\ge 64.5\text{ mm/day}$):**
  * **Hits:** 0
  * **Misses:** 23
  * **False Alarms:** 0
  * **Correct Negatives:** 233
  * **Probability of Detection (POD):** **$0.00$** ($0 / 23$)
  * **Critical Success Index (CSI):** **$0.00$**

### 3.5 Scientific Assessment of Meteorological Skill
These empirical findings do **not** imply that NOAA GFS is defective as a global atmospheric model; rather, they demonstrate that the evaluated product had poor heavy-rain detection in this particular sample and study period. Global 25-km models mechanically average moisture over hundreds of square kilometers, smoothing out localized, high-intensity convective cloudbursts ($>70\text{ mm/hr}$). 

Local X-band Doppler weather radar is presented as a **possible future source of higher-resolution observations** for convective nowcasting, rather than a proven necessary or sufficient remedy on its own.

---

## 4. Flood Evidence & Observational Coverage (Track B)

### 4.1 Count Reconciliation: Incidents, Locations & Cells
Ground flood observations from the August–September 2022 deluges were audited to resolve terminology differences:

```
+-------------------------------------------------------------------------------+
|                      FLOOD OBSERVATION COUNT RESOLUTION                       |
|                                                                               |
|  24 Incident Records       --> Distinct temporal event reports                |
|           |                                                                   |
|           v                                                                   |
|  17 Physical Locations     --> Unique named geographical sites                |
|           |                                                                   |
|           v                                                                   |
|  13 Positive 1-km Cells    --> Intersected EPSG:6933 1-km grid cells (1.11%)  |
|                                                                               |
|  PLUS:                                                                        |
|   7 Monitored Proxy Cells  --> 5 high-ridge proxies + 2 drainage sites (0.60%)|
|                                                                               |
|  REMAINDER:                                                                   |
|  1,150 Unobserved Cells    --> No monitoring sensors / records (98.29%)       |
+-------------------------------------------------------------------------------+
```

* **24 Incident Records:** Discrete temporal flood event entries in `independent_flood_incident_inventory.parquet`. Multiple records exist for chronic locations that flooded repeatedly across successive storm cycles (e.g., Rainbow Drive flooded on Aug 30, Sep 02, and Sep 05; RMZ Ecoworld flooded on Sep 02 and Sep 05).
* **17 Distinct Physical Locations:** When the 24 event reports are grouped by physical site name, they represent 17 unique geographic locations.
* **13 Positive 1-km Grid Cells:** When mapped to the EPSG:6933 1-km equal-area grid, some locations fall into the same 1-km cell (e.g., Kasavanahalli Main Road and Kasavanahalli Lake Outfall share cell `g1000_7494_1632`). Thus, 17 locations occupy 13 positive cells.
* **7 Monitored Negative-Control / Proxy Cells:** Consist of 5 high-ridge locations with monitored dry conditions (`MONITORED_DRY_HIGH_RIDGE`) and 2 locations with confirmed functioning drainage (`MONITORED_DRY_FUNCTIONAL_DRAINAGE`). These are **monitored negative-control proxy cells**, not comprehensively verified dry ground across all conditions.
* **1,150 Unobserved Domain Cells:** The remaining 1,150 cells ($98.29\%$ of the urban domain) have **limited observational coverage** with no verified reference sensors or field reports. **Unobserved cells must never be treated as negative (dry) labels.**

### 4.2 Supervised Learning Status
Because only $1.71\%$ ($20/1,170\text{ cells}$) of the domain has reference observations and confirmed flood reports exhibit strong spatial clustering along IT corridors (reporting bias), training a supervised classifier produces severe pseudo-absence bias.

* **Official Governance Status:**  
  `CURRENTLY_BLOCKED_BY_INSUFFICIENT_REPRESENTATIVE_INDEPENDENT_EVIDENCE`
* **Pseudo-Absence Clarification:** In an invalid pseudo-absence scenario where unobserved cells are arbitrarily assumed to be "dry", a naive null classifier predicting "no flood" everywhere would trivially achieve $98.3\%$ accuracy ($1,150 / 1,170$). This is **not an actual model result**, but a mathematical demonstration of why supervised machine learning evaluation is disqualified on this dataset.

---

## 5. Satellite SAR Remote Sensing Architecture (Track B)

### 5.1 Radar Data Provenance & Processing Execution
* **Satellite Platform:** Copernicus Sentinel-1A C-SAR (C-band, $5.405\text{ GHz}$, wavelength $\lambda \approx 5.6\text{ cm}$, Interferometric Wide Swath, Level-1 Ground Range Detected [GRD], descending relative orbit 165).
* **Co-Event Acquisition:** September 5, 2022 at 00:46:16 UTC (06:16 AM IST), capturing peak inundation immediately following the overnight cloudburst.
* **Processing Execution Audit:**
  * Three authentic Sentinel-1 SAFE catalogue records were verified in `sar_scene_audit_registry.parquet`.
  * As established in the Phase 6.1 audit, **local SAFE archive decompression and local SNAP GPT graph execution were not executed locally in this repository**.
  * The repository does not contain an executable Gamma-zero calibration or $7\times 7$ Lee speckle-filter pipeline; existing backscatter rasters reflect pre-calibrated products.

### 5.2 Deconstructed Radar Regimes Across the 13 Inundated Cells
Analysis of backscatter values across the 13 positive cells in `phase7_sar_evidence_comparison.parquet` reveals four distinct physical scattering regimes:

| Regime Classification | Cell Count | Percentage | Representative Cells / Locations | Physical Radar Mechanism |
|---|:---:|:---:|---|---|
| **Candidate Specular Water Signals** | 5 | **38.5%** | `g1000_7487_1631` (Vijaya Bank), `g1000_7489_1636` (Koramangala 4th), `g1000_7489_1650` (Manyata), `g1000_7495_1633` (Rainbow Drive), `g1000_7495_1635` (RMZ Ecoworld) | Calm open floodwater acts as a specular reflector, bouncing radar pulses away from the antenna (observed $\Delta\text{VV} = -0.05\text{ dB}$ to $-0.74\text{ dB}$). |
| **Permanent Lake Confounders** | 4 | **30.8%** | `g1000_7494_1632` (Kasavanahalli), `g1000_7496_1632` (Greenwood/Hadosiddapura), `g1000_7496_1643` (Mahadevapura), `g1000_7500_1636` (Varthur Outlet) | Pre-existing water bodies exhibit low backscatter year-round ($\Delta\text{VV} \approx 0.00\text{ dB}$). Conflates lake surfaces with flood expansion. |
| **Dielectric Double-Bounce Anomaly** | 1 | **7.7%** | `g1000_7495_1637` (Divyasree 77 East Villas, Yamalur) | Floodwater meeting vertical villa walls forms a 90° dihedral corner reflector, causing backscatter to *increase* ($\Delta\text{VV} = +0.02\text{ dB}$) rather than decrease. |
| **Poor Observability / Shadow-Related** | 3 | **23.1%** | `g1000_7490_1648` (HBR Layout/Nagavara), `g1000_7497_1641` (Doddanekkundi Ph 2), `g1000_7498_1639` (Munnekolala/Spice Garden) | Radar pulse attenuated or obstructed by dense tree canopy, industrial roofs, and narrow urban street canyon shadowing ($\Delta\text{VV} = 0.00\text{ dB}$). |

### 5.3 Cautious Interpretation
* **38.5% is a candidate specular signal rate**, not a validated operational detection sensitivity.
* The three unobserved cases are **obscuration/shadow-related cases**, not confirmed flood misses, because sub-meter independent ground-truth boundary extent was not available to verify water presence beneath canopies at 06:16 AM.

---

## 6. Physical Hydrological Architecture (Track C)

### 6.1 Terrain Ingestion & Catchment Routing
* **Source DEM:** NASA/USGS Shuttle Radar Topography Mission (SRTM) 1 arc-second ($\approx 30\text{m}$ native resolution), reprojected and aggregated to the EPSG:6933 1-km analytical grid.
* **Flow Direction Algorithm:** Deterministic D8 steepest descent (O'Callaghan & Mark, 1984), routing surface runoff from each cell to the steepest downslope neighbor.
* **Flow Accumulation:** Propagated flow area calculated in **square kilometers ($\text{km}^2$)**. Accumulation across the domain spans from $1.0\text{ km}^2$ (headwater ridge divides) to $186.0\text{ km}^2$ (regional trunk valleys draining toward the Ponnaiyar and Arkavathi basins).
* **Topographic Wetness Index (TWI):** Formulated as $\text{TWI} = \ln\left(\frac{a}{\tan \beta}\right)$, where $a$ is specific catchment area per unit contour length ($L = 1,000\text{ m}$) and $\beta$ is local slope gradient. TWI values range from $10.08$ on steep ridge crests to $19.04$ on valley drainage floors.

### 6.2 DEM-Derived Depressions & Sink Slices
* **Algorithm:** 2D priority-flood depression identification (`fill_depressions_2d` in `scripts/phase6/build_hydrology.py`).
* **Depression Count:** **19 DEM-derived depressions/sinks** identified where surface cells cannot drain to neighbors without filling.
* **Computed Depression Depths:** Maximum computed depression depth is **4.85 m** in Phase 6 conditioned analysis and **6.17 m** in Phase 7 unconditioned sensitivity analysis.
* **Physical Caveat:** Computed depression depth is **not a measured water depth**. These 19 features are **DEM-derived depressions/sinks**, not confirmed physical retention basins.
* **Storage Volume Caveat:** Specific volumetric water storage is **not calculated** because detailed sub-surface bathymetry, sediment infill, and staged capacity curves were not available.

### 6.3 Susceptibility Discrimination & ROC-AUC Analysis
Terrain susceptibility was evaluated using the Hydrological Inundation Potential Index (HIPI):
$$\text{HIPI} = 0.35 \cdot \text{Normalized}(\text{TWI}) + 0.25 \cdot \text{Normalized}(\text{Sink Depth}) + 0.40 \cdot \text{Forecast Runoff}$$

* **Evaluation Sample:** $N = 20$ reference cells (13 verified positive, 7 monitored negative proxies).
* **Empirical ROC-AUC:** **$0.560$** (marginally above $0.500$).
* **Standard Error ($\text{SE}$):** $0.131$ (Hanley & McNeil, 1982 formulation).
* **Analytical 95% Confidence Interval:** **$[0.303, 0.817]$**
* **Scientific Interpretation:** Because the 95% confidence interval completely spans $0.500$, this small evaluation does **not demonstrate useful predictive performance**. However, this does not establish statistical equivalence to pure chance; rather, the small reference sample ($N=20$) is statistically insufficient to prove discrimination.
* **Scale Limitation:** Macro-scale 30m / 1-km terrain models cannot resolve 2-meter roadside masonry walls, stormwater culverts, road berms, or localized trash blockages that control street-level urban flooding.

---

## 7. Real Dashboard & REST API Architecture

### 7.1 Backend Server & Route Architecture
The dashboard backend is implemented in `src/floodrisk/dashboard/server.py` using Python's standard library `http.server.ThreadingHTTPServer`. It loads an in-memory `DashboardDataStore` during initialization.

```
                    REQUEST DISPATCH ARCHITECTURE
+-------------------------------------------------------------------+
|                        HTTP GET REQUEST                           |
+---------------------------------+---------------------------------+
                                  |
            +---------------------+---------------------+
            | clean_path.startswith('/api/')             | Other path
            v                                           v
+-------------------------------+           +-----------------------+
|  19 Live REST API Endpoints   |           | Static Asset Router   |
|  - JSON Data Payloads         |           | - '/' -> index.html   |
|  - CORS & Error Middleware    |           | - static assets       |
+-------------------------------+           +-----------------------+
```

### 7.2 Complete REST API Endpoint Inventory
The platform serves **19 active REST API endpoints** under `/api/*`:

| # | Endpoint Route | Method | Response Type | Underlying Data Source |
|---|---|:---:|:---:|---|
| 1 | `/api/summary` | GET | `application/json` | In-memory summary dictionary (`features_integrated_bengaluru.parquet`) |
| 2 | `/api/cells` | GET | `application/json` | `grid_bengaluru_urban_1000m.geojson` (1,170 cells) |
| 3 | `/api/incidents` | GET | `application/json` | `flood_event_inventory_bengaluru.parquet` |
| 4 | `/api/episodes` | GET | `application/json` | `flood_event_monitoring_log.parquet` |
| 5 | `/api/manifest` | GET | `application/json` | `reports/dataset_manifest.json` |
| 6 | `/api/phase5/verification-metrics` | GET | `application/json` | `phase5_forecast_verification.parquet` |
| 7 | `/api/phase5/flood-validation` | GET | `application/json` | `phase5_flood_validation_dataset.parquet` |
| 8 | `/api/phase5/sar-manifest` | GET | `application/json` | `phase5_sar_observations.parquet` |
| 9 | `/api/phase5/readiness-gates` | GET | `application/json` | Phase 5 readiness checklist dictionary |
| 10 | `/api/phase6/summary` | GET | `application/json` | Phase 6 milestone summary dictionary |
| 11 | `/api/phase6/nwp` | GET | `application/json` | `nwp_forecast_provenance.parquet` & GFS verification |
| 12 | `/api/phase6/ground-rainfall` | GET | `application/json` | `rain_gauge_station_registry.parquet` & observations |
| 13 | `/api/phase6/flood-evidence` | GET | `application/json` | `flood_validation_ground_truth_matrix.parquet` & gate audit |
| 14 | `/api/phase6/sar` | GET | `application/json` | `sar_scene_audit_registry.parquet` & cross-validation |
| 15 | `/api/phase6/hydrology` | GET | `application/json` | `topographic_routing_stats.parquet` & depression sinks |
| 16 | `/api/phase6/manifest` | GET | `application/json` | `reports/phase_6/phase_6_master_manifest.json` |
| 17 | `/api/phase7/summary` | GET | `application/json` | `reports/phase_7/phase_7F_final_results.md` (parsed) |
| 18 | `/api/phase7/uncertainty` | GET | `application/json` | `reports/phase_7/phase7B_grouped_uncertainty_results.json` |
| 19 | `/api/health` | GET | `application/json` | System health check (`{"status": "ok"}`) |

#### Reconciliation of 15 vs 19 Endpoints:
* In Phase 6 (Workstream 6F), the initial operational delivery contained **15 REST endpoints** (9 baseline endpoints + 5 Phase 6 endpoints + 1 health endpoint).
* In Phase 7, two new analytical endpoints were introduced (`/api/phase7/summary` and `/api/phase7/uncertainty`), and two Phase 6 endpoints were further modularized (`/api/phase6/hydrology` and `/api/phase6/manifest`), bringing the total to **19 REST endpoints**.
* Static frontend routes (`/` and `/index.html`) serve the HTML user interface and are distinguished from API endpoints.

### 7.3 Frontend User Interface Verification
Inspection of `src/floodrisk/dashboard/static/index.html` reveals the actual UI layout:
* **Layout Structure:** A full-screen interactive Leaflet map canvas accompanied by an Executive Header and a slide-out Side Inspection Panel.
* **Side Panel Tabs:** Implements **three drawer tabs** (not six separate full-page tabs):
  1. `inspectorTab` ("Cell Audit"): Displays 4-layer cell diagnostics (Static Susceptibility, Observed Monsoonal Exposure, NWP Forecast Exposure, and Ground Flood Evidence).
  2. `forecastTab` ("72h Timeline"): Displays rolling hourly rainfall forecast charts for the selected cell.
  3. `incidentsTab` ("Incidents (21)"): Displays catalogued ground deluge incidents and allows zoom-to-location.
* **Phase 6 Embedded Cards:** A dedicated collapsible view (`phase6Tab`) rendering status cards for Stages 6A through 6E, prominently displaying the `ML Gate: BLOCKED` warning.
* **Dynamic Styling:** Features JavaScript color scaling (`getDynamicColor`, `getStaticColor`, `getForecastColor`) rendering cells with green/amber/red susceptibility gradients based on MCDA static scores and rolling rainfall.
* **External CDN Dependencies:** The frontend is **not completely offline or dependency-free**:
  * Loads Leaflet JavaScript from `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js`.
  * Loads Leaflet CSS from `https://unpkg.com/leaflet@1.9.4/dist/leaflet.css`.
  * Renders basemap tiles via CartoDB Positron (`https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png`).

---

## 8. Statistical Terminology & Bootstrap Methodology

### 8.1 Exact Bootstrap Implementation in `grouped_uncertainty.py`
To avoid misrepresenting statistical methods, the exact implementation in `scripts/phase7/grouped_uncertainty.py` is documented below:
* **Resampling Unit:** Forecast cycle date (`target_obs_date`).
* **Cluster Definition:** **Date-clustered resampling**. All 16 primary stations recorded on a given date are sampled together as an intact cluster block to preserve spatial autocorrelation across stations during a storm.
* **Cluster Sample Size:** 16 unique calendar dates.
* **Iterations:** 2,000 bootstrap iterations (`n_iter = 2000`, seeded at 42).
* **Replacement Procedure:** Unrestricted random draw with replacement from the set of 16 dates (`np.random.choice(unique_dates, size=16, replace=True)`).
* **Recalculated Statistics:** MAE, RMSE, Mean Bias ($\text{Forecast} - \text{Observed}$), and Pearson correlation ($r$) recomputed on each pooled pseudo-sample ($N=256$).

### 8.2 Derivation of Uncertainty Width Inflation Factors
The reported inflation factors ($3.1\times$ to $4.2\times$) represent the **Uncertainty Width Inflation Factor**, defined as the ratio of the 95% confidence interval width under date-clustered resampling to the width under naive i.i.d. resampling:
$$\text{Uncertainty Width Inflation Factor} = \frac{\text{CI}_{97.5\%}^{\text{date}} - \text{CI}_{2.5\%}^{\text{date}}}{\text{CI}_{97.5\%}^{\text{naive}} - \text{CI}_{2.5\%}^{\text{naive}}}$$

| Evaluation Metric | Point Estimate | Naive i.i.d. 95% CI | Naive Width | Date-Clustered 95% CI | Clustered Width | Uncertainty Width Inflation Factor |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **MAE** | $18.64\text{ mm}$ | $[15.34, 22.31]$ | $6.97\text{ mm}$ | $[8.71, 30.64]$ | $21.93\text{ mm}$ | **$3.15\times$** |
| **RMSE** | $33.19\text{ mm}$ | $[26.94, 39.35]$ | $12.41\text{ mm}$ | $[11.40, 49.57]$ | $38.17\text{ mm}$ | **$3.08\times$** |
| **Mean Bias** | $-10.88\text{ mm}$ | $[-15.14, -7.22]$ | $7.92\text{ mm}$ | $[-24.89, +1.27]$ | $26.16\text{ mm}$ | **$3.30\times$** |
| **Pearson $r$** | $0.142$ | $[0.077, 0.216]$ | $0.138$ | $[-0.075, +0.505]$ | $0.580$ | **$4.19\times$** |

### 8.3 Methodological Clarifications
* **Resampling Type:** This is **date-clustered resampling**, not a spatial block bootstrap. It clusters by temporal forecast cycle rather than spatial bounding boxes.
* **Confidence Interval Interpretation:** Naive i.i.d. resampling artificially narrows confidence intervals by treating autocorrelated stations as independent samples. When clustered by storm date, the 95% confidence interval for Pearson correlation widens to **$[-0.07, +0.50]$**, which crosses zero, indicating that the correlation is not statistically distinguishable from zero at the 95% confidence level.

---

## 9. Software Quality & Reproducible Reviewer Protocol

### 9.1 Automated Test Suite Results
The full test suite was executed via `.venv\Scripts\pytest.exe -v`:
* **Total Tests Executed:** **109 items** across 16 test modules.
* **Test Suite Result:** **109 passed, 0 failed, 0 errors** (100% pass rate in 63.14 seconds).
* **Scope Tested:** Manifest integrity, EPSG:6933 grid geometry, GFS GRIB2 parsing, rain-gauge validation matching, SAR backscatter extraction, D8 flow routing, SAGA TWI computation, 2D depression filling, Hanley–McNeil AUC calculation, and HTTP server endpoint dispatch.

### 9.2 Reproducible Verification Commands for Reviewers

```powershell
# 1. Verify all 73 datasets bit-for-bit against recorded SHA-256 hashes
.venv\Scripts\python.exe scratch\phase7_final_verify_all.py

# 2. Execute full automated test suite (109 tests)
.venv\Scripts\pytest.exe -v

# 3. Launch live dashboard server on port 8000
.venv\Scripts\python.exe -m floodrisk.cli dashboard --port 8000

# 4. Query live REST API telemetry endpoints
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/summary"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/phase6/nwp"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/phase7/uncertainty"
```

---

## 10. Honest Future Research Directions & Municipal Recommendations

Based on the verified physical and observational constraints established by this platform, future urban flood risk engineering should prioritize:
1. **Convective Nowcasting Infrastructure:** Global NWP (GFS 25-km) cannot resolve tropical cloudbursts. Municipal authorities should evaluate dual-polarization X-band Doppler weather radar (1-km spatial, 5-minute temporal resolution) combined with convective nowcasting models.
2. **Micro-Hydraulic Urban Elevation Models:** Replace 30m SRTM DEMs with 1m airborne LiDAR, explicitly incorporating 1D/2D hydraulic pipe-network modeling (e.g., EPA SWMM or HEC-RAS) to simulate sub-surface storm drains, compound walls, and culvert head losses.
3. **Multi-Sensor Satellite Constellations:** Complement C-band SAR with high-resolution X-band SAR (TerraSAR-X) and L-band SAR (NISAR) to overcome street-canyon shadowing and improve building-water double-bounce classification.
4. **Dense IoT Telemetry:** Deploy ultrasonic water-level sensors across the 19 identified natural depression sinks and cascading lake sluice gates to transition from unobserved domains ($98.29\%$) to representative real-time ground truth.

---

## 11. Final Academic Submission Declaration

The **Urban Flood Risk Platform** is officially documented, reconciled, and code-frozen. By replacing premature machine learning claims with rigorous physical evaluation, dependence-aware uncertainty quantification, and defensive software engineering, this research provides a transparent, scientifically defensible foundation for urban flood intelligence.

* **Final Designation:** `FINAL_PROJECT_ACCEPTED_WITH_DOCUMENTED_LIMITATIONS`
* **Supervised Learning Gate:** `CURRENTLY_BLOCKED_BY_INSUFFICIENT_REPRESENTATIVE_INDEPENDENT_EVIDENCE`

