# Phase 5 Final — Master Baseline Freeze & Scientific Integrity Report

**Milestone:** Phase 5 Final Acceptance Campaign — Step 1: Baseline Preservation & Inspection  
**Author:** Antigravity Autonomous Agent (Google DeepMind Advanced Agentic Coding)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Study Domain:** Bengaluru Urban provisional study domain (1,170 equal-area 1-km cells, EPSG:6933, bounded provisionally by $77.45^\circ - 77.75^\circ\text{E}, 12.85^\circ - 13.15^\circ\text{N}$, boundary status: `pending_authoritative_boundary`)  
**Baseline Test Status:** 94 passed / 94 total across 10 test modules (100% pass rate in 43.31s)  
**Cryptographic Integrity:** 33 baseline datasets verified (100% match); 8 initial Phase 5 datasets verified (100% match)  

---

## 1. Executive Summary & Freeze Declaration

Prior to executing the scientific integrity audit, methodological corrections, and final acceptance evaluations of Phase 5, all upstream datasets from Phases 1 through 4.7, as well as initial Phase 5 deliverables, are formally audited and frozen. 

This freeze establishes an immutable benchmark:
1. Under no circumstances will original Phase 2, Phase 3, Phase 4, Phase 4.7, or initial Phase 5 files be overwritten, mutated, or deleted.
2. All corrected, re-evaluated, or versioned datasets generated during this master campaign will be written exclusively to new, dedicated versioned paths under `data/processed/phase5_final/`.
3. The baseline manifest [`reports/dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/dataset_manifest.json) and initial Phase 5 manifest [`reports/phase_5_dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_dataset_manifest.json) remain permanently frozen. A new, independent manifest [`reports/phase_5_final_dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_dataset_manifest.json) will catalogue the final corrected deliverables.

---

## 2. Cryptographic Inventory of Frozen Baseline (33 Datasets)

Every file in the baseline manifest [`reports/dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/dataset_manifest.json) was cryptographically re-verified via SHA-256 calculation:

| Dataset ID | Relative Path | File Size (Bytes) | SHA-256 Checksum | Baseline Role |
| :--- | :--- | :---: | :--- | :--- |
| `dynamic_risk_intelligence_bengaluru` | `data/processed/dynamic_risk_intelligence_bengaluru.parquet` | 107,397 | `6081fd84222233531108f6700e20eb3a8c51b34bff01840af4631defb382fd69` | Canonical 4-layer dynamic risk index |
| `esa_worldcover_10m_2021_v200_n12e075_map` | `data/raw/land_cover/ESA_WorldCover_10m_2021_v200_N12E075_Map.tif` | 127,650,362 | `f9269901e07d86c2e180d661d0e8924e3ee57dd589f7433b9874861b3c65a978` | Authentic ESA land cover raster |
| `exploratory_risk_indicators_bengaluru` | `data/processed/exploratory_risk_indicators_bengaluru.parquet` | 663,821 | `3b1e329891f07f5cf9c1f74987694411f86a3dae4d11df08b72649ffe928c902` | Phase 2B multi-criteria indicator set |
| `feature_registry` | `data/processed/feature_registry.json` | 11,710 | `081c59607c38caa82b648c0af6d1330232c1d7d0ecb2e48da3639ead874ad49d` | Feature metadata schema & definitions |
| `features_integrated_bengaluru` | `data/processed/features_integrated_bengaluru.parquet` | 165,317 | `e6c48c665a559293186a3484ed310fe5a6e333c1326027a5fdccf27667bb8f4f` | Merged static & dynamic feature matrix |
| `features_rainfall_bengaluru` | `data/processed/features_rainfall_bengaluru.parquet` | 72,626 | `a1084f34a160bb2c47d21fb00d29107658c7ddff33d2f0d9e3d391ecb42741dd` | GPM IMERG calibrated rainfall series |
| `features_static_bengaluru` | `data/processed/features_static_bengaluru.parquet` | 80,989 | `cbbdac220de4d03c30c52a0b86e9f322ea94ae950e2e7b7f4b9f280444eb9218` | Topographic & land-cover features |
| `flood_event_inventory_bengaluru` | `data/processed/flood_event_inventory_bengaluru.parquet` | 27,828 | `9e1917c17838b7b8dd3c40bbbc1e989c51155db396713ea12266da148b3f0aa6` | 21 historical flood incident records |
| `flood_event_monitoring_log` | `data/processed/flood_event_monitoring_log.parquet` | 12,967 | `0d205caba6fe5c145391eb2b422d0835cee48986fec8d5421e2c30d29c5bdb15` | 6 monitored flood/watch episodes |
| `flood_source_registry_bengaluru` | `data/processed/flood_source_registry_bengaluru.parquet` | 8,826 | `9a5f2017f24b5740288f23b5b49ed9a6fe2f4a1353e8a770989f49aaec50b018` | Source institutions & publications |
| `forecast_exposure_indicators_bengaluru` | `data/processed/forecast_exposure_indicators_bengaluru.parquet` | 19,204 | `5cc021f802b8846d9767da435ada53233a226f702ef463eb9d55a4d137bde543` | 24h & 72h forecast hazard exposure |
| `forecast_rainfall_bengaluru` | `data/processed/forecast_rainfall_bengaluru.parquet` | 431,406 | `2a96d9106446c1ae8f29f837f74e32b50230c6218a30246ad4c87610e915bcf8` | Canonical 67,860-row NWP forecast |
| `grid_bengaluru_rural_1000m` | `data/processed/grid_bengaluru_rural_1000m.geojson` | 6,544,631 | `948fdd609b123223b74765ae5882191d066811a843ab6c9fa1e3709df0e1e52b` | External rural domain reference |
| `grid_bengaluru_urban_1000m` | `data/processed/grid_bengaluru_urban_1000m.gpkg` | 569,344 | `aa11c33bd648ea07573d1421981cc63abf898d95cefb5516cd9e34ce41fc64a2` | 1,170 master cells in EPSG:6933 |
| `grid_features_bengaluru_urban_1000m` | `data/processed/grid_features_bengaluru_urban_1000m.parquet` | 50,412 | `d5404934065182e050369d0f1352b931e06b010283f56231dfe698c97976b6ee` | Grid cell geometry & coordinates |
| `grid_mysuru_urban_1000m` | `data/processed/grid_mysuru_urban_1000m.geojson` | 469,289 | `afb1542de2cc68bb2e70e86497b5bc8f0317e24f46e057f6e29557b21765add3` | Transferability test grid |
| `n12e077` | `data/raw/elevation/srtm/N12E077.hgt` | 25,934,402 | `d70ed4171e76a7296268016e903563027329086be8c6d89136de8582b9a5ed96` | Raw SRTM tile South |
| `n12e077.srtmgl1` | `data/raw/elevation/srtm/N12E077.SRTMGL1.tif` | 8,095,151 | `697aa24791cd02b43a5002fc5b7f6137434d74c420d5a7a0d6f58743b1595b15` | GeoTIFF conversion South |
| `n12e077.srtmgl1.hgt` | `data/raw/elevation/srtm/N12E077.SRTMGL1.hgt.zip` | 10,071,528 | `37c8aafaa1acae395053cab5bd1d3766676897a7c08724590a1999d4caa28d76` | STEP archive archive zip South |
| `n13e077` | `data/raw/elevation/srtm/N13E077.hgt` | 25,934,402 | `4a9c7d71333a6c83bf0d6afbf1ebfd47b8fcee8558f6f11c88b678ee63391627` | Raw SRTM tile North |
| `n13e077.srtmgl1` | `data/raw/elevation/srtm/N13E077.SRTMGL1.tif` | 6,783,967 | `d9a8821fd3017803f3ab7086afd7ba60679aa2e7b4c1dde09395f649073d2fd6` | GeoTIFF conversion North |
| `n13e077.srtmgl1.hgt` | `data/raw/elevation/srtm/N13E077.SRTMGL1.hgt.zip` | 7,813,126 | `17d69dfe6a9c484a23844d81b682adb27fcf384f4f4cc27b06935079ef659790` | STEP archive archive zip North |
| `phase3_isolation_forest_results` | `data/processed/phase3_isolation_forest_results.parquet` | 1,092,964 | `6fc85f51c25e32a76b936e7857b5b6cd72718f3306f4f4e56d32671e8d3a6916` | Unsupervised spatial anomaly scores |
| `phase3_mahalanobis_results` | `data/processed/phase3_mahalanobis_results.parquet` | 728,236 | `0ccf10549bc75ec0ac03d4ec4735cf8852bafe9992b0d003eb8f12b4c412f65e` | Statistical distance baseline |
| `phase3_mcda_results` | `data/processed/phase3_mcda_results.parquet` | 894,578 | `2167e804e8c675ef3f109402054b779d69873994e8cf1f3ed90d8dc61e2b6a2d` | Multi-criteria physical evaluation |
| `phase3_model_comparison` | `data/processed/phase3_model_comparison.parquet` | 1,487,931 | `59c33bbaf00126c364523797c8334de4c3f43119e9c565fefb1e3633589b1277` | Cross-model comparative matrix |
| `phase3_model_features` | `data/processed/phase3_model_features.parquet` | 275,694 | `fa56947820baf01bc67034342912843563665a8a25f35e5827327b92772cce79` | Standardized feature inputs |
| `sentinel1_candidate_flood_change_mask_bengaluru` | `data/processed/sentinel1_candidate_flood_change_mask_bengaluru.tif` | 336,641 | `f41f6b6de685f3b56314cdc2e96b18c0c3b50a1ba4e36b75b8bd748bfe29fa4f` | Change detection mask |
| `sentinel1_candidate_water_mask_bengaluru` | `data/processed/sentinel1_candidate_water_mask_bengaluru.tif` | 374,203 | `cb874190a894ae244d4a2f18381d9af80125b7a5e906d8bfabf2a59331e82f75` | Otsu water threshold mask |
| `sentinel1_grid_features_bengaluru` | `data/processed/sentinel1_grid_features_bengaluru.parquet` | 40,711 | `6675ede51339e813170d15f3d9d236c0da609cf3092ecddbab4601e8aecda8ec` | Grid-level SAR statistics |
| `sentinel1_incident_comparison_bengaluru` | `data/processed/sentinel1_incident_comparison_bengaluru.parquet` | 10,503 | `3a74099ac24b5220e20f79ebe52e0ca9e14e372109f9c37718ac5fe8419f4d53` | Incident overlap table |
| `sentinel1_scene_registry_bengaluru` | `data/processed/sentinel1_scene_registry_bengaluru.parquet` | 11,806 | `234d58d00cd56329e3db3543e282e59776eb7d118b4c3984646901126c28138b` | Scene geometry registry |
| `srtmgl1_n12_n13_e077_bengaluru` | `data/raw/elevation/srtm/SRTMGL1_N12_N13_E077_Bengaluru.tif` | 14,876,879 | `ba45614211dbcbf686a47b36e19a32a9cfd82ce7c82a80bcc9e269a95d93946f` | Authentic merged 30m DEM mosaic |

---

## 3. Cryptographic Inventory of Initial Phase 5 Deliverables (8 Datasets)

Every file in the initial Phase 5 manifest [`reports/phase_5_dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_dataset_manifest.json) was cryptographically verified:

| Dataset ID | Relative Path | Rows | Size (Bytes) | SHA-256 Checksum |
| :--- | :--- | :---: | :---: | :--- |
| `archived_nwp_forecasts_bengaluru` | `data/processed/phase5_forecast_archive/...` | 198,900 | 620,362 | `a9f538e14e21aeb9773ea6e6dd27e3687e83e9b1cfc5344319803bce36c7e2ad` |
| `independent_rainfall_observations_bengaluru` | `data/processed/phase5_rainfall_observations/...` | 59,670 | 50,521 | `d2825cbaee8bb40a835a6b57912a76f2d28aa07f6f1782e4f0dd17b074a3da49` |
| `forecast_observation_matched_pairs` | `data/processed/phase5_forecast_observation_matches/...` | 183,690 | 1,743,615 | `734914c62fb4bfdbf1f506e76cf0ce790380387b3370e0a5c43d9a0d4c84eb6c` |
| `forecast_verification_metrics_by_lead_time` | `data/processed/phase5_forecast_verification/...` | 15 | 15,622 | `b5b7b99c9521361c4728d8a7c2c99f9c73e04e9089ff5ca52c08ec13ef2b77a7` |
| `authentic_sar_scene_manifest` | `data/processed/phase5_sar_observations/...` | 3 | 10,567 | `7d727b3d36b8159b34db3b27b1f51667104b2b51ee2bc3d7bc936ba5458dfae1` |
| `independent_flood_evidence_records` | `data/processed/phase5_flood_evidence/...` | 21 | 11,487 | `4c7adfa7ff95be8374d6b5e022f462c1630c7e29cb4135eec0a1c1d0922851cf` |
| `flood_validation_reference_matrix` | `data/processed/phase5_flood_validation_dataset/...` | 1,170 | 48,020 | `e5bc99ecf3e2efd23e5a32ec4210667c4273292437632616f98ae18525e98fd0` |
| `flood_evidence_evaluation_metrics` | `data/processed/phase5_flood_validation_dataset/...` | 5 | 8,732 | `e3b2e5661136c3ee7ea7be147b40d7c7c345a3be2faef196884ee9b00869a84d` |

---

## 4. Resolution of Forecast Dataset Row Count Discrepancy

During the Phase 4.7 audit, a transition occurred between two versions of `forecast_rainfall_bengaluru.parquet`:
- **Phase 4.2 initial version:** 72,540 rows ($1,170\text{ cells} \times 62\text{ steps}$).
- **Phase 4.7 canonical version:** 67,860 rows ($1,170\text{ cells} \times 58\text{ steps}$).

**Audit Confirmation:** The Phase 4.7 file (`data/processed/forecast_rainfall_bengaluru.parquet`, SHA-256: `2a96d9106446c1ae8f29f837f74e32b50230c6218a30246ad4c87610e915bcf8`, 431,406 bytes) is confirmed as the **sole canonical operational forecast baseline**. The row count reduction from 72,540 to 67,860 resulted strictly from the rolling dynamic forecast lead-time horizon in the live Open-Meteo ingestion window.

---

## 5. Scope of Outstanding Scientific Audits for Phase 5 Final

This master campaign will rigorously audit and resolve the following outstanding scientific and methodological issues:

1. **Forecast Sample Independence:** The reported 183,690 matched pairs represent only 9 regional NWP anchors mapped to 1,170 cells (a replication factor of ~130x). Effective independent degrees of freedom ($N_{\text{eff}}$) must be computed and metrics evaluated at the anchor level.
2. **Contingency Table Edge Cases:** Investigate the degenerate contingency table at 6h Light Rain (HSS = 0, TSS = NaN) and negative HSS at 48h-72h.
3. **Threshold Derivation Transparency:** Document that 6h and 12h rainfall thresholds are derived scaled disaggregations, not official statutory IMD categories.
4. **Flood Evidence Taxonomy & Censorship:** Explicitly report that 1,148 of 1,170 cells ($98.13\%$) are completely unobserved.
5. **Negative Observation Audit:** Rigorously audit the 5 "monitored no-inundation" cells (campus ridge weather stations) and verify whether rainfall telemetry on a ridge justifies a cell-wide no-flood label.
6. **ROC-AUC & PR-AUC Audit:** Explain why static susceptibility and dynamic risk produced identical ROC-AUC ($0.7231$), and reveal that the 5-km buffer subset had only 1 negative cell ($N_{\text{neg}} = 1$), explaining its trivial $1.0000$ AUC.
7. **Authentic SAR SAFE Status:** Distinguish catalogued scene metadata from raw L1 GRD SNAP processing, documenting that raw reprocessing is blocked by CDSE OAuth credentials while synthetic SAR remains quarantined.

