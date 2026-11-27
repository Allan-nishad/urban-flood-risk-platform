"""Automated Unit and Integration Tests for Phase 5.

Verifies:
1. Operational NWP latency enforcement and forecast cycle reconstruction.
2. Independent rainfall observation harmonization across reporting intervals.
3. Space-time matching, continuous error metrics, and WMO categorical skill metrics.
4. Copernicus Sentinel-1A SAR SAFE audit and 24-day baseline constraints.
5. 7-class flood validation matrix, unobserved cell handling, and ROC-AUC / PR-AUC metrics.
6. Cryptographic integrity of the Phase 5 dataset manifest.
7. Dashboard REST API endpoints for Phase 5 verification views.
"""

import hashlib
import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from floodrisk.dashboard.server import run_dashboard
from floodrisk.validation.forecast_verification import (
    calculate_categorical_contingency_metrics,
    calculate_continuous_verification_metrics,
    enforce_latency_rule,
    ingest_independent_rainfall_observations,
    match_forecast_and_observations,
    reconstruct_archived_nwp_forecasts,
)
from floodrisk.validation.flood_validation import (
    audit_sentinel1_safe_manifest,
    build_flood_validation_matrix,
    evaluate_risk_indicators_against_evidence,
    structure_independent_flood_evidence,
)


def test_phase5_forecast_reconstruction_and_latency():
    """Verify operational NWP latency rule and cycle reconstruction."""
    t_init = "2022-09-05T00:00:00Z"
    assert enforce_latency_rule(t_init, "2022-09-05T04:30:00Z", latency_hours=4.5) is True
    assert enforce_latency_rule(t_init, "2022-09-05T05:00:00Z", latency_hours=4.5) is True
    assert enforce_latency_rule(t_init, "2022-09-05T04:29:59Z", latency_hours=4.5) is False
    assert enforce_latency_rule(t_init, "2022-09-05T02:00:00Z", latency_hours=4.5) is False

    # Test reconstruction on a mini grid
    df_grid = pd.DataFrame({
        "grid_id": ["g1", "g2", "g3"],
        "centroid_lat": [12.90, 13.00, 13.10],
        "centroid_lon": [77.50, 77.60, 77.70],
    })
    df_fcst = reconstruct_archived_nwp_forecasts(
        df_grid=df_grid,
        start_date="2022-09-04",
        end_date="2022-09-05",
        lead_times_hours=[6, 12, 24, 48, 72],
        cycles_per_day=[0, 12],
    )
    assert len(df_fcst) == 2 * 2 * 5 * 3  # 2 days * 2 cycles * 5 lead times * 3 cells = 60
    assert "source_pixel_id" in df_fcst.columns
    assert "forecast_depth_mm" in df_fcst.columns
    assert (df_fcst["forecast_depth_mm"] >= 0).all()
    assert set(df_fcst["lead_time_hours"].unique()) == {6, 12, 24, 48, 72}


def test_phase5_rainfall_observations_ingestion():
    """Verify independent rainfall observation ingestion and category mapping."""
    df_grid = pd.DataFrame({"grid_id": ["g1", "g2"]})
    df_rain = pd.DataFrame({
        "grid_id": ["g1", "g2"],
        "date": ["2022-09-05", "2022-09-05"],
        "rainfall_daily_depth_mm": [75.0, 10.0],
    })
    df_obs = ingest_independent_rainfall_observations(df_rain, df_grid)
    assert len(df_obs) == 6  # 2 cells * 3 intervals (24h, 12h, 6h)
    assert "observation_source" in df_obs.columns
    assert "observed_category" in df_obs.columns
    
    # 24h category checks
    sub_24 = df_obs[df_obs["accumulation_interval_hours"] == 24]
    assert sub_24.loc[sub_24["grid_id"] == "g1", "observed_category"].iloc[0] == "HEAVY_RAINFALL_CATEGORY"
    assert sub_24.loc[sub_24["grid_id"] == "g2", "observed_category"].iloc[0] == "LIGHT_RAINFALL_CATEGORY"


def test_phase5_space_time_matching_and_metrics():
    """Verify space-time matching, continuous error metrics, and WMO contingency scores."""
    # Synthetic forecast and observation
    y_f = np.array([5.0, 15.0, 25.0, 70.0, 80.0])
    y_o = np.array([4.0, 16.0, 20.0, 65.0, 90.0])

    cont = calculate_continuous_verification_metrics(y_f, y_o)
    assert cont["sample_size"] == 5
    assert cont["mae_mm"] > 0
    assert cont["rmse_mm"] >= cont["mae_mm"]
    assert cont["pearson_r"] > 0.95

    # Categorical threshold at 64.5 mm
    cat = calculate_categorical_contingency_metrics(y_f, y_o, threshold_mm=64.5)
    assert cat["hits"] == 2
    assert cat["false_alarms"] == 0
    assert cat["misses"] == 0
    assert cat["correct_negatives"] == 3
    assert cat["pod"] == 1.0
    assert cat["far"] == 0.0
    assert cat["csi"] == 1.0
    assert cat["heidke_skill_score"] == 1.0


def test_phase5_sentinel1_manifest_audit():
    """Verify Copernicus Sentinel-1A SAR SAFE scene manifest properties."""
    df_sar = audit_sentinel1_safe_manifest(output_path="scratch/test_sar_manifest.parquet")
    assert len(df_sar) == 3
    assert "S1A_IW_GRDH_1SDV_20220905T004616" in df_sar["scene_id"].iloc[1]
    assert df_sar["relative_orbit"].iloc[0] == 165
    assert df_sar["flight_direction"].iloc[0] == "DESCENDING"
    assert df_sar["role"].tolist() == ["PRE_EVENT_BASELINE", "CO_FLOOD_PEAK", "POST_FLOOD_RECESSION"]


def test_phase5_flood_validation_matrix_and_taxonomy():
    """Verify 7-class validation matrix and non-circular evaluation."""
    df_grid = pd.DataFrame({
        "grid_id": [f"g_{i}" for i in range(10)],
        "centroid_lat": np.linspace(12.9, 13.1, 10),
        "centroid_lon": np.linspace(77.5, 77.7, 10),
        "elevation_mean_m": np.linspace(920, 850, 10),
        "slope_mean_deg": np.ones(10) * 1.5,
        "builtup_fraction": np.linspace(0.8, 0.2, 10),
        "twi_mean": np.linspace(6.0, 10.0, 10),
    })
    df_ev = pd.DataFrame({
        "event_id": ["ev_1", "ev_2"],
        "event_date": ["2022-09-05", "2022-09-05"],
        "location_name": ["Loc1", "Loc2"],
        "latitude": [12.92, 12.95],
        "longitude": [77.52, 77.55],
        "grid_id": ["g_1", "g_2"],
        "evidence_category": ["confirmed_inundation", "reported_waterlogging"],
        "evidence_confidence": ["high", "medium"],
        "spatial_uncertainty_m": [100.0, 200.0],
    })
    df_dyn = pd.DataFrame({
        "grid_id": [f"g_{i}" for i in range(10)],
        "dynamic_risk_prioritization_score": np.linspace(0.1, 0.9, 10),
        "static_susceptibility_score": np.linspace(0.2, 0.8, 10),
        "forecast_exposure_score_24h": np.linspace(0.1, 0.5, 10),
    })
    
    df_matrix = build_flood_validation_matrix(
        df_grid=df_grid,
        df_evidence=structure_independent_flood_evidence(df_ev, "scratch/test_ev.parquet"),
        df_dynamic=df_dyn,
        output_path="scratch/test_val_matrix.parquet",
    )
    assert len(df_matrix) == 10
    assert "UNOBSERVED" in df_matrix["validation_class"].values
    assert "CONFIRMED_INUNDATION" in df_matrix["validation_class"].values
    assert "distance_to_nearest_flood_km" in df_matrix.columns

    df_eval = evaluate_risk_indicators_against_evidence(
        df_matrix,
        output_path="scratch/test_eval.parquet",
    )
    assert len(df_eval) >= 3
    assert "roc_auc" in df_eval.columns
    assert "pr_auc" in df_eval.columns


def test_phase5_manifest_integrity():
    """Verify that all 8 datasets in phase_5_dataset_manifest.json exist and match checksums."""
    manifest_path = Path("reports/phase_5_dataset_manifest.json")
    assert manifest_path.is_file(), "phase_5_dataset_manifest.json missing"
    
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["campaign"] == "PHASE_5_INDEPENDENT_VALIDATION_AND_FORECAST_SKILL_ASSESSMENT"
    assert len(data["datasets"]) == 8

    for ds_id, meta in data["datasets"].items():
        p = Path(meta["file_path"])
        assert p.is_file(), f"File {p} does not exist"
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert h == meta["sha256_checksum"], f"SHA256 mismatch for {ds_id}"
        assert meta["rows"] > 0, f"Empty dataset {ds_id}"


def test_phase5_dashboard_endpoints():
    """Verify that Phase 5 dashboard REST endpoints respond with HTTP 200 and valid schemas."""
    server = run_dashboard(host="127.0.0.1", port=8598, blocking=False)
    try:
        # 1. Verification metrics
        url_m = "http://127.0.0.1:8598/api/phase5/verification-metrics"
        with urllib.request.urlopen(url_m, timeout=5) as resp:
            assert resp.status == 200
            data_m = json.loads(resp.read().decode())
            assert len(data_m) == 15
            assert "lead_time_hours" in data_m[0]

        # 2. Flood validation
        url_v = "http://127.0.0.1:8598/api/phase5/flood-validation"
        with urllib.request.urlopen(url_v, timeout=5) as resp:
            assert resp.status == 200
            data_v = json.loads(resp.read().decode())
            assert data_v["total_cells"] == 1170
            assert data_v["unobserved_cells"] == 1148

        # 3. SAR Manifest
        url_s = "http://127.0.0.1:8598/api/phase5/sar-manifest"
        with urllib.request.urlopen(url_s, timeout=5) as resp:
            assert resp.status == 200
            data_s = json.loads(resp.read().decode())
            assert len(data_s) == 3

        # 4. Readiness Gates
        url_g = "http://127.0.0.1:8598/api/phase5/readiness-gates"
        with urllib.request.urlopen(url_g, timeout=5) as resp:
            assert resp.status == 200
            data_g = json.loads(resp.read().decode())
            assert data_g["gate_a"]["status"] == "CONDITIONAL_ACCEPTANCE"
            assert data_g["gate_b"]["status"] == "REJECTED_BLOCKED"
    finally:
        server.shutdown()
        server.server_close()

