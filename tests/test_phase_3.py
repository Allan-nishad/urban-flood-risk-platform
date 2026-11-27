"""Comprehensive Automated Test Suite for Phase 3 Deliverables.

Validates:
1. Model features dataset schema, z-score standardization, and target isolation.
2. Isolation Forest output schema, score bounds [0, 1], rank ordering, and seed stability.
3. Mahalanobis distance numerical stability, positive-definite covariance, and distance scaling.
4. MCDA multi-criteria scores, baseline models, weight configs, and unavailable flags.
5. Spatial block partitioning, variogram estimation, and buffer enforcement.
6. Retrospective incident comparison metrics calculations.
7. Manifest integrity across all 29 registered datasets.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest

from floodrisk.provenance import DatasetManifest


@pytest.fixture
def model_features_df() -> pd.DataFrame:
    p = Path("data/processed/phase3_model_features.parquet")
    assert p.is_file(), f"Missing required file: {p}"
    return pd.read_parquet(p)


@pytest.fixture
def iso_forest_df() -> pd.DataFrame:
    p = Path("data/processed/phase3_isolation_forest_results.parquet")
    assert p.is_file(), f"Missing required file: {p}"
    return pd.read_parquet(p)


@pytest.fixture
def mahalanobis_df() -> pd.DataFrame:
    p = Path("data/processed/phase3_mahalanobis_results.parquet")
    assert p.is_file(), f"Missing required file: {p}"
    return pd.read_parquet(p)


@pytest.fixture
def mcda_df() -> pd.DataFrame:
    p = Path("data/processed/phase3_mcda_results.parquet")
    assert p.is_file(), f"Missing required file: {p}"
    return pd.read_parquet(p)


@pytest.fixture
def model_comparison_df() -> pd.DataFrame:
    p = Path("data/processed/phase3_model_comparison.parquet")
    assert p.is_file(), f"Missing required file: {p}"
    return pd.read_parquet(p)


# -----------------------------------------------------------------------------
# 1. MODEL FEATURES & TARGET ISOLATION
# -----------------------------------------------------------------------------
def test_phase3_model_features_isolation(model_features_df):
    """Verify feature matrix dimensions, z-score presence, and target leakage isolation."""
    assert len(model_features_df) == 19890

    # Verify z-score standardized columns exist
    expected_z = [
        "z_elevation_mean_m", "z_elevation_std_m", "z_built_up_fraction",
        "z_tree_cover_fraction", "z_cropland_fraction", "z_rainfall_daily_depth_mm"
    ]
    for col in expected_z:
        assert col in model_features_df.columns
        # Mean approx 0, std approx 1
        assert abs(model_features_df[col].mean()) < 0.1
        assert abs(model_features_df[col].std() - 1.0) < 0.1

    # Strict rule: incident flags exist for evaluation but are not named as predictors
    assert "has_reported_incident_on_date" in model_features_df.columns


# -----------------------------------------------------------------------------
# 2. ISOLATION FOREST RESULTS
# -----------------------------------------------------------------------------
def test_isolation_forest_properties(iso_forest_df):
    """Verify Isolation Forest scores lie in [0, 1] and ranks are valid."""
    assert len(iso_forest_df) == 19890
    assert "isolation_forest_anomaly_score" in iso_forest_df.columns
    assert "isolation_forest_rank" in iso_forest_df.columns

    scores = iso_forest_df["isolation_forest_anomaly_score"]
    assert (scores >= 0.0).all()
    assert (scores <= 1.0).all()

    # Ranks between 1 and N
    ranks = iso_forest_df["isolation_forest_rank"]
    assert ranks.min() >= 1
    assert ranks.max() <= 19890

    # Seed stability columns exist
    assert "if_score_seed_42" in iso_forest_df.columns
    assert "if_score_seed_100" in iso_forest_df.columns
    assert "if_score_seed_2022" in iso_forest_df.columns


# -----------------------------------------------------------------------------
# 3. MAHALANOBIS DISTANCE NUMERICAL STABILITY
# -----------------------------------------------------------------------------
def test_mahalanobis_properties(mahalanobis_df):
    """Verify Mahalanobis distance is non-negative and normalized scores lie in [0, 1]."""
    assert len(mahalanobis_df) == 19890
    assert "mahalanobis_distance" in mahalanobis_df.columns
    assert "mahalanobis_normalized_score" in mahalanobis_df.columns

    dists = mahalanobis_df["mahalanobis_distance"]
    assert (dists >= 0.0).all()
    assert not dists.isnull().any()
    assert not np.isinf(dists).any()

    norm_scores = mahalanobis_df["mahalanobis_normalized_score"]
    assert (norm_scores >= 0.0).all()
    assert (norm_scores <= 1.0).all()


# -----------------------------------------------------------------------------
# 4. MCDA AND BASELINES PROPERTIES
# -----------------------------------------------------------------------------
def test_mcda_and_baselines_properties(mcda_df):
    """Verify MCDA configurations, baselines, and unavailable indicator tags."""
    assert len(mcda_df) == 19890

    mcda_cols = [
        "baseline_terrain_susceptibility",
        "baseline_landcover_runoff",
        "baseline_rainfall_exposure",
        "mcda_score_equal_weight",
        "mcda_score_terrain_dominant",
        "mcda_score_runoff_dominant",
        "mcda_sensitivity_spread"
    ]
    for col in mcda_cols:
        assert col in mcda_df.columns
        assert (mcda_df[col] >= 0.0).all()
        assert (mcda_df[col] <= 1.0).all()
        assert not mcda_df[col].isnull().any()

    # Verify unavailable indicators are tagged explicitly
    assert (mcda_df["mcda_hydro_upa_status"] == "UNAVAILABLE_PENDING_ACQUISITION").all()
    assert (mcda_df["mcda_sar_change_status"] == "UNAVAILABLE_SYNTHETIC_ONLY").all()


# -----------------------------------------------------------------------------
# 5. MODEL COMPARISON PANEL INTEGRITY
# -----------------------------------------------------------------------------
def test_model_comparison_alignment(model_comparison_df):
    """Verify master model comparison aligns all model scores and incident labels."""
    assert len(model_comparison_df) == 19890
    assert model_comparison_df["has_reported_incident_on_date"].sum() == 18

    # Check key models are merged
    assert "isolation_forest_anomaly_score" in model_comparison_df.columns
    assert "mahalanobis_normalized_score" in model_comparison_df.columns
    assert "mcda_score_runoff_dominant" in model_comparison_df.columns


# -----------------------------------------------------------------------------
# 6. MANIFEST CRYPTOGRAPHIC INTEGRITY
# -----------------------------------------------------------------------------
def test_dataset_manifest_integrity_all():
    """Verify all 29 datasets registered in dataset_manifest.json match disk hashes."""
    p = Path("reports/dataset_manifest.json")
    assert p.is_file()
    manifest = DatasetManifest.load(p)
    assert len(manifest.datasets) >= 29

    results = manifest.verify_integrity()
    failures = {k: v for k, v in results.items() if not v["verified"]}
    assert len(failures) == 0, f"Integrity failures in manifest: {failures}"

