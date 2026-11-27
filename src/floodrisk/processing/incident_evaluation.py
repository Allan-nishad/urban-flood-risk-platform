"""Phase 3.3 Retrospective Flood Incident Evaluation Module.

Evaluates exploratory model scores and ranks against the historical flood event inventory
using descriptive retrospective metrics:
- Incident rank percentiles
- Top-k% capture/hit rates (Top 5%, Top 10%, Top 20%)
- Distance to nearest high-risk zone
- Stratification by evidence category and source confidence
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


def evaluate_retrospective_incidents(
    df_comparison: pd.DataFrame,
    df_inventory: pd.DataFrame,
    model_score_cols: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Perform descriptive retrospective comparison between model outputs and reported incidents.
    
    Args:
        df_comparison: Master model comparison panel dataset.
        df_inventory: Historical flood incident inventory.
        model_score_cols: List of model score columns to evaluate.
        
    Returns:
        Dictionary containing retrospective metrics, category breakdowns, and baseline comparisons.
    """
    if model_score_cols is None:
        model_score_cols = [
            "isolation_forest_anomaly_score",
            "mahalanobis_normalized_score",
            "baseline_terrain_susceptibility",
            "baseline_rainfall_exposure",
            "mcda_score_equal_weight",
            "mcda_score_runoff_dominant",
        ]

    # Filter inventory to usable geocoded records
    usable_categories = ["confirmed_inundation", "reported_waterlogging", "flood_disruption"]
    df_geo_incidents = df_inventory[df_inventory["evidence_category"].isin(usable_categories)].copy()

    total_records = len(df_inventory)
    eligible_count = len(df_geo_incidents)

    # Convert dates to string for matching
    df_comp = df_comparison.copy()
    df_comp["date_str"] = df_comp["date"].apply(lambda d: d.isoformat() if hasattr(d, "isoformat") else str(d))

    # Match incident cell-dates in comparison panel
    incident_cell_dates = df_comp[df_comp["has_reported_incident_on_date"] == True].copy()
    n_incident_cell_dates = len(incident_cell_dates)

    results_by_model = {}

    for col in model_score_cols:
        # Compute daily percentile ranks for this model
        # Percentile: 100% = highest anomaly / risk, 0% = lowest
        daily_percentiles = []
        hit_top05 = []
        hit_top10 = []
        hit_top20 = []

        # Group by date to evaluate spatial ranking on the specific day of the incident
        for date_str, group in df_comp.groupby("date_str"):
            n_cells = len(group)
            scores = group[col].values
            ranks = pd.Series(scores).rank(ascending=False, method="min").values
            # Percentile: (N - rank + 1) / N * 100
            pcts = ((n_cells - ranks + 1.0) / n_cells) * 100.0

            sub_incidents = group[group["has_reported_incident_on_date"] == True]
            if len(sub_incidents) > 0:
                inc_indices = np.where(group["has_reported_incident_on_date"].values)[0]
                for idx in inc_indices:
                    p = pcts[idx]
                    daily_percentiles.append(p)
                    hit_top05.append(p >= 95.0)
                    hit_top10.append(p >= 90.0)
                    hit_top20.append(p >= 80.0)

        # Distance to nearest top-10% cell on incident date
        distances_km = []
        for date_str, group in df_comp.groupby("date_str"):
            inc_cells = group[group["has_reported_incident_on_date"] == True]
            if len(inc_cells) == 0:
                continue

            top10_cells = group[group[col] >= group[col].quantile(0.90)]
            top10_coords = top10_cells[["col_idx", "row_idx"]].values

            for _, inc_row in inc_cells.iterrows():
                inc_c, inc_r = inc_row["col_idx"], inc_row["row_idx"]
                dists = np.sqrt((top10_coords[:, 0] - inc_c)**2 + (top10_coords[:, 1] - inc_r)**2)
                min_d = float(np.min(dists)) if len(dists) > 0 else 0.0
                distances_km.append(min_d)

        results_by_model[col] = {
            "mean_rank_percentile": round(float(np.mean(daily_percentiles)), 2) if daily_percentiles else 0.0,
            "median_rank_percentile": round(float(np.median(daily_percentiles)), 2) if daily_percentiles else 0.0,
            "hit_rate_top_05_pct": round(float(np.mean(hit_top05) * 100.0), 2) if hit_top05 else 0.0,
            "hit_rate_top_10_pct": round(float(np.mean(hit_top10) * 100.0), 2) if hit_top10 else 0.0,
            "hit_rate_top_20_pct": round(float(np.mean(hit_top20) * 100.0), 2) if hit_top20 else 0.0,
            "mean_distance_to_top10_km": round(float(np.mean(distances_km)), 2) if distances_km else 0.0,
            "median_distance_to_top10_km": round(float(np.median(distances_km)), 2) if distances_km else 0.0,
        }

    # Category breakdown (for primary MCDA Runoff-Dominant and Isolation Forest)
    category_breakdown = {}
    for cat in usable_categories:
        cat_incidents = df_comp[
            (df_comp["has_reported_incident_on_date"] == True) &
            (df_comp["incident_categories_on_date"].str.contains(cat, na=False))
        ]
        category_breakdown[cat] = {
            "incident_cell_dates_count": len(cat_incidents),
            "mcda_runoff_dominant_mean_score": round(float(cat_incidents["mcda_score_runoff_dominant"].mean()), 3) if len(cat_incidents) > 0 else 0.0,
            "isolation_forest_mean_score": round(float(cat_incidents["isolation_forest_anomaly_score"].mean()), 3) if len(cat_incidents) > 0 else 0.0,
            "mahalanobis_mean_score": round(float(cat_incidents["mahalanobis_normalized_score"].mean()), 3) if len(cat_incidents) > 0 else 0.0,
        }

    return {
        "inventory_total_records": total_records,
        "eligible_geocoded_records": eligible_count,
        "incident_cell_dates_matched": n_incident_cell_dates,
        "model_retrospective_metrics": results_by_model,
        "evidence_category_breakdown": category_breakdown,
    }

