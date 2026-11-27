# Phase 5 Final Execution Summary & Handoff

## 1. Executive Summary

The Phase 5 Final Acceptance Campaign for the **AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data** platform (`urban-flood-risk-platform`) has been executed in full compliance with scientific integrity standards, reproducible verification principles, and strict baseline preservation rules.

All 33 baseline datasets from Phases 1–4.7 and all 8 initial Phase 5 datasets remain bit-for-bit frozen and verified against their recorded SHA-256 manifests. Eight new corrected and audited datasets have been generated and versioned in `data/processed/phase5_final/`. Eighteen comprehensive technical reports, an updated REST API backend, an expanded interactive dashboard, and a 94-test regression suite have been delivered.

The campaign establishes two definitive decision gates:
* **Gate A (Meteorological Forecast Skill):** **`CONDITIONALLY_SUPPORTED`**. Archived ECMWF numerical weather predictions demonstrate high, statistically significant skill at short lead times ($\le 24\text{h}$, with $r = 0.857$ at 6h, $0.783$ at 12h, $0.562$ at 24h across regional anchors), but display negative skill and severe spatial phase displacement at medium ranges ($r = -0.063$ at 48h, $r = -0.146$ at 72h). Automated flood alert generation is strictly prohibited beyond 24 hours.
* **Gate B (Supervised Flood Modeling Readiness):** **`BLOCKED_BY_DATA_ACCESS` / `INSUFFICIENT_INDEPENDENT_EVIDENCE`**. With only 13 verified positive flood cells ($1.11\%$ of the study area), 5 high-ground ridge proxy stations, zero verified valley dry observations, and $98.13\%$ spatial unobserved censoring, supervised machine learning or deep learning flood-prediction modeling is blocked. Proceeding with supervised training would induce severe label noise, spatial pseudo-replication, and circular confirmation bias.

The overall platform status is formally determined as **`CONDITIONALLY_ACCEPTED`**.

---

## 2. Inventory of Deliverables

### A. Core Source & Dashboard Code
* [`src/floodrisk/dashboard/server.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/dashboard/server.py): Enhanced to prioritize `data/processed/phase5_final/` datasets with automatic fallback; registered 4 Phase 5 REST endpoints (`/api/phase5/verification-metrics`, `/api/phase5/flood-validation`, `/api/phase5/sar-manifest`, `/api/phase5/readiness-gates`).
* [`src/floodrisk/dashboard/static/index.html`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/dashboard/static/index.html): Added Phase 5 interactive verification tab with Gate A/B status cards, lead-time contingency matrix, 7-class flood evidence taxonomy, bootstrap discrimination charts, and authentic SAR metadata tables.
* [`tests/test_phase_5.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/tests/test_phase_5.py): Added 7 comprehensive unit and integration tests verifying Phase 5 data integrity, anchor independence, bootstrap discrimination, and REST API functionality.

### B. Versioned Data Deliverables (`data/processed/phase5_final/`)
1. [`forecast_archive/archived_nwp_forecasts_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/phase5_final/forecast_archive/archived_nwp_forecasts_bengaluru.parquet) (198,900 rows, 15 columns, 620,362 bytes)
2. [`rainfall_observations/independent_rainfall_observations_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/phase5_final/rainfall_observations/independent_rainfall_observations_bengaluru.parquet) (59,670 rows, 11 columns, 50,521 bytes)
3. [`forecast_observation_matches/forecast_observation_matched_pairs.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/phase5_final/forecast_observation_matches/forecast_observation_matched_pairs.parquet) (183,690 rows, 27 columns, 1,743,615 bytes)
4. [`forecast_verification/forecast_verification_metrics_by_lead_time.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/phase5_final/forecast_verification/forecast_verification_metrics_by_lead_time.parquet) (15 rows, 26 columns, 18,076 bytes)
5. [`sar_observations/authentic_sar_scene_manifest.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/phase5_final/sar_observations/authentic_sar_scene_manifest.parquet) (3 rows, 15 columns, 10,567 bytes)
6. [`flood_evidence/independent_flood_evidence_records.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/phase5_final/flood_evidence/independent_flood_evidence_records.parquet) (21 rows, 13 columns, 11,487 bytes)
7. [`flood_validation_dataset/flood_validation_reference_matrix.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/phase5_final/flood_validation_dataset/flood_validation_reference_matrix.parquet) (1,170 rows, 17 columns, 48,020 bytes)
8. [`flood_validation_dataset/flood_evidence_evaluation_metrics.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/phase5_final/flood_validation_dataset/flood_evidence_evaluation_metrics.parquet) (7 rows, 16 columns, 11,280 bytes)

### C. Dataset Manifests
* [`reports/dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/dataset_manifest.json): Frozen Phases 1–4.7 baseline manifest (33 datasets, 100% verified).
* [`reports/phase_5_dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_dataset_manifest.json): Frozen initial Phase 5 baseline manifest (8 datasets, 100% verified).
* [`reports/phase_5_final_dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_dataset_manifest.json): Final Phase 5 Acceptance manifest (8 versioned datasets, complete SHA-256 audit).

### D. Complete Suite of 18 Technical Reports (`reports/`)
1. [`reports/phase_5_final_baseline_freeze.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_baseline_freeze.md): Baseline verification & freeze audit.
2. [`reports/phase_5_final_data_acquisition_registry.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_data_acquisition_registry.md): Independent data sourcing & provenance registry.
3. [`reports/phase_5_final_forecast_reconstruction.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_forecast_reconstruction.md): Archived NWP cycles & anti-lookahead reconstruction.
4. [`reports/phase_5_final_forecast_observation_matching.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_forecast_observation_matching.md): Spatiotemporal forecast-observation matching protocol.
5. [`reports/phase_5_final_forecast_independence_audit.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_forecast_independence_audit.md): Spatial pseudo-replication audit ($N_{\text{eff}} = 711$ vs $183,690$).
6. [`reports/phase_5_final_continuous_forecast_verification.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_continuous_forecast_verification.md): Continuous error metrics & degradation curves across lead times.
7. [`reports/phase_5_final_contingency_and_threshold_audit.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_contingency_and_threshold_audit.md): Categorical contingency tables, threshold derivation, and base-rate anomalies.
8. [`reports/phase_5_final_flood_taxonomy_audit.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_flood_taxonomy_audit.md): 7-class evidence taxonomy and 98.13% unobserved censoring.
9. [`reports/phase_5_final_negative_observation_audit.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_negative_observation_audit.md): High-ground ridge station audit (proxy status vs ground truth).
10. [`reports/phase_5_final_discrimination_metric_audit.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_discrimination_metric_audit.md): Discrimination metrics, bootstrap CIs, and small-sample degenerate artifacts.
11. [`reports/phase_5_final_sar_authenticity_and_processing_audit.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_sar_authenticity_and_processing_audit.md): Authentic Sentinel-1 CDSE query audit & urban radar limitations.
12. [`reports/phase_5_final_spatiotemporal_validation.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_spatiotemporal_validation.md): Spatial autocorrelation and buffer contamination analysis.
13. [`reports/phase_5_final_dashboard_and_operational_updates.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_dashboard_and_operational_updates.md): Dashboard transparency, REST endpoints, and truthfulness alerts.
14. [`reports/phase_5_final_model_readiness_assessment.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_model_readiness_assessment.md): Formal evaluation of Gate A and Gate B.
15. [`reports/phase_5_final_scientific_acceptance.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_scientific_acceptance.md): Master Scientific Acceptance Scorecard (Items A through R).
16. [`reports/phase_5_final_technical_report.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_technical_report.md): Consolidated comprehensive Phase 5 technical monograph.
17. [`reports/phase_5_final_execution_summary.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_execution_summary.md): This executive summary and final handoff dossier.
18. [`reports/phase_5_final_test_summary.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_test_summary.md): Comprehensive 94-test regression verification report.

---

## 3. Preserved Baselines & Versioning Integrity

To guarantee absolute scientific reproducibility, no historical data from prior phases was altered or deleted:

| Phase Baseline | Scope | File Count | Storage Location | Manifest Verification |
| :--- | :--- | :--- | :--- | :--- |
| **Phases 1–4.7** | Terrain, static features, IMERG rainfall, incident registry, baseline models, operational risk intelligence | 33 Parquet / GeoTIFF files | `data/processed/` subdirectories | 100% SHA-256 match with [`reports/dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/dataset_manifest.json) |
| **Initial Phase 5** | Initial forecast reconstruction, initial matched pairs, initial metrics, initial evidence reference | 8 Parquet files | `data/processed/phase5_*` | 100% SHA-256 match with [`reports/phase_5_dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_dataset_manifest.json) |
| **Phase 5 Final** | Corrected, audited, and expanded deliverables | 8 Parquet files | `data/processed/phase5_final/` | 100% SHA-256 registered in [`reports/phase_5_final_dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_dataset_manifest.json) |

---

## 4. Retained vs Corrected Findings: Audit Comparison Table

| Finding / Component | Initial Phase 5 Finding | Phase 5 Final Corrected Finding | Scientific Root Cause & Remediation |
| :--- | :--- | :--- | :--- |
| **Forecast Sample Size** | Claimed $N = 183,690$ independent verification degrees of freedom | Disclosed 9 regional forecast anchors across 1,170 cells ($130\times$ spatial replication); $N_{\text{eff}} = 711$ spatiotemporal units | Raw cell counts constituted severe spatial pseudo-replication. Verified and reported anchor-level metrics side-by-side. |
| **72h Forecast Correlation** | Reported $r = 0.5284$ ($p < 10^{-100}$) | Corrected to regional anchor correlation $r = -0.1460$ ($p = 0.1028$) | Cell-level correlation was an artifact of repeating the same forecast across 130 cells. Regional skill at 72h is statistically zero. |
| **48h/72h Heavy Rain Skill** | Negative HSS ($-0.1493$, $-0.1284$) left unexplained | Documented as severe spatial and temporal phase displacement | Convective monsoon cells shifted by $10–30\text{ km}$, yielding $3,633$ false alarms and $6,160$ misses. |
| **6h Light Rain Contingency** | Reported $HSS = 0.0$ and $TSS = \text{NaN}$ without explanation | Classified as `DEGENERATE_ZERO_NEGATIVES` | 100% base-rate precipitation caused zero true negatives ($C=0$) and zero false alarms ($F=0$), resulting in division by zero. |
| **Threshold Sourcing** | All thresholds labeled as IMD standards | Separated 24h statutory IMD thresholds from derived 6h/12h diurnal disaggregations | 6h ($1.0, 6.2, 25.8\text{ mm}$) and 12h ($1.6, 10.1, 41.9\text{ mm}$) are mathematically derived, not official IMD definitions. |
| **Flood Evidence Taxonomy** | Binary label (13 positives vs 5 negatives) | 7-class formal taxonomy; domain is **98.13% unobserved** | Unobserved cells ($1,148/1,170$) explicitly marked as censored; never imputed as negative or dry. |
| **Inundation vs Waterlogging** | Conflated inundation and waterlogging as single positive target | Disaggregated Outcome A (Confirmed Inundation: 7 cells) and Outcome B (Combined Impact: 13 cells) | Evaluated both separately: Outcome A AUC = $0.7714$, Outcome B AUC = $0.7231$. |
| **Negative Reference Station Validity** | 5 stations treated as confirmed dry ground truth | Reclassified as `CONDITIONALLY_MONITORED_HIGH_GROUND_PROXIES` | Stations are on high-elevation ridges ($>918\text{ m}$) without flood sensors; a dry ridge does not prove adjacent valleys are dry. |
| **Identical Static & Dynamic AUC** | Noted as identical ($0.7231$) without mathematical explanation | Proved rank-order invariance: Spearman rank correlation $r_s = 0.9979$, identical Mann-Whitney $U = 47.0$ | Dynamic weights perturbed magnitude without changing relative risk ranking of the 18 evaluated cells. |
| **5-km Buffer Discrimination** | Celebrated as "perfect discrimination" ($\text{ROC-AUC} = 1.0000$) | Classified as `DEGENERATE_SAMPLE_ARTIFACT` | Within the 5-km buffer, only **1 negative cell** remained ($N_{\text{pos}}=13, N_{\text{neg}}=1$). Any single negative below positives yields AUC = 1.0. |
| **Statistical Confidence of AUC** | Point estimate $0.723$ reported as validation | Disclosed 95% bootstrap confidence interval: **$0.294$ to $1.000$** ($p = 0.0867$) | Wide CI demonstrates the small sample size cannot reject the null hypothesis of random guessing ($\text{AUC} = 0.5$) at $\alpha = 0.05$. |
| **Sentinel-1 SAR Status** | Claimed authentic SAR processing | Clarified as `SCENE_AUDIT_ONLY`; identified double-bounce urban radar barrier | 3 scenes queried from CDSE; SNAP preprocessing was not run locally due to credentials/storage; synthetic fixture strictly quarantined. |

---

## 5. Formal Decision Determinations

### Gate A: Meteorological Forecast Skill
* **Determination:** **`CONDITIONALLY_SUPPORTED`**
* **Lead-Time Specific Approvals:**
  * **6-Hour Lead Time:** `APPROVED` ($r = 0.857, \text{RMSE} = 3.65\text{ mm}, \text{MAE} = 2.47\text{ mm}$). Highly suitable for operational drainage mobilization.
  * **12-Hour Lead Time:** `APPROVED` ($r = 0.783, \text{RMSE} = 4.38\text{ mm}, \text{MAE} = 3.01\text{ mm}$). Approved for emergency shift scheduling.
  * **24-Hour Lead Time:** `APPROVED` ($r = 0.562, \text{RMSE} = 5.21\text{ mm}, \text{MAE} = 3.82\text{ mm}$). Approved for advisory preparedness notices.
  * **48-Hour Lead Time:** `NOT_APPROVED` ($r = -0.063$, negative HSS for heavy rain). Unreliable timing and location.
  * **72-Hour Lead Time:** `NOT_APPROVED` ($r = -0.146$, negative HSS for heavy rain). Skill indistinguishable from random chance.
* **Operational Constraint:** Automated emergency flood alerting and public warning dissemination based on forecast rainfall beyond 24 hours is **strictly prohibited**.

### Gate B: Supervised Flood Prediction Modeling Readiness
* **Determination:** **`BLOCKED_BY_DATA_ACCESS` / `INSUFFICIENT_INDEPENDENT_EVIDENCE`**
* **Technical Justification:**
  1. *Extreme Spatial Censorship:* 1,148 of 1,170 cells ($98.13\%$) have unrecorded flood status. Treating unobserved cells as negative introduces massive false-negative contamination ($>90\%$).
  2. *Severe Positive Scarcity:* Only 13 positive cells across the study period ($1.11\%$).
  3. *Unverified Negative Ground Truth:* Zero verified negative cells exist in low-lying valley bottoms or natural drainage pathways; all 5 candidate negative cells are located on elevated ridges.
  4. *Bootstrap Confidence Interval:* The $95\%$ bootstrap CI of ROC-AUC spans from $0.294$ (worse than coin flip) to $1.000$, with two-sided $p = 0.0867$.
* **Approved Modeling Paradigm:** Unsupervised physical multi-criteria vulnerability indexing (static vulnerability and antecedent rainfall accumulation) is **approved** for spatial planning and situational awareness. Supervised binary classification, regression, or deep learning is **permanently blocked** until an automated ground sensor network is operational.

---

## 6. Dashboard & Operational Verification

The interactive operational dashboard (`src/floodrisk/dashboard/server.py` and `static/index.html`) was updated and verified:
1. **Active Endpoints:**
   * `/api/health` $\to$ HTTP 200 (`status: healthy`).
   * `/api/phase5/verification-metrics` $\to$ HTTP 200 (returns continuous and contingency metrics by lead time, $N_{\text{eff}}$, and degenerate statuses).
   * `/api/phase5/flood-validation` $\to$ HTTP 200 (returns 7-class reference matrix summary, bootstrap CIs, and Outcome A vs B comparison).
   * `/api/phase5/sar-manifest` $\to$ HTTP 200 (returns authentic CDSE scene records and `SCENE_AUDIT_ONLY` disclaimer).
   * `/api/phase5/readiness-gates` $\to$ HTTP 200 (returns Gate A `CONDITIONALLY_SUPPORTED` and Gate B `BLOCKED`).
2. **Interactive UI Features:**
   * Prominent **Readiness Gate Status Cards** with color-coded badges and lead-time constraints.
   * **Contingency Verification Grid** displaying POD, FAR, CSI, HSS, and degenerate zero-negative flags.
   * **7-Class Evidence Distribution** highlighting the $98.13\%$ unobserved domain proportion.
   * **Discrimination Metric Card** displaying the bootstrap CI ($0.294–1.000$) and explaining the $1.0000$ 5-km buffer artifact.
   * **Authentic SAR Metadata Viewer** explicitly declaring the synthetic fixture quarantine.

---

## 7. Automated Test Suite Verification

The regression test suite was executed in full:
* **Total Tests:** 94
* **Passed:** 94
* **Failed:** 0
* **Errors:** 0
* **Execution Time:** 42.8 seconds
* **Coverage Modules:** 10 test modules covering Phase 5 verification, Phase 4 operational pipeline, SAR processing, rainfall ingestion, grid generation, terrain analysis, zonal statistics, CLI, dynamic risk engine, and real data integration.

---

## 8. Summary of Dataset Manifests & Checksums

All deliverables in `data/processed/phase5_final/` have been cryptographically hashed and registered in [`reports/phase_5_final_dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_5_final_dataset_manifest.json):

```
1. archived_nwp_forecasts_bengaluru.parquet
   SHA-256: e2dc657549dec3279e5c7d15e0b571b8c81135416d16a9e9e15843777d232b4b (620,362 bytes, 198,900 rows)
2. independent_rainfall_observations_bengaluru.parquet
   SHA-256: a9ecdb24b060400f4af3b466862851affa0537bee11288d485cc59ace6516db9 (50,521 bytes, 59,670 rows)
3. forecast_observation_matched_pairs.parquet
   SHA-256: 458a5c09bcc8c5bb744bfca87fb6469cf327da48cb2f9b877239fb6784d5df65 (1,743,615 bytes, 183,690 rows)
4. forecast_verification_metrics_by_lead_time.parquet
   SHA-256: 100be6fadac2be0fef39ffdb4dcde1367a7398f51a44c5fbc575395ce6eb9db2 (18,076 bytes, 15 rows)
5. authentic_sar_scene_manifest.parquet
   SHA-256: 87483121cae6b83f344cb8dd1b8a514d3392d4f23e201b1a778c13fb5973be26 (10,567 bytes, 3 rows)
6. independent_flood_evidence_records.parquet
   SHA-256: 94b1ba00851ba5c65f02bc4502d91f278ebc64ec34a625ca4e50efb942551bf5 (11,487 bytes, 21 rows)
7. flood_validation_reference_matrix.parquet
   SHA-256: 1c87db6ee76bb53e77fe7847c5417aebe408b0ae49a756b1076f6fbca2c09ea5 (48,020 bytes, 1,170 rows)
8. flood_evidence_evaluation_metrics.parquet
   SHA-256: 152c46a6c89e240ce44d2d6657252066fa48ba97412e8417c490a612501a340b (11,280 bytes, 7 rows)
```

---

## 9. Explicit Scientific Limitations

1. **Study Boundary Status:** The 1,170-cell grid is bounded by a provisional coordinate rectangle ($77.45^\circ - 77.75^\circ\text{E}, 12.85^\circ - 13.15^\circ\text{N}$) in EPSG:6933. It remains tagged as `pending_authoritative_boundary` awaiting official Bruhat Bengaluru Mahanagara Palike (BBMP) administrative vector boundaries.
2. **Forecast Resolution Limitation:** Numerical weather prediction grids (~9–10 km native resolution) cannot resolve microscale urban convective cells ($1–2\text{ km}$). Spatial downscaling provides interpolated guidance, not local convective initiation.
3. **Severe Observation Censorship:** Over $98\%$ of the urban study domain lacks automated flood-depth monitoring. Citizen reports and emergency call logs suffer from severe reporting bias toward affluent and high-traffic corridors.
4. **Proxy Negative Limitation:** High-ground weather stations verify only that ridges did not flood; they do not establish that neighboring unmonitored valley bottoms remained dry.
5. **Urban SAR Physical Limits:** C-band SAR backscatter suffers from corner reflections (building-ground double bounces) that mask standing water on urban streets. Reliable SAR flood mapping in high-density urban areas requires high-resolution X-band or multi-temporal interferometric coherence (InSAR) methods.

---

## 10. Recommended Next Steps

1. **Ingest Authoritative Administrative Boundary:** Replace the rectangular provisional bounding box with official BBMP ward-level vector polygons to eliminate edge-cell distortion.
2. **Deploy Automated Urban Water-Level Telemetry:** Partner with local civic authorities to install ultrasonic or pressure transducer water-level sensors in chronic flood hotspots and storm drain culverts.
3. **Acquire High-Resolution X-band / L-band SAR:** Supplement Sentinel-1 with high-resolution radar (e.g., TerraSAR-X, COSMO-SkyMed, or NISAR) to penetrate urban street canyons and overcome double-bounce backscatter masking.
4. **Develop Physically Based Hydraulic 1D/2D Routing:** Integrate shallow water equation hydrodynamic models (e.g., EPA-SWMM or LISFLOOD-FP) forced by 0–24h NWP rainfall forecasts to simulate street-level inundation depths.
5. **Revisit Gate B Supervised Modeling:** Once at least 50 verified flood incidents and 50 instrumented negative valley locations are monitored over 3+ monsoon seasons, re-evaluate Gate B for machine learning model training.

