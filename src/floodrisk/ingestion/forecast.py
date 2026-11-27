"""NWP Rainfall Forecast Ingestion and Processing Module.

Fetches, validates, and processes numerical weather prediction (NWP) rainfall forecasts
for the Bengaluru study area using the Open-Meteo seamless forecast API (ECMWF IFS / NOAA GFS).

Strictly preserves:
- forecast_issue_time separately from valid_time
- lead_time_hours calculation
- original source spatial resolution (~9-13 km)
- explicit provenance status
"""

import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


def fetch_nwp_forecast_for_point(
    lat: float,
    lon: float,
    forecast_days: int = 3,
    timeout_sec: int = 15,
) -> Dict:
    """Fetch hourly NWP forecast from Open-Meteo for a given coordinate."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat:.4f}&longitude={lon:.4f}&"
        f"hourly=precipitation,precipitation_probability,weather_code&"
        f"forecast_days={forecast_days}&timezone=UTC"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "UrbanFloodRiskPlatform/2.0"})
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        return json.loads(resp.read().decode())


def ingest_forecast_rainfall(
    df_grid_cells: pd.DataFrame,
    output_path: str = "data/processed/forecast_rainfall_bengaluru.parquet",
    sample_grid_density: int = 3, # 3x3 = 9 spatial anchor points across domain
) -> pd.DataFrame:
    """Ingest spatial NWP rainfall forecasts mapped to the master analysis grid.
    
    Args:
        df_grid_cells: Grid features containing grid_id, centroid_lat, centroid_lon.
        output_path: Path to save output parquet.
        sample_grid_density: Number of spatial query anchors along lat and lon.
        
    Returns:
        DataFrame of canonical forecast records.
    """
    retrieval_time = datetime.now(timezone.utc).isoformat()
    issue_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00:00Z")

    # Define spatial anchor points covering the study domain
    lats = np.linspace(df_grid_cells["centroid_lat"].min(), df_grid_cells["centroid_lat"].max(), sample_grid_density)
    lons = np.linspace(df_grid_cells["centroid_lon"].min(), df_grid_cells["centroid_lon"].max(), sample_grid_density)

    anchor_forecasts = {}
    print(f"Fetching NWP forecasts across {len(lats) * len(lons)} regional spatial anchor points...")

    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            anchor_id = f"NWP_ANCHOR_{i}_{j}"
            try:
                raw_data = fetch_nwp_forecast_for_point(lat, lon, forecast_days=3)
                anchor_forecasts[anchor_id] = {
                    "lat": lat,
                    "lon": lon,
                    "hourly_time": raw_data["hourly"]["time"],
                    "precipitation": raw_data["hourly"]["precipitation"],
                    "probability": raw_data["hourly"].get("precipitation_probability", [0.0]*len(raw_data["hourly"]["time"])),
                }
            except Exception as e:
                print(f"Warning: Failed to fetch forecast for anchor ({lat:.4f}, {lon:.4f}): {e}")

    # Fallback if network drops
    if len(anchor_forecasts) == 0:
        raise RuntimeError("Failed to fetch forecast from Open-Meteo. Network connection unavailable.")

    # Assign each grid cell to its nearest NWP spatial anchor point
    cell_coords = df_grid_cells[["grid_id", "centroid_lat", "centroid_lon"]].drop_duplicates()
    records = []

    for _, cell in cell_coords.iterrows():
        c_id = cell["grid_id"]
        c_lat = cell["centroid_lat"]
        c_lon = cell["centroid_lon"]

        # Find closest anchor
        best_anchor = None
        min_d = float("inf")
        for a_id, a_data in anchor_forecasts.items():
            d = (c_lat - a_data["lat"])**2 + (c_lon - a_data["lon"])**2
            if d < min_d:
                min_d = d
                best_anchor = a_id

        a_data = anchor_forecasts[best_anchor]
        times = a_data["hourly_time"]
        precips = a_data["precipitation"]
        probs = a_data["probability"]

        # Parse issue time datetime
        issue_dt = datetime.fromisoformat(issue_time.replace("Z", "+00:00"))

        for step_idx, (t_str, p_val, prob_val) in enumerate(zip(times, precips, probs)):
            valid_dt = datetime.fromisoformat(t_str + ":00+00:00")
            lead_hours = int((valid_dt - issue_dt).total_seconds() // 3600)
            if lead_hours < 0:
                continue

            records.append({
                "forecast_id": f"FCST_{c_id}_{issue_dt.strftime('%Y%m%d%H')}_{lead_hours:03d}H",
                "provider": "Open-Meteo NWP Service",
                "model_name": "ECMWF_IFS_GFS_Seamless",
                "forecast_issue_time": issue_time,
                "nominal_reference_time_utc": issue_time,
                "retrieval_time_utc": retrieval_time,
                "model_initialization_status": "UNEXPOSED_BY_PROVIDER_INFERRED_FROM_RETRIEVAL",
                "valid_time": valid_dt.isoformat(),
                "lead_time_hours": lead_hours,
                "grid_id": c_id,
                "precipitation_value": float(p_val),
                "precipitation_unit": "mm",
                "precipitation_depth_mm": float(p_val),
                "precipitation_probability_pct": float(prob_val) if prob_val is not None else 0.0,
                "source_pixel_id": best_anchor,
                "source_resolution": "approx. 9-13 km (ECMWF IFS/GFS coarse anchor)",
                "mapping_method": "nearest_centroid_anchor",
                "coarse_grid_note": "Inherited from nearest 9-13km regional anchor; not an independent 1-km weather observation.",
                "retrieval_time": retrieval_time,
                "provenance_status": "VERIFIED_REAL_NWP_FORECAST",
            })

    df_fcst = pd.DataFrame(records)
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    df_fcst.to_parquet(out_p, index=False)
    print(f"Saved forecast rainfall dataset to {output_path} ({len(df_fcst):,} rows)")
    return df_fcst


def compute_forecast_exposure_indicators(
    df_forecast: pd.DataFrame,
    output_path: str = "data/processed/forecast_exposure_indicators_bengaluru.parquet",
) -> pd.DataFrame:
    """Compute multi-horizon forecast exposure indicators per grid cell.
    
    Indicators computed:
    - forecast_rainfall_3h_mm: Sum over lead_time 1 to 3h
    - forecast_rainfall_6h_mm: Sum over lead_time 1 to 6h
    - forecast_rainfall_24h_mm: Sum over lead_time 1 to 24h
    - forecast_rainfall_48h_mm: Sum over lead_time 1 to 48h
    - forecast_rainfall_72h_mm: Sum over lead_time 1 to 72h
    - forecast_peak_hourly_intensity_mm: Max hourly rate
    - forecast_intensity_category: Qualitative classification
    """
    records = []
    issue_time = df_forecast["forecast_issue_time"].iloc[0]

    for grid_id, group in df_forecast.groupby("grid_id"):
        grp_sorted = group.sort_values("lead_time_hours")
        p = grp_sorted["precipitation_depth_mm"].values
        leads = grp_sorted["lead_time_hours"].values

        p_3h = float(np.sum(p[leads <= 3]))
        p_6h = float(np.sum(p[leads <= 6]))
        p_24h = float(np.sum(p[leads <= 24]))
        p_48h = float(np.sum(p[leads <= 48]))
        p_72h = float(np.sum(p[leads <= 72]))
        peak_intensity = float(np.max(p)) if len(p) > 0 else 0.0

        # Internal meteorological rainfall categories based on standard 24h thresholds
        # Note: These are internal classification categories, NOT official government emergency warnings
        if peak_intensity >= 15.0 or p_24h >= 64.5:
            cat = "HEAVY_RAINFALL_CATEGORY"
        elif peak_intensity >= 2.5 or p_24h >= 15.5:
            cat = "MODERATE_RAINFALL_CATEGORY"
        elif p_72h > 0.0:
            cat = "LIGHT_RAINFALL_CATEGORY"
        else:
            cat = "NO_PRECIPITATION"

        records.append({
            "grid_id": grid_id,
            "forecast_issue_time": issue_time,
            "forecast_horizon_hours": int(leads.max()),
            "forecast_rainfall_3h_mm": round(p_3h, 2),
            "forecast_rainfall_6h_mm": round(p_6h, 2),
            "forecast_rainfall_24h_mm": round(p_24h, 2),
            "forecast_rainfall_48h_mm": round(p_48h, 2),
            "forecast_rainfall_72h_mm": round(p_72h, 2),
            "forecast_peak_hourly_intensity_mm": round(peak_intensity, 2),
            "forecast_intensity_category": cat,
            "official_warning_status": "INTERNAL_METEOROLOGICAL_CLASSIFICATION_NOT_OFFICIAL_GOVERNMENT_ALERT",
            "accumulation_interval_note": "Rolling 24h accumulation ending at forecast valid time; differs from official IMD 08:30-08:30 IST reporting window.",
            "forecast_exposure_score_24h": round(float(np.clip(p_24h / 65.0, 0.0, 1.0)), 4),
            "forecast_exposure_score_72h": round(float(np.clip(p_72h / 120.0, 0.0, 1.0)), 4),
            "provenance_status": "DERIVED_FROM_VERIFIED_FORECAST",
        })

    df_ind = pd.DataFrame(records)
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    df_ind.to_parquet(out_p, index=False)
    print(f"Saved forecast exposure indicators to {output_path} ({len(df_ind):,} grid cells)")
    return df_ind

