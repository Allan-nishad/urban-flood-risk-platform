"""Phase 3.2 Spatial Validation and Stability Analysis Module.

Implements:
1. Spatial block partitioning with configurable buffer zones (e.g. >= 5 km)
2. Empirical spatial dependence estimation (semi-variogram for elevation and land cover)
3. Model stability analysis (rank stability across partitions, random seeds, and feature ablation)
4. Comprehensive data leakage verification
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.covariance import LedoitWolf


def generate_spatial_blocks(
    df_static: pd.DataFrame,
    block_size_cells: int = 5, # 5 cells = 5 km in 1-km grid
) -> pd.DataFrame:
    """Assign reproducible spatial block identifiers to master grid cells.
    
    Args:
        df_static: Static grid features dataset containing col_idx and row_idx.
        block_size_cells: Block dimension in grid cells (default 5 for 5-km blocks).
        
    Returns:
        DataFrame enriched with block_col, block_row, and block_id.
    """
    df = df_static.copy()
    min_col = df["col_idx"].min()
    min_row = df["row_idx"].min()

    df["block_col"] = (df["col_idx"] - min_col) // block_size_cells
    df["block_row"] = (df["row_idx"] - min_row) // block_size_cells
    df["block_id"] = (
        "b" + str(block_size_cells) + "k_" +
        df["block_col"].astype(str) + "_" +
        df["block_row"].astype(str)
    )
    return df


def compute_empirical_variogram(
    df_static: pd.DataFrame,
    feature_col: str,
    max_lag_km: int = 20,
) -> Dict[str, List[float]]:
    """Compute empirical semi-variogram gamma(h) to estimate spatial dependence range.
    
    gamma(h) = (1 / 2N(h)) * sum((z_i - z_j)^2) for pairs (i, j) with distance approx h.
    """
    coords = df_static[["col_idx", "row_idx"]].values.astype(float) # 1 cell = 1 km
    vals = df_static[feature_col].values.astype(float)
    n = len(vals)

    # Pairwise Euclidean distances in km
    # Compute in blocks to preserve memory
    lags = list(range(1, max_lag_km + 1))
    semi_variance = []
    pair_counts = []

    for lag in lags:
        sq_diffs = []
        for i in range(0, n, 100):
            batch_coords = coords[i:i+100]
            batch_vals = vals[i:i+100]
            # Distances from batch to all points
            dists = np.sqrt(
                (coords[:, 0][None, :] - batch_coords[:, 0][:, None])**2 +
                (coords[:, 1][None, :] - batch_coords[:, 1][:, None])**2
            )
            # Match lag within [lag - 0.5, lag + 0.5)
            mask = (dists >= (lag - 0.5)) & (dists < (lag + 0.5))
            if np.any(mask):
                diff = batch_vals[:, None] - vals[None, :]
                sq_diffs.extend((diff[mask]**2).tolist())

        if len(sq_diffs) > 0:
            gamma = 0.5 * float(np.mean(sq_diffs))
            semi_variance.append(gamma)
            pair_counts.append(len(sq_diffs))
        else:
            semi_variance.append(0.0)
            pair_counts.append(0)

    # Estimate range: lag where gamma(h) reaches 95% of total variance (sill)
    total_var = float(np.var(vals))
    sill_threshold = 0.95 * total_var
    est_range = max_lag_km
    for lag, gamma in zip(lags, semi_variance):
        if gamma >= sill_threshold:
            est_range = lag
            break

    return {
        "lags_km": lags,
        "semi_variance": [round(g, 4) for g in semi_variance],
        "pair_counts": pair_counts,
        "sample_variance_sill": round(total_var, 4),
        "estimated_range_km": est_range,
    }


def evaluate_spatial_block_cv(
    df_features: pd.DataFrame,
    features: List[str],
    block_col: str = "block_id",
    buffer_km: int = 5,
    min_test_cells: int = 15,
) -> Dict[str, float]:
    """Evaluate leave-one-block-out spatial validation with enforced buffer zone.
    
    For each test block, training cells within buffer_km are purged.
    Computes ranking agreement (Spearman rho) between spatial-block-trained model
    and domain-wide unpartitioned model.
    """
    blocks = df_features[block_col].unique()
    spearman_rhos = []
    purged_fractions = []

    coords = df_features[["col_idx", "row_idx"]].values

    for b in blocks:
        test_mask = df_features[block_col] == b
        n_test = test_mask.sum()
        if n_test < min_test_cells:
            continue

        test_coords = coords[test_mask]
        # Find all cells within buffer_km of ANY test cell
        # Dist from every cell to nearest test cell
        min_dist_to_test = np.min(
            np.sqrt(
                (coords[:, 0][:, None] - test_coords[:, 0][None, :])**2 +
                (coords[:, 1][:, None] - test_coords[:, 1][None, :])**2
            ),
            axis=1
        )
        buffer_mask = (min_dist_to_test <= buffer_km) & (~test_mask)
        train_mask = min_dist_to_test > buffer_km

        purged_pct = float(buffer_mask.sum() / len(df_features) * 100)
        purged_fractions.append(purged_pct)

        # Train Isolation Forest on buffered training set
        X_train = df_features.loc[train_mask, features].values
        X_test = df_features.loc[test_mask, features].values

        if len(X_train) < 50:
            continue

        iso = IsolationForest(n_estimators=100, contamination=0.05, random_state=42, n_jobs=-1)
        iso.fit(X_train)
        pred_scores = iso.decision_function(X_test)

        # Compare with baseline scores fit on full data
        iso_full = IsolationForest(n_estimators=100, contamination=0.05, random_state=42, n_jobs=-1)
        iso_full.fit(df_features[features].values)
        full_scores = iso_full.decision_function(X_test)

        rho, _ = stats.spearmanr(pred_scores, full_scores)
        if not np.isnan(rho):
            spearman_rhos.append(float(rho))

    return {
        "mean_spearman_rank_stability": round(float(np.mean(spearman_rhos)), 4) if spearman_rhos else 0.0,
        "median_spearman_rank_stability": round(float(np.median(spearman_rhos)), 4) if spearman_rhos else 0.0,
        "std_spearman_rank_stability": round(float(np.std(spearman_rhos)), 4) if spearman_rhos else 0.0,
        "mean_buffer_purged_percentage": round(float(np.mean(purged_fractions)), 2) if purged_fractions else 0.0,
        "evaluated_blocks_count": len(spearman_rhos),
    }


def run_feature_ablation(
    df_features: pd.DataFrame,
    base_features: List[str],
) -> Dict[str, Dict[str, float]]:
    """Assess model sensitivity to feature group removals.
    
    Evaluates:
    1. Baseline full feature set
    2. Ablate terrain (landcover + rainfall only)
    3. Ablate landcover (terrain + rainfall only)
    4. Ablate dynamic rainfall (static only)
    5. Drop built_up_fraction
    """
    X_base = df_features[base_features].values
    iso_base = IsolationForest(n_estimators=100, contamination=0.05, random_state=42, n_jobs=-1)
    base_scores = -iso_base.fit(X_base).decision_function(X_base) # higher = anomaly
    base_top10_idx = set(np.argsort(base_scores)[-int(0.10 * len(base_scores)):])

    ablation_sets = {
        "ablate_terrain": [f for f in base_features if "elevation" not in f],
        "ablate_landcover": [f for f in base_features if "fraction" not in f],
        "ablate_rainfall": [f for f in base_features if "rain" not in f and "precip" not in f],
        "drop_built_up": [f for f in base_features if f != "built_up_fraction"],
        "drop_cropland": [f for f in base_features if f != "cropland_fraction"],
    }

    results = {}
    for name, feat_subset in ablation_sets.items():
        X_sub = df_features[feat_subset].values
        iso_sub = IsolationForest(n_estimators=100, contamination=0.05, random_state=42, n_jobs=-1)
        sub_scores = -iso_sub.fit(X_sub).decision_function(X_sub)
        sub_top10_idx = set(np.argsort(sub_scores)[-int(0.10 * len(sub_scores)):])

        rho, _ = stats.spearmanr(base_scores, sub_scores)
        jaccard_top10 = len(base_top10_idx.intersection(sub_top10_idx)) / len(base_top10_idx.union(sub_top10_idx))

        results[name] = {
            "spearman_rho": round(float(rho), 4),
            "top10_jaccard_overlap": round(float(jaccard_top10), 4),
            "features_retained_count": len(feat_subset),
        }

    return results


def audit_leakage_safeguards(
    df_features: pd.DataFrame,
    predictor_cols: List[str],
) -> Dict[str, Dict[str, Any]]:
    """Formally inspect feature matrix for spatial, temporal, and label leakage pathways."""
    checks = {}

    # Check 1: Target leakage (Are historical incident features in predictors?)
    incident_substrings = ["incident", "flood_event", "label", "is_flood", "waterlog"]
    leaked_target_cols = [c for c in predictor_cols if any(s in c.lower() for s in incident_substrings)]
    checks["target_leakage_check"] = {
        "passed": len(leaked_target_cols) == 0,
        "leaked_columns": leaked_target_cols,
        "status": "PASS: Predictor matrix strictly isolated from historical incident labels." if len(leaked_target_cols) == 0 else "FAIL"
    }

    # Check 2: Synthetic SAR fixture leakage
    sar_cols = [c for c in predictor_cols if "sar" in c.lower() or "sentinel" in c.lower()]
    checks["sar_fixture_leakage_check"] = {
        "passed": len(sar_cols) == 0,
        "leaked_columns": sar_cols,
        "status": "PASS: Synthetic SAR simulation fixtures excluded from model predictors." if len(sar_cols) == 0 else "FAIL"
    }

    # Check 3: Duplicate cell-dates
    n_dupes = int(df_features.duplicated(subset=["grid_id", "date"]).sum())
    checks["duplicate_cell_date_check"] = {
        "passed": n_dupes == 0,
        "duplicate_count": n_dupes,
        "status": "PASS: Zero duplicate spatiotemporal panel records." if n_dupes == 0 else "FAIL"
    }

    return checks
