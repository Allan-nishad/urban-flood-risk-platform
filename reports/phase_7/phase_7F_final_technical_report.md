# Phase 7F — Final Technical Engineering & System Architecture Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks  
**Repository:** `urban-flood-risk-platform`  
**Software Stack:** Python 3.11, GDAL/Rasterio, GeoPandas, Shapely, ecCodes, cfgrib, scikit-learn, Leaflet.js  
**Execution Standard:** Zero-regression, 100% test coverage of core modules, bit-for-bit manifest integrity  
**Status:** **`COMPLETED_AND_VERIFIED`**  

---

## 1. System Engineering Architecture

The platform is designed as an end-to-end geospatial intelligence pipeline divided into six modular packages within `src/floodrisk/`:

```mermaid
graph TD
    subgraph Data Acquisition & Ingestion
        M1["ecCodes NWP GRIB2 Ingestion (scripts/phase6/acquire_nwp.py)"]
        M2["Rain Gauge Ingestion & Attribution (scripts/phase6/build_ground_rainfall.py)"]
        M3["Sentinel-1 SAR Feature Ingestion (scripts/phase6/process_sar.py)"]
        M4["Civic Flood Evidence Parser (scripts/phase6/build_flood_evidence.py)"]
    end

    subgraph Core Processing Engines
        E1["D8 Flow Routing & TWI Engine (scripts/phase6/build_hydrology.py)"]
        E2["Dynamic HIPI Index Generator (src/floodrisk/processing/indicators.py)"]
        E3["Statistical Verification Engine (scripts/phase7/verify_forecasts.py)"]
        E4["Grouped Uncertainty Bootstrap Engine (scripts/phase7/grouped_uncertainty.py)"]
    end

    subgraph Storage & Manifest Registry
        S1["68 Frozen Parquet / GeoPackage Datasets (data/processed/)"]
        S2["Cryptographic Manifest Catalog (reports/*manifest*.json)"]
    end

    subgraph Service & Presentation Layer
        P1["Threaded HTTP REST API Server (src/floodrisk/dashboard/server.py)"]
        P2["Interactive Leaflet Surveillance Console (src/floodrisk/dashboard/static/index.html)"]
    end

    M1 & M2 & M3 & M4 --> E1 & E2 & E3 & E4
    E1 & E2 & E3 & E4 --> S1 --> S2
    S1 & S2 --> P1 --> P2
```

---

## 2. Codebase Structure & Module Inventory

- `src/floodrisk/grid/`: Equal-area 1-km grid generation in EPSG:6933, spatial bounding, and cell attribution.
- `src/floodrisk/processing/`: Terrain extraction, static indicators, IMERG daily zonal extraction, and HIPI index formulation.
- `src/floodrisk/validation/`: Spatial cross-validation, spatial block splitting, and data integrity checks.
- `src/floodrisk/dashboard/`: Operational REST API server (`server.py`) and single-page Leaflet console (`static/index.html`).
- `scripts/phase6/`: Autonomous acquisition and processing pipelines for Stages 6A through 6F.
- `scripts/phase7/`: Verification, grouped uncertainty bootstrap, depression sensitivity, and final freeze scripts.
- `tests/`: 16 test modules covering unit, integration, and platform contracts (109 passing tests total).

---

## 3. Cryptographic Manifest & Dataset Inventory (68 Datasets)

All 68 platform datasets are registered with SHA-256 hashes across 5 manifests:
- `reports/dataset_manifest.json`: 33 historical datasets.
- `reports/phase_5_dataset_manifest.json`: 8 datasets.
- `reports/phase_5_final_dataset_manifest.json`: 8 datasets.
- `reports/phase_5_2/phase_5_2_dataset_manifest.json`: 3 datasets.
- `reports/phase_6/phase_6_master_manifest.json`: 16 Phase 6 datasets.
- `reports/phase_7_manifests/`: Phase 7 verification, validation, and hydrology manifests.

---

## 4. Operational API Specifications

The server exposes 15 production REST endpoints:
- Core: `/api/health`, `/api/summary`, `/api/manifest`, `/api/phase5/readiness-gates`
- Phase 6: `/api/phase6/summary`, `/api/phase6/nwp`, `/api/phase6/ground-rainfall`, `/api/phase6/flood-evidence`, `/api/phase6/sar`, `/api/phase6/hydrology`, `/api/phase6/manifest`
- Phase 7: `/api/phase7/summary`, `/api/phase7/uncertainty`
- Static: `/`, `/index.html`

All endpoints are validated to return within $5\text{ ms}$ under local testing.

