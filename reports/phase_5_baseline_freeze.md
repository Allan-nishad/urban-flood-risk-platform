# Phase 5 — Baseline Freeze & Scientific Integrity Report

**Milestone:** Phase 5 Initiation — Baseline State Verification  
**Author:** Antigravity Autonomous Agent (Google DeepMind Advanced Agentic Coding)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Study Domain:** Bengaluru Urban provisional study domain (1,170 equal-area 1-km cells, EPSG:6933, bounded provisionally by $77.45^\circ - 77.75^\circ\text{E}, 12.85^\circ - 13.15^\circ\text{N}$, boundary status: `pending_authoritative_boundary`)  
**Test Suite Verification:** 87 passed / 87 total across 9 test modules (100% pass rate in 34.15s)  
**Manifest Verification:** 33 registered baseline datasets verified with identical SHA-256 checksums  

---

## 1. Executive Summary & Freeze Declaration

Prior to initiating **Phase 5 (Independent Validation, Forecast Skill Assessment & Scientific Readiness Campaign)**, all upstream data assets, statistical indicators, machine learning results, API contracts, and user-facing dashboards from Phases 1 through 4.7 are formally audited and frozen. 

This freeze establishes a strict, immutable foundation for independent evaluation. Under no circumstances will Phase 5 overwrite, modify, or corrupt baseline datasets registered in [`reports/dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/dataset_manifest.json). All Phase 5 data deliverables will be stored in isolated directories under `data/processed/phase5_*` and registered into an independent manifest: [`reports/phase_5_dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_dataset_manifest.json).

---

## 2. Baseline Architecture & Scientific Status

The frozen platform architecture spans five primary phases:

1. **Phase 1 (Geospatial Grid & Spatial Indexing):**
   - Equal-area cylindrical 1-km grid ($1,000 \times 1,000\text{ m}$) in projected CRS EPSG:6933.
   - 1,170 cells provisionally covering Bengaluru Urban, with dual GeoJSON and Geopackage representations.
   - Administrative boundary flagged as `pending_authoritative_boundary` pending Survey of India release.

2. **Phase 2A & 2B (Static & Hydrometeorological Foundation):**
   - Authentic SRTM GL1 30m DEM mosaic (ESA STEP auxiliary archive, SHA-256: `ba456142...`).
   - Authentic ESA WorldCover 10m 2021 v200 land cover raster (SHA-256: `f9269901...`).
   - Extracted terrain and land-cover features across all 1,170 cells (elevation, slope, aspect, TWI, built-up fraction, tree cover, water fraction).
   - Historical flood event inventory (85 records) and source registry (9 sources).
   - Space-time rainfall features (GPM IMERG multi-day episodes).

3. **Phase 3 (Exploratory Risk Modeling & Spatial Validation):**
   - Exploratory unsupervised spatial anomaly models: Multi-Criteria Decision Analysis (MCDA), Mahalanobis Distance, and Isolation Forest.
   - Spatial block cross-validation enforcing 5 km, 10 km, and 15 km spatial buffer holdouts to counteract variogram-derived spatial autocorrelation.
   - Formal Decision Gate B: Supervised flood-prediction modeling blocked due to severe spatial reporting bias in historical flood records (unreported locations cannot be assumed dry).

4. **Phase 4 & Phase 4.7 (Operational Intelligence & Integrity Audit):**
   - Automated NWP forecast ingestion and downscaling via nearest-centroid anchor mapping across a $3 \times 3$ regional anchor grid (approx. 9–13 km native model resolution).
   - Four-layer decoupled risk intelligence engine: Static Physical Susceptibility, Antecedent Observed Rainfall, Forecast Rainfall Exposure, and Ground Incident Evidence.
   - Strict non-circularity: Ground Incident Evidence is excluded from composite mathematical scoring.
   - Comprehensive Phase 4.7 Scientific Acceptance & Operational Integrity Audit (10 dedicated audit reports).
   - Quarantine of synthetic Sentinel-1 SAR rasters: classified strictly as engineering test fixtures, removed from operational map views, and banned from scientific validation.

---

## 3. Cryptographic Baseline Inventory (33 Verified Datasets)

Every file listed below was verified via SHA-256 hash calculation against [`reports/dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/dataset_manifest.json):

| Dataset Key | Relative Path | File Size (Bytes) | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| `dynamic_risk_intelligence_bengaluru` | `data/processed/dynamic_risk_intelligence_bengaluru.parquet` | 107,397 | `6081fd84222233531108f6700e20eb3a8c51b34bff01840af4631defb382fd69` |
| `esa_worldcover_10m_2021_v200_n12e075_map` | `data/raw/land_cover/ESA_WorldCover_10m_2021_v200_N12E075_Map.tif` | 127,650,362 | `f9269901e07d86c2e180d661d0e8924e3ee57dd589f7433b9874861b3c65a978` |
| `exploratory_risk_indicators_bengaluru` | `data/processed/exploratory_risk_indicators_bengaluru.parquet` | 663,821 | `3b1e329891f07f5cf9c1f74987694411f86a3dae4d11df08b72649ffe928c902` |
| `feature_registry` | `data/processed/feature_registry.json` | 11,710 | `081c59607c38caa82b648c0af6d1330232c1d7d0ecb2e48da3639ead874ad49d` |
| `features_integrated_bengaluru` | `data/processed/features_integrated_bengaluru.parquet` | 165,317 | `e6c48c665a559293186a3484ed310fe5a6e333c1326027a5fdccf27667bb8f4f` |
| `features_rainfall_bengaluru` | `data/processed/features_rainfall_bengaluru.parquet` | 72,626 | `a1084f34a160bb2c47d21fb00d29107658c7ddff33d2f0d9e3d391ecb42741dd` |
| `features_static_bengaluru` | `data/processed/features_static_bengaluru.parquet` | 80,989 | `cbbdac220de4d03c30c52a0b86e9f322ea94ae950e2e7b7f4b9f280444eb9218` |
| `flood_event_inventory_bengaluru` | `data/processed/flood_event_inventory_bengaluru.parquet` | 27,828 | `9e1917c17838b7b8dd3c40bbbc1e989c51155db396713ea12266da148b3f0aa6` |
| `flood_event_monitoring_log` | `data/processed/flood_event_monitoring_log.parquet` | 12,967 | `0d205caba6fe5c145391eb2b422d0835cee48986fec8d5421e2c30d29c5bdb15` |
| `flood_source_registry_bengaluru` | `data/processed/flood_source_registry_bengaluru.parquet` | 8,826 | `9a5f2017f24b5740288f23b5b49ed9a6fe2f4a1353e8a770989f49aaec50b018` |
| `forecast_exposure_indicators_bengaluru` | `data/processed/forecast_exposure_indicators_bengaluru.parquet` | 19,204 | `5cc021f802b8846d9767da435ada53233a226f702ef463eb9d55a4d137bde543` |
| `forecast_rainfall_bengaluru` | `data/processed/forecast_rainfall_bengaluru.parquet` | 431,406 | `2a96d9106446c1ae8f29f837f74e32b50230c6218a30246ad4c87610e915bcf8` |
| `grid_bengaluru_rural_1000m` | `data/processed/grid_bengaluru_rural_1000m.geojson` | 6,544,631 | `948fdd609b123223b74765ae5882191d066811a843ab6c9fa1e3709df0e1e52b` |
| `grid_bengaluru_urban_1000m` | `data/processed/grid_bengaluru_urban_1000m.gpkg` | 569,344 | `aa11c33bd648ea07573d1421981cc63abf898d95cefb5516cd9e34ce41fc64a2` |
| `grid_features_bengaluru_urban_1000m` | `data/processed/grid_features_bengaluru_urban_1000m.parquet` | 50,412 | `d5404934065182e050369d0f1352b931e06b010283f56231dfe698c97976b6ee` |
| `grid_mysuru_urban_1000m` | `data/processed/grid_mysuru_urban_1000m.geojson` | 469,289 | `afb1542de2cc68bb2e70e86497b5bc8f0317e24f46e057f6e29557b21765add3` |
| `n12e077` | `data/raw/elevation/srtm/N12E077.hgt` | 25,934,402 | `d70ed4171e76a7296268016e903563027329086be8c6d89136de8582b9a5ed96` |
| `n12e077.srtmgl1` | `data/raw/elevation/srtm/N12E077.SRTMGL1.tif` | 8,095,151 | `697aa24791cd02b43a5002fc5b7f6137434d74c420d5a7a0d6f58743b1595b15` |
| `n12e077.srtmgl1.hgt` | `data/raw/elevation/srtm/N12E077.SRTMGL1.hgt.zip` | 10,071,528 | `37c8aafaa1acae395053cab5bd1d3766676897a7c08724590a1999d4caa28d76` |
| `n13e077` | `data/raw/elevation/srtm/N13E077.hgt` | 25,934,402 | `4a9c7d71333a6c83bf0d6afbf1ebfd47b8fcee8558f6f11c88b678ee63391627` |
| `n13e077.srtmgl1` | `data/raw/elevation/srtm/N13E077.SRTMGL1.tif` | 6,783,967 | `d9a8821fd3017803f3ab7086afd7ba60679aa2e7b4c1dde09395f649073d2fd6` |
| `n13e077.srtmgl1.hgt` | `data/raw/elevation/srtm/N13E077.SRTMGL1.hgt.zip` | 7,813,126 | `17d69dfe6a9c484a23844d81b682adb27fcf384f4f4cc27b06935079ef659790` |
| `phase3_isolation_forest_results` | `data/processed/phase3_isolation_forest_results.parquet` | 1,092,964 | `6fc85f51c25e32a76b936e7857b5b6cd72718f3306f4f4e56d32671e8d3a6916` |
| `phase3_mahalanobis_results` | `data/processed/phase3_mahalanobis_results.parquet` | 728,236 | `0ccf10549bc75ec0ac03d4ec4735cf8852bafe9992b0d003eb8f12b4c412f65e` |
| `phase3_mcda_results` | `data/processed/phase3_mcda_results.parquet` | 894,578 | `2167e804e8c675ef3f109402054b779d69873994e8cf1f3ed90d8dc61e2b6a2d` |
| `phase3_model_comparison` | `data/processed/phase3_model_comparison.parquet` | 1,487,931 | `59c33bbaf00126c364523797c8334de4c3f43119e9c565fefb1e3633589b1277` |
| `phase3_model_features` | `data/processed/phase3_model_features.parquet` | 275,694 | `fa56947820baf01bc67034342912843563665a8a25f35e5827327b92772cce79` |
| `sentinel1_candidate_flood_change_mask_bengaluru` | `data/processed/sentinel1_candidate_flood_change_mask_bengaluru.tif` | 336,641 | `f41f6b6de685f3b56314cdc2e96b18c0c3b50a1ba4e36b75b8bd748bfe29fa4f` |
| `sentinel1_candidate_water_mask_bengaluru` | `data/processed/sentinel1_candidate_water_mask_bengaluru.tif` | 374,203 | `cb874190a894ae244d4a2f18381d9af80125b7a5e906d8bfabf2a59331e82f75` |
| `sentinel1_grid_features_bengaluru` | `data/processed/sentinel1_grid_features_bengaluru.parquet` | 40,711 | `6675ede51339e813170d15f3d9d236c0da609cf3092ecddbab4601e8aecda8ec` |
| `sentinel1_incident_comparison_bengaluru` | `data/processed/sentinel1_incident_comparison_bengaluru.parquet` | 10,503 | `3a74099ac24b5220e20f79ebe52e0ca9e14e372109f9c37718ac5fe8419f4d53` |
| `sentinel1_scene_registry_bengaluru` | `data/processed/sentinel1_scene_registry_bengaluru.parquet` | 11,806 | `234d58d00cd56329e3db3543e282e59776eb7d118b4c3984646901126c28138b` |
| `srtmgl1_n12_n13_e077_bengaluru` | `data/raw/elevation/srtm/SRTMGL1_N12_N13_E077_Bengaluru.tif` | 14,876,879 | `ba45614211dbcbf686a47b36e19a32a9cfd82ce7c82a80bcc9e269a95d93946f` |

---

## 4. Operational Transition & Audit Clarifications

### 4.1 Forecast Row Count Transition (Phase 4.2 to Phase 4.7)
In Phase 4.2, the forecast dataset (`forecast_rainfall_bengaluru.parquet`) was initially generated with 72,540 rows ($1,170\text{ cells} \times 62\text{ hourly steps}$). In Phase 4.7, during the operational integrity audit, the forecast pipeline was re-run with live upstream timestamps, yielding 67,860 rows ($1,170\text{ cells} \times 58\text{ hourly steps}$) due to the rolling dynamic forecast lead-time horizon. 

The updated file (`data/processed/forecast_rainfall_bengaluru.parquet`, SHA-256: `2a96d9106446c1ae8f29f837f74e32b50230c6218a30246ad4c87610e915bcf8`, size: 431,406 bytes) is the canonical frozen baseline. It incorporates explicit provenance columns (`nominal_reference_time_utc`, `retrieval_time_utc`, `model_initialization_status`, `source_pixel_id`, `source_resolution`, and `mapping_method`).

### 4.2 Sentinel-1 SAR Test Fixture Quarantine
The Sentinel-1 water change raster (`data/processed/sentinel1_water_change_20220812_20220905_bengaluru.tif`) is formally classified as a **SYNTHETIC ENGINEERING FIXTURE**. It has been excluded from the primary operational map, placed in a segregated developer drawer with explicit warning badges, and is strictly banned from acting as ground-truth flood validation in Phase 5.

### 4.3 Separation of Forecast Skill (Track A) and Flood Evidence (Track B)
A fundamental scientific principle governing Phase 5 is the **strict non-conflation of meteorological skill and hydrological consequence**:
- **Track A (Meteorological Forecast Skill):** Evaluates how accurately numerical weather prediction models forecast quantitative precipitation depth against independent rainfall observations (IMD/KSNDMC). Metrics include MAE, RMSE, Pearson $r$, Spearman $\rho$, and threshold contingency metrics (POD, FAR, CSI).
- **Track B (Flood-Impact Evidence Validation):** Evaluates whether platform risk indicators spatially align with authentic physical inundation, reported municipal waterlogging, or traffic disruption.
- Under no circumstances will a successful rainfall forecast be interpreted as proof that flooding occurred, nor will absent flood reports be treated as an NWP forecast failure.

---

## 5. Automated Test Suite Baseline

Prior to Phase 5 execution, all automated tests were executed using Python 3.11.15 in `.venv`:
```
87 passed, 2453 warnings in 34.15s
```
Across all 9 test modules:
- `tests/test_cli.py` (4 tests)
- `tests/test_dynamic_risk.py` (6 tests)
- `tests/test_forecast.py` (6 tests)
- `tests/test_grid.py` (8 tests)
- `tests/test_integration_real_data.py` (12 tests)
- `tests/test_monitoring.py` (6 tests)
- `tests/test_phase_4.py` (6 tests)
- `tests/test_rainfall.py` (10 tests)
- `tests/test_sar.py` (9 tests)
- `tests/test_terrain.py` (8 tests)
- `tests/test_validation.py` (8 tests)
- `tests/test_zonal.py` (4 tests)

The platform baseline is confirmed healthy, mathematically consistent, cryptographically frozen, and ready for Phase 5 campaign execution.

