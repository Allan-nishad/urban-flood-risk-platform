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


@pytest.fixture(scope="module")
def live_server_url():
    from floodrisk.dashboard.server import run_dashboard

    srv = run_dashboard(host="127.0.0.1", port=0, blocking=False)
    port = srv.server_address[1]
    yield f"http://127.0.0.1:{port}"
    srv.shutdown()
    srv.server_close()


def _http_req(url: str, method: str = "GET"):
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, dict(resp.headers), json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except Exception:
            body = raw
        return e.code, dict(e.headers), body


def test_api_cells_filter_and_404_on_invalid_grid_id(live_server_url):
    sc, _, body = _http_req(f"{live_server_url}/api/cells?grid_id=INVALID_999")
    assert sc == 404
    assert {"error", "code", "detail"}.issubset(body.keys())

    sc_ok, _, body_ok = _http_req(f"{live_server_url}/api/cells?grid_id=g1000_7472_1625")
    assert sc_ok == 200
    assert len(body_ok["features"]) == 1
    assert body_ok["features"][0]["properties"]["grid_id"] == "g1000_7472_1625"


def test_api_400_on_unknown_query_params(live_server_url):
    for path in ["/api/cells?foo=bar", "/api/summary?bad=1"]:
        sc, _, body = _http_req(f"{live_server_url}{path}")
        assert sc == 400
        assert {"error", "code", "detail"}.issubset(body.keys())


def test_api_405_json_on_unsupported_method(live_server_url):
    sc, hdrs, body = _http_req(f"{live_server_url}/api/cells", method="POST")
    assert sc == 405
    assert "application/json" in hdrs.get("Content-Type", "")
    assert isinstance(body, dict)
    assert {"error", "code", "detail"}.issubset(body.keys())


def test_api_404_unified_error_schema(live_server_url):
    sc, _, body = _http_req(f"{live_server_url}/api/nonexistent")
    assert sc == 404
    assert {"error", "code", "detail"}.issubset(body.keys())


def test_api_cross_endpoint_consistency(live_server_url):
    _, _, summary = _http_req(f"{live_server_url}/api/summary")
    _, _, cells = _http_req(f"{live_server_url}/api/cells")
    _, _, incidents = _http_req(f"{live_server_url}/api/incidents")
    _, _, p6_ev = _http_req(f"{live_server_url}/api/phase6/flood-evidence")
    _, _, p7_man = _http_req(f"{live_server_url}/api/phase7/manifest")

    assert summary["study_area"]["total_cells"] == len(cells["features"]) == 1170
    assert summary["historical_surveillance"]["total_incidents_catalogued"] == len(incidents) == 21
    assert p6_ev["incident_record_count"] == 24
    assert p7_man["total_datasets_registered"] == 73

