# Phase 4.1 — Unified Data Acquisition & Operational Readiness Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban (1,170 Cells, 1-km Grid)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Reporting Date:** 2026-11-05  

---

## 1. Executive Summary

This report establishes the comprehensive data readiness baseline for Phase 4. It summarizes the provenance audit across all primary satellite, topographic, hydrological, meteorological, and incident layers, clearly distinguishing verified physical observations from qualified engines, simulation fixtures, and pending external dependencies.

---

## 2. Master Dataset Readiness & Provenance Classification Matrix

| Dataset Category | Dataset Name | Primary Provider | Provenance Status | File Size / Format | Operational Readiness | Scientific Role in Phase 4 |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Land Cover** | ESA WorldCover 10m (2021 v200) | VITO / ESA | `VERIFIED_REAL` | 127.65 MB / GeoTIFF | **Fully Operational** | Static surface impermeability & canopy predictor. |
| **Terrain (DEM)** | SRTM GL1 30m DEM | NASA / ESA STEP | `VERIFIED_REAL` | 14.88 MB / GeoTIFF | **Fully Operational** | Static topographic depression & slope proxy. |
| **Spatial Grid** | Equal-Area Analysis Grid (EPSG:6933) | Platform Engine | `VERIFIED_REAL` | 569 KB / GeoPackage | **Fully Operational** | Master spatial resolution ($1,000\text{ m}$) canvas. |
| **Historical Incidents**| Flood Incident Inventory | Multimodal News/Social | `VERIFIED_REAL` (Inventory) | 28.5 KB / Parquet | **Fully Operational** | Retrospective evaluation probe; NOT training labels. |
| **Source Registry** | Traceable Evidence Register | Platform Engine | `VERIFIED_REAL` | 9.0 KB / Parquet | **Fully Operational** | Lineage and source confidence tracking. |
| **Static Feature Matrix**| Harmonized Static Predictors | Platform Engine | `VERIFIED_REAL` | 81.0 KB / Parquet | **Fully Operational** | Merged static layer for risk intelligence. |
| **Rainfall Forecast** | Open-Meteo NWP Stream | ECMWF/GFS Seamless | `VERIFIED_REAL` | Programmatic API / Parquet | **Fully Operational** | Dynamic forward-looking meteorological forcing. |
| **Historical Rainfall** | NASA GPM IMERG V07B | NASA GES DISC | `PARTIALLY_VERIFIED` | Staged Engine / Script | **Qualified Operational** | Historical monsoonal timeline; raw NetCDF pending. |
| **Upstream Hydrology** | MERIT Hydro 90m UPA | Yamazaki Lab / U-Tokyo | `PENDING_ACQUISITION` | 0 rows / `NaN` | **Preserved Blocked** | Preserved as `NaN`; hydro routing unavailable. |
| **Satellite Radar (SAR)**| Sentinel-1A Level-1 SAFE | Copernicus CDSE | `SYNTHETIC_TEST_ONLY` | Test fixtures only | **Strictly Quarantined** | Excluded from models and dashboard observational layers. |
| **Administrative Boundary**| Official BBMP Ward Polygons | Karnataka GIS / KSRSAC | `PENDING_AUTHORITATIVE` | Bounding Box active | **Provisional Active** | Rectangular bbox ($77.45 - 77.75^\circ\text{E}$) labeled provisional. |

---

## 3. Detailed Scientific Blocker Audit & Manual Action Plan

| Blocker ID | Affected Component | Root Cause | Severity | Exact Manual Resolution Instructions |
| :--- | :--- | :--- | :---: | :--- |
| **BLK-01** | Raw IMERG NetCDF Granules | GES DISC HTTPS access requires NASA Earthdata Login credentials (`.netrc`). | **Medium** | 1. Register free at `https://urs.earthdata.nasa.gov/`.<br>2. Add credentials to `~/.netrc`.<br>3. Run `bash scripts/download_imerg_gesdisc.sh`. |
| **BLK-02** | MERIT Hydro 90m Flow Accumulation | Flow routing data gated by Yamazaki Lab individual user agreement. | **High** | 1. Register at `http://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_Hydro/`.<br>2. Download `n10e075_upa.tif`.<br>3. Save to `data/raw/hydrology/merit_hydro/`. |
| **BLK-03** | Official BBMP Ward GIS Polygons | Authoritative municipal ward shapefile not yet imported into repo. | **Low** | 1. Download official 198-ward GeoJSON from OpenCity/KGIS.<br>2. Save to `data/raw/boundaries/bbmp_wards_official.geojson`.<br>3. Execute `python -m floodrisk.spatial.grid --clip-boundary`. |
| **BLK-04** | Authentic Copernicus Sentinel-1A SAFE | Raw SAR Level-1 SAFE archives require multi-gigabyte download and SNAP preprocessing. | **Medium** | 1. Query Copernicus Data Space (`dataspace.copernicus.eu`).<br>2. Download Orbit 165 SAFE packages for 2022-08-12 and 2022-09-05.<br>3. Process through SNAP Range-Doppler terrain correction. |

---

## 4. Clearance for Phase 4.2 Implementation

With the successful verification and selection of the **Open-Meteo NWP Forecast API** as the live numerical weather prediction stream, and the strict isolation of synthetic fixtures and preservation of missing data, **the platform is formally cleared to proceed with Phase 4.2 Forecast Data Integration and Phase 4.3 Dynamic Risk Intelligence**.

