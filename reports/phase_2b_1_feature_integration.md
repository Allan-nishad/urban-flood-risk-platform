# Phase 2B.1 Integration Report: Multimodal Feature Integration & Feature Registry

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Sub-Phase:** Phase 2B.1 — Multimodal Feature Integration  
**Date:** 2026-11-05  
**Domain Scope:** Bengaluru Urban provisional development domain (1,170 equal-area 1-km cells in EPSG:6933)  
**Execution Runtime:** Python 3.11.15 in `.venv`  
**Deliverable Datasets:**
1. [`features_static_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/features_static_bengaluru.parquet) (80,989 bytes, SHA-256: `cbbdac220de4d03c30c52a0b86e9f322ea94ae950e2e7b7f4b9f280444eb9218`, 1,170 cells, 31 columns)
2. [`features_rainfall_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/features_rainfall_bengaluru.parquet) (72,626 bytes, SHA-256: `a1084f34a160bb2c47d21fb00d29107658c7ddff33d2f0d9e3d391ecb42741dd`, 19,890 rows, 18 columns)
3. [`features_integrated_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/features_integrated_bengaluru.parquet) (165,317 bytes, SHA-256: `e6c48c665a559293186a3484ed310fe5a6e333c1326027a5fdccf27667bb8f4f`, 19,890 rows, 53 columns)
4. [`feature_registry.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/feature_registry.json) (11,710 bytes, SHA-256: `081c59607c38caa82b648c0af6d1330232c1d7d0ecb2e48da3639ead874ad49d`, 15 documented variables)

---

## 1. Executive Summary & Architecture Principles

In Phase 2B.1, the platform unified all verified environmental data into canonical spatial and spatiotemporal datasets, enforcing strict scientific separation across modalities:

1. **Separation of Scientific Concepts:**
   - **Static Physical Features:** Terrain and land cover remain strictly isolated in [`features_static_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/features_static_bengaluru.parquet).
   - **Dynamic Rainfall Observations:** Time-varying meteorological forcings and multi-day antecedent saturations remain strictly isolated in [`features_rainfall_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/features_rainfall_bengaluru.parquet).
   - **Historical Flood Incidents:** Documented incident evidence remains strictly decoupled from environmental predictors in [`features_integrated_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/features_integrated_bengaluru.parquet).
   - **Synthetic SAR Fixtures:** In accordance with the Phase 2A.5.1 Audit (Decision C), the synthetic SAR rasters generated in Phase 2A.5 are **strictly excluded from the primary observational feature matrix**.
2. **Authenticity Enforcement:**
   - Only `VERIFIED_REAL` datasets (SRTM GL1 30m DEM and ESA WorldCover 10m) entered the primary static matrix.
   - MERIT Hydro UPA features are preserved as clean `NaN`s (`PENDING_ACQUISITION`).
   - Dynamic rainfall is flagged as `PARTIALLY_VERIFIED` (`PROVISIONAL_STAGED_IMERG_ENGINE`) with explicit disclaimers regarding native 10-km satellite microwave resolution.
3. **No False Assumptions:**
   - Absence of reported flood incidents in a grid cell is **never converted to a negative flood label** (`0`).
   - The 1,170-cell domain is strictly identified as a **provisional development bounding box**, not an officially validated Survey of India administrative boundary.

---

## 2. Source-Data Verification Matrix

| Dataset Category | Dataset Name | Local File & Size | Cryptographic SHA-256 | Verification Status | Scientific Role in Phase 2B |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Terrain (DEM)** | SRTM GL1 30m Mosaic | `SRTMGL1_N12_N13_E077_Bengaluru.tif` (14.88 MB) | `ba45614211dbcbf6...` | **`VERIFIED_REAL`** | Macro-topography, elevation distribution, flatness/slope proxy |
| **Land Cover** | ESA WorldCover 10m 2021 v200 | `ESA_WorldCover_10m_2021_v200_N12E075_Map.tif` (127.65 MB) | `f9269901e07d86c2...` | **`VERIFIED_REAL`** | Sealed surface proxy (Class 50), permanent water (Class 80), vegetation |
| **Hydrology** | MERIT Hydro 90m UPA | `n10e075_upa.tif` (Missing) | — | **`PENDING_ACQUISITION`** | Contributing upstream catchment area (preserved as `NaN`) |
| **Precipitation**| NASA GPM IMERG V07B | Staged engine & download scripts | — | **`PARTIALLY_VERIFIED`** | Daily depth and antecedent saturation indices (API $\alpha=0.85$) |
| **Satellite Radar**| Sentinel-1A Level-1 GRDH | Synthetic rasters (Phase 2A.5 simulation) | — | **`SYNTHETIC_TEST_ONLY`** | **EXCLUDED** from real observational feature matrix |
| **Flood Incidents**| Bengaluru 2022 Inventory | `flood_event_inventory_bengaluru.parquet` (27.8 KB) | `9e1917c17838b7b8...` | **`VERIFIED_REAL`** | Traceable ground truth anchors (21 events; 18 geocoded flood/disruptions) |
| **Study Grid** | 1-km Equal-Area Grid | `grid_bengaluru_urban_1000m.gpkg` (569 KB) | `aa11c33bd648ea07...` | **`VERIFIED_REAL`** | Canonical spatial spatial unit (1,170 equal-area cells in EPSG:6933) |

---

## 3. Static Spatial Feature Dataset

Stored in [`data/processed/features_static_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/features_static_bengaluru.parquet) (1,170 rows, 31 columns):

### Key Variables Extracted
- **SRTM Elevation Variables:** `elevation_mean_m` (min: 755.54 m, mean: 885.54 m, max: 944.55 m, std: 34.29 m), `elevation_min_m`, `elevation_max_m`, `elevation_std_m`. Valid pixel fraction is **100.0%**.
- **ESA WorldCover 10m Land Cover Fractions:**
  - `built_up_fraction` (Class 50): mean 44.29%, max 99.04%.
  - `water_fraction` (Class 80): mean 0.91%, max 48.33% (lake cells like Bellandur/Varthur).
  - `tree_cover_fraction` (Class 10): mean 18.28%.
  - `cropland_fraction` (Class 40): mean 20.24% (peri-urban agricultural belt).
  - `grassland_fraction` (Class 30): mean 3.81%.
  - `shrubland_fraction` (Class 20): mean 9.30%.
- **MERIT Hydro UPA:** Preserved as clean `NaN`s across 1,170 cells, preventing artificial assumptions of zero contributing area.

---

## 4. Dynamic Rainfall Feature Dataset

Stored in [`data/processed/features_rainfall_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/features_rainfall_bengaluru.parquet) ($1,170 \times 17 = 19,890$ rows, 18 columns):

- **Temporal Coverage:** August 25, 2022 to September 10, 2022 (17 daily steps).
- **Antecedent Lookback:** Full 14-day prior window (August 11 to August 24) pre-computed so that Day 1 (August 25) contains complete antecedent soil saturation history without missingness or lookahead bias.
- **Physical Features:**
  - `rainfall_daily_depth_mm`: Daily rainfall accumulation in mm.
  - `precip_antecedent_3d_mm`, `precip_antecedent_7d_mm`, `precip_antecedent_14d_mm`: Strictly prior rolling sums.
  - `precip_api_decay_mm`: Antecedent Precipitation Index ($\text{API}_t = \sum_{k=1}^{14} P_{t-k} \cdot 0.85^k$).
- **Provenance & Quality Flags:** Tagged with `source_granule_id`, `data_quality_flag = "PROVISIONAL_STAGED_IMERG_ENGINE"`, and `verification_status = "PARTIALLY_VERIFIED"`.

---

## 5. Integrated Panel Dataset & Event Decoupling

Stored in [`data/processed/features_integrated_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/features_integrated_bengaluru.parquet) (19,890 rows, 53 columns):

- Preserves the $(t, s)$ panel structure ($1,170 \text{ cells} \times 17 \text{ dates}$).
- Static environmental properties are aligned with daily rainfall forcings.
- Historical flood incidents are linked as **observational event markers**:
  - `has_reported_incident_on_date`: Exactly 18 cell-date combinations correspond to documented Group A or B flood events (e.g. August 30 initial wave and September 4–5 disaster peak).
  - `incident_boundary_ambiguity_flag`: Identifies whether the incident fell within its uncertainty radius of an adjacent cell edge.
  - The remaining 19,872 cell-date rows remain unlabelled (never assumed non-flooded).
- `sar_observational_status`: Explicitly flagged as `"SYNTHETIC_TEST_ONLY_EXCLUDED"`.

---

## 6. Machine-Readable Feature Registry

Stored in [`data/processed/feature_registry.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/feature_registry.json):
- Fully describes 15 platform variables, specifying their exact mathematical formulas, native spatial resolutions, units, missingness policies, provenance source URLs, and scientific caveats.

