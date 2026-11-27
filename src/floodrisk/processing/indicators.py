"""Exploratory Flood-Risk Indicators Module.

Provides transparent, rule-based, un-trained multi-criteria flood susceptibility
and dynamic exposure scoring across the 1-km spatial grid.

Explicitly isolates real observational features from pending/synthetic fixtures:
- Real observational inputs: SRTM GL1 30m DEM, ESA WorldCover 10m, GPM IMERG V07B.
- Pending inputs: MERIT Hydro UPA (explicitly NaN / UNAVAILABLE).
- Excluded inputs: Sentinel-1 SAR (synthetic test fixture; strictly excluded).
"""

from typing import Dict, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def compute_terrain_indicator(
    elevation_mean: pd.Series,
    elevation_std: pd.Series,
) -> pd.Series:
    """Compute topographic susceptibility indicator in [0.0, 1.0].
    
    Higher susceptibility is assigned to lower relative elevations (topographic depressions)
    and low terrain roughness / slope proxy (flat areas prone to ponding).
    
    Formula:
        elev_norm = (elevation_mean - min) / (max - min)
        roughness_norm = (elevation_std - min) / (max - min)
        I_terrain = 0.60 * (1.0 - elev_norm) + 0.40 * (1.0 - roughness_norm)
    """
    e_min, e_max = elevation_mean.min(), elevation_mean.max()
    elev_norm = (elevation_mean - e_min) / (e_max - e_min) if e_max > e_min else pd.Series(0.5, index=elevation_mean.index)

    r_min, r_max = elevation_std.min(), elevation_std.max()
    rough_norm = (elevation_std - r_min) / (r_max - r_min) if r_max > r_min else pd.Series(0.5, index=elevation_std.index)

    i_terrain = 0.60 * (1.0 - elev_norm) + 0.40 * (1.0 - rough_norm)
    return i_terrain.clip(0.0, 1.0).astype(np.float32)


def compute_landcover_indicator(
    built_up: pd.Series,
    water: pd.Series,
    tree_cover: pd.Series,
    cropland: pd.Series,
) -> pd.Series:
    """Compute land cover runoff potential / imperviousness indicator in [0.0, 1.0].
    
    Higher susceptibility is driven by impervious built-up surfaces and proximity
    to surface water bodies, mitigated by permeable vegetative canopy.
    
    Formula:
        I_raw = 0.75 * built_up + 0.25 * water - 0.20 * (tree_cover + cropland)
        Normalized and clipped to [0.0, 1.0].
    """
    i_raw = 0.75 * built_up + 0.25 * water - 0.20 * (tree_cover + cropland)
    # Map to positive range [0, 1]
    raw_min, raw_max = i_raw.min(), i_raw.max()
    if raw_max > raw_min:
        i_lc = (i_raw - raw_min) / (raw_max - raw_min)
    else:
        i_lc = pd.Series(0.5, index=built_up.index)
    return i_lc.clip(0.0, 1.0).astype(np.float32)


def compute_rainfall_indicator(
    daily_depth: pd.Series,
    api_decay: pd.Series,
) -> pd.Series:
    """Compute dynamic meteorological exposure indicator in [0.0, 1.0].
    
    Combines daily rainfall intensity with soil moisture memory via API.
    
    Formula:
        rain_norm = clip(daily_depth / 150.0, 0, 1)
        api_norm = clip(api_decay / 250.0, 0, 1)
        I_rainfall = 0.55 * rain_norm + 0.45 * api_norm
    """
    rain_norm = (daily_depth / 150.0).clip(0.0, 1.0)
    api_norm = (api_decay / 250.0).clip(0.0, 1.0)
    i_rain = 0.55 * rain_norm + 0.45 * api_norm
    return i_rain.clip(0.0, 1.0).astype(np.float32)


def compute_exploratory_risk_indicators(
    df_integrated: pd.DataFrame,
) -> pd.DataFrame:
    """Compute transparent multi-criteria exploratory risk indicators across all panel records.
    
    Args:
        df_integrated: Integrated multimodal panel dataset.
        
    Returns:
        DataFrame enriched with component indicators, composite risk indices,
        and sensitivity classifications.
    """
    df = df_integrated.copy()

    # 1. Component Indicators
    df["indicator_terrain"] = compute_terrain_indicator(
        df["elevation_mean_m"], df["elevation_std_m"]
    )
    df["indicator_landcover"] = compute_landcover_indicator(
        df["built_up_fraction"], df["water_fraction"],
        df["tree_cover_fraction"], df["cropland_fraction"]
    )
    df["indicator_rainfall"] = compute_rainfall_indicator(
        df["rainfall_daily_depth_mm"], df["precip_api_decay_mm"]
    )

    # 2. Explicitly Disclosed Unavailable / Isolated Fixtures
    df["indicator_hydro"] = np.nan
    df["indicator_hydro_status"] = "UNAVAILABLE_PENDING_MERIT_HYDRO"
    
    df["indicator_sar"] = np.nan
    df["indicator_sar_status"] = "UNAVAILABLE_SAR_SYNTHETIC_ONLY"

    # 3. Composite Indicators across 3 Weighting Schemes
    # Scheme 1: Equal Weighting (Balanced)
    df["composite_risk_equal"] = (
        (1.0 / 3.0) * df["indicator_terrain"] +
        (1.0 / 3.0) * df["indicator_landcover"] +
        (1.0 / 3.0) * df["indicator_rainfall"]
    ).clip(0.0, 1.0).astype(np.float32)

    # Scheme 2: Terrain-Dominant (Topographic Depression & Accumulation Focus)
    df["composite_risk_terrain_dominant"] = (
        0.50 * df["indicator_terrain"] +
        0.25 * df["indicator_landcover"] +
        0.25 * df["indicator_rainfall"]
    ).clip(0.0, 1.0).astype(np.float32)

    # Scheme 3: Runoff/Rainfall-Dominant (Urban Flash-Flood Imperviousness Focus)
    df["composite_risk_runoff_dominant"] = (
        0.20 * df["indicator_terrain"] +
        0.40 * df["indicator_landcover"] +
        0.40 * df["indicator_rainfall"]
    ).clip(0.0, 1.0).astype(np.float32)

    # 4. Sensitivity Discrepancy Metric (Spread across weighting schemes)
    weights_max = np.maximum(
        np.maximum(df["composite_risk_equal"], df["composite_risk_terrain_dominant"]),
        df["composite_risk_runoff_dominant"],
    )
    weights_min = np.minimum(
        np.minimum(df["composite_risk_equal"], df["composite_risk_terrain_dominant"]),
        df["composite_risk_runoff_dominant"],
    )
    df["weight_sensitivity_spread"] = (weights_max - weights_min).astype(np.float32)

    return df


def generate_exploratory_figures(
    df_indicators: pd.DataFrame,
    peak_date: str = "2022-09-05",
    output_path: str = "reports/figures/phase_2b/exploratory_risk_indicators_map.png",
) -> None:
    """Generate high-resolution multi-panel maps of the exploratory flood risk indicators."""
    # Peak date: 2022-09-05 (Catastrophic flood peak)
    peak_date_str = str(peak_date)
    # Support both datetime.date and string in date column
    date_strs = df_indicators["date"].apply(lambda d: d.isoformat() if hasattr(d, "isoformat") else str(d))
    df_peak = df_indicators[date_strs == peak_date_str].copy()
    if len(df_peak) == 0:
        raise ValueError(f"No records found for peak date {peak_date_str}. Available dates: {sorted(date_strs.unique())}")

    cols = sorted(df_peak["col_idx"].unique())
    rows = sorted(df_peak["row_idx"].unique(), reverse=True)

    lookup = df_peak.set_index(["row_idx", "col_idx"])

    grid_terrain = np.zeros((len(rows), len(cols)))
    grid_landcover = np.zeros((len(rows), len(cols)))
    grid_rainfall = np.zeros((len(rows), len(cols)))
    grid_composite = np.zeros((len(rows), len(cols)))

    for r_i, r in enumerate(rows):
        for c_i, c in enumerate(cols):
            grid_terrain[r_i, c_i] = lookup.loc[(r, c), "indicator_terrain"]
            grid_landcover[r_i, c_i] = lookup.loc[(r, c), "indicator_landcover"]
            grid_rainfall[r_i, c_i] = lookup.loc[(r, c), "indicator_rainfall"]
            grid_composite[r_i, c_i] = lookup.loc[(r, c), "composite_risk_runoff_dominant"]

    extent = [
        df_peak["centroid_lon"].min(), df_peak["centroid_lon"].max(),
        df_peak["centroid_lat"].min(), df_peak["centroid_lat"].max()
    ]

    # Geocoded flood incidents for peak date
    incidents_today = df_peak[df_peak["has_reported_incident_on_date"] == True]

    fig, axes = plt.subplots(2, 2, figsize=(14, 12), dpi=300)

    panels = [
        (grid_terrain, "A. Topographic Susceptibility ($I_{terrain}$)", "Blues", axes[0, 0]),
        (grid_landcover, "B. Land Cover Runoff Potential ($I_{landcover}$)", "YlOrBr", axes[0, 1]),
        (grid_rainfall, f"C. Dynamic Rainfall Exposure ($I_{{rainfall}}$, {peak_date})", "PuBu", axes[1, 0]),
        (grid_composite, f"D. Composite Risk Score (Runoff-Dominant, {peak_date})", "YlOrRd", axes[1, 1]),
    ]

    for data, title, cmap, ax in panels:
        im = ax.imshow(data, extent=extent, cmap=cmap, aspect="equal", vmin=0, vmax=1)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel("Longitude (°E)")
        ax.set_ylabel("Latitude (°N)")
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("Normalized Indicator Index [0, 1]")
        if len(incidents_today) > 0:
            ax.scatter(
                incidents_today["centroid_lon"], incidents_today["centroid_lat"],
                color="cyan", edgecolor="black", s=45, linewidth=1.0,
                label=f"Reported Incidents (N={len(incidents_today)})", zorder=5
            )
            ax.legend(loc="lower left", fontsize=8)

    plt.suptitle(
        f"Exploratory Multimodal Flood-Risk Indicators across Bengaluru Urban (1-km Grid)\nEvaluated on Peak Monsoon Inundation Date: {peak_date}",
        fontsize=13, fontweight="bold"
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved exploratory risk maps to {output_path}")
