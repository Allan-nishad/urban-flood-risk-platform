"""Comprehensive Automated Test Suite for Phase 2B Deliverables.

Validates:
1. Feature Registry completeness and scientific status tags.
2. Static feature matrix schema, bounds, physical consistency, and explicit UPA NaNs.
3. Rainfall feature matrix temporal consistency, units, and antecedent calculations.
4. Integrated panel merge integrity, SAR fixture exclusion, and incident linking.
5. Exploratory risk indicators mathematical bounds [0, 1], unavailable fixtures, and sensitivity spread.
6. Dataset Manifest cryptographic integrity across all registered deliverables.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from floodrisk.provenance import DatasetManifest


@pytest.fixture
def static_df() -> pd.DataFrame:
    p = Path("data/processed/features_static_bengaluru.parquet")
    assert p.is_file(), f"Missing required file: {p}"
    return pd.read_parquet(p)


@pytest.fixture
def rainfall_df() -> pd.DataFrame:
    p = Path("data/processed/features_rainfall_bengaluru.parquet")
    assert p.is_file(), f"Missing required file: {p}"
    return pd.read_parquet(p)


@pytest.fixture
def integrated_df() -> pd.DataFrame:
    p = Path("data/processed/features_integrated_bengaluru.parquet")
    assert p.is_file(), f"Missing required file: {p}"
    return pd.read_parquet(p)


@pytest.fixture
def indicators_df() -> pd.DataFrame:
    p = Path("data/processed/exploratory_risk_indicators_bengaluru.parquet")
    assert p.is_file(), f"Missing required file: {p}"
    return pd.read_parquet(p)


@pytest.fixture
def feature_registry() -> dict:
    p = Path("data/processed/feature_registry.json")
    assert p.is_file(), f"Missing required file: {p}"
    with open(p, "r") as f:
        return json.load(f)


# -----------------------------------------------------------------------------
# 1. FEATURE REGISTRY VALIDATION
# -----------------------------------------------------------------------------
def test_feature_registry_structure(feature_registry):
    """Test registry schema, versioning, and presence of mandatory fields."""
    assert feature_registry["registry_version"] == "1.0.0"
    features = feature_registry["features"]
    assert len(features) >= 15

    for feat_name, feat in features.items():
        assert "source_dataset" in feat
        assert "verification_status" in feat
        assert "units" in feat
        assert "native_spatial_resolution" in feat
        assert "temporal_type" in feat

        # Strict rule: SAR is synthetic test only, cannot be registered as verified real
        if "sar" in feat_name.lower():
            assert feat["verification_status"] != "VERIFIED_REAL"


# -----------------------------------------------------------------------------
# 2. STATIC FEATURES MATRIX VALIDATION
# -----------------------------------------------------------------------------
def test_static_features_dimensions_and_ids(static_df):
    """Verify static dataset dimensions (1,170 cells) and ID naming standard."""
    assert len(static_df) == 1170
    assert "grid_id" in static_df.columns

    # Verify ID format: g{size}_{col}_{row}
    sample_ids = static_df["grid_id"].head(50).tolist()
    for gid in sample_ids:
        assert gid.startswith("g1000_"), f"Invalid grid ID format: {gid}"
        parts = gid.split("_")
        assert len(parts) == 3
        assert parts[1].isdigit()
        assert parts[2].isdigit()


def test_static_features_completeness_and_physical_consistency(static_df):
    """Ensure authentic features have 0 nulls, UPA has 100% nulls, and elevations are ordered."""
    verified_cols = [
        "elevation_mean_m", "elevation_min_m", "elevation_max_m", "elevation_std_m",
        "built_up_fraction", "water_fraction", "tree_cover_fraction",
        "cropland_fraction", "grassland_fraction", "shrubland_fraction",
    ]
    for col in verified_cols:
        assert static_df[col].isnull().sum() == 0, f"Unexpected nulls in {col}"

    # Physical elevation ordering: min <= mean <= max
    assert (static_df["elevation_min_m"] <= static_df["elevation_mean_m"]).all()
    assert (static_df["elevation_mean_m"] <= static_df["elevation_max_m"]).all()

    # Elevation range for Bengaluru Deccan plateau
    assert static_df["elevation_mean_m"].min() >= 700.0
    assert static_df["elevation_mean_m"].max() <= 1000.0

    # Land cover fractions in [0, 1] and sum <= 1.0001
    lc_cols = [
        "built_up_fraction", "water_fraction", "tree_cover_fraction",
        "cropland_fraction", "grassland_fraction", "shrubland_fraction"
    ]
    for col in lc_cols:
        assert (static_df[col] >= 0.0).all()
        assert (static_df[col] <= 1.0).all()

    lc_sum = static_df[lc_cols].sum(axis=1)
    assert (lc_sum <= 1.0001).all(), "Land cover sum exceeds 1.0"

    # MERIT Hydro UPA must be 100% null (pending acquisition)
    assert static_df["upa_mean_sqkm"].isnull().all()
    assert static_df["upa_max_sqkm"].isnull().all()


# -----------------------------------------------------------------------------
# 3. RAINFALL FEATURES MATRIX VALIDATION
# -----------------------------------------------------------------------------
def test_rainfall_features_panel_structure(rainfall_df):
    """Verify rainfall panel row count (1,170 cells * 17 dates = 19,890)."""
    assert len(rainfall_df) == 19890
    assert rainfall_df["grid_id"].nunique() == 1170
    assert rainfall_df["date"].nunique() == 17

    # Depth must be non-negative and realistic
    assert (rainfall_df["rainfall_daily_depth_mm"] >= 0.0).all()
    assert (rainfall_df["rainfall_daily_depth_mm"] <= 300.0).all()

    # Antecedent precipitation index must be positive
    assert (rainfall_df["precip_api_decay_mm"] >= 0.0).all()


# -----------------------------------------------------------------------------
# 4. INTEGRATED PANEL DATASET VALIDATION
# -----------------------------------------------------------------------------
def test_integrated_panel_merge_integrity(integrated_df):
    """Verify integrated panel merge completeness, SAR exclusion, and incident counts."""
    assert len(integrated_df) == 19890
    assert len(integrated_df.columns) == 53

    # Ensure SAR is explicitly marked as excluded from observational matrix
    assert (integrated_df["sar_observational_status"] == "SYNTHETIC_TEST_ONLY_EXCLUDED").all()

    # Verify incident counts: exactly 18 rows link to verified geocoded flood incidents
    incident_rows = integrated_df[integrated_df["has_reported_incident_on_date"] == True]
    assert len(incident_rows) == 18

    # Ensure unlabelled rows are NOT assigned a synthetic negative label
    assert "binary_flood_label" not in integrated_df.columns
    assert "is_dry" not in integrated_df.columns


# -----------------------------------------------------------------------------
# 5. EXPLORATORY RISK INDICATORS VALIDATION
# -----------------------------------------------------------------------------
def test_exploratory_risk_indicators_bounds_and_sensitivities(indicators_df):
    """Verify all indicators are strictly bounded in [0.0, 1.0], and unavailable fixtures are NaN."""
    assert len(indicators_df) == 19890

    component_indicators = [
        "indicator_terrain",
        "indicator_landcover",
        "indicator_rainfall",
    ]
    for ind in component_indicators:
        assert (indicators_df[ind] >= 0.0).all()
        assert (indicators_df[ind] <= 1.0).all()
        assert indicators_df[ind].isnull().sum() == 0

    # Unavailable fixtures
    assert indicators_df["indicator_hydro"].isnull().all()
    assert (indicators_df["indicator_hydro_status"] == "UNAVAILABLE_PENDING_MERIT_HYDRO").all()
    assert indicators_df["indicator_sar"].isnull().all()
    assert (indicators_df["indicator_sar_status"] == "UNAVAILABLE_SAR_SYNTHETIC_ONLY").all()

    # Composite schemes bounded in [0, 1]
    composite_schemes = [
        "composite_risk_equal",
        "composite_risk_terrain_dominant",
        "composite_risk_runoff_dominant",
    ]
    for scheme in composite_schemes:
        assert (indicators_df[scheme] >= 0.0).all()
        assert (indicators_df[scheme] <= 1.0).all()
        assert indicators_df[scheme].isnull().sum() == 0

    # Sensitivity spread non-negative
    assert (indicators_df["weight_sensitivity_spread"] >= 0.0).all()

    # Meteorological response: peak storm day (2022-09-05) must have higher mean rainfall indicator than baseline (2022-08-25)
    date_strs = indicators_df["date"].apply(lambda d: d.isoformat() if hasattr(d, "isoformat") else str(d))
    mean_rain_peak = indicators_df[date_strs == "2022-09-05"]["indicator_rainfall"].mean()
    mean_rain_base = indicators_df[date_strs == "2022-08-25"]["indicator_rainfall"].mean()
    assert mean_rain_peak > mean_rain_base * 2.0


# -----------------------------------------------------------------------------
# 6. MANIFEST CRYPTOGRAPHIC INTEGRITY
# -----------------------------------------------------------------------------
def test_manifest_cryptographic_integrity():
    """Verify that every single registered dataset in dataset_manifest.json matches its disk hash."""
    manifest_path = Path("reports/dataset_manifest.json")
    assert manifest_path.is_file()

    manifest = DatasetManifest.load(manifest_path)
    assert len(manifest.datasets) >= 24

    results = manifest.verify_integrity()
    failures = {k: v for k, v in results.items() if not v["verified"]}
    assert len(failures) == 0, f"Manifest integrity failures detected: {failures}"
