# Data Coverage & Acquisition Status Report (Phase 2B Final Audit)

**Project:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Phase:** 2B — Multimodal Feature Integration, Data Quality, and Training Dataset Readiness  
**Reporting Date:** 2026-11-05  
**Execution Environment:** Python 3.11.15 (`.venv`)  

---

## 1. Summary of Dataset Readiness & Scientific Status

| Dataset Category | Dataset Name | Verification Status | File on Disk | Dimensions / Rows | Scientific & Operational Status |
| :--- | :--- | :---: | :--- | :---: | :--- |
| **Spatial Master Grid** | Global Equal-Area Grid (EPSG:6933, 1km) | `VERIFIED_REAL` | `grid_bengaluru_urban_1000m.gpkg` | 1,170 cells | **Fully Operational.** Regular $30 \times 39$ grid; geodesic distortion $< 0.05\%$. |
| **Land Cover** | ESA WorldCover 10m (2021 v200) | `VERIFIED_REAL` | `ESA_WorldCover_10m_2021_v200_N12E075_Map.tif` | 127.65 MB | **Fully Verified & Extracted.** Exact polygon geometry masking (`all_touched=False`). |
| **Terrain (DEM)** | SRTM GL1 30m (`N12E077`, `N13E077`) | `VERIFIED_REAL` | `SRTMGL1_N12_N13_E077_Bengaluru.tif` | 14.88 MB | **Fully Verified & Extracted.** Mosaicked $3,601 \times 7,201$ GeoTIFF; 100% cell coverage. |
| **Upstream Hydrology** | MERIT Hydro 90m (`n10e075_upa.tif`) | `PENDING_ACQUISITION` | Pending download | 0 rows (NaN) | **Pending User Registration.** Access gated at Yamazaki Lab Google Form. Preserved cleanly as `NaN`. |
| **Precipitation** | NASA GPM IMERG V07B | `PARTIALLY_VERIFIED` | Staged Engine / Script | 19,890 cell-days | **Engine Verified.** Unit-checked daily depth (mm) and API decay ($\alpha=0.85$); Earthdata NetCDF pending. |
| **Satellite Radar (SAR)**| Sentinel-1A IW GRDH | `SYNTHETIC_TEST_ONLY` | Simulation rasters | Isolated | **Phase 2A.5.1 Audit Decision C.** Pipeline verified, but rasters are simulation fixtures; strictly excluded from feature matrix. |
| **Flood Event Inventory**| Historical Incident Register | `VERIFIED_REAL` (Inventory) | `flood_event_inventory_bengaluru.parquet` | 21 records | **Compiled & Provenance-Linked.** 18 geocoded incidents mapped to grid; NOT binary ML labels. |
| **Static Feature Matrix**| Harmonized Static Predictors | `VERIFIED_REAL` | `features_static_bengaluru.parquet` | 1,170 rows, 31 cols | **Phase 2B.1 Deliverable.** Complete SRTM and WorldCover statistics per 1-km cell. |
| **Rainfall Feature Matrix**| Time-Varying Meteorological Grid | `PARTIALLY_VERIFIED` | `features_rainfall_bengaluru.parquet` | 19,890 rows, 18 cols | **Phase 2B.1 Deliverable.** 17 dates $\times$ 1,170 cells; 3d, 7d, 14d lookbacks + API. |
| **Integrated Panel** | Multimodal Spatiotemporal Panel | `HARMONIZED_PANEL` | `features_integrated_bengaluru.parquet` | 19,890 rows, 53 cols | **Phase 2B.1 Deliverable.** Merged panel with explicit SAR exclusion and incident link. |
| **Exploratory Indicators** | Multi-Criteria Susceptibility Scores | `VERIFIED_SCORING` | `exploratory_risk_indicators_bengaluru.parquet`| 19,890 rows, 62 cols | **Phase 2B.3 Deliverable.** Transparent $I_{\text{terrain}}$, $I_{\text{landcover}}$, $I_{\text{rainfall}}$, and 3 composite scores. |
| **Administrative Boundary**| Bengaluru Urban District Boundary | `PENDING_AUTHORITATIVE` | Bounding Box ($77.45 - 77.75^\circ\text{E}$) | 1,170 cells | **Provisional Development Grid Active.** Official BBMP boundary pending ingestion. |

---

## 2. Processed Datasets Directory Structure

```
data/
├── raw/
│   ├── land_cover/
│   │   └── ESA_WorldCover_10m_2021_v200_N12E075_Map.tif           [AUTHENTIC - 127.65 MB, SHA-256 verified]
│   ├── elevation/
│   │   └── srtm/
│   │       ├── N12E077.SRTMGL1.hgt.zip                            [AUTHENTIC - 10.60 MB]
│   │       ├── N13E077.SRTMGL1.hgt.zip                            [AUTHENTIC - 8.16 MB]
│   │       └── SRTMGL1_N12_N13_E077_Bengaluru.tif                 [AUTHENTIC MOSAIC - 14.88 MB, 3601x7201]
│   ├── hydrology/
│   │   └── merit_hydro/                                           [STAGING - Awaiting n10e075_upa.tif]
│   ├── rainfall/
│   │   └── gpm_imerg_v07/                                         [STAGING - GES DISC curl script generated]
│   └── weather/
│       └── sentinel1/                                             [SIMULATION FIXTURES - Isolated for regression testing]
├── processed/
│   ├── grid_bengaluru_urban_1000m.gpkg                            [569 KB, 1,170 equal-area cells]
│   ├── flood_event_inventory_bengaluru.parquet                    [27.8 KB, 21 provenance-linked records]
│   ├── flood_source_registry_bengaluru.parquet                    [8.8 KB, 8 sources registered]
│   ├── features_static_bengaluru.parquet                          [80.9 KB, 1,170 rows, 31 columns]
│   ├── features_rainfall_bengaluru.parquet                        [72.6 KB, 19,890 rows, 18 columns]
│   ├── features_integrated_bengaluru.parquet                      [165.3 KB, 19,890 rows, 53 columns]
│   ├── feature_registry.json                                      [11.7 KB, 15 formal feature definitions]
│   └── exploratory_risk_indicators_bengaluru.parquet              [663.8 KB, 19,890 rows, 62 columns]
```

---

## 3. Data Integrity & Manifest Verification

All 24 registered datasets in [`reports/dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/dataset_manifest.json) have been cryptographically verified:
- **Total Datasets Monitored:** 24
- **Checksum Verification Rate:** 100% (24 / 24 verified valid)
- **Tampering / Corruption Count:** 0
