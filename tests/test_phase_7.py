"""
tests/test_phase_7.py
Unit and Integration Tests for Phase 7 Research Deliverables, Verification, and Uncertainty.
"""
import os
import json
import hashlib
import pytest
import pandas as pd
import numpy as np

from floodrisk.dashboard.server import load_dashboard_data, DashboardDataStore

def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_phase7_datasets_exist():
    expected_files = [
        "data/processed/phase7/nwp/phase7_forecast_error_registry.parquet",
        "data/processed/phase7/verification/phase7_forecast_verification_metrics.parquet",
        "data/processed/phase7/flood_evidence/phase7_flood_evidence_assessment.parquet",
        "data/processed/phase7/sar_validation/phase7_sar_evidence_comparison.parquet",
        "data/processed/phase7/hydrology/phase7_hydrology_comparison.parquet"
    ]
    for p in expected_files:
        assert os.path.exists(p), f"Missing Phase 7 dataset at: {p}"
        assert os.path.getsize(p) > 0, f"Empty file: {p}"

def test_phase7_nwp_verification_metrics():
    df = pd.read_parquet("data/processed/phase7/nwp/phase7_forecast_error_registry.parquet")
    assert len(df) == 256, f"Expected 256 pairs, found {len(df)}"
    assert df["station_id"].nunique() == 16, "Expected 16 primary stations"
    assert df["target_obs_date"].nunique() == 16, "Expected 16 target dates"
    
    mae = float(df["abs_error_mm"].mean())
    rmse = float(np.sqrt((df["forecast_error_mm"]**2).mean()))
    bias = float(df["forecast_error_mm"].mean())
    r = float(np.corrcoef(df["gfs_forecast_24h_mm"], df["observed_24h_mm"])[0, 1])
    
    assert round(mae, 2) == 18.64
    assert round(rmse, 2) == 33.19
    assert round(bias, 2) == -10.88
    assert round(r, 3) == 0.142

def test_phase7_contingency_heavy_rain_pod():
    m_df = pd.read_parquet("data/processed/phase7/verification/phase7_forecast_verification_metrics.parquet")
    row_64 = m_df[m_df["threshold_mm"] == 64.5].iloc[0]
    
    assert row_64["hits"] == 0, "Expected 0 hits at >= 64.5 mm"
    assert row_64["misses"] == 23, "Expected 23 misses at >= 64.5 mm"
    assert row_64["pod"] == 0.0, "Expected POD = 0.00 at >= 64.5 mm"
    assert row_64["correct_negatives"] == 233

def test_phase7_grouped_uncertainty_inflation():
    json_path = "reports/phase_7/phase7B_grouped_uncertainty_results.json"
    assert os.path.exists(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    comp = {row["metric"]: row for row in data["uncertainty_comparison"]}
    # Verify uncertainty inflation is >= 2.0x due to spatial/temporal clustering
    assert comp["MAE"]["uncertainty_width_inflation_factor"] >= 2.5
    assert comp["RMSE"]["uncertainty_width_inflation_factor"] >= 2.5
    assert comp["Pearson r"]["uncertainty_width_inflation_factor"] >= 3.0
    
    # Verify date-clustered CI for Pearson r spans zero
    r_ci = comp["Pearson r"]["date_clustered_ci_95"]
    assert r_ci[0] < 0.0 and r_ci[1] > 0.0, f"Expected Pearson r CI to span zero, got {r_ci}"

def test_phase7_flood_evidence_domain_accounting():
    df = pd.read_parquet("data/processed/phase7/flood_evidence/phase7_flood_evidence_assessment.parquet")
    assert len(df) == 1170
    vc = df["observation_status"].value_counts().to_dict()
    assert vc["UNOBSERVED_DOMAIN_CELL"] == 1150
    assert vc["VERIFIED_POSITIVE"] == 13
    assert vc["VERIFIED_NEGATIVE"] == 7
    
    # Verify no unobserved cell is marked usable for supervised training
    unobs = df[df["observation_status"] == "UNOBSERVED_DOMAIN_CELL"]
    assert (unobs["is_usable_for_supervised_training"] == False).all()
    assert (unobs["binary_flood_target"] == -1).all()

def test_phase7_sar_sensitivity_deconstruction():
    df = pd.read_parquet("data/processed/phase7/sar_validation/phase7_sar_evidence_comparison.parquet")
    pos = df[df["ground_truth_status"] == "VERIFIED_POSITIVE"]
    assert len(pos) == 13
    
    # 5 true specular, 4 permanent water, 1 double-bounce, 3 missed
    vc = pos["rigorous_evaluation_class"].value_counts().to_dict()
    assert vc["TRUE_POSITIVE_FLOOD_EXPANSION"] == 5
    assert vc["CONFLATED_PERMANENT_WATER"] == 4
    assert vc["DIELECTRIC_BUILDING_REFLECTION"] == 1
    assert vc["FALSE_NEGATIVE_MISSED_BY_RADAR"] == 3

def test_phase7_hydrology_depression_and_auc_bounds():
    df = pd.read_parquet("data/processed/phase7/hydrology/phase7_hydrology_comparison.parquet")
    assert len(df) == 1170
    assert df["is_closed_sink"].sum() == 19
    
    # Verify that flow accumulation differs downstream due to sink overflow
    diff = df["flow_acc_conditioned_km2"] - df["flow_acc_retained_km2"]
    assert diff.max() >= 10.0, "Expected at least 10 km2 divergence from sink overflow"

def test_phase7_dashboard_store_and_endpoints():
    ds = DashboardDataStore()
    ds.load_data()
    assert "7A_Data_Freeze" in ds.phase7_summary.get("workstreams", {})
    assert ds.phase7_summary.get("supervised_ml_flood_prediction_gate") == "BLOCKED_BY_INSUFFICIENT_EVIDENCE"
    assert "uncertainty_comparison" in ds.phase7_uncertainty

