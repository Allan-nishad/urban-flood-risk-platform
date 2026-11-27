"""
scripts/phase6/acquire_nwp.py

Phase 6A: Genuine NOAA GFS 0.25 NWP Acquisition Pipeline
- Downloads authentic GRIB2 byte slices from AWS Open Data (noaa-gfs-bdp-pds)
- Validates GRIB2 headers and metadata with ecCodes
- Extracts native 0.25-deg grid values over Bengaluru Urban
- Maps to 1,170 1-km provisional study cells with transparent spatial attribution
- Generates provenance records, acquisition logs, Parquet datasets, and manifest
"""

import os
import sys
import glob
import math
import hashlib
import json
import logging
from datetime import datetime, timedelta
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np
import geopandas as gpd
import eccodes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

BASE_S3_URL = "https://noaa-gfs-bdp-pds.s3.amazonaws.com"
RAW_DIR = "data/raw/phase6/nwp"
INTERIM_DIR = "data/interim/phase6/nwp"
PROCESSED_DIR = "data/processed/phase6/nwp"
MANIFEST_DIR = "reports/phase_6/phase_6_manifests"
REPORTS_DIR = "reports/phase_6"

GRID_PATH = "data/processed/grid_bengaluru_urban_1000m.gpkg"

START_DATE = datetime(2022, 8, 25)
END_DATE = datetime(2022, 9, 10)
CYCLES = ["00", "12"]
LEAD_TIMES = [6, 12, 24, 48, 72]

def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def fetch_and_slice(cycle_date_str: str, cycle_hour: str, lead_hour: int):
    lead_str = f"f{lead_hour:03d}"
    idx_url = f"{BASE_S3_URL}/gfs.{cycle_date_str}/{cycle_hour}/atmos/gfs.t{cycle_hour}z.pgrb2.0p25.{lead_str}.idx"
    grib_url = f"{BASE_S3_URL}/gfs.{cycle_date_str}/{cycle_hour}/atmos/gfs.t{cycle_hour}z.pgrb2.0p25.{lead_str}"
    
    out_dir = os.path.join(RAW_DIR, f"gfs.{cycle_date_str}", cycle_hour)
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"gfs.t{cycle_hour}z.pgrb2.0p25.{lead_str}.APCP.grib2")
    idx_file = os.path.join(out_dir, f"gfs.t{cycle_hour}z.pgrb2.0p25.{lead_str}.APCP.idx")
    
    # Check if already downloaded
    if os.path.exists(out_file) and os.path.getsize(out_file) > 1000 and os.path.exists(idx_file):
        sha256 = compute_sha256(out_file)
        return {
            "status": "CACHED",
            "cycle_date": cycle_date_str,
            "cycle_hour": cycle_hour,
            "lead_hour": lead_hour,
            "file_path": out_file,
            "idx_path": idx_file,
            "source_url": grib_url,
            "idx_url": idx_url,
            "file_size_bytes": os.path.getsize(out_file),
            "sha256": sha256
        }

    # Fetch index
    req = urllib.request.Request(idx_url, headers={'User-Agent': 'urban-flood-risk-platform/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read().decode('utf-8')
    except Exception as e:
        return {
            "status": "INDEX_ERROR",
            "cycle_date": cycle_date_str,
            "cycle_hour": cycle_hour,
            "lead_hour": lead_hour,
            "error": str(e)
        }

    lines = content.strip().split('\n')
    parsed = []
    for line in lines:
        parts = line.split(':')
        if len(parts) >= 6:
            parsed.append({
                'num': int(parts[0]),
                'offset': int(parts[1]),
                'date': parts[2],
                'var': parts[3],
                'level': parts[4],
                'desc': parts[5],
            })
            
    apcp_indices = [i for i, p in enumerate(parsed) if p['var'] == 'APCP' and p['level'] == 'surface']
    if not apcp_indices:
        return {
            "status": "APCP_NOT_FOUND",
            "cycle_date": cycle_date_str,
            "cycle_hour": cycle_hour,
            "lead_hour": lead_hour,
            "error": "No APCP:surface record found in index"
        }
        
    first_idx = apcp_indices[0]
    last_idx = apcp_indices[-1]
    
    range_start = parsed[first_idx]['offset']
    if last_idx + 1 < len(parsed):
        range_end = parsed[last_idx + 1]['offset'] - 1
    else:
        range_end = ""
        
    range_header = f"bytes={range_start}-{range_end}" if range_end else f"bytes={range_start}-"
    
    # Save index lines
    with open(idx_file, "w", encoding="utf-8") as f:
        for idx in apcp_indices:
            p = parsed[idx]
            f.write(f"{p['num']}:{p['offset']}:{p['date']}:{p['var']}:{p['level']}:{p['desc']}\n")
            
    # Download slice
    req2 = urllib.request.Request(grib_url, headers={'User-Agent': 'urban-flood-risk-platform/1.0', 'Range': range_header})
    try:
        with urllib.request.urlopen(req2, timeout=40) as resp:
            data = resp.read()
        with open(out_file, "wb") as f:
            f.write(data)
            
        sha256 = compute_sha256(out_file)
        return {
            "status": "DOWNLOADED",
            "cycle_date": cycle_date_str,
            "cycle_hour": cycle_hour,
            "lead_hour": lead_hour,
            "file_path": out_file,
            "idx_path": idx_file,
            "source_url": grib_url,
            "idx_url": idx_url,
            "range_header": range_header,
            "byte_start": range_start,
            "byte_end": range_end,
            "file_size_bytes": len(data),
            "sha256": sha256
        }
    except Exception as e:
        return {
            "status": "DOWNLOAD_ERROR",
            "cycle_date": cycle_date_str,
            "cycle_hour": cycle_hour,
            "lead_hour": lead_hour,
            "error": str(e)
        }

def parse_grib_file(file_info):
    fpath = file_info["file_path"]
    provenance_records = []
    native_grid_records = []
    
    with open(fpath, "rb") as f:
        msg_idx = 0
        while True:
            try:
                gid = eccodes.codes_grib_new_from_file(f)
            except Exception as e:
                logging.warning(f"Error reading message from {fpath}: {e}")
                break
                
            if gid is None:
                break
            msg_idx += 1
            
            # Extract header metadata
            short_name = eccodes.codes_get(gid, "shortName")
            var_name = eccodes.codes_get(gid, "name")
            units = eccodes.codes_get(gid, "units")
            step_range = eccodes.codes_get(gid, "stepRange")
            step_type = eccodes.codes_get(gid, "stepType")
            data_date = str(eccodes.codes_get(gid, "dataDate"))
            data_time = int(eccodes.codes_get(gid, "dataTime"))
            val_date = str(eccodes.codes_get(gid, "validityDate"))
            val_time = int(eccodes.codes_get(gid, "validityTime"))
            grid_type = eccodes.codes_get(gid, "gridType")
            ni = eccodes.codes_get(gid, "Ni")
            nj = eccodes.codes_get(gid, "Nj")
            
            init_dt = datetime.strptime(f"{data_date}{data_time:04d}", "%Y%m%d%H%M")
            valid_dt = datetime.strptime(f"{val_date}{val_time:04d}", "%Y%m%d%H%M")
            
            lats = eccodes.codes_get_double_array(gid, "latitudes")
            lons = eccodes.codes_get_double_array(gid, "longitudes")
            vals = eccodes.codes_get_double_array(gid, "values")
            
            # Record provenance
            prov = {
                "file_path": fpath,
                "cycle_date": file_info["cycle_date"],
                "cycle_hour": file_info["cycle_hour"],
                "lead_hour": file_info["lead_hour"],
                "message_index": msg_idx,
                "short_name": short_name,
                "variable_name": var_name,
                "units": units,
                "step_range": step_range,
                "step_type": step_type,
                "initialization_time_utc": init_dt.isoformat() + "Z",
                "valid_time_utc": valid_dt.isoformat() + "Z",
                "grid_type": grid_type,
                "grid_points_global": len(vals),
                "grid_ni": ni,
                "grid_nj": nj,
                "global_min_val": float(vals.min()),
                "global_max_val": float(vals.max()),
                "sha256": file_info["sha256"],
                "file_size_bytes": file_info["file_size_bytes"]
            }
            provenance_records.append(prov)
            
            # Extract 0.25-deg cells near Bengaluru (12.5 - 13.5 N, 77.0 - 78.0 E)
            mask = (lats >= 12.5) & (lats <= 13.5) & (lons >= 77.0) & (lons <= 78.0)
            b_lats = lats[mask]
            b_lons = lons[mask]
            b_vals = vals[mask]
            
            for lat, lon, v in zip(b_lats, b_lons, b_vals):
                native_grid_records.append({
                    "cycle_date": file_info["cycle_date"],
                    "cycle_hour": file_info["cycle_hour"],
                    "lead_hour": file_info["lead_hour"],
                    "message_index": msg_idx,
                    "step_range": step_range,
                    "step_type": step_type,
                    "initialization_time_utc": init_dt.isoformat() + "Z",
                    "valid_time_utc": valid_dt.isoformat() + "Z",
                    "gfs_lat": round(float(lat), 4),
                    "gfs_lon": round(float(lon), 4),
                    "rainfall_value_mm": round(float(v), 4)
                })
                
            eccodes.codes_release(gid)
            
    return provenance_records, native_grid_records

def main():
    print("="*80)
    print("PHASE 6A: NOAA GFS GENUINE ARCHIVED NWP ACQUISITION CAMPAIGN")
    print("="*80)
    
    # 1. Build acquisition task list
    tasks = []
    curr = START_DATE
    while curr <= END_DATE:
        ymd = curr.strftime("%Y%m%d")
        for ch in CYCLES:
            for lh in LEAD_TIMES:
                tasks.append((ymd, ch, lh))
        curr += timedelta(days=1)
        
    print(f"Total forecast slices scheduled: {len(tasks)} (17 dates x 2 cycles x 5 leads)")
    
    # 2. Execute acquisition using ThreadPoolExecutor
    print("\nExecuting byte-range downloads from AWS Open Data (noaa-gfs-bdp-pds)...")
    download_results = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(fetch_and_slice, ymd, ch, lh): (ymd, ch, lh) for ymd, ch, lh in tasks}
        for fut in as_completed(futures):
            res = fut.result()
            download_results.append(res)
            st = res.get("status")
            if st in ("DOWNLOADED", "CACHED"):
                sys.stdout.write(".")
            else:
                sys.stdout.write("x")
            sys.stdout.flush()
            
    print("\n\nAcquisition download phase completed.")
    success_downloads = [r for r in download_results if r.get("status") in ("DOWNLOADED", "CACHED")]
    print(f"Successful downloads: {len(success_downloads)} / {len(tasks)}")
    
    # Save acquisition log CSV
    log_df = pd.DataFrame(download_results)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    log_csv_path = os.path.join(PROCESSED_DIR, "nwp_acquisition_log.csv")
    log_df.to_csv(log_csv_path, index=False)
    print(f"Acquisition log saved: {log_csv_path}")
    
    if len(success_downloads) == 0:
        print("[CRITICAL ERROR] No forecast slices acquired! Gate 6A BLOCKED.")
        sys.exit(1)
        
    # 3. Parse downloaded GRIB2 files with ecCodes
    print("\nDecoding authentic GRIB2 messages and extracting native grid slices...")
    all_provenance = []
    all_native_grid = []
    
    for item in success_downloads:
        prov, nat = parse_grib_file(item)
        all_provenance.extend(prov)
        all_native_grid.extend(nat)
        
    print(f"Total GRIB2 messages decoded: {len(all_provenance)}")
    print(f"Total regional native grid records extracted: {len(all_native_grid)}")
    
    prov_df = pd.DataFrame(all_provenance)
    prov_parquet_path = os.path.join(PROCESSED_DIR, "nwp_forecast_provenance.parquet")
    prov_df.to_parquet(prov_parquet_path, index=False)
    print(f"Provenance dataset saved: {prov_parquet_path} ({len(prov_df)} records)")
    
    # 4. Map to 1,170 provisional study cells
    print("\nMapping native 0.25-deg forecasts to 1,170 study cells (EPSG:6933)...")
    grid_gdf = gpd.read_file(GRID_PATH)
    
    # Find unique GFS grid coordinates extracted
    nat_df = pd.DataFrame(all_native_grid)
    gfs_coords = nat_df[["gfs_lat", "gfs_lon"]].drop_duplicates().values
    print(f"Extracted {len(gfs_coords)} unique GFS native 0.25-deg coordinates across domain.")
    
    # Compute nearest GFS point for each 1-km cell centroid
    cell_mapping = []
    for idx, row in grid_gdf.iterrows():
        c_lat = row["centroid_lat"]
        c_lon = row["centroid_lon"]
        gid = row["grid_id"]
        
        # Find closest GFS point
        best_dist = float("inf")
        best_gfs = None
        for g_lat, g_lon in gfs_coords:
            d = haversine_km(c_lat, c_lon, g_lat, g_lon)
            if d < best_dist:
                best_dist = d
                best_gfs = (g_lat, g_lon)
                
        cell_mapping.append({
            "grid_id": gid,
            "centroid_lon": c_lon,
            "centroid_lat": c_lat,
            "nearest_gfs_lat": best_gfs[0],
            "nearest_gfs_lon": best_gfs[1],
            "distance_to_nearest_gfs_km": round(best_dist, 3),
            "mapping_method": "nearest_native_0p25",
            "native_spatial_resolution_km": 27.75,
            "is_native_resolution": False
        })
    cell_map_df = pd.DataFrame(cell_mapping)
    
    # Reorganize native grid by (cycle, lead, gfs_lat, gfs_lon)
    pivot_rows = []
    for (cdate, chour, lhour, glat, glon), group in nat_df.groupby(["cycle_date", "cycle_hour", "lead_hour", "gfs_lat", "gfs_lon"]):
        init_utc = group["initialization_time_utc"].iloc[0]
        valid_utc = group["valid_time_utc"].iloc[0]
        
        interval_val = np.nan
        accum_val = np.nan
        
        for _, r in group.iterrows():
            sr = str(r["step_range"])
            val = r["rainfall_value_mm"]
            if lhour == 6:
                interval_val = val
                accum_val = val
            else:
                if sr.startswith("0-"):
                    accum_val = val
                else:
                    interval_val = val
                    
        pivot_rows.append({
            "cycle_date": cdate,
            "cycle_hour": chour,
            "lead_hour": lhour,
            "initialization_time_utc": init_utc,
            "valid_time_utc": valid_utc,
            "gfs_lat": glat,
            "gfs_lon": glon,
            "apcp_interval_mm": interval_val,
            "apcp_accum_mm": accum_val
        })
    gfs_ts_df = pd.DataFrame(pivot_rows)
    
    # Merge cell mapping with GFS time series
    print("Merging cell mapping with gridded forecast time series...")
    merged_archive = pd.merge(
        cell_map_df,
        gfs_ts_df,
        left_on=["nearest_gfs_lat", "nearest_gfs_lon"],
        right_on=["gfs_lat", "gfs_lon"],
        how="inner"
    )
    
    # Format and save forecast archive
    merged_archive = merged_archive.sort_values(["initialization_time_utc", "lead_hour", "grid_id"]).reset_index(drop=True)
    archive_parquet_path = os.path.join(PROCESSED_DIR, "nwp_forecast_archive.parquet")
    merged_archive.to_parquet(archive_parquet_path, index=False)
    print(f"NWP forecast archive saved: {archive_parquet_path} ({len(merged_archive)} rows)")
    
    # 5. Build Stage 6A NWP Manifest
    os.makedirs(MANIFEST_DIR, exist_ok=True)
    manifest_path = os.path.join(MANIFEST_DIR, "nwp_manifest.json")
    
    manifest_entries = {
        "nwp_acquisition_log": {
            "file_path": log_csv_path,
            "file_size_bytes": os.path.getsize(log_csv_path),
            "sha256_checksum": compute_sha256(log_csv_path),
            "description": "Log of NOAA GFS byte-range acquisition attempts and HTTP status",
            "record_count": len(log_df)
        },
        "nwp_forecast_provenance": {
            "file_path": prov_parquet_path,
            "file_size_bytes": os.path.getsize(prov_parquet_path),
            "sha256_checksum": compute_sha256(prov_parquet_path),
            "description": "ecCodes decoded message provenance and WMO GRIB2 headers",
            "record_count": len(prov_df)
        },
        "nwp_forecast_archive": {
            "file_path": archive_parquet_path,
            "file_size_bytes": os.path.getsize(archive_parquet_path),
            "sha256_checksum": compute_sha256(archive_parquet_path),
            "description": "Cell-mapped authentic NOAA GFS forecast rainfall time series across study domain",
            "record_count": len(merged_archive)
        }
    }
    
    manifest_data = {
        "manifest_name": "Phase 6A Authentic NOAA GFS NWP Manifest",
        "study_area": "Bengaluru Urban provisional study domain (1,170 cells, EPSG:6933)",
        "source": "NOAA Global Forecast System (GFS) 0.25-deg AWS Open Data (s3://noaa-gfs-bdp-pds)",
        "created_at_utc": datetime.utcnow().isoformat() + "Z",
        "datasets": manifest_entries
    }
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"Stage 6A Manifest written to: {manifest_path}")
    
    print("\n" + "="*80)
    print("STAGE 6A ACQUISITION AND COMPILATION COMPLETED SUCCESSFULLY")
    print("="*80)

if __name__ == "__main__":
    main()
