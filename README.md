# AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data
### Phase 1: Data Foundation | Bengaluru First | India-Ready Architecture

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CRS EPSG:6933](https://img.shields.io/badge/CRS-EPSG%3A6933-green.svg)](https://epsg.io/6933)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Quick Start & Deployment

- **Beginner Deployment Guide (Docker / VPS / Local):** See [DEPLOY.md](DEPLOY.md)
- **Architecture & Data Flow:** See [docs/V8_ARCHITECTURE_AND_DATAFLOW.md](docs/V8_ARCHITECTURE_AND_DATAFLOW.md)
- **Stage & Audit Reports:** See [docs/reports/](docs/reports/)

```bash
cp .env.example .env          # Set FLOODRISK_ADMIN_TOKEN
docker compose up -d --build  # Starts dashboard on http://127.0.0.1:8501
```

---

## 1. Executive Summary

This repository hosts the **data foundation and geospatial processing engine** for the research-grade platform: *AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data*.

The initial operational study area is **Bengaluru Urban, Karnataka, India**, built on an **India-ready architecture** designed to scale seamlessly across Karnataka districts and pan-India without altering the processing engine or model pipeline.

### Core Scientific Distinctions
- **Flood Susceptibility:** Static topographic and land-surface vulnerability (slope, elevation depressions, upstream catchment area, impervious fraction).
- **Short-Term Flood Risk:** Dynamic hazard level driven by real-time precipitation accumulation, soil moisture status, and immediate convective storms interacting with susceptible terrain.
- **Flood Forecasting:** Future time-specific prediction conditioned on numerical weather predictions (NWP) and validated against historical inundation records.
- *Strict Rule:* Terrain screening scores are never labeled or claimed as validated flood forecasts.

---

## 2. India-Wide Spatial Grid Architecture (EPSG:6933)

To ensure geographic scalability across all of India, the platform utilizes **EPSG:6933** (`WGS 84 / NSIDC EASE-Grid 2.0 Global`; projection method: `Lambert Cylindrical Equal Area`, standard parallel $30^\circ\text{N/S}$) with a **globally anchored 1,000-metre ($1\text{ km}^2$) square grid**:

- **Global Anchoring:** Anchored at `(0.0, 0.0)` global coordinates in EPSG:6933:
  $$\text{col} = \lfloor x / 1000 \rfloor, \quad \text{row} = \lfloor y / 1000 \rfloor$$
- **Persistent Cell Identifiers:** `g{cell_size_m}_{col}_{row}` (e.g. `g1000_7472_1625`).
- **Boundary Invariance:** Any 1-km cell retains the **exact same ID and spatial footprint** whether processed within Bengaluru Urban alone, a sub-district, Karnataka state, or an India-wide regional grid.

---

## 3. Project Directory Structure

```
urban-flood-risk-platform/
│
├── configs/
│   ├── areas/
│   │   ├── bengaluru.yaml       # Canonical study-area config for Bengaluru Urban
│   │   ├── bengaluru_rural.yaml # Contiguous district config (overlap verification)
│   │   └── mysuru.yaml          # Demonstrator config proving geography independence
│   ├── schemas.yaml             # Canonical tabular data schemas (rainfall, forecast, events)
│   └── datasets.yaml            # Scientific dataset catalogue & unit conversion rules
│
├── data/
│   ├── raw/                     # Original, immutable source files (never overwritten)
│   │   ├── rainfall/
│   │   ├── weather/
│   │   ├── terrain/
│   │   ├── hydrology/
│   │   ├── land_cover/
│   │   └── flood_events/
│   ├── interim/                 # Cleaned, standardized, quarantined data
│   ├── processed/               # Standardized equal-area grids (GeoJSON/GPKG)
│   └── external/
│       ├── boundaries/          # Authoritative administrative polygons (SOI, KSRSAC, BBMP)
│       └── reference_locations/ # Critical infrastructure, lake catchments, gauges
│
├── src/
│   └── floodrisk/
│       ├── __init__.py
│       ├── cli.py               # Unified Click-based command line interface
│       ├── config.py            # Typed Pydantic configuration schemas & loaders
│       ├── ingestion.py         # Controlled file staging & registration
│       ├── provenance.py        # SHA-256 cryptographic provenance & manifest tracking
│       ├── validate.py          # CSV, raster, and vector validation engines
│       ├── spatial/
│       │   ├── __init__.py
│       │   ├── crs.py           # EPSG:6933 and WGS84 projection transformations
│       │   ├── grid.py          # Globally anchored equal-area grid generator
│       │   └── boundaries.py    # Boundary loader & development envelope fallback
│       └── processing/
│           ├── __init__.py
│           └── rainfall.py      # IMERG unit verification & rate-to-depth conversion
│
├── notebooks/                   # Research notebooks (Phase 2)
├── tests/                       # Complete automated pytest test suite (35 passing tests in Python 3.11)
│   ├── conftest.py              # Synthetic test fixtures (clearly isolated)
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_grid.py
│   ├── test_provenance.py
│   ├── test_rainfall.py
│   └── test_validation.py
│
├── reports/                     # Manifests, configuration & coverage reports
│   ├── bengaluru_configuration_report.md
│   ├── data_coverage_report.md
│   ├── flood_event_feasibility_report.md
│   ├── grid_distortion_report.json
│   └── dataset_manifest.json
│
├── docs/                        # Scientific documentation & limitations
│   └── data_sources_and_limitations.md
│
├── requirements.txt
├── pyproject.toml
├── .gitignore
└── README.md
```

---

## 4. Installation & Setup

### Prerequisites
- Python 3.11+
- Virtual environment tool (e.g., `venv` or `uv`)

### Installation via uv / pip

```powershell
# 1. Clone or navigate to the workspace
cd urban-flood-risk-platform

# 2. Install dependencies
python -m uv pip install -r requirements.txt

# 3. Install the floodrisk package in editable development mode
python -m uv pip install -e .
```

---

## 5. Command-Line Interface (CLI) Usage

The platform exposes an operational CLI via `floodrisk` or `python -m floodrisk.cli`:

### 1. Show Study-Area Configuration
Inspect study area metadata, bounding box, CRS, and grid parameters:
```powershell
python -m floodrisk.cli show-config --config configs/areas/bengaluru.yaml
```

### 2. Generate Initial Geographic Grid
Generate a globally anchored 1,000-metre equal-area grid in GeoJSON or GeoPackage format:
```powershell
# GeoJSON format (RFC 7946 standard WGS84 coordinates with EPSG:6933 attributes)
python -m floodrisk.cli generate-grid --config configs/areas/bengaluru.yaml --out data/processed/grid_bengaluru_urban_1000m.geojson --format geojson

# GeoPackage format (Native EPSG:6933 metric coordinates)
python -m floodrisk.cli generate-grid --config configs/areas/bengaluru.yaml --out data/processed/grid_bengaluru_urban_1000m.gpkg --format gpkg
```

### 3. Validate Tabular CSV Streams
Validate rainfall, weather forecasts, or flood events against canonical schemas:
```powershell
# Validate rainfall observations with quarantine export
python -m floodrisk.cli validate-csv data/raw/rainfall/example.csv --kind rainfall --quarantine data/interim/quarantine.csv

# Validate weather forecasts (detects information leakage: issue_time > valid_time)
python -m floodrisk.cli validate-csv data/raw/weather/forecast.csv --kind forecast
```

### 4. Inspect & Validate Raster Datasets
Inspect GeoTIFF raster integrity, CRS, resolution, nodata, and sampled band statistics:
```powershell
python -m floodrisk.cli validate-raster data/raw/terrain/srtm_dem.tif --expected-crs EPSG:4326
```

### 5. Inspect & Validate Vector Datasets
Check geometry topology, CRS, feature counts, and duplicate IDs:
```powershell
python -m floodrisk.cli validate-vector data/processed/grid_bengaluru_urban_1000m.geojson
```

### 6. Geodesic Grid Distortion & Boundary Coverage Analysis
Compute exact geodesic measurements on the WGS84 ellipsoid and boundary fractions:
```powershell
python -m floodrisk.cli report-distortion --grid data/processed/grid_bengaluru_urban_1000m.geojson --out reports/grid_distortion_report.json
```

### 7. Generate Cryptographic Dataset Manifest
Scan data folders and record SHA-256 hashes for data integrity and scientific reproducibility:
```powershell
python -m floodrisk.cli generate-manifest --dir data --out reports/dataset_manifest.json
```

---

## 6. Running Automated Tests

Run the full automated test suite in Python 3.11 covering configuration loading, bounding box validation, stable global grid indexing, multi-district overlap, IMERG unit verification, CSV/raster/vector validation, forecast leakage detection, and CLI operations:

```powershell
.venv\Scripts\python.exe -m pytest tests/ -v
```

**Results:** `40 passed in 3.04s` (100% passing rate in Python 3.11.15).

---

## 7. Adding a New Study Area

To add a new study area (e.g., Mysuru, Mangaluru, or a river basin), **zero Python code modifications are needed**:

1. Create a configuration file in `configs/areas/<area_id>.yaml`:
   ```yaml
   study_area:
     id: mysuru_urban
     name: Mysuru Urban
     country: India
     admin_level: district
     bbox_wgs84:
       west: 76.55
       south: 12.25
       east: 76.75
       north: 12.40
     boundary_file: data/external/boundaries/mysuru_urban.geojson
     boundary_status: pending_authoritative_boundary
   spatial:
     analysis_crs: EPSG:6933
     grid_size_m: 1000
   ```
2. Run grid generation:
   ```powershell
   python -m floodrisk.cli generate-grid --config configs/areas/mysuru.yaml
   ```
3. The generated grid cells automatically align with the global grid grid without offset or coordinate skew.

