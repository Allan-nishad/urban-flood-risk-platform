"""Reproducible experimental ML training, group-aware validation, and model serialization."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

from .features import FEATURE_COLUMNS, FEATURE_DICTIONARY, prepare_ml_dataset


def _compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> Dict[str, Any]:
    y_pred = (y_prob >= threshold).astype(int)
    n_pos = int((y_true == 1).sum())
    n_neg = int((y_true == 0).sum())
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else None
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else None
    roc_auc = round(float(roc_auc_score(y_true, y_prob)), 4) if (n_pos > 0 and n_neg > 0) else None
    pr_auc = round(float(average_precision_score(y_true, y_prob)), 4) if (n_pos > 0 and n_neg > 0) else None
    brier = round(float(brier_score_loss(y_true, y_prob)), 4) if len(y_true) > 0 else None

    return {
        "n_total": int(len(y_true)),
        "n_pos": n_pos,
        "n_neg": n_neg,
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "brier_score": brier,
        "fpr": round(fpr, 4) if fpr is not None else None,
        "fnr": round(fnr, 4) if fnr is not None else None,
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def _build_candidate_models(seed: int = 42) -> Dict[str, Any]:
    return {
        "logistic_regression": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=seed)),
        ]),
        "random_forest": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("clf", RandomForestClassifier(n_estimators=100, max_depth=4, class_weight="balanced", random_state=seed)),
        ]),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            max_depth=3, min_samples_leaf=5, max_iter=100, random_state=seed
        ),
        "xgboost": xgb.XGBClassifier(
            n_estimators=80, max_depth=3, learning_rate=0.05, random_state=seed, eval_metric="logloss"
        ),
    }


def _assess_calibration_and_uncertainty(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    seed: int = 42,
    n_boot: int = 200,
) -> Dict[str, Any]:
    """Assess out-of-fold probability calibration and bootstrap CI on AUC metrics."""
    if len(y_true) < 10 or len(np.unique(y_true)) < 2:
        return {"status": "INSUFFICIENT_SAMPLE_SIZE", "n_total": int(len(y_true))}
    obs_rate = float(np.mean(y_true))
    pred_mean = float(np.mean(y_prob))
    rng = np.random.default_rng(seed)
    rocs: List[float] = []
    prs: List[float] = []
    n = len(y_true)
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        yt = y_true[idx]
        yp = y_prob[idx]
        if len(np.unique(yt)) < 2:
            continue
        rocs.append(float(roc_auc_score(yt, yp)))
        prs.append(float(average_precision_score(yt, yp)))
    return {
        "status": "EXPLORATORY_SMALL_SAMPLE",
        "n_total": int(n),
        "observed_positive_rate": round(obs_rate, 4),
        "mean_predicted_probability": round(pred_mean, 4),
        "calibration_bias": round(pred_mean - obs_rate, 4),
        "brier_score": round(float(brier_score_loss(y_true, y_prob)), 4),
        "bootstrap_iterations": len(rocs),
        "roc_auc_ci95": [round(float(np.percentile(rocs, 2.5)), 4), round(float(np.percentile(rocs, 97.5)), 4)] if rocs else None,
        "pr_auc_ci95": [round(float(np.percentile(prs, 2.5)), 4), round(float(np.percentile(prs, 97.5)), 4)] if prs else None,
        "note": "Small sample (n=48) and single-group negative controls prevent formal clinical/operational calibration.",
    }


def _evaluate_spatial_group_cv(model_factory, X: pd.DataFrame, y: pd.Series, groups: pd.Series, n_splits: int = 5) -> Dict[str, Any]:
    n_unique_groups = groups.nunique()
    k = min(n_splits, n_unique_groups)
    if k < 2:
        return {"status": "VALIDATION_INSUFFICIENT", "detail": "Fewer than 2 spatial groups"}

    gkf = GroupKFold(n_splits=k)
    oof_probs = np.zeros(len(y), dtype=float)
    for train_idx, test_idx in gkf.split(X, y, groups):
        y_tr = y.iloc[train_idx]
        if y_tr.nunique() < 2:
            return {"status": "VALIDATION_INSUFFICIENT", "detail": "Single-class training fold encountered"}
        clf = model_factory()
        clf.fit(X.iloc[train_idx], y_tr)
        oof_probs[test_idx] = clf.predict_proba(X.iloc[test_idx])[:, 1]

    metrics = _compute_metrics(y.values, oof_probs)
    metrics["calibration_and_uncertainty"] = _assess_calibration_and_uncertainty(y.values, oof_probs)
    return metrics


def _evaluate_temporal_holdout_recall(model_factory, X: pd.DataFrame, y: pd.Series, meta: pd.DataFrame) -> Dict[str, Any]:
    is_future = meta["event_timestamp_utc"].str[:4].isin(["2023", "2024", "2025"])
    is_past = ~is_future
    if y[is_past].nunique() < 2 or is_future.sum() == 0:
        return {"status": "VALIDATION_INSUFFICIENT", "detail": "Insufficient pre/post-2023 split"}
    clf = model_factory()
    clf.fit(X[is_past], y[is_past])
    probs = clf.predict_proba(X[is_future])[:, 1]
    preds = (probs >= 0.5).astype(int)
    return {
        "n_test_future_positives": int((y[is_future] == 1).sum()),
        "n_test_future_negatives": int((y[is_future] == 0).sum()),
        "future_positive_recall": round(float((preds[y[is_future] == 1] == 1).mean()), 4),
        "note": "0 negative controls exist in 2023-2025; only positive recall is measurable.",
    }


def train_and_evaluate_experimental_models(
    dataset_path: Path | str = Path("data/phase8/flood_event_grid_dataset.parquet"),
    dyn_baseline_path: Path | str = Path("data/processed/dynamic_risk_intelligence_bengaluru.parquet"),
    model_dir: Path | str = Path("models/v8_experimental"),
    seed: int = 42,
) -> Dict[str, Any]:
    """Train, compare, validate, and serialize experimental ML flood-risk models."""
    df_raw = pd.read_parquet(dataset_path)
    df_dyn = pd.read_parquet(dyn_baseline_path)
    out_dir = Path(model_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Primary exploratory subset: all 48 labeled records (34 pos + 14 proxy-neg)
    X, y, meta = prepare_ml_dataset(df_raw, subset="all_labeled")

    # Check LOEGO feasibility across canonical event groups
    neg_groups = meta[y == 0]["event_group_id"].nunique()
    pos_groups = meta[y == 1]["event_group_id"].nunique()
    loeo_feasible = bool(neg_groups >= 2 and pos_groups >= 2)

    # Baselines evaluated on the exact same 48 records
    static_map = df_dyn.set_index("grid_id")["static_susceptibility_score"].to_dict()
    mcda_scores = meta["grid_id"].map(static_map).fillna(0.5).values
    rain_24h = X["era5_rain_24h_pre_mm"].fillna(0.0).values
    rain_prob_15_6 = (rain_24h >= 15.6).astype(float)

    baseline_results = {
        "static_mcda_baseline": _compute_metrics(y.values, mcda_scores, threshold=0.5),
        "era5_rain_ge_15_6mm_baseline": _compute_metrics(y.values, rain_prob_15_6, threshold=0.5),
    }

    # Candidate ML models
    candidates = _build_candidate_models(seed=seed)
    model_results: Dict[str, Any] = {}
    best_name = None
    best_pr_auc = -1.0

    for name in candidates:
        spatial_cv = _evaluate_spatial_group_cv(lambda n=name: _build_candidate_models(seed=seed)[n], X, y, meta["grid_id"])
        temp_rec = _evaluate_temporal_holdout_recall(lambda n=name: _build_candidate_models(seed=seed)[n], X, y, meta)
        model_results[name] = {
            "spatial_block_5fold_cv": spatial_cv,
            "temporal_2023_2025_holdout": temp_rec,
        }
        pr = spatial_cv.get("pr_auc") or 0.0
        if pr > best_pr_auc:
            best_pr_auc = pr
            best_name = name

    # Sensitivity experiments (confirmed-only & deduplicated event-group)
    X_conf, y_conf, m_conf = prepare_ml_dataset(df_raw, subset="confirmed_only")
    X_dedup, y_dedup, m_dedup = prepare_ml_dataset(df_raw, subset="dedup_event_group")
    sensitivity = {
        "confirmed_only": {
            "n_pos": int((y_conf == 1).sum()),
            "n_neg": int((y_conf == 0).sum()),
            "random_forest_spatial_cv": _evaluate_spatial_group_cv(
                lambda: _build_candidate_models(seed=seed)["random_forest"], X_conf, y_conf, m_conf["grid_id"]
            ),
        },
        "dedup_event_group": {
            "n_pos": int((y_dedup == 1).sum()),
            "n_neg": int((y_dedup == 0).sum()),
            "random_forest_spatial_cv": _evaluate_spatial_group_cv(
                lambda: _build_candidate_models(seed=seed)["random_forest"], X_dedup, y_dedup, m_dedup["grid_id"]
            ),
        },
    }

    # Fit selected experimental model on all 48 labeled records and serialize
    selected_name = best_name or "random_forest"
    final_pipeline = _build_candidate_models(seed=seed)[selected_name]
    final_pipeline.fit(X, y)

    # Feature importances (if tree-based or linear)
    importances: Dict[str, float] = {}
    est = final_pipeline[-1] if isinstance(final_pipeline, Pipeline) else final_pipeline
    if hasattr(est, "feature_importances_"):
        importances = {col: round(float(val), 4) for col, val in zip(FEATURE_COLUMNS, est.feature_importances_)}
    elif hasattr(est, "coef_"):
        importances = {col: round(float(abs(val)), 4) for col, val in zip(FEATURE_COLUMNS, est.coef_[0])}

    model_version = "v8.0-exp-rf-20261127" if selected_name == "random_forest" else f"v8.0-exp-{selected_name}-20261127"
    data_sha = hashlib.sha256(Path(dataset_path).read_bytes()).hexdigest()[:16] if Path(dataset_path).is_file() else "unknown"
    data_version = f"stage2-event-grid-{len(df_raw)}rows-{data_sha}"
    model_path = out_dir / "flood_risk_model_v8_exp.joblib"
    joblib.dump(final_pipeline, model_path)

    metadata = {
        "model_name": selected_name,
        "model_version": model_version,
        "data_version": data_version,
        "model_artifact_path": str(model_path).replace("\\", "/"),
        "trained_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "random_seed": seed,
        "qualification_status": "EXPERIMENTAL_UNVALIDATED",
        "warning_gate": "BLOCKED_EXPERIMENTAL_MODEL",
        "qualification_reason": (
            f"Trained on {len(y)} labeled records ({int((y==1).sum())} positive, {int((y==0).sum())} proxy-negative). "
            f"Leave-One-Event-Group-Out (LOEGO) binary validation is INFEASIBLE because all {int((y==0).sum())} "
            "proxy-negative records belong to a single event group (EG_2022_08_09_MONSOON)."
        ),
        "event_group_summary": {
            "canonical_event_groups_total": int(meta["event_group_id"].nunique()),
            "positive_event_groups": int(pos_groups),
            "negative_control_event_groups": int(neg_groups),
            "loeo_feasible": loeo_feasible,
        },
        "training_sample_counts": {
            "n_total": int(len(y)),
            "n_positive": int((y == 1).sum()),
            "n_proxy_negative": int((y == 0).sum()),
            "n_verified_negative": 0,
        },
        "feature_columns": FEATURE_COLUMNS,
        "feature_dictionary": FEATURE_DICTIONARY,
        "feature_importances": importances,
        "baselines": baseline_results,
        "candidate_models": model_results,
        "sensitivity_analyses": sensitivity,
    }
    meta_path = out_dir / "model_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata
