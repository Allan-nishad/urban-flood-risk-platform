"""Phase 3 Exploratory Modeling Module.

Provides reproducible, un-trained, and unsupervised exploratory modeling algorithms:
1. Feature preparation & standardization (strict separation of static, dynamic, and target probes)
2. Isolation Forest anomaly scoring across multiple contamination settings and seeds
3. Regularized Mahalanobis Distance for multivariate atypicality detection
4. Transparent physical baselines and Multi-Criteria Decision Analysis (MCDA)
5. Comprehensive model comparison dataset generation
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.covariance import LedoitWolf
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def prepare_phase3_features(
    df_integrated: pd.DataFrame,
    output_path: Optional[str] = "data/processed/phase3_model_features.parquet",
) -> pd.DataFrame:
    """Prepare and standardize model-ready feature datasets with strict provenance tags.
    
    Separates:
    - Group A: Static Terrain (SRTM 30m DEM)
    - Group B: Land Cover (ESA WorldCover 10m)
    - Group C: Dynamic Rainfall (GPM IMERG V07B - Partially Verified)
    - Target Probe: Historical Flood Incidents (strictly excluded from predictors)
    """
    df = df_integrated.copy()

    # Define predictor feature groups
    terrain_cols = [
        "elevation_mean_m", "elevation_min_m", "elevation_max_m", "elevation_std_m"
    ]
    landcover_cols = [
        "built_up_fraction", "tree_cover_fraction", "cropland_fraction",
        "water_fraction", "grassland_fraction", "shrubland_fraction"
    ]
    rainfall_cols = [
        "rainfall_daily_depth_mm", "precip_antecedent_3d_mm",
        "precip_antecedent_7d_mm", "precip_antecedent_14d_mm",
        "precip_api_decay_mm"
    ]
    all_predictors = terrain_cols + landcover_cols + rainfall_cols

    # Standardize predictors (z-score)
    scaler = StandardScaler()
    scaled_matrix = scaler.fit_transform(df[all_predictors].fillna(0.0))
    for i, col in enumerate(all_predictors):
        df[f"z_{col}"] = scaled_matrix[:, i].astype(np.float32)

    # Document scaling parameters
    scaling_params = {
        col: {"mean": float(scaler.mean_[i]), "std": float(scaler.scale_[i])}
        for i, col in enumerate(all_predictors)
    }
    df.attrs["scaling_params"] = scaling_params

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out_p, index=False)
        print(f"Saved model features to {output_path} ({len(df):,} rows, {len(df.columns)} columns)")

    return df


def run_isolation_forest(
    df_features: pd.DataFrame,
    features: Optional[List[str]] = None,
    contaminations: Tuple[float, ...] = (0.01, 0.02, 0.05, 0.10),
    random_seeds: Tuple[int, ...] = (42, 100, 2022),
    default_contamination: float = 0.05,
    default_seed: int = 42,
    output_path: Optional[str] = "data/processed/phase3_isolation_forest_results.parquet",
) -> pd.DataFrame:
    """Train unsupervised Isolation Forest models across multiple contamination rates and seeds.
    
    Evaluates anomaly stability across random seeds and contamination hyperparameters.
    """
    if features is None:
        features = [
            "elevation_mean_m", "elevation_std_m", "built_up_fraction",
            "water_fraction", "tree_cover_fraction", "cropland_fraction",
            "rainfall_daily_depth_mm", "precip_api_decay_mm"
        ]

    df_out = df_features[["grid_id", "date", "col_idx", "row_idx", "centroid_lon", "centroid_lat", "has_reported_incident_on_date"]].copy()
    X = df_features[features].values

    # Primary model (default seed 42, default contamination 0.05)
    iso_primary = IsolationForest(
        n_estimators=100,
        contamination=default_contamination,
        random_state=default_seed,
        n_jobs=-1
    )
    raw_scores = iso_primary.fit(X).decision_function(X) # Higher = normal, lower = anomalous
    
    # Invert so higher score = higher anomaly, normalize to [0, 1]
    raw_min, raw_max = raw_scores.min(), raw_scores.max()
    norm_anomaly_score = (raw_max - raw_scores) / (raw_max - raw_min) if raw_max > raw_min else np.zeros_like(raw_scores)
    df_out["isolation_forest_raw_score"] = raw_scores.astype(np.float32)
    df_out["isolation_forest_anomaly_score"] = norm_anomaly_score.astype(np.float32)
    df_out["isolation_forest_rank"] = pd.Series(df_out["isolation_forest_anomaly_score"]).rank(ascending=False, method="min").astype(int)
    df_out["isolation_forest_is_anomaly"] = iso_primary.predict(X) == -1

    # Contamination sensitivity grid
    for c in contaminations:
        iso_c = IsolationForest(n_estimators=100, contamination=c, random_state=default_seed, n_jobs=-1)
        df_out[f"if_is_anomaly_c_{int(c*100):02d}pct"] = iso_c.fit_predict(X) == -1

    # Seed stability grid
    for s in random_seeds:
        iso_s = IsolationForest(n_estimators=100, contamination=default_contamination, random_state=s, n_jobs=-1)
        raw_s = iso_s.fit(X).decision_function(X)
        s_min, s_max = raw_s.min(), raw_s.max()
        norm_s = (s_max - raw_s) / (s_max - s_min) if s_max > s_min else np.zeros_like(raw_s)
        df_out[f"if_score_seed_{s}"] = norm_s.astype(np.float32)
        df_out[f"if_rank_seed_{s}"] = pd.Series(norm_s).rank(ascending=False, method="min").astype(int)

    # Compute seed rank stability metric (Spearman rank correlation across seeds)
    seed_ranks = [df_out[f"if_rank_seed_{s}"] for s in random_seeds]
    seed_corr_matrix = pd.DataFrame(seed_ranks).T.corr(method="spearman")
    df_out.attrs["seed_correlation_matrix"] = seed_corr_matrix.to_dict()

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_parquet(out_p, index=False)
        print(f"Saved Isolation Forest results to {output_path} ({len(df_out):,} rows)")

    return df_out


def run_mahalanobis_distance(
    df_features: pd.DataFrame,
    features: Optional[List[str]] = None,
    regularization_eps: float = 1e-4,
    output_path: Optional[str] = "data/processed/phase3_mahalanobis_results.parquet",
) -> pd.DataFrame:
    """Calculate regularized Mahalanobis distance for multivariate atypicality detection.
    
    Uses Ledoit-Wolf shrinkage covariance estimation to prevent singularity
    from collinear landcover features, ensuring positive-definite inversion.
    """
    if features is None:
        features = [
            "elevation_mean_m", "elevation_std_m", "built_up_fraction",
            "water_fraction", "tree_cover_fraction", "cropland_fraction",
            "rainfall_daily_depth_mm", "precip_api_decay_mm"
        ]

    df_out = df_features[["grid_id", "date", "col_idx", "row_idx", "centroid_lon", "centroid_lat", "has_reported_incident_on_date"]].copy()
    X = df_features[features].values
    p_dim = len(features)

    # Robust regularized covariance via Ledoit-Wolf shrinkage
    lw = LedoitWolf()
    lw.fit(X)
    mean_vec = lw.location_
    cov_matrix = lw.covariance_

    # Additional ridge safeguard to guarantee condition number stability
    cov_reg = cov_matrix + regularization_eps * np.eye(p_dim)
    inv_cov = np.linalg.inv(cov_reg)

    diff = X - mean_vec
    # D_M^2 = sum_j sum_k diff_j * inv_cov_jk * diff_k
    sq_mahalanobis = np.sum((diff @ inv_cov) * diff, axis=1)
    sq_mahalanobis = np.maximum(sq_mahalanobis, 0.0) # Ensure non-negative
    mahalanobis_dist = np.sqrt(sq_mahalanobis)

    # Chi-squared CDF percentile (theoretical p-value of atypicality)
    p_values = 1.0 - stats.chi2.cdf(sq_mahalanobis, df=p_dim)
    atypicality_percentile = stats.chi2.cdf(sq_mahalanobis, df=p_dim)

    # Normalize Mahalanobis distance to [0, 1] for visual and ranking comparison
    d_min, d_max = mahalanobis_dist.min(), mahalanobis_dist.max()
    norm_mahalanobis = (mahalanobis_dist - d_min) / (d_max - d_min) if d_max > d_min else np.zeros_like(mahalanobis_dist)

    df_out["mahalanobis_sq_distance"] = sq_mahalanobis.astype(np.float32)
    df_out["mahalanobis_distance"] = mahalanobis_dist.astype(np.float32)
    df_out["mahalanobis_normalized_score"] = norm_mahalanobis.astype(np.float32)
    df_out["mahalanobis_atypicality_percentile"] = atypicality_percentile.astype(np.float32)
    df_out["mahalanobis_p_value"] = p_values.astype(np.float32)
    df_out["mahalanobis_rank"] = pd.Series(norm_mahalanobis).rank(ascending=False, method="min").astype(int)

    df_out.attrs["covariance_condition_number"] = float(np.linalg.cond(cov_reg))
    df_out.attrs["ledoit_wolf_shrinkage"] = float(lw.shrinkage_)

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_parquet(out_p, index=False)
        print(f"Saved Mahalanobis results to {output_path} (Condition number: {df_out.attrs['covariance_condition_number']:.2f})")

    return df_out


def run_transparent_baselines_and_mcda(
    df_features: pd.DataFrame,
    output_path: Optional[str] = "data/processed/phase3_mcda_results.parquet",
) -> pd.DataFrame:
    """Compute transparent domain baselines and Multi-Criteria Decision Analysis (MCDA).
    
    1. Terrain Baseline: Topographic depression + flatness proxy
    2. Dynamic Rainfall Baseline: Daily depth + API decay
    3. MCDA Schemes: Equal-weight, Terrain-dominant, Runoff-dominant
    """
    df_out = df_features[["grid_id", "date", "col_idx", "row_idx", "centroid_lon", "centroid_lat", "has_reported_incident_on_date"]].copy()

    # 1. Topographic Susceptibility Baseline
    e = df_features["elevation_mean_m"]
    e_std = df_features["elevation_std_m"]
    e_norm = (e - e.min()) / (e.max() - e.min())
    std_norm = (e_std - e_std.min()) / (e_std.max() - e_std.min())
    s_terrain = (0.60 * (1.0 - e_norm) + 0.40 * (1.0 - std_norm)).clip(0.0, 1.0)
    df_out["baseline_terrain_susceptibility"] = s_terrain.astype(np.float32)
    df_out["baseline_terrain_rank"] = s_terrain.rank(ascending=False, method="min").astype(int)

    # 2. Land Cover Runoff Potential
    b = df_features["built_up_fraction"]
    w = df_features["water_fraction"]
    veg = df_features["tree_cover_fraction"] + df_features["cropland_fraction"]
    lc_raw = 0.75 * b + 0.25 * w - 0.20 * veg
    s_landcover = ((lc_raw - lc_raw.min()) / (lc_raw.max() - lc_raw.min())).clip(0.0, 1.0)
    df_out["baseline_landcover_runoff"] = s_landcover.astype(np.float32)

    # 3. Dynamic Meteorological Exposure Baseline
    p_daily = df_features["rainfall_daily_depth_mm"]
    api = df_features["precip_api_decay_mm"]
    p_norm = (p_daily / 150.0).clip(0.0, 1.0)
    api_norm = (api / 250.0).clip(0.0, 1.0)
    s_rainfall = (0.55 * p_norm + 0.45 * api_norm).clip(0.0, 1.0)
    df_out["baseline_rainfall_exposure"] = s_rainfall.astype(np.float32)
    df_out["baseline_rainfall_rank"] = s_rainfall.rank(ascending=False, method="min").astype(int)

    # 4. Multi-Criteria Decision Analysis (MCDA) Scoring Configurations
    # Config 1: Equal-Weight
    mcda_equal = ((1.0 / 3.0) * s_terrain + (1.0 / 3.0) * s_landcover + (1.0 / 3.0) * s_rainfall).clip(0.0, 1.0)
    df_out["mcda_score_equal_weight"] = mcda_equal.astype(np.float32)
    df_out["mcda_rank_equal_weight"] = mcda_equal.rank(ascending=False, method="min").astype(int)

    # Config 2: Terrain-Dominant
    mcda_terrain = (0.50 * s_terrain + 0.25 * s_landcover + 0.25 * s_rainfall).clip(0.0, 1.0)
    df_out["mcda_score_terrain_dominant"] = mcda_terrain.astype(np.float32)
    df_out["mcda_rank_terrain_dominant"] = mcda_terrain.rank(ascending=False, method="min").astype(int)

    # Config 3: Runoff-Dominant
    mcda_runoff = (0.20 * s_terrain + 0.40 * s_landcover + 0.40 * s_rainfall).clip(0.0, 1.0)
    df_out["mcda_score_runoff_dominant"] = mcda_runoff.astype(np.float32)
    df_out["mcda_rank_runoff_dominant"] = mcda_runoff.rank(ascending=False, method="min").astype(int)

    # MCDA Sensitivity Spread across configurations
    mcda_max = np.maximum(np.maximum(mcda_equal, mcda_terrain), mcda_runoff)
    mcda_min = np.minimum(np.minimum(mcda_equal, mcda_terrain), mcda_runoff)
    df_out["mcda_sensitivity_spread"] = (mcda_max - mcda_min).astype(np.float32)

    # Retain unavailable indicators explicitly
    df_out["mcda_hydro_upa_status"] = "UNAVAILABLE_PENDING_ACQUISITION"
    df_out["mcda_sar_change_status"] = "UNAVAILABLE_SYNTHETIC_ONLY"

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_out.to_parquet(out_p, index=False)
        print(f"Saved MCDA results to {output_path} ({len(df_out):,} rows)")

    return df_out


def assemble_phase3_comparison(
    df_features: pd.DataFrame,
    df_iso: pd.DataFrame,
    df_maha: pd.DataFrame,
    df_mcda: pd.DataFrame,
    output_path: Optional[str] = "data/processed/phase3_model_comparison.parquet",
) -> pd.DataFrame:
    """Assemble master multi-model comparison dataset aligning scores, ranks, and incidents."""
    # Key merge columns
    keys = ["grid_id", "date"]

    df_comp = df_features[[
        "grid_id", "date", "col_idx", "row_idx", "centroid_lon", "centroid_lat",
        "elevation_mean_m", "built_up_fraction", "rainfall_daily_depth_mm", "precip_api_decay_mm",
        "has_reported_incident_on_date", "incident_ids_on_date", "incident_categories_on_date"
    ]].copy()

    # Isolation Forest features
    iso_cols = [c for c in df_iso.columns if c.startswith("isolation_forest_")]
    df_comp = df_comp.merge(df_iso[keys + iso_cols], on=keys, how="left")

    # Mahalanobis features
    maha_cols = ["mahalanobis_distance", "mahalanobis_normalized_score", "mahalanobis_atypicality_percentile", "mahalanobis_rank"]
    df_comp = df_comp.merge(df_maha[keys + maha_cols], on=keys, how="left")

    # MCDA & Baseline features
    mcda_cols = [
        "baseline_terrain_susceptibility", "baseline_rainfall_exposure",
        "mcda_score_equal_weight", "mcda_score_terrain_dominant",
        "mcda_score_runoff_dominant", "mcda_rank_runoff_dominant",
        "mcda_sensitivity_spread"
    ]
    df_comp = df_comp.merge(df_mcda[keys + mcda_cols], on=keys, how="left")

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_comp.to_parquet(out_p, index=False)
        print(f"Saved master model comparison to {output_path} ({len(df_comp):,} rows, {len(df_comp.columns)} columns)")

    return df_comp

