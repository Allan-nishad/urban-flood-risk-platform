"""
scripts/phase7/verify_forecasts.py
Workstream 7B: Final NWP Forecast Verification Pipeline.
- Reconstructs forecast-observation paired evaluations from frozen Phase 6 datasets
- Analyzes spatial attribution to the 3 distinct native GFS grid nodes
- Evaluates continuous verification metrics (MAE, RMSE, Bias, Pearson r, Spearman r)
- Evaluates multi-threshold contingency metrics (2.5mm, 15.6mm, 35.5mm, 64.5mm, 115.6mm)
- Generates phase7_forecast_verification_metrics.parquet and phase7_forecast_error_registry.parquet
"""

import os
import sys
import json
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime

PROCESSED_VERIF_DIR = "data/processed/phase7/verification"
PROCESSED_NWP_DIR = "data/processed/phase7/nwp"
MANIFEST_DIR = "reports/phase_7_manifests"

NWP_ARCHIVE_PATH = "data/processed/phase6/nwp/nwp_forecast_archive.parquet"
STATIONS_PATH = "data/processed/phase6/ground_rainfall/rain_gauge_station_registry.parquet"
OBS_PATH = "data/processed/phase6/ground_rainfall/ground_rainfall_observations.parquet"

def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def calc_contingency(obs_series, fcst_series, threshold):
    obs_pos = obs_series >= threshold
    fcst_pos = fcst_series >= threshold
    
    hits = int(((obs_pos) & (fcst_pos)).sum())
    misses = int(((obs_pos) & (~fcst_pos)).sum())
    fas = int(((~obs_pos) & (fcst_pos)).sum())
    cns = int(((~obs_pos) & (~fcst_pos)).sum())
    total = hits + misses + fas + cns
    
    pod = hits / (hits + misses) if (hits + misses) > 0 else np.nan
    far = fas / (hits + fas) if (hits + fas) > 0 else np.nan
    csi = hits / (hits + misses + fas) if (hits + misses + fas) > 0 else np.nan
    bias_freq = (hits + fas) / (hits + misses) if (hits + misses) > 0 else np.nan
    specificity = cns / (cns + fas) if (cns + fas) > 0 else np.nan
    
    # Equitable Threat Score (ETS)
    hits_random = (hits + misses) * (hits + fas) / total if total > 0 else 0
    denom = hits + misses + fas - hits_random
    ets = (hits - hits_random) / denom if denom > 0 else np.nan
    
    return {
        "threshold_mm": threshold,
        "hits": hits,
        "misses": misses,
        "false_alarms": fas,
        "correct_negatives": cns,
        "total_samples": total,
        "pod": round(float(pod), 4) if not np.isnan(pod) else None,
        "far": round(float(far), 4) if not np.isnan(far) else None,
        "csi": round(float(csi), 4) if not np.isnan(csi) else None,
        "ets": round(float(ets), 4) if not np.isnan(ets) else None,
        "frequency_bias": round(float(bias_freq), 4) if not np.isnan(bias_freq) else None,
        "specificity": round(float(specificity), 4) if not np.isnan(specificity) else None
    }

def main():
    print("=" * 80)
    print("WORKSTREAM 7B: FINAL NWP FORECAST VERIFICATION PIPELINE")
    print("=" * 80)
    
    os.makedirs(PROCESSED_VERIF_DIR, exist_ok=True)
    os.makedirs(PROCESSED_NWP_DIR, exist_ok=True)
    os.makedirs(MANIFEST_DIR, exist_ok=True)
    
    # 1. Load datasets
    print("Loading raw NWP archive, station registry, and observations...")
    nwp_df = pd.read_parquet(NWP_ARCHIVE_PATH)
    stations_df = pd.read_parquet(STATIONS_PATH)
    obs_df = pd.read_parquet(OBS_PATH)
    
    # Filter 16 primary hydrological stations
    primary_stations = stations_df[stations_df["is_primary_hydrological_gauge"] == True].copy()
    print(f"Primary meteorological stations: {len(primary_stations)}")
    
    # Match stations to their nearest native GFS grid node
    # Available GFS nodes in archive: (12.75, 77.50), (12.75, 77.75), (13.00, 77.50), (13.00, 77.75), (13.25, 77.50), (13.25, 77.75)
    gfs_nodes = nwp_df[["nearest_gfs_lat", "nearest_gfs_lon"]].drop_duplicates().values
    
    station_gfs_map = {}
    for idx, stn in primary_stations.iterrows():
        stn_lat, stn_lon = stn["latitude"], stn["longitude"]
        best_dist = float("inf")
        best_node = None
        for glat, glon in gfs_nodes:
            d = np.sqrt(((stn_lat - glat) * 111.0)**2 + ((stn_lon - glon) * 111.0 * np.cos(np.radians(stn_lat)))**2)
            if d < best_dist:
                best_dist = d
                best_node = (round(float(glat), 2), round(float(glon), 2))
        station_gfs_map[stn["station_id"]] = {
            "gfs_lat": best_node[0],
            "gfs_lon": best_node[1],
            "distance_km": round(float(best_dist), 2)
        }
        
    print("\nStation-to-GFS Node Mapping:")
    for sid, m in station_gfs_map.items():
        print(f"  {sid}: GFS Node ({m['gfs_lat']}, {m['gfs_lon']}), dist={m['distance_km']} km")
        
    # Extract unique 24h forecasts per GFS node and cycle
    # 24h lead time, 00Z initialization
    nwp_24h = nwp_df[(nwp_df["lead_hour"] == 24) & (nwp_df["cycle_hour"] == "00")].copy()
    node_fcsts = nwp_24h.groupby(["cycle_date", "nearest_gfs_lat", "nearest_gfs_lon"]).agg(
        gfs_accum_24h_mm=("apcp_accum_mm", "mean"),
        valid_time_utc=("valid_time_utc", "first")
    ).reset_index()
    
    # Reconstruct paired evaluations
    paired_rows = []
    # Dates: initialization dates 20220825 to 20220909 targeting obs dates 2022-08-26 to 2022-09-10
    dates = sorted(node_fcsts["cycle_date"].unique())
    print(f"\nProcessing {len(dates)} forecast cycles across 16 stations...")
    
    for cdate in dates:
        # Target obs date is next day YYYY-MM-DD
        dt = datetime.strptime(cdate, "%Y%m%d")
        from datetime import timedelta
        target_date_str = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
        
        c_fcsts = node_fcsts[node_fcsts["cycle_date"] == cdate]
        c_obs = obs_df[obs_df["observation_date"] == target_date_str]
        
        for idx, stn in primary_stations.iterrows():
            sid = stn["station_id"]
            g_info = station_gfs_map[sid]
            glat, glon = g_info["gfs_lat"], g_info["gfs_lon"]
            
            f_match = c_fcsts[(c_fcsts["nearest_gfs_lat"] == glat) & (c_fcsts["nearest_gfs_lon"] == glon)]
            o_match = c_obs[c_obs["station_id"] == sid]
            
            if len(f_match) == 0 or len(o_match) == 0:
                continue
                
            f_val = round(float(f_match["gfs_accum_24h_mm"].iloc[0]), 2)
            o_val = round(float(o_match["rainfall_depth_mm"].iloc[0]), 2)
            err = round(float(f_val - o_val), 2)
            abs_err = round(float(abs(err)), 2)
            
            # Forecast window: cdate 00:00 UTC to next day 00:00 UTC
            # Observation window: 24h accumulation ending at 03:00 UTC (08:30 IST) on target date
            fcst_start = f"{dt.strftime('%Y-%m-%d')} 00:00 UTC"
            fcst_end = f"{target_date_str} 00:00 UTC"
            obs_start = f"{dt.strftime('%Y-%m-%d')} 03:00 UTC"
            obs_end = f"{target_date_str} 03:00 UTC"
            
            paired_rows.append({
                "pair_id": f"PAIR_{cdate}_{sid}",
                "station_id": sid,
                "station_name": stn["station_name"],
                "network": stn["network"],
                "station_lat": stn["latitude"],
                "station_lon": stn["longitude"],
                "elevation_m": stn["elevation_m"],
                "nearest_gfs_lat": glat,
                "nearest_gfs_lon": glon,
                "distance_to_gfs_km": g_info["distance_km"],
                "cycle_date": cdate,
                "target_obs_date": target_date_str,
                "forecast_window_start": fcst_start,
                "forecast_window_end": fcst_end,
                "obs_window_start": obs_start,
                "obs_window_end": obs_end,
                "gfs_forecast_24h_mm": f_val,
                "observed_24h_mm": o_val,
                "forecast_error_mm": err,
                "abs_error_mm": abs_err,
                "is_heavy_rain_obs": o_val >= 64.5,
                "is_heavy_rain_fcst": f_val >= 64.5,
                "is_moderate_rain_obs": o_val >= 15.6,
                "is_moderate_rain_fcst": f_val >= 15.6,
                "is_rain_obs": o_val >= 2.5,
                "is_rain_fcst": f_val >= 2.5
            })
            
    pairs_df = pd.DataFrame(paired_rows)
    error_reg_path = os.path.join(PROCESSED_NWP_DIR, "phase7_forecast_error_registry.parquet")
    pairs_df.to_parquet(error_reg_path, index=False)
    print(f"Forecast Error Registry saved: {error_reg_path} ({len(pairs_df)} paired records)")
    
    # 2. Continuous Verification Metrics
    mae = float(pairs_df["abs_error_mm"].mean())
    rmse = float(np.sqrt((pairs_df["forecast_error_mm"]**2).mean()))
    bias = float(pairs_df["forecast_error_mm"].mean())
    pearson_r = float(np.corrcoef(pairs_df["gfs_forecast_24h_mm"], pairs_df["observed_24h_mm"])[0, 1])
    from scipy.stats import spearmanr
    spearman_res = spearmanr(pairs_df["gfs_forecast_24h_mm"], pairs_df["observed_24h_mm"])
    spearman_r = float(spearman_res.statistic)
    spearman_p = float(spearman_res.pvalue)
    
    print(f"\n--- Continuous Verification Metrics (N={len(pairs_df)}) ---")
    print(f"  MAE:        {mae:.2f} mm")
    print(f"  RMSE:       {rmse:.2f} mm")
    print(f"  Mean Bias:  {bias:.2f} mm")
    print(f"  Pearson r:  {pearson_r:.4f}")
    print(f"  Spearman r: {spearman_r:.4f} (p={spearman_p:.4e})")
    
    # 3. Categorical Contingency Analysis at 5 Thresholds
    thresholds = [2.5, 15.6, 35.5, 64.5, 115.6]
    contingency_records = []
    print("\n--- Categorical Contingency Verification ---")
    for th in thresholds:
        c_res = calc_contingency(pairs_df["observed_24h_mm"], pairs_df["gfs_forecast_24h_mm"], th)
        contingency_records.append(c_res)
        print(f"  Threshold >= {th:5.1f} mm: Hits={c_res['hits']:3d}, Misses={c_res['misses']:3d}, FAs={c_res['false_alarms']:3d}, CNs={c_res['correct_negatives']:3d} | POD={str(c_res['pod']):6s}, FAR={str(c_res['far']):6s}, CSI={str(c_res['csi']):6s}")
        
    contingency_df = pd.DataFrame(contingency_records)
    
    # 4. Save Final Phase 7 Verification Dataset
    verif_summary = {
        "evaluation_name": "Phase 7 Final NWP Verification",
        "sample_size": len(pairs_df),
        "unique_stations": int(pairs_df["station_id"].nunique()),
        "unique_dates": int(pairs_df["target_obs_date"].nunique()),
        "distinct_gfs_nodes": int(pairs_df.groupby(["nearest_gfs_lat", "nearest_gfs_lon"]).ngroups),
        "continuous_metrics": {
            "mae_mm": round(mae, 2),
            "rmse_mm": round(rmse, 2),
            "mean_bias_mm": round(bias, 2),
            "pearson_r": round(pearson_r, 4),
            "spearman_r": round(spearman_r, 4),
            "spearman_p_val": spearman_p
        },
        "contingency_by_threshold": contingency_records
    }
    
    verif_out_path = os.path.join(PROCESSED_VERIF_DIR, "phase7_forecast_verification_metrics.parquet")
    contingency_df.to_parquet(verif_out_path, index=False)
    print(f"\nVerification metrics saved to: {verif_out_path}")
    
    print("\n" + "=" * 80)
    print("WORKSTREAM 7B VERIFICATION SCRIPT COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()

