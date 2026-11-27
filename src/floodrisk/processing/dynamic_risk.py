"""Phase 4.3 Dynamic Risk-Intelligence Engine.

Combines four distinct, un-conflated information layers:
1. Static Susceptibility (Terrain depressions & land-cover imperviousness via MCDA)
2. Observed Rainfall Exposure (Verified historical/recent observations and antecedent saturation)
3. Forecast Rainfall Exposure (NWP forward-looking rainfall depth and lead time)
4. Observed Flood Evidence (Independent ground incident records and spatial uncertainty)

Generates an interpretable dynamic risk-intelligence matrix without false probability claims.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


def compute_dynamic_risk_intelligence(
    df_static: pd.DataFrame,
    df_forecast_exp: pd.DataFrame,
    df_incidents: pd.DataFrame,
    df_mcda: Optional[pd.DataFrame] = None,
    recent_observed_rain_mm: float = 12.5,
    recent_observed_api_mm: float = 35.0,
    output_path: str = "data/processed/dynamic_risk_intelligence_bengaluru.parquet",
) -> pd.DataFrame:
    """Compute integrated dynamic risk-intelligence matrix across all 1,170 master grid cells.
    
    Args:
        df_static: Static physical grid features (elevation, land cover, coordinates).
        df_forecast_exp: Forecast exposure indicators per cell.
        df_incidents: Historical/recent ground incident evidence inventory.
        df_mcda: Optional pre-computed MCDA susceptibility scores.
        recent_observed_rain_mm: Recent 24h observed rainfall domain baseline.
        recent_observed_api_mm: Recent antecedent moisture index baseline.
        output_path: Output parquet path.
        
    Returns:
        DataFrame containing separate analytical components and exploratory composite prioritization.
    """
    # 1. Base Layer: Grid identifiers, coordinates, and static features
    df = df_static[[
        "grid_id", "col_idx", "row_idx", "centroid_lon", "centroid_lat",
        "elevation_mean_m", "elevation_std_m", "built_up_fraction",
        "tree_cover_fraction", "cropland_fraction", "water_fraction"
    ]].drop_duplicates().copy()

    # Compute static physical susceptibility baseline [0, 1]
    e = df["elevation_mean_m"]
    e_std = df["elevation_std_m"]
    e_norm = (e - e.min()) / (e.max() - e.min())
    std_norm = (e_std - e_std.min()) / (e_std.max() - e_std.min())
    s_terrain = (0.60 * (1.0 - e_norm) + 0.40 * (1.0 - std_norm)).clip(0.0, 1.0)
    df["baseline_terrain_susceptibility"] = s_terrain.astype(np.float32)

    b = df["built_up_fraction"]
    w = df["water_fraction"]
    veg = df["tree_cover_fraction"] + df["cropland_fraction"]
    lc_raw = 0.75 * b + 0.25 * w - 0.20 * veg
    s_landcover = ((lc_raw - lc_raw.min()) / (lc_raw.max() - lc_raw.min())).clip(0.0, 1.0)
    df["baseline_landcover_runoff"] = s_landcover.astype(np.float32)

    # Static susceptibility: 0.50 * terrain + 0.50 * landcover
    s_static = 0.50 * df["baseline_terrain_susceptibility"] + 0.50 * df["baseline_landcover_runoff"]
    df["static_susceptibility_score"] = s_static.clip(0.0, 1.0).astype(np.float32)
    df["static_susceptibility_rank"] = df["static_susceptibility_score"].rank(ascending=False, method="min").astype(int)

    # 2. Observed Exposure Layer (Recent historical antecedent baseline)
    df["observed_rainfall_24h_mm"] = float(recent_observed_rain_mm)
    df["observed_api_decay_mm"] = float(recent_observed_api_mm)
    obs_exposure = (
        0.55 * np.clip(recent_observed_rain_mm / 100.0, 0.0, 1.0) +
        0.45 * np.clip(recent_observed_api_mm / 150.0, 0.0, 1.0)
    )
    df["observed_rainfall_exposure_score"] = round(float(obs_exposure), 4)

    # 3. Forecast Exposure Layer (Merged from Phase 4.2 NWP indicators)
    df = df.merge(
        df_forecast_exp[[
            "grid_id", "forecast_issue_time", "forecast_rainfall_3h_mm",
            "forecast_rainfall_6h_mm", "forecast_rainfall_24h_mm",
            "forecast_rainfall_72h_mm", "forecast_peak_hourly_intensity_mm",
            "forecast_exposure_score_24h", "forecast_intensity_category"
        ]],
        on="grid_id",
        how="left"
    )

    # 4. Observed Flood Evidence Layer (From verified incident inventory)
    # Check if cell has historical/recent incident records
    inc_counts = df_incidents.groupby("grid_id").size().to_dict()
    inc_cats = df_incidents.groupby("grid_id")["evidence_category"].apply(lambda s: "; ".join(s.unique())).to_dict()

    df["historical_incident_count"] = df["grid_id"].map(inc_counts).fillna(0).astype(int)
    df["historical_incident_categories"] = df["grid_id"].map(inc_cats).fillna("none")
    df["has_ground_flood_evidence"] = df["historical_incident_count"] > 0

    # 5. Exploratory Dynamic Prioritization Index (Optional Un-trained Secondary Metric)
    # The primary platform outputs remain the four separate, un-conflated layers above.
    # The composite score below is an optional, exploratory multi-criteria screening index:
    # 35% Static Susceptibility + 30% Observed Catchment Antecedent + 35% Forward Forecast Exposure
    # NOTE: Historical incident evidence is deliberately EXCLUDED from this formula to prevent circularity
    # when the resulting risk rankings are evaluated against reported flood occurrences.
    dynamic_priority = (
        0.35 * df["static_susceptibility_score"] +
        0.30 * df["observed_rainfall_exposure_score"] +
        0.35 * df["forecast_exposure_score_24h"]
    ).clip(0.0, 1.0).astype(np.float32)

    df["dynamic_risk_prioritization_score"] = dynamic_priority
    df["dynamic_risk_rank"] = df["dynamic_risk_prioritization_score"].rank(ascending=False, method="min").astype(int)
    df["dynamic_score_status"] = "OPTIONAL_UNCALIBRATED_PRIORITIZATION_INDEX"

    # 6. Qualitative Research Monitoring Levels (Explicitly NOT official warnings)
    def assign_monitoring_level(score):
        if score >= 0.70:
            return "RESEARCH_PRIORITY_VERY_HIGH"
        elif score >= 0.50:
            return "RESEARCH_PRIORITY_HIGH"
        elif score >= 0.35:
            return "RESEARCH_PRIORITY_MODERATE"
        else:
            return "RESEARCH_PRIORITY_LOW"

    df["research_monitoring_level"] = df["dynamic_risk_prioritization_score"].apply(assign_monitoring_level)
    df["scientific_disclaimer"] = (
        "Exploratory risk prioritization score [0, 1]. Reflects relative physical susceptibility "
        "and meteorological exposure. Not an official government emergency warning or calibrated flood probability. "
        "Primary scientific outputs are the 4 segregated information layers."
    )

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_p, index=False)
    print(f"Saved dynamic risk-intelligence dataset to {output_path} ({len(df):,} grid cells)")
    return df
