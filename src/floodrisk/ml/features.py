"""Reproducible ML dataset contract, event-group mapping, and leakage prevention."""

from typing import Any, Dict, List, Tuple
import pandas as pd

# Group EP_2022_08_30 and EP_2022_09_05 into one continuous late-Aug/early-Sep 2022 meteorological episode
EVENT_GROUP_MAP: Dict[str, str] = {
    "EP_2020_10_23": "EG_2020_10",
    "EP_2022_05_18": "EG_2022_05",
    "EP_2022_08_30": "EG_2022_08_09_MONSOON",
    "EP_2022_09_05": "EG_2022_08_09_MONSOON",
    "EP_2023_05_21": "EG_2023_05",
    "EP_2024_10_15": "EG_2024_10",
    "EP_2025_05_18": "EG_2025_05",
    "EP_2025_10_09": "EG_2025_10",
}

FORBIDDEN_LEAKAGE_COLS = {
    "flood_label",
    "evidence_status",
    "label_source",
    "label_confidence",
    "sar_delta_vv_db",
    "sar_evidence_state",
    "era5_rain_during_event_mm",
    "event_id",
    "event_group_id",
    "grid_id",
}

FEATURE_DICTIONARY: Dict[str, Dict[str, str]] = {
    "elevation_m": {"source": "SRTM 30m DEM", "unit": "m", "type": "static_terrain"},
    "slope_deg": {"source": "SRTM 30m DEM", "unit": "degrees", "type": "static_terrain"},
    "upstream_contributing_area_km2": {"source": "D8 Flow Routing", "unit": "km2", "type": "static_hydrology"},
    "topographic_wetness_index": {"source": "D8 TWI ln(a/tan b)", "unit": "dimensionless", "type": "static_hydrology"},
    "depression_depth_m": {"source": "Raw SRTM Pit Depth", "unit": "m", "type": "static_hydrology"},
    "is_closed_sink": {"source": "DEM Sink Indicator", "unit": "binary", "type": "static_hydrology"},
    "built_up_fraction": {"source": "ESA WorldCover 10m", "unit": "fraction [0,1]", "type": "static_landcover"},
    "tree_cover_fraction": {"source": "ESA WorldCover 10m", "unit": "fraction [0,1]", "type": "static_landcover"},
    "cropland_fraction": {"source": "ESA WorldCover 10m", "unit": "fraction [0,1]", "type": "static_landcover"},
    "water_fraction": {"source": "ESA WorldCover 10m", "unit": "fraction [0,1]", "type": "static_landcover"},
    "era5_rain_24h_pre_mm": {"source": "Open-Meteo ERA5-Land (< event_start_utc)", "unit": "mm", "type": "pre_event_reanalysis"},
    "era5_rain_72h_pre_mm": {"source": "Open-Meteo ERA5-Land (< event_start_utc)", "unit": "mm", "type": "pre_event_reanalysis"},
    "era5_api_7d_pre_mm": {"source": "Open-Meteo ERA5-Land 7d decay (< event_start_utc)", "unit": "mm", "type": "pre_event_reanalysis"},
    "era5_pre_missing_flag": {"source": "Missing-data indicator for pre-event rain", "unit": "binary", "type": "missing_flag"},
}

FEATURE_COLUMNS: List[str] = list(FEATURE_DICTIONARY.keys())


def prepare_ml_dataset(
    df_event_grid: pd.DataFrame,
    subset: str = "all_labeled",
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Prepare strictly leakage-free predictor matrix X, binary target y, and metadata.

    Subsets:
      - 'all_labeled': all rows with flood_label in {0, 1}
      - 'confirmed_only': CONFIRMED_FLOOD + PROXY_NEGATIVE only
      - 'dedup_event_group': deduplicated by (event_group_id, grid_id)
    """
    df = df_event_grid.copy()
    df["event_group_id"] = df["event_id"].map(EVENT_GROUP_MAP).fillna(df["event_id"])

    # Strictly keep only labeled rows; never convert UNOBSERVED/UNKNOWN to 0
    df = df[df["flood_label"].isin([0, 1, 0.0, 1.0])].copy()
    if subset == "confirmed_only":
        df = df[df["evidence_status"].isin(["CONFIRMED_FLOOD", "PROXY_NEGATIVE"])].copy()
    elif subset == "dedup_event_group":
        df = df.sort_values(["event_group_id", "grid_id", "flood_label"], ascending=[True, True, False])
        df = df.drop_duplicates(subset=["event_group_id", "grid_id"], keep="first").copy()
    elif subset != "all_labeled":
        raise ValueError(f"Unknown subset '{subset}'")

    df["era5_pre_missing_flag"] = (
        df[["era5_rain_24h_pre_mm", "era5_rain_72h_pre_mm", "era5_api_7d_pre_mm"]].isna().any(axis=1).astype(int)
    )

    for col in FEATURE_COLUMNS:
        if col in FORBIDDEN_LEAKAGE_COLS:
            raise AssertionError(f"Leakage violation: forbidden column {col} in features!")

    X = df[FEATURE_COLUMNS].copy()
    y = df["flood_label"].astype(int).copy()
    meta = df[["event_id", "event_group_id", "grid_id", "event_timestamp_utc", "evidence_status", "label_source", "label_confidence"]].copy()
    return X, y, meta
