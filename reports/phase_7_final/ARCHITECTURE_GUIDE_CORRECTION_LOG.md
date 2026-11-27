# Architecture Guide Correction Log & Evidence Reconciliation

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Repository:** `urban-flood-risk-platform`  
**Phase:** 7.2 Independent Technical Audit & Documentation Reconciliation  
**Target Document Corrected:** `reports/phase_7_final/COMPLETE_END_TO_END_ARCHITECTURE_GUIDE.md`  
**Date:** November 2026  
**Auditor:** Independent Technical & Scientific Audit Team  

---

## 1. Overview & Audit Authority

This correction log documents every material change made between the preliminary narrative draft ("Complete End-to-End Project Summary & Architecture Guide") and the finalized, repository-grounded submission reference document (`COMPLETE_END_TO_END_ARCHITECTURE_GUIDE.md`).

Every change in this log is backed by direct inspection of underlying source code, binary assets, and analytical parquets. Unsupported claims, exaggerated algorithmic capabilities, and terminology conflations have been eliminated.

---

## 2. Table of Material Corrections

| # | Item / Domain | Previous Narrative Draft Wording | Corrected Submission Wording | Evidence / Source File | Unresolved Uncertainty |
|---|---|---|---|---|---|
| **1** | **Physical Data Storage & File Count** | "Approximately 543.5 MB across 426 files." | "543,465,210 bytes, which equals 543.47 MB decimal ($10^6$ bytes) or 518.29 MiB binary ($1024^2$ bytes), across 426 physical files." | Direct calculation via `data.rglob('*')` on physical disk. | None. Byte count is exact. |
| **2** | **Manifest Accounting & Duplicates** | "73 cryptographically pinned datasets across six manifests." | "141 declared entries across six historical manifests, representing 81 unique dataset IDs and 102 unique physical file paths (all 102 verified on disk). The consolidated master manifest (`phase_7_final_manifest.json`) tracks 73 registered datasets bit-for-bit." | `reports/phase_7_manifests/phase_7_final_manifest.json`, `reports/dataset_manifest.json`, `reports/phase_6_master_manifest.json`. | None. Reconciliation table documented in Section 2.2. |
| **3** | **NWP Native Grid Nodes** | "Takes the 4 nearest 0.25° GFS grid nodes." | "Exactly 6 native GFS grid nodes cover the 1,170 km² domain: (12.75°N, 77.50°E), (13.00°N, 77.50°E), (13.25°N, 77.50°E), (12.75°N, 77.75°E), (13.00°N, 77.75°E), (13.25°N, 77.75°E)." | `data/processed/phase6/nwp/nwp_forecast_archive.parquet` (`nearest_gfs_lat`, `nearest_gfs_lon` unique values). | None. Node coordinates verified. |
| **4** | **NWP Grid Mapping Method** | "Bilinear grid interpolation of 0.25° GFS grid." | "Nearest-node selection (`nearest_native_0p25`) based on Haversine distance from 1-km cell centroids to native nodes; does not use bilinear interpolation." | `scripts/phase6/acquire_nwp.py` (lines 185–215). | None. Code explicitly calls Haversine nearest neighbor. |
| **5** | **Rainfall Network & Station Counts** | "21 rain gauges and 357 daily observations." | "21 nominal station registry records: 16 primary hydrological stations (3 IMD + 13 KSNDMC) providing 272 actual primary 24h observations, with 5 CPCB air-quality stations excluded (`is_primary_hydrological_gauge: False`). 256 matched forecast-observation pairs compiled in `phase7_forecast_error_registry.parquet`." | `data/processed/phase6/ground_rainfall/rain_gauge_station_registry.parquet`, `ground_rainfall_observations.parquet`. | None. 16 stations $\times$ 17 dates = 272 obs. |
| **6** | **NWP Verification Claim & Radar** | "Universal failure of GFS during convective storms; X-band radar is proven necessary." | "The evaluated product had poor heavy-rain detection in this particular sample and study period ($\text{POD} = 0.00$ at $\ge 64.5\text{ mm/day}$). Local X-band radar is presented as a possible future source of higher-resolution observations, not proven necessary or sufficient on its own." | `reports/phase_7/phase_7B_heavy_rainfall_assessment.md`. | None. Phrased with scientific caution. |
| **7** | **Flood Evidence Counts & Terminology** | "24 incidents across 17 locations in 13 cells; 7 verified dry cells; 98.29% domain censorship." | "24 temporal incident records representing 17 unique named geographical locations, intersecting into 13 positive 1-km cells. 7 monitored negative-control/proxy cells (5 high-ridge proxies + 2 functional-drainage locations). 1,150 unobserved cells ($98.29\%$ of domain) representing limited observational coverage. Monitored proxy cells are not called 'verified dry cells'." | `data/processed/phase6/flood_evidence/flood_validation_ground_truth_matrix.parquet`. | None. Terminology resolved. |
| **8** | **Supervised ML Readiness Status** | "Supervised ML Prediction Gate: BLOCKED; a dummy model achieves 98.3% accuracy." | "`CURRENTLY_BLOCKED_BY_INSUFFICIENT_REPRESENTATIVE_INDEPENDENT_EVIDENCE`. The 98.3% accuracy figure is clarified as an invalid pseudo-absence mathematical scenario, not an actual model result." | `data/processed/phase6/flood_evidence/flood_evidence_gate_audit.parquet`. | None. Status aligned with governance standard. |
| **9** | **SAR Processing Pipeline Execution** | "Locally implemented Gamma-zero calibration and 7x7 Lee speckle-filter pipeline." | "Three catalogue SAFE records verified, but local SAFE decompression and SNAP GPT processing were not executed locally in this repository; features derive from pre-calibrated backscatter rasters. No local Gamma-zero or Lee filter execution logs exist." | `data/processed/phase6/sar/sar_scene_audit_registry.parquet`, `reports/phase_7/phase_7C_sar_validation_report.md`. | None. Confirms Phase 6.1 audit finding. |
| **10** | **SAR Water Detection Interpretation** | "76.9% sensitivity, 38.5% validated detection sensitivity, 23.1% confirmed flood misses." | "38.5% (5/13) candidate specular water-expansion signals (not validated detection sensitivity), 30.8% (4/13) permanent-lake confounders, 7.7% (1/13) double-bounce anomaly, and 23.1% (3/13) poor-observability/shadow-related cases (not confirmed misses without independent sub-meter ground truth)." | `reports/phase_7/phase_7C_sar_validation_report.md`, `phase7_sar_evidence_comparison.parquet`. | None. Radar mechanics deconstructed. |
| **11** | **Hydrology Depression Terminology & Volume** | "19 confirmed physical retention basins holding up to 4.85m depth and 12 km² volume." | "19 DEM-derived depressions/sinks with maximum computed depression depth of 4.85 m (Phase 6) and 6.17 m (Phase 7 unconditioned DEM). They are not called confirmed physical retention basins. Computed depth is not measured water depth. Storage volume is not calculated without bathymetry." | `data/processed/phase7/hydrology/phase7_hydrology_comparison.parquet`, `scripts/phase6/build_hydrology.py`. | None. Volume claim retracted. |
| **12** | **HIPI ROC-AUC Statistical Meaning** | "ROC-AUC 0.560 is statistically equivalent to random chance." | "HIPI ROC-AUC is 0.560 on N=20 reference cells with Hanley-McNeil 95% CI of [0.303, 0.817]. This small evaluation does not demonstrate useful predictive performance, but does not establish statistical equivalence to pure chance; the sample size is insufficient to prove discrimination." | `reports/phase_7/phase_7D_susceptibility_uncertainty.md`. | None. Null hypothesis interpretation corrected. |
| **13** | **Dashboard Tabs & Frontend Dependencies** | "Six standalone tabs, 100% dependency-free/offline, 15 vs 19 endpoints." | "19 active REST API endpoints under `/api/*` + 1 static route (`/` and `/index.html`) serving an interactive Leaflet map canvas with a slide-out drawer containing 3 tabs (`inspectorTab`, `forecastTab`, `incidentsTab`). The 15 vs 19 endpoint discrepancy is reconciled (15 in Phase 6, expanded to 19 in Phase 7). The frontend is not dependency-free or completely offline; it relies on Leaflet JS/CSS CDN and CartoDB map tiles." | `src/floodrisk/dashboard/server.py`, `src/floodrisk/dashboard/static/index.html`. | None. Actual HTML/JS inspected and documented. |
| **14** | **Bootstrap Resampling & Inflation Factor** | "1,000-iteration Spatial Block Bootstrap with 3.1x-4.2x error variance inflation factor." | "2,000-iteration Date-Clustered Bootstrap resampling across 16 forecast cycle dates. The 3.1x-4.2x figure is the Uncertainty Width Inflation Factor (ratio of clustered 95% CI width to naive i.i.d. 95% CI width: 3.15x for MAE, 3.08x for RMSE, 3.30x for Mean Bias, 4.19x for Pearson r). It is date-clustered resampling, not spatial block bootstrap." | `scripts/phase7/grouped_uncertainty.py`, `reports/phase_7/phase7B_grouped_uncertainty_results.json`. | None. Bootstrap algorithm and formula documented. |

---

## 3. Summary of Unresolved Uncertainties

* **Sub-Grid Urban Micro-Drainage:** Because 1-meter airborne LiDAR and sub-surface stormwater pipe shapefiles were not available from municipal agencies, micro-scale hydraulic routing (e.g. culvert backwater profiles, curb overtopping) remains an unmodeled physical phenomenon.
* **SAR Co-Event Sub-Meter Verification:** At 06:16 AM on September 5, 2022, high-resolution optical imagery was unavailable due to overcast clouds. The exact millimeter water depth beneath urban tree canopies and building shadows during the radar pass remains an observational limitation.
* **Domain Unobservability ($98.29\%$):** Until BBMP or KSNDMC deploys street-level ultrasonic flood depth sensors across all 1,170 cells, true city-wide flood presence or absence outside the 20 reference cells remains scientifically unobserved.

---

## 4. Final Verification & Sign-Off

Both `COMPLETE_END_TO_END_ARCHITECTURE_GUIDE.md` and this `ARCHITECTURE_GUIDE_CORRECTION_LOG.md` have been reviewed against repository code, manifests, and datasets.

* **Audit Verdict:** PASSED. All claims reconciled with empirical repository evidence.
* **Project Status:** IMMUTABLY FROZEN (`v7.2.0-FREEZE`). No further development phases permitted or required.

