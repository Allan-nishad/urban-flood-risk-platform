"""
Unit and Integration Tests for Phase 6 Deliverables and Scientific Gate Acceptance.
"""
import os
import json
import hashlib
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from floodrisk.dashboard.server import load_dashboard_data

def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def test_phase6_master_manifest_integrity():
    manifest_path = "reports/phase_6/phase_6_master_manifest.json"
    assert os.path.exists(manifest_path), "Phase 6 Master Manifest must exist"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    datasets = data.get("datasets", {})
    assert len(datasets) == 16, f"Expected 16 Phase 6 datasets, found {len(datasets)}"
    
    for ds_id, info in datasets.items():
        fpath = info["file_path"]
        assert os.path.exists(fpath), f"Phase 6 dataset {ds_id} missing at {fpath}"
        assert os.path.getsize(fpath) == info["file_size_bytes"], f"Size mismatch for {ds_id}"
        actual_sha = compute_sha256(fpath)
        assert actual_sha == info["sha256_checksum"], f"SHA256 mismatch for {ds_id}"

def test_phase6_nwp_dataset_integrity():
    arch_path = "data/processed/phase6/nwp/nwp_forecast_archive.parquet"
    assert os.path.exists(arch_path)
    df = pd.read_parquet(arch_path)
    
    assert len(df) == 198900, f"Expected 198,900 rows, got {len(df)}"
    assert df["grid_id"].nunique() == 1170
    assert df["initialization_time_utc"].nunique() == 34
    assert set(df["lead_hour"].unique()) == {6, 12, 24, 48, 72}
    assert df["is_native_resolution"].all() == False
    assert (df["native_spatial_resolution_km"] == 27.75).all()
    assert df["apcp_interval_mm"].isna().sum() == 0
    assert df["apcp_accum_mm"].isna().sum() == 0

def test_phase6_ground_rainfall_and_validation():
    reg_path = "data/processed/phase6/ground_rainfall/rain_gauge_station_registry.parquet"
    val_path = "data/processed/phase6/ground_rainfall/gfs_vs_gauge_validation_metrics.parquet"
    assert os.path.exists(reg_path)
    assert os.path.exists(val_path)
    
    df_reg = pd.read_parquet(reg_path)
    df_val = pd.read_parquet(val_path)
    
    assert len(df_reg) == 21
    assert df_reg["is_primary_hydrological_gauge"].sum() == 16
    assert len(df_val) == 256
    
    # MAE should be genuine and positive
    mae = df_val["abs_error_mm"].mean()
    assert 15.0 <= mae <= 25.0, f"Expected genuine MAE ~18 mm, got {mae}"
    
    # Pearson r should be positive but modest
    r = df_val["gfs_forecast_24h_mm"].corr(df_val["observed_24h_mm"])
    assert 0.05 <= r <= 0.35, f"Expected genuine correlation ~0.14, got {r}"

def test_phase6_flood_evidence_and_gate_enforcement():
    gt_path = "data/processed/phase6/flood_evidence/flood_validation_ground_truth_matrix.parquet"
    gate_path = "data/processed/phase6/flood_evidence/flood_evidence_gate_audit.parquet"
    assert os.path.exists(gt_path)
    assert os.path.exists(gate_path)
    
    df_gt = pd.read_parquet(gt_path)
    df_gate = pd.read_parquet(gate_path)
    
    assert len(df_gt) == 1170
    unobs_count = (df_gt["observation_status"] == "UNOBSERVED_DOMAIN_CELL").sum()
    assert unobs_count == 1150, f"Expected 1,150 unobserved cells, got {unobs_count}"
    assert round(unobs_count / len(df_gt) * 100.0, 2) == 98.29
    
    gate_status = df_gate["supervised_ml_flood_prediction_gate"].iloc[0]
    assert gate_status == "BLOCKED_BY_INSUFFICIENT_EVIDENCE"

def test_phase6_sar_processing():
    scene_path = "data/processed/phase6/sar/sar_scene_audit_registry.parquet"
    feat_path = "data/processed/phase6/sar/sar_flood_signature_features.parquet"
    xval_path = "data/processed/phase6/sar/sar_ground_truth_cross_validation.parquet"
    assert os.path.exists(scene_path)
    assert os.path.exists(feat_path)
    assert os.path.exists(xval_path)
    
    df_scenes = pd.read_parquet(scene_path)
    assert len(df_scenes) == 3
    co_flood = df_scenes[df_scenes["role"] == "CO_FLOOD_PEAK_ACQUISITION"]
    assert len(co_flood) == 1
    assert "2022-09-05" in co_flood["acquisition_timestamp_utc"].iloc[0]
    
    df_feat = pd.read_parquet(feat_path)
    assert len(df_feat) == 1170
    assert "CONFIRMED_SPECULAR_WATER_EXPANSION" in df_feat["sar_physical_inundation_class"].values

def test_phase6_hydrology_modelling():
    stat_path = "data/processed/phase6/hydrology/topographic_routing_static_features.parquet"
    dyn_path = "data/processed/phase6/hydrology/dynamic_hydrological_inundation_potential.parquet"
    val_path = "data/processed/phase6/hydrology/hydrology_ground_truth_validation.parquet"
    assert os.path.exists(stat_path)
    assert os.path.exists(dyn_path)
    assert os.path.exists(val_path)
    
    df_stat = pd.read_parquet(stat_path)
    assert len(df_stat) == 1170
    assert df_stat["is_topographic_sink"].sum() == 19
    assert df_stat["upstream_contributing_area_km2"].max() >= 100.0
    
    df_val = pd.read_parquet(val_path)
    pos_hipi = df_val[df_val["observation_status"] == "VERIFIED_POSITIVE"]["hydrological_inundation_potential_index"].mean()
    neg_hipi = df_val[df_val["observation_status"] == "VERIFIED_NEGATIVE"]["hydrological_inundation_potential_index"].mean()
    assert pos_hipi > neg_hipi, f"Positive cells HIPI ({pos_hipi}) must exceed dry cells HIPI ({neg_hipi})"

def test_dashboard_phase6_endpoints():
    ds = load_dashboard_data()
    assert ds.phase6_nwp.get("total_grib2_slices") == 170
    assert ds.phase6_ground_rainfall.get("total_stations_catalogued") == 21
    assert ds.phase6_flood_evidence.get("supervised_ml_flood_prediction_gate") == "BLOCKED_BY_INSUFFICIENT_EVIDENCE"
    assert ds.phase6_sar.get("satellite") == "Sentinel-1A C-SAR (5.405 GHz)"
    assert ds.phase6_hydrology.get("topographic_sinks_identified") == 19
    assert ds.phase6_manifest.get("total_datasets") == 16

