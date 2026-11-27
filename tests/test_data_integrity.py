"""Tier 4 Data Integrity & Scientific Consistency Tests."""

import json
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


def test_master_grid_count_ids_and_crs():
    gdf = gpd.read_file("data/processed/grid_bengaluru_urban_1000m.gpkg")
    assert len(gdf) == 1170
    assert gdf["grid_id"].nunique() == 1170
    assert str(gdf.crs) == "EPSG:6933"

    pattern = re.compile(r"^g1000_\d+_\d+$")
    assert gdf["grid_id"].apply(lambda gid: bool(pattern.match(str(gid)))).all()
    expected = [f"g1000_{r['col_idx']}_{r['row_idx']}" for _, r in gdf.iterrows()]
    assert list(gdf["grid_id"]) == expected


def test_spatial_joins_preserve_grid_ids():
    gdf = gpd.read_file("data/processed/grid_bengaluru_urban_1000m.gpkg")
    master_ids = set(gdf["grid_id"])

    for p in [
        "data/processed/dynamic_risk_intelligence_bengaluru.parquet",
        "data/processed/phase6/flood_evidence/flood_validation_ground_truth_matrix.parquet",
        "data/processed/phase6/hydrology/topographic_routing_static_features.parquet",
        "data/processed/phase7/hydrology/phase7_hydrology_comparison.parquet",
    ]:
        df = pd.read_parquet(p)
        assert len(df) == 1170, f"{p} expected 1170 rows, got {len(df)}"
        assert df["grid_id"].nunique() == 1170
        assert set(df["grid_id"]) == master_ids


def test_dynamic_risk_formula_reproduces_baseline():
    df = pd.read_parquet("data/processed/dynamic_risk_intelligence_bengaluru.parquet")
    recomputed = (
        0.35 * df["static_susceptibility_score"]
        + 0.30 * df["observed_rainfall_exposure_score"]
        + 0.35 * df["forecast_exposure_score_24h"]
    ).clip(0.0, 1.0)
    max_err = float(np.abs(df["dynamic_risk_prioritization_score"] - recomputed).max())
    assert max_err < 1e-6


def test_unobserved_nulls_not_coerced_to_zero_or_dry():
    df_gt = pd.read_parquet("data/processed/phase6/flood_evidence/flood_validation_ground_truth_matrix.parquet")
    counts = df_gt["observation_status"].value_counts().to_dict()
    assert counts["UNOBSERVED_DOMAIN_CELL"] == 1150
    assert counts["VERIFIED_POSITIVE"] == 13
    assert counts["VERIFIED_NEGATIVE"] == 7

    unobs = df_gt[df_gt["observation_status"] == "UNOBSERVED_DOMAIN_CELL"]
    assert (unobs["binary_flood_target"] == -1).all()
    assert unobs["water_depth_est_m"].isna().all()


def test_manifests_separate_and_consistent():
    m33 = json.loads(Path("reports/dataset_manifest.json").read_text(encoding="utf-8"))
    m16 = json.loads(Path("reports/phase_6/phase_6_master_manifest.json").read_text(encoding="utf-8"))
    m73 = json.loads(Path("reports/phase_7_manifests/phase_7_final_manifest.json").read_text(encoding="utf-8"))

    assert len(m33["datasets"]) == 33
    assert len(m16["datasets"]) == 16
    assert len(m73["datasets"]) == 73
    assert m73["total_datasets_registered"] == 73

    # Verify Phase 7.2 frozen manifest paths exist and sizes match
    for ds_id, rec in m73["datasets"].items():
        fp = Path(rec["file_path"])
        assert fp.is_file(), f"Missing frozen manifest file for {ds_id}: {fp}"
        assert fp.stat().st_size == rec["file_size_bytes"], f"Size mismatch for {ds_id}"


def test_incident_inventories_separate_and_traceable():
    df21 = pd.read_parquet("data/processed/flood_event_inventory_bengaluru.parquet")
    df24 = pd.read_parquet("data/processed/phase6/flood_evidence/independent_flood_incident_inventory.parquet")
    assert len(df21) == 21
    assert len(df24) == 24
    assert "event_id" in df21.columns
    assert "evidence_id" in df24.columns


def test_sar_sensitivity_audit_matches_phase7_evidence():
    df_p7s = pd.read_parquet("data/processed/phase7/sar_validation/phase7_sar_evidence_comparison.parquet")
    pos = df_p7s[df_p7s["ground_truth_status"] == "VERIFIED_POSITIVE"]
    assert len(pos) == 13
    assert int(pos["is_true_specular_flood_detection"].sum()) == 5
    assert int(pos["is_conflated_with_permanent_lake"].sum()) == 4
    assert int(pos["is_missed_due_to_urban_canyon"].sum()) == 3
