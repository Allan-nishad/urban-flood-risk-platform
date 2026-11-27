"""Regression and contract tests for Dashboard HTTP API and Data-State Contract."""

import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest


def test_state_contract_vocabulary_exists():
    from floodrisk.state_contract import DATA_STATES, make_state_field

    assert set(DATA_STATES) == {
        "AVAILABLE",
        "PARTIAL",
        "UNAVAILABLE",
        "UNOBSERVED",
        "UNVALIDATED",
        "STALE",
    }
    field = make_state_field(None, "UNOBSERVED", "test_source", "2026-11-27T00:00:00Z")
    assert field == {
        "value": None,
        "status": "UNOBSERVED",
        "source": "test_source",
        "timestamp": "2026-11-27T00:00:00Z",
    }


def test_phase7_manifest_and_phase6_evidence_in_datastore():
    from floodrisk.dashboard.server import DashboardDataStore

    ds = DashboardDataStore(data_dir=Path("data/processed"), reports_dir=Path("reports"))
    # Phase 7 manifest (73 entries)
    assert ds.phase7_manifest.get("status") == "AVAILABLE"
    assert ds.phase7_manifest.get("total_datasets_registered") == 73
    assert len(ds.phase7_manifest.get("datasets", {})) == 73

    # Phase 6 24-record independent incident inventory separate from legacy 21-record incidents
    assert len(ds.incidents) == 21
    assert ds.phase6_flood_evidence.get("incident_record_count") == 24
    assert len(ds.phase6_flood_evidence.get("incident_records", [])) == 24
    assert "independent_flood_incident_inventory.parquet" in ds.phase6_flood_evidence.get("incident_inventory_source", "")

    # Stale rainfall provenance on /api/cells
    feat0 = ds.cells_geojson["features"][0]["properties"]
    assert feat0.get("observed_rainfall_state") == "STALE"
    assert "Phase 4.3" in feat0.get("observed_rainfall_source", "")
    assert feat0.get("observed_rainfall_timestamp") is not None


def test_cli_process_rainfall_missing_dir_reports_unavailable(tmp_path):
    from click.testing import CliRunner
    from floodrisk.cli import main

    runner = CliRunner()
    missing_dir = tmp_path / "nonexistent_imerg"
    res = runner.invoke(main, ["process-rainfall", "--rainfall-dir", str(missing_dir)])
    assert res.exit_code == 0
    assert "UNAVAILABLE" in res.output
