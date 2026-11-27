"""
Phase 4 & 4.7 Automated Validation Test Suite.
Validates NWP forecast ingestion, multi-horizon exposure indicators,
four-layer dynamic risk intelligence, flood event monitoring lifecycle,
dashboard REST APIs, and cryptographic manifest integrity.
"""

from pathlib import Path
import json
import urllib.request
import time
import pytest
import pandas as pd
import numpy as np

from floodrisk.provenance import DatasetManifest
from floodrisk.dashboard.server import get_datastore, run_dashboard


DATA_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")


def test_forecast_rainfall_schema_and_decoupling():
    """Verify forecast dataset schema, temporal decoupling, and non-negative rainfall."""
    p = DATA_DIR / "forecast_rainfall_bengaluru.parquet"
    assert p.is_file(), f"Forecast dataset missing: {p}"

    df = pd.read_parquet(p)
    assert len(df) >= 60000, f"Expected >= 60,000 rows, got {len(df)}"

    expected_cols = [
        "forecast_id", "provider", "model_name", "forecast_issue_time",
        "valid_time", "lead_time_hours", "grid_id",
        "precipitation_value", "precipitation_depth_mm",
        "source_pixel_id", "source_resolution", "mapping_method",
        "model_initialization_status"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing expected forecast column: {col}"

    # Temporal decoupling: lead hours must be non-negative
    assert (df["lead_time_hours"] >= 0).all(), "Detected negative lead hours"

    # Issue time must precede or equal valid time
    issue_ts = pd.to_datetime(df["forecast_issue_time"])
    valid_ts = pd.to_datetime(df["valid_time"])
    assert (valid_ts >= issue_ts).all(), "Detected valid time strictly earlier than issue time"

    # Physical validity: rainfall rate cannot be negative
    assert (df["precipitation_value"] >= 0.0).all(), "Detected negative precipitation value"
    assert (df["precipitation_depth_mm"] >= 0.0).all(), "Detected negative precipitation depth"

    # Spatial coarse grid verification: exactly 9 unique anchors
    unique_anchors = df["source_pixel_id"].unique()
    assert len(unique_anchors) == 9, f"Expected exactly 9 coarse regional anchors, got {len(unique_anchors)}"


def test_forecast_exposure_indicators_bounds_and_categories():
    """Verify 1,170 cell multi-horizon indicators and internal rainfall categories."""
    p = DATA_DIR / "forecast_exposure_indicators_bengaluru.parquet"
    assert p.is_file(), f"Indicators dataset missing: {p}"

    df = pd.read_parquet(p)
    assert len(df) == 1170, f"Expected exactly 1,170 grid cells, got {len(df)}"

    # Check accumulations are non-decreasing across horizons
    assert (df["forecast_rainfall_24h_mm"] >= 0.0).all()
    assert (df["forecast_rainfall_72h_mm"] >= df["forecast_rainfall_24h_mm"] - 1e-5).all()

    # Check valid internal rainfall categories (explicitly not official warnings)
    valid_cats = {
        "LIGHT_RAINFALL_CATEGORY",
        "MODERATE_RAINFALL_CATEGORY",
        "HEAVY_RAINFALL_CATEGORY",
        "NO_PRECIPITATION"
    }
    cats_present = set(df["forecast_intensity_category"].unique())
    assert cats_present.issubset(valid_cats), f"Unexpected warning categories: {cats_present - valid_cats}"

    # Verify official warning disclaimer column exists
    assert "official_warning_status" in df.columns
    assert "INTERNAL_METEOROLOGICAL_CLASSIFICATION" in df["official_warning_status"].iloc[0]

    # Categorization logic consistency
    heavy_mask = df["forecast_rainfall_24h_mm"] >= 64.5
    assert (df.loc[heavy_mask, "forecast_intensity_category"] == "HEAVY_RAINFALL_CATEGORY").all()

    mod_mask = (df["forecast_rainfall_24h_mm"] >= 15.6) & (df["forecast_rainfall_24h_mm"] < 64.5)
    assert (df.loc[mod_mask, "forecast_intensity_category"] == "MODERATE_RAINFALL_CATEGORY").all()


def test_dynamic_risk_intelligence_four_layer_separation():
    """Verify segregation of the 4 data layers and composite score bounds."""
    p = DATA_DIR / "dynamic_risk_intelligence_bengaluru.parquet"
    assert p.is_file(), f"Dynamic risk intelligence dataset missing: {p}"

    df = pd.read_parquet(p)
    assert len(df) == 1170, f"Expected 1,170 rows, got {len(df)}"

    # Layer 1: Static Susceptibility
    assert "elevation_mean_m" in df.columns
    assert "built_up_fraction" in df.columns
    assert "static_susceptibility_score" in df.columns
    assert "static_susceptibility_rank" in df.columns

    # Layer 2: Observed Rainfall Exposure
    assert "observed_rainfall_24h_mm" in df.columns
    assert "observed_api_decay_mm" in df.columns
    assert "observed_rainfall_exposure_score" in df.columns

    # Layer 3: Forecast Rainfall Exposure
    assert "forecast_rainfall_24h_mm" in df.columns
    assert "forecast_exposure_score_24h" in df.columns
    assert "forecast_intensity_category" in df.columns

    # Layer 4: Ground Flood Evidence
    assert "has_ground_flood_evidence" in df.columns
    assert "historical_incident_count" in df.columns
    assert "historical_incident_categories" in df.columns

    # Dynamic composite score
    assert "dynamic_risk_prioritization_score" in df.columns
    assert "dynamic_risk_rank" in df.columns
    assert "dynamic_score_status" in df.columns
    assert "research_monitoring_level" in df.columns

    # Bounds check [0, 1]
    scores = df["dynamic_risk_prioritization_score"]
    assert scores.min() >= 0.0, f"Score below 0: {scores.min()}"
    assert scores.max() <= 1.0, f"Score above 1: {scores.max()}"

    # Ranking consistency: rank 1 must have the maximum score
    rank_1_score = df.loc[df["dynamic_risk_rank"] == 1, "dynamic_risk_prioritization_score"].iloc[0]
    assert rank_1_score == scores.max(), "Rank 1 does not correspond to highest score"


def test_flood_event_monitoring_log_lifecycle():
    """Verify monitoring log episodes, separation of archive vs live watch."""
    p = DATA_DIR / "flood_event_monitoring_log.parquet"
    assert p.is_file(), f"Monitoring log missing: {p}"

    df = pd.read_parquet(p)
    assert len(df) == 6, f"Expected 6 monitored episodes, got {len(df)}"

    valid_states = {"WATCH", "ACTIVE_RAINFALL_EVENT", "FLOOD_EVIDENCE_REPORTED", "UNDER_REVIEW", "CLOSED"}
    assert set(df["lifecycle_state"].unique()).issubset(valid_states)

    # Active forecast episode must be in WATCH state and NOT historical archive
    fc_ep = df[df["episode_id"] == "EP-LIVE-FCST"]
    assert len(fc_ep) == 1
    assert fc_ep["lifecycle_state"].iloc[0] == "WATCH"
    assert bool(fc_ep["is_historical_archive"].iloc[0]) is False

    # Historical Aug-Sep 2022 episodes must be in CLOSED state and IS historical archive
    closed_eps = df[df["episode_id"].isin(["EP-2022-08-W1", "EP-2022-08-STORM1", "EP-2022-09-DELUGE"])]
    assert (closed_eps["lifecycle_state"] == "CLOSED").all()
    assert (closed_eps["is_historical_archive"] == True).all()


def test_dashboard_datastore_and_rest_endpoints():
    """Verify dashboard in-memory store and live HTTP responses."""
    store = get_datastore(data_dir=DATA_DIR, reports_dir=REPORTS_DIR)
    assert store.summary["study_area"]["total_cells"] == 1170
    assert store.summary["study_area"]["boundary_status"] == "pending_authoritative_boundary"
    assert len(store.cells_geojson["features"]) == 1170
    assert len(store.incidents) == 21
    assert len(store.episodes) == 6

    # Launch test server on port 8586
    server = run_dashboard(port=8586, data_dir=DATA_DIR, reports_dir=REPORTS_DIR, blocking=False)
    time.sleep(0.5)

    try:
        endpoints = [
            "/api/health",
            "/api/summary",
            "/api/cells",
            "/api/incidents",
            "/api/episodes",
            "/api/manifest",
            "/"
        ]
        for ep in endpoints:
            url = f"http://127.0.0.1:8586{ep}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                assert resp.status == 200, f"Endpoint {ep} returned status {resp.status}"
                data = resp.read()
                assert len(data) > 0, f"Endpoint {ep} returned empty payload"
    finally:
        server.shutdown()
        server.server_close()


def test_cryptographic_manifest_integrity():
    """Verify that 100% of registered datasets match their cryptographic SHA-256 hashes."""
    manifest_p = REPORTS_DIR / "dataset_manifest.json"
    assert manifest_p.is_file(), f"Manifest missing: {manifest_p}"

    manifest = DatasetManifest.load(manifest_p)
    assert len(manifest.datasets) >= 33, f"Expected >= 33 registered datasets, got {len(manifest.datasets)}"

    phase4_keys = [
        "forecast_rainfall_bengaluru",
        "forecast_exposure_indicators_bengaluru",
        "dynamic_risk_intelligence_bengaluru",
        "flood_event_monitoring_log"
    ]
    for k in phase4_keys:
        assert k in manifest.datasets, f"Phase 4 deliverable '{k}' missing from manifest"

    verif = manifest.verify_integrity()
    failures = {k: v for k, v in verif.items() if v["status"] != "VALID"}
    assert len(failures) == 0, f"Manifest verification failed for: {failures}"
