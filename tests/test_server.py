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
        "LIVE",
        "RECENT",
        "HISTORICAL",
        "INVALID",
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


def test_frontend_html_integration_and_no_duplicates():
    html = Path("src/floodrisk/dashboard/static/index.html").read_text(encoding="utf-8")

    # 1. No duplicate phase6Tab or table body IDs
    assert html.count('id="phase6Tab"') == 1
    assert html.count('id="phase6GroundTruthTbody"') == 1
    assert html.count('id="phase6ManifestTbody"') == 1

    # 2. Phase 6 & 7 endpoints actually fetched by frontend
    for route in [
        "/api/phase6/nwp",
        "/api/phase6/sar",
        "/api/phase6/hydrology",
        "/api/phase7/summary",
        "/api/phase7/uncertainty",
        "/api/phase7/manifest",
    ]:
        assert route in html, f"Frontend missing fetch for {route}"

    # 3. No hardcoded Rainbow Drive row in JS and no null->NORMAL fallback
    assert "<tr><td><strong>Rainbow Drive Layout</strong>" not in html
    assert '|| "NORMAL"' not in html
    assert 'id="apiErrorBanner"' in html
    assert "STALE" in html


def test_all_registered_routes_inventory_and_valid_json(live_server_url):
    import re
    server_src = Path("src/floodrisk/dashboard/server.py").read_text(encoding="utf-8")
    routes = sorted(set(re.findall(r'clean_path\s*==\s*[\'"](/api/[^\'"]+)[\'"]', server_src)))
    assert len(routes) >= 20

    for route in routes:
        sc, hdrs, body = _http_req(f"{live_server_url}{route}")
        assert sc == 200, f"{route} returned {sc}"
        assert "application/json" in hdrs.get("Content-Type", "")
        assert isinstance(body, (dict, list)) and len(body) > 0, f"{route} returned empty payload"


def test_sar_metric_review_exposes_audited_breakdown(live_server_url):
    sc, _, sar = _http_req(f"{live_server_url}/api/phase6/sar")
    assert sc == 200
    assert sar["verified_positive_total"] == 13
    assert sar["true_specular_detections"] == 5
    assert sar["true_specular_sensitivity_pct"] == 38.5
    assert sar["lake_conflated_count"] == 4
    assert sar["sar_metric_status"] == "EXPLORATORY_UNVALIDATED"


def test_datastore_missing_and_empty_data_behavior(tmp_path):
    from floodrisk.dashboard.server import DashboardDataStore

    ds = DashboardDataStore(data_dir=tmp_path, reports_dir=tmp_path)
    assert ds.cells_geojson == {}
    assert ds.incidents == []
    assert ds.episodes == []
    assert ds.phase7_manifest["status"] == "UNAVAILABLE"
    assert ds.summary["study_area"]["total_cells"] == 0


def test_playwright_interactive_dashboard(live_server_url):
    from playwright.sync_api import sync_playwright

    edge_path = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    if not edge_path.is_file():
        pytest.skip("Microsoft Edge binary not installed")

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(edge_path), headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        page_errors = []
        failed_api = []
        page.on("pageerror", lambda err: page_errors.append(str(err)))
        page.on("response", lambda resp: failed_api.append((resp.url, resp.status)) if "/api/" in resp.url and resp.status >= 400 else None)

        page.goto(live_server_url, wait_until="networkidle")
        page.wait_for_function("document.getElementById('kpiTotalCells').innerText.includes('1,170')")

        # 1. Verify initial KPIs, SAR honest metric, and V8 Stage 1 live weather bar
        assert page.inner_text("#kpiHeavyRain") == "0 Cells"
        assert page.inner_text("#kpiMax24h") == "6.10 mm"
        assert "STALE" in page.inner_text("#inspObsStateBadge")
        assert page.inner_text("#p6SarVal") == "5/13 True Specular (38.5%)"
        page.wait_for_function("document.getElementById('liveFcstProvider').innerText !== 'Loading...'")
        assert page.inner_text("#liveFcstProvider") == "open_meteo"
        assert page.inner_text("#liveFcstModel") == "ecmwf_ifs025"
        assert page.inner_text("#liveObsStatus") == "UNAVAILABLE"

        # 2. Switch every top-right panel tab
        for tab in ["forecastTab", "incidentsTab", "inspectorTab"]:
            page.click(f'button[data-tab="{tab}"]')
            assert page.is_visible(f"#{tab}")

        # 3. Switch every bottom analytics tab & verify Phase 6 (24 rows) + Phase 7 manifest (73 rows)
        for btab in ["manifestTableTab", "devSarTab", "phase5Tab", "phase6Tab", "episodesTableTab"]:
            page.click(f'button[data-bottom-tab="{btab}"]')
            assert page.is_visible(f"#{btab}")

        page.click('button[data-bottom-tab="phase6Tab"]')
        assert page.locator("#phase6GroundTruthTbody tr").count() == 24
        assert page.locator("#phase7ManifestTbody tr").count() == 73

        # 4. Click a grid cell polygon on the Leaflet map and verify cell inspector updates
        first_id = page.inner_text("#inspCellId")
        polygons = page.locator("svg.leaflet-zoom-animated path.leaflet-interactive")
        assert polygons.count() > 100
        polygons.nth(10).click(force=True)
        assert len(page.inner_text("#inspCellId")) > 0 and page.inner_text("#inspCellId") != "Loading..."

        # 5. Mobile viewport check (375x812)
        page.set_viewport_size({"width": 375, "height": 812})
        assert page.is_visible("#map")
        assert len(page_errors) == 0, f"JS page errors: {page_errors}"
        assert len(failed_api) == 0, f"Failed API requests: {failed_api}"

        # 6. Simulate API failure and verify #apiErrorBanner becomes visible
        err_page = browser.new_page()
        err_page.route("**/api/cells", lambda route: route.abort())
        err_page.goto(live_server_url, wait_until="domcontentloaded")
        err_page.wait_for_selector("#apiErrorBanner", state="visible", timeout=5000)
        assert "API_ERROR" in err_page.inner_text("#apiErrorBanner")

        browser.close()



