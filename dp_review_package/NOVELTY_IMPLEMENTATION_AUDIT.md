# Novelty Implementation Audit

Every claimed contribution is classified strictly from repository code inspection:

| # | Contribution | Status | Code Evidence |
| :--- | :--- | :--- | :--- |
| 1 | **Three-state flood evidence classification** (`VERIFIED_POSITIVE`, `VERIFIED_NEGATIVE`, `UNOBSERVED_DOMAIN_CELL`) | **Implemented** | `data/processed/phase6/flood_evidence/flood_validation_ground_truth_matrix.parquet` (`13` pos, `7` neg, `1150` unobserved); `src/floodrisk/ml/features.py` (never converts unobserved to `0`). |
| 2 | **Independent dynamic risk prioritisation** (non-circular exclusion of flood labels) | **Implemented** | `src/floodrisk/processing/dynamic_risk.py` lines 104–110; `src/floodrisk/alerts/risk_engine.py`. |
| 3 | **Conditional priority tiers instead of flood probabilities** | **Implemented** | `dynamic_risk.py` (`RESEARCH_PRIORITY_*`, `OPTIONAL_UNCALIBRATED_PRIORITIZATION_INDEX`); `risk_engine.py` (`is_calibrated_probability: False`). |
| 4 | **Forecast reliability evaluation** (NWP vs. ground rain gauges) | **Implemented** | `data/processed/phase6/ground_rainfall/gfs_vs_gauge_validation_metrics.parquet` (`16` gauges, `256` pairs, `MAE=18.64 mm`, `bias=-10.88 mm`, `r=0.142`, `POD=0.000`). |
| 5 | **Spatial and temporal model validation** | **Implemented (Experimental ML)** | `src/floodrisk/ml/train.py` (`_evaluate_spatial_group_cv` via 5-fold `GroupKFold`, `_evaluate_temporal_holdout_recall` on `2023–2025`). |
| 6 | **Stateful alert lifecycle** (`ACTIVE` → `ACKNOWLEDGED` → `RESOLVED`/`EXPIRED` + cooldown) | **Implemented** | `src/floodrisk/alerts/engine.py`, `storage.py`, `rules.py` (`120 min` cooldown, `alert_audit_log`). |
| 7 | **Spatial alert clustering** (`~5.5 km` tiles per forecast zone) | **Implemented** | `src/floodrisk/alerts/clustering.py` (`cluster_alerts`, `CLU-{zone_id}-{tile}`). |
| 8 | **Evidence-aware dual-priority hotspot clustering** | **Proposed / Not present** | `clustering.py` groups by `(forecast_zone_id, 0.05° tile)` and `SEVERITY_RANK` only; does not incorporate flood evidence states. |
| 9 | **Forecast-reliability-weighted risk fusion** | **Proposed / Not present** | Phase 6B/7B reliability metrics are reported in `/api/phase6/ground-rainfall`, not dynamically weighted in `dynamic_risk.py` or `risk_engine.py`. |
| 10 | **Temporal risk escalation velocity** | **Partially implemented** | `risk_engine.py` evaluates `1h–72h` horizons and `engine.py` tracks escalation/de-escalation across runs, but no explicit `d(risk)/dt` velocity metric is computed. |
