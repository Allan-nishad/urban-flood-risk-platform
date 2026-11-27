# V8 STAGE 3: EXPERIMENTAL AI/ML DEVELOPMENT & VALIDATION REPORT

**Branch:** `upgrade/v8-operational-ai`  
**Qualification Status:** `EXPERIMENTAL_UNVALIDATED`  
**Warning Gate:** `BLOCKED_EXPERIMENTAL_MODEL`  
**Model Artifact:** `models/v8_experimental/flood_risk_model_v8_exp.joblib` (`v8.0-exp-rf-20261127`)  
**Metadata Artifact:** `models/v8_experimental/model_metadata.json` (`trained_at_utc: 2026-11-27T04:54:53Z`)

---

## 1. Executive Summary & Scientific Restrictions

Stage 3 implemented a reproducible, leakage-free experimental ML training, validation, serialization, and gated inference pipeline on top of the Stage 2 multi-event dataset (`data/phase8/flood_event_grid_dataset.parquet`).

**Key scientific conclusion:** Although candidate models outperform static MCDA and simple ERA5-24h threshold baselines under 5-fold spatial-block cross-validation (`GroupKFold(grid_id)`), **the model remains strictly `EXPERIMENTAL_UNVALIDATED` and `BLOCKED_EXPERIMENTAL_MODEL` for operational alerting** because:
1. **LOEGO Binary Validation is Infeasible:** Grouping `EP_2022_08_30` and `EP_2022_09_05` into a single continuous late-Aug/early-Sep 2022 meteorological episode (`EG_2022_08_09_MONSOON`) leaves only **1 event group** containing negative controls (`14` `PROXY_NEGATIVE` records, `0` verified negatives across other event groups).
2. **Poor Temporal Generalization (2023–2025 Holdout):** When trained on pre-2023 data and evaluated on `2023–2025` held-out flood episodes (`3` positive records, `0` negative controls), tree/boosting models (`random_forest`, `hist_gradient_boosting`, `xgboost`) achieve only **33.33% (`1/3`) positive recall** and `logistic_regression` achieves **0.0% (`0/3`)**—reflecting geographic/regime shift from 2022 East/SE Bengaluru events (`cropland_fraction`-correlated) to 2023 Central underpass and 2024 North Yelahanka events.

---

## 2. Event Independence & Negative-Control Audit

1. **Event-Group Consolidation (`EVENT_GROUP_MAP` in `src/floodrisk/ml/features.py`):**
   - `EP_2022_08_30` and `EP_2022_09_05` are grouped into `EG_2022_08_09_MONSOON`.
   - Across the full Stage 2 event inventory (`8` episodes → `7` canonical event groups), `6` canonical event groups have mapped labeled cells (`EG_2020_10`, `EG_2022_05`, `EG_2022_08_09_MONSOON`, `EG_2023_05`, `EG_2024_10`, `EG_2025_10`; `EP_2025_05_18` has no mapped labeled cells).
2. **Negative-Control Audit:**
   - Retained only the **14 documented `PROXY_NEGATIVE` records** in `EG_2022_08_09_MONSOON`.
   - Zero dry-date negative controls were fabricated for 2020, 2023, 2024, or 2025.
   - `UNOBSERVED` / `UNKNOWN` rows are strictly excluded from training and never coerced to `0`.
3. **Sample Counts (`prepare_ml_dataset`):**
   - `all_labeled`: `48` total (`34` positive, `14` proxy-negative, `0` verified-negative)
   - `confirmed_only`: `44` total (`30` `CONFIRMED_FLOOD`, `14` `PROXY_NEGATIVE`)
   - `dedup_event_group`: `37` total (`30` positive, `7` negative after deduplicating by `(event_group_id, grid_id)`)

---

## 3. Feature Contract & Leakage Prevention

All 14 prediction-time features in `FEATURE_DICTIONARY` (`src/floodrisk/ml/features.py`) are strictly pre-event or static terrain/hydrology/landcover variables:
- **Static terrain (SRTM 30m DEM):** `elevation_m`, `slope_deg`
- **Static hydrology (D8 Flow Routing / DEM Pit):** `upstream_contributing_area_km2`, `topographic_wetness_index`, `depression_depth_m`, `is_closed_sink`
- **Static landcover (ESA WorldCover 10m):** `built_up_fraction`, `tree_cover_fraction`, `cropland_fraction`, `water_fraction`
- **Pre-event reanalysis (Open-Meteo ERA5-Land `< event_start_utc`):** `era5_rain_24h_pre_mm`, `era5_rain_72h_pre_mm`, `era5_api_7d_pre_mm`
- **Missingness indicator:** `era5_pre_missing_flag`

**Leakage Guard (`FORBIDDEN_LEAKAGE_COLS`):** `flood_label`, `evidence_status`, `label_source`, `label_confidence`, `sar_delta_vv_db`, `sar_evidence_state`, `era5_rain_during_event_mm`, `event_id`, `event_group_id`, `grid_id` are explicitly asserted disjoint from `FEATURE_COLUMNS`.

---

## 4. Baselines & Candidate Model Comparison

Evaluated on the `48` labeled records (`34` positive, `14` proxy-negative) using **5-fold spatial-block CV (`GroupKFold(grid_id)`)** and **temporal 2023–2025 positive-recall holdout**:

| Model / Baseline | Precision | Recall | F1 | ROC-AUC | PR-AUC | Brier | FPR | FNR | Temporal 2023–2025 Recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `static_mcda_baseline` | 0.7297 | 0.7941 | 0.7606 | 0.6113 | 0.8144 | 0.2177 | 0.7143 | 0.2059 | N/A |
| `era5_rain_ge_15_6mm_baseline` | 0.5333 | 0.2353 | 0.3265 | 0.3676 | 0.6672 | 0.6875 | 0.5000 | 0.7647 | N/A |
| `logistic_regression` | 0.9091 | 0.8824 | 0.8955 | 0.8067 | 0.8264 | 0.1260 | 0.2143 | 0.1176 | 0.0000 (`0/3`) |
| `random_forest` *(selected)* | 0.8571 | 0.8824 | 0.8696 | 0.8382 | 0.9232 | 0.1425 | 0.3571 | 0.1176 | 0.3333 (`1/3`) |
| `hist_gradient_boosting` | 0.7949 | 0.9118 | 0.8493 | 0.6922 | 0.8339 | 0.2077 | 0.5714 | 0.0882 | 0.3333 (`1/3`) |
| `xgboost` | 0.7838 | 0.8529 | 0.8169 | 0.7668 | 0.9004 | 0.1987 | 0.5714 | 0.1471 | 0.3333 (`1/3`) |

### Sensitivity Analyses (`random_forest`, spatial-block 5-fold CV)
- `confirmed_only` (`n_pos=30, n_neg=14`): Precision `0.8438`, Recall `0.9000`, F1 `0.8710`, ROC-AUC `0.8607`, PR-AUC `0.9137`, Brier `0.1283`
- `dedup_event_group` (`n_pos=30, n_neg=7`): Precision `0.9667`, Recall `0.9667`, F1 `0.9667`, ROC-AUC `0.9119`, PR-AUC `0.9748`, Brier `0.0852`

### Top Feature Importances (`random_forest`)
1. `cropland_fraction`: `0.2081`
2. `elevation_m`: `0.1865`
3. `slope_deg`: `0.1423`
4. `topographic_wetness_index`: `0.1339`
5. `built_up_fraction`: `0.0853`
6. `water_fraction`: `0.0673`

---

## 5. Inference, Qualification Gate, API & UI Integration

- **Inference (`src/floodrisk/ml/infer.py` → `ExperimentalFloodInference`):**
  - Reloads `flood_risk_model_v8_exp.joblib` and `model_metadata.json`.
  - Returns `experimental_score` with `is_calibrated_probability: False`, `qualification_status: "EXPERIMENTAL_UNVALIDATED"`, `warning_gate: "BLOCKED_EXPERIMENTAL_MODEL"`, and explicit `missing_inputs` per record.
  - Raises `ValueError` on empty record lists or missing required feature columns; returns `UNAVAILABLE` / `BLOCKED_MISSING_MODEL` if artifacts are absent.
- **Dashboard API (`src/floodrisk/dashboard/server.py`):**
  - `GET /api/ml/experimental` returns experimental model metadata, baselines, candidate CV/temporal metrics, and qualification gate.
  - `GET /api/ml/experimental?grid_id=<id>` returns cell-level gated inference (`400` on empty `grid_id`, `404` on unknown `grid_id`).
- **Dashboard UI (`src/floodrisk/dashboard/static/index.html`):**
  - Added `#mlExpStatusVal` / `#mlExpStatusDesc` card in `phase6Tab` displaying `EXPERIMENTAL_UNVALIDATED` status, gate, and CV metrics without altering operational MCDA alerts.

---

## 6. Verification & Test Results

- **Stage 3 Test Suite (`tests/test_stage3_ml.py`):** 4 new tests covering event-group independence, `UNOBSERVED` exclusion, subset filtering (`all_labeled`, `confirmed_only`, `dedup_event_group`), leakage guard, serialization/reload in `tmp_path`, `ExperimentalFloodInference` missing-data & error handling, and `/api/ml/experimental` HTTP contract (`200`, `400`, `404`).
- **Full Regression Suite (`.venv\Scripts\python.exe -m pytest tests/ -q`):** **149 passed, 0 failed** (145 existing Stage 1/2/v7.3 tests + 4 Stage 3 tests).
- **Frozen Baseline:** `v7.2.0-FREEZE` and existing risk formulas/weights remain untouched.

---

## 7. Next Gate

Stage 3 is complete and ready for user review before proceeding to **Stage 4**.
