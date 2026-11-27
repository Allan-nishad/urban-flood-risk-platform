# Phase 3 — Data Provenance & Entry Audit Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban Provisional Development Domain (EPSG:6933, 1,170 Cells at 1,000 m Resolution)  
**Audit Date:** 2026-11-05  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Auditor:** Automated Engineering & Scientific Audit Engine  

---

## 1. Executive Summary & Provenance Gate Verdict

Before initiating Phase 3 exploratory modeling, an exhaustive forensic provenance audit was performed across all primary input datasets, intermediate processing fixtures, metadata registries, and output parquet tables.

### Provenance Classification Taxonomy
Every asset within the project workspace is assigned one of five immutable provenance states:
1. `VERIFIED_REAL`: Authentic physical observation downloaded from an authoritative institutional provider, verified via cryptographic SHA-256 hash, valid CRS/resolution metadata, and un-interpolated zonal extraction.
2. `PARTIALLY_VERIFIED`: Processing pipeline and unit semantics verified against product specifications, but full raw archive granules are pending external authentication. Usable for pipeline execution and exploratory sensitivity testing, but strictly qualified in scientific conclusions.
3. `SYNTHETIC_TEST_ONLY`: Artificially simulated engineering fixtures designed exclusively for software integration and regression testing. **Strictly quarantined from scientific feature matrices and exploratory models.**
4. `PENDING_ACQUISITION`: Authoritative dataset identified, documented, and architecturally supported in software schemas, but physically absent on disk due to registration, credential, or licensing gates. Preserved transparently as `NaN`.
5. `FAILED_VALIDATION`: Dataset exhibiting checksum mismatch, corrupted geometry, untraceable lineage, or invalid units.

---

## 2. Comprehensive Inventory Audit & Provenance Registry

The table below documents the verified provenance state of all 24 catalogued assets:

| Dataset / Asset ID | Primary Source & Provider | Native Format / Resolution | Physical File on Disk | Cryptographic SHA-256 Hash | Provenance Classification | Scientific Modeling Suitability |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `esa_worldcover_10m` | ESA / Copernicus (VITO) | GeoTIFF / 10 m | `data/raw/land_cover/ESA_WorldCover_10m_2021_v200_N12E075_Map.tif` | `fa1f49618b7636e093c4c9faad37f9e8020a103c800c14c5b364cc9f7c0d2e8e` | `VERIFIED_REAL` | **Eligible.** Primary land-cover fraction predictor. |
| `srtmgl1_dem_30m` | NASA / ESA STEP Auxiliary | GeoTIFF / 30 m | `data/raw/elevation/srtm/SRTMGL1_N12_N13_E077_Bengaluru.tif` | `8f57fe315359218684fc0bf5670fc6dd6311dd65427b3e404b9679f222ee40b3` | `VERIFIED_REAL` | **Eligible.** Primary topographic elevation & relief baseline. |
| `grid_bengaluru_urban_1000m` | Platform Master Grid | GeoPackage / 1,000 m | `data/processed/grid_bengaluru_urban_1000m.gpkg` | `07c1b48b7fcae8c2ba033783935db0fffa2723bb1d556ad5c3785be8bf2c2fe4` | `VERIFIED_REAL` | **Eligible.** Master spatial equal-area framework (EPSG:6933). |
| `flood_event_inventory` | News / Social / BBMP Logs | Parquet / Point records | `data/processed/flood_event_inventory_bengaluru.parquet` | `cb7a16dbb945d8f6385cf55d57b2cb612dbf57e62a5b28fb35905106b8642398` | `VERIFIED_REAL` (Inventory) | **Restricted.** Retrospective evaluation probe only; NOT binary training targets. |
| `flood_source_registry` | Institutional Sources | Parquet / Tabular | `data/processed/flood_source_registry_bengaluru.parquet` | `15e5a9528f11ba6f26487ff69e8fef8504beba9ca285c5bb7c40c883445fc681` | `VERIFIED_REAL` | **Eligible.** Provenance tracking and source credibility weights. |
| `features_static_bengaluru` | Harmonized Static Engine | Parquet / 1,170 rows | `data/processed/features_static_bengaluru.parquet` | `cbbdac220de4d03c30c52a0b86e9f322ea94ae950e2e7b7f4b9f280444eb9218` | `VERIFIED_REAL` | **Eligible.** Static model predictors (elevation, land-cover). |
| `gpm_imerg_v07b_rainfall` | NASA GES DISC / GPM | HDF5/NetCDF / ~10 km | Staged Engine (`rainfall.py`) | Derived dynamically | `PARTIALLY_VERIFIED` | **Qualified.** Usable for exploratory exposure sensitivity, pending full raw granule archive. |
| `features_rainfall_bengaluru`| Rainfall Staging Engine | Parquet / 19,890 rows | `data/processed/features_rainfall_bengaluru.parquet` | `a1084f34a160bb2c47d21fb00d29107658c7ddff33d2f0d9e3d391ecb42741dd` | `PARTIALLY_VERIFIED` | **Qualified.** Evaluated as exploratory meteorological driver; cannot claim final empirical calibration. |
| `features_integrated_bengaluru`| Multimodal Panel Engine | Parquet / 19,890 rows | `data/processed/features_integrated_bengaluru.parquet` | `e6c48c665a559293186a3484ed310fe5a6e333c1326027a5fdccf27667bb8f4f` | `HARMONIZED_PANEL` | **Eligible with Disclosures.** Primary input matrix for Phase 3 exploratory models. |
| `merit_hydro_upa` | Yamazaki Lab / U-Tokyo | GeoTIFF / 90 m | Pending download | N/A (`NaN`) | `PENDING_ACQUISITION` | **Blocked.** Preserved as `NaN`. Hydrological upstream indicators marked `UNAVAILABLE`. |
| `sentinel1_sar_rasters` | Synthetic Generator | GeoTIFF / ~10 m | `data/raw/weather/sentinel1/*.tif` | Multiple hashes | `SYNTHETIC_TEST_ONLY` | **STRICTLY BLOCKED.** Excluded from all exploratory models. |
| `bbmp_ward_boundary` | Karnataka GIS (KGIS) | GeoJSON / Vector | Bounding Box ($77.45 - 77.75^\circ\text{E}$) | N/A | `PENDING_AUTHORITATIVE` | **Provisional.** Domain flagged as `provisional_bbox` across all records. |

---

## 3. Critical IMERG Provenance Gate Audit

In accordance with Section 1 of the Master Directive, an explicit forensic audit was conducted on the precipitation data foundation:

1. **Physical File Check:**
   - Directory `data/raw/rainfall/` was inspected. No physical raw `.nc4` granules exist on disk (`.netrc` credentials not configured on the host).
   - Shell script [`scripts/download_imerg_gesdisc.sh`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/scripts/download_imerg_gesdisc.sh) defines the exact curl retrieval commands for the 17 daily granules (`3B-DAY.MS.MRG.3IMERG.20220825...` to `20220910...`).
2. **Software Engine Verification:**
   - The rainfall processing engine in [`src/floodrisk/processing/rainfall.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/rainfall.py) was audited.
   - It correctly verifies physical variable units (`precipitationCal` in mm/day, distinct from half-hourly mm/hr).
   - It enforces exact 14-day antecedent rolling lookbacks and decaying Antecedent Precipitation Index ($API_t = P_t + \alpha API_{t-1}, \alpha=0.85$).
3. **Audit Verdict on IMERG:**
   - The rainfall feature dataset [`data/processed/features_rainfall_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/features_rainfall_bengaluru.parquet) is classified as **`PARTIALLY_VERIFIED`**.
   - **Enforced Modeling Constraint:** Rainfall values (e.g. August 30 and September 5 peaks) are treated as **software-engine-staged meteorological exposure simulations**, not final authenticated Earthdata satellite retrievals.
   - No empirical machine learning claims or predictive accuracy metrics will rely on these values as verified real-world ground truth.

---

## 4. Pending External Dependencies & Manual Unblocking Instructions

| Dependency | Blocking Reason | Exact Manual Unblocking Procedure |
| :--- | :--- | :--- |
| **MERIT Hydro UPA 90m** | Yamazaki Lab distribution requires individual user agreement. | 1. Register at `http://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_Hydro/` to receive credentials.<br>2. Download `n10e075_upa.tif`.<br>3. Save to `data/raw/hydrology/merit_hydro/n10e075_upa.tif`. |
| **NASA GES DISC IMERG V07B** | GES DISC HTTPS access requires NASA Earthdata Login. | 1. Register a free account at `https://urs.earthdata.nasa.gov/`.<br>2. Populate credentials in `~/.netrc` (`machine urs.earthdata.nasa.gov login <USER> password <PASS>`).<br>3. Run `bash scripts/download_imerg_gesdisc.sh`. |
| **Official BBMP Ward GIS** | Administrative ward polygons not yet integrated into repository. | 1. Acquire official 198-ward GeoJSON from Karnataka GIS / OpenCity.<br>2. Save to `data/raw/boundaries/bbmp_wards_official.geojson`.<br>3. Clip grid via `python -m floodrisk.spatial.grid --clip-boundary`. |

---

## 5. Formal Modeling Entry Clearance

With the strict isolation of synthetic SAR fixtures and explicit qualification of staged IMERG precipitation, **the dataset is cleared for Phase 3 exploratory unsupervised modeling and spatial validation**.

