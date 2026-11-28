# Machine Learning Training & Evaluation (`src/floodrisk/ml/`)

> **Important Distinction:** The operational dashboard alerts and risk scores are **rule-based / multi-criteria** (`rules.py`, `dynamic_risk.py`, `risk_engine.py`), **NOT** driven by ML. The ML pipeline is strictly **experimental** (`EXPERIMENTAL_UNVALIDATED`, `BLOCKED_EXPERIMENTAL_MODEL`).

---

## 8. Implemented Machine-Learning Algorithms (`src/floodrisk/ml/train.py`)

Four binary classification models are implemented and compared on the exact same **48 labeled event-grid records** (**34 positive** flood records, **14 proxy-negative** records; `9,312` unobserved rows are excluded):

| Algorithm | Library / Pipeline | Key Hyperparameters (Manually Configured) |
| :--- | :--- | :--- |
| **Logistic Regression** | `Pipeline(SimpleImputer('median'), StandardScaler, LogisticRegression)` | `class_weight='balanced'`, `max_iter=1000`, `random_state=42` |
| **Random Forest** *(Selected)* | `Pipeline(SimpleImputer('median'), RandomForestClassifier)` | `n_estimators=100`, `max_depth=4`, `class_weight='balanced'`, `random_state=42` |
| **HistGradientBoosting** | `HistGradientBoostingClassifier` | `max_depth=3`, `min_samples_leaf=5`, `max_iter=100`, `random_state=42` |
| **XGBoost** | `xgb.XGBClassifier` | `n_estimators=80`, `max_depth=3`, `learning_rate=0.05`, `eval_metric='logloss'`, `random_state=42` |

- **14 Input Features (`FEATURE_COLUMNS` in `features.py`):** `elevation_m`, `slope_deg`, `upstream_contributing_area_km2`, `topographic_wetness_index`, `depression_depth_m`, `is_closed_sink`, `built_up_fraction`, `tree_cover_fraction`, `cropland_fraction`, `water_fraction`, `era5_rain_24h_pre_mm`, `era5_rain_72h_pre_mm`, `era5_api_7d_pre_mm`, `era5_pre_missing_flag`.
- **How Random Forest Works:** Trains 100 shallow decision trees (`max_depth=4`) on bootstrap samples of the 48 records using balanced class weights, then averages their predicted class probabilities across all 100 trees to reduce variance.
- **Model Version & Storage:** `v8.0-exp-rf-20261127` saved at `models/v8_experimental/flood_risk_model_v8_exp.joblib` and `models/v8_experimental/model_metadata.json`.

---

## 9. Training, Validation & Hyperparameter Tuning

- **Hyperparameter Tuning:** **No** `GridSearchCV` or `RandomizedSearchCV` was used; shallow regularized hyperparameters (`max_depth=3..4`, `n_estimators=80..100`) were **manually configured** to limit overfitting on 48 samples.
- **Leakage Prevention:** `FORBIDDEN_LEAKAGE_COLS` (`flood_label`, `sar_delta_vv_db`, `era5_rain_during_event_mm`, `grid_id`, etc.) are blocked by assertion in `prepare_ml_dataset()`. Pre-event ERA5-Land rainfall strictly uses `< event_start_utc`.
- **Spatial-Block CV:** 5-fold `GroupKFold` grouped by `grid_id` (`_evaluate_spatial_group_cv`), ensuring the same cell never appears in both train and test folds.
- **Temporal Holdout:** Trains on `2020–2022` records (`45` rows: 31 pos, 14 neg) and tests on `2023–2025` (`3` positive records, `0` negative controls).

---

## 10. Verified Evaluation Results (from `models/v8_experimental/model_metadata.json`)

| Model / Baseline | Spatial CV ROC-AUC | Spatial CV PR-AUC | F1 | Precision | Recall | Brier | Confusion Matrix (`TN/FP/FN/TP`) | Temporal 2023–2025 Recall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random Forest (`v8.0-exp-rf-20261127`)** | **0.8382** | **0.9232** | **0.8696** | 0.8571 | 0.8824 | 0.1425 | `9 / 5 / 4 / 30` | **0.3333** (1/3) |
| **XGBoost** | 0.7668 | 0.9004 | 0.8169 | 0.7838 | 0.8529 | 0.1987 | `6 / 8 / 5 / 29` | 0.3333 |
| **HistGradientBoosting** | 0.6922 | 0.8339 | 0.8493 | 0.7949 | 0.9118 | 0.2077 | `6 / 8 / 3 / 31` | 0.3333 |
| **Logistic Regression** | 0.8067 | 0.8264 | 0.8955 | 0.9091 | 0.8824 | 0.1260 | `11 / 3 / 4 / 30` | 0.0000 |
| *Static MCDA Baseline* | 0.6113 | 0.8144 | 0.7606 | 0.7297 | 0.7941 | 0.2177 | `4 / 10 / 7 / 27` | N/A |

- **Top Random Forest Feature Importances:** `cropland_fraction` (`0.2081`), `elevation_m` (`0.1865`), `slope_deg` (`0.1423`), `topographic_wetness_index` (`0.1339`), `built_up_fraction` (`0.0853`), `water_fraction` (`0.0673`), `tree_cover_fraction` (`0.0656`).
- **Why Spatial CV (0.8382) and Temporal Holdout (0.3333) Differ:** Spatial CV tests on `2020–2022` events where all 14 negative controls sit on high-ground stations in one episode (`EG_2022_08_09_MONSOON`), making spatial separation easy. Temporal holdout tests on `2023–2025` (only 3 positives, 0 negatives), exposing generalization limits across new years/storm regimes. Therefore, the model remains **`EXPERIMENTAL_UNVALIDATED` / `BLOCKED_EXPERIMENTAL_MODEL`**.
