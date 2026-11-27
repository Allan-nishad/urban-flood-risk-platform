"""Stage 4.1 Spatial Coverage, Threshold Provenance, and Full Lifecycle Audit Tests.

All fixtures are explicitly synthetic and isolated in tmp_path.
"""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import urllib.request

from floodrisk.alerts import AlertRuleConfig, AlertStore, OperationalAlertEngine
from floodrisk.dashboard.server import DashboardDataStore, run_dashboard


def _fc(freshness="LIVE", next_24h=70.0, peak_1h=18.0, issue_time="2026-11-27T00:00:00Z"):
    return {
        "provider": "test_fixture_open_meteo",
        "model": "ecmwf_ifs025",
        "freshness": freshness,
        "status": freshness,
        "location_ref": "bengaluru_centroid",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "issue_time_utc": issue_time,
        "retrieval_time_utc": "2026-11-27T05:15:00Z",
        "valid_from_utc": "2026-11-27T06:00:00Z",
        "valid_to_utc": "2026-11-28T06:00:00Z",
        "next_24h_precipitation_mm": next_24h,
        "peak_hourly_precipitation_mm": peak_1h,
        "hourly_forecast": [{"valid_time_utc": "2026-11-27T06:00:00Z", "precipitation": peak_1h}] if freshness in ("LIVE", "RECENT") else [],
    }


def test_633_alert_fixture_spatial_breakdown_and_anchor_scope(tmp_path):
    ds = DashboardDataStore(data_dir=Path("data/processed"), reports_dir=Path("reports"))
    cells = [
        {**f["properties"], "latitude": f["properties"].get("centroid_lat"), "longitude": f["properties"].get("centroid_lon")}
        for f in ds.cells_geojson["features"]
    ]
    assert len(cells) == 1170

    store = AlertStore(tmp_path / "s41_633.db")
    engine = OperationalAlertEngine(store)
    run = engine.evaluate(cells=cells, forecast_payload=_fc(next_24h=70.0, peak_1h=18.0))
    assert run["alerts_created"] == 633

    alerts = store.list_alerts(limit=1000)
    high_cnt = sum(1 for a in alerts if a["severity"] == "HIGH")
    adv_cnt = sum(1 for a in alerts if a["severity"] == "ADVISORY")
    assert high_cnt == 270
    assert adv_cnt == 363
    # Verify explicit regional single-anchor scope metadata
    assert alerts[0]["triggering_inputs"]["spatial_forcing_scope"] == "REGIONAL_SINGLE_ANCHOR_BENGALURU"
    assert alerts[0]["triggering_inputs"]["observed_rainfall_status"] == "UNAVAILABLE"
    store.close()


def test_lifecycle_outage_deescalation_autoresolve_and_active_restart(tmp_path):
    db_path = tmp_path / "s41_lifecycle.db"
    cfg = AlertRuleConfig(cooldown_minutes=120, default_ttl_hours=12.0)
    store = AlertStore(db_path)
    engine = OperationalAlertEngine(store, config=cfg)

    cell = [{
        "grid_id": "TEST_CELL_01",
        "latitude": 12.95,
        "longitude": 77.65,
        "static_susceptibility_score": 0.72,
    }]
    t0 = datetime(2026, 11, 27, 5, 0, tzinfo=timezone.utc)

    # 1. Create WATCH (20mm)
    r1 = engine.evaluate(cell, _fc(next_24h=20.0, peak_1h=4.0, issue_time="2026-11-27T00:00:00Z"), now_utc=t0)
    assert r1["alerts_created"] == 1
    aid = store.list_alerts(lifecycle_state="ACTIVE")[0]["alert_id"]

    # 2. Repeated identical forecast -> suppressed
    r2 = engine.evaluate(cell, _fc(next_24h=20.0, peak_1h=4.0, issue_time="2026-11-27T00:00:00Z"), now_utc=t0 + timedelta(minutes=10))
    assert r2["alerts_suppressed"] == 1

    # 3. Escalate WATCH -> HIGH (70mm)
    r3 = engine.evaluate(cell, _fc(next_24h=70.0, peak_1h=18.0, issue_time="2026-11-27T01:00:00Z"), now_utc=t0 + timedelta(minutes=20))
    assert r3["alerts_updated"] == 1
    assert store.get_alert(aid)["severity"] == "HIGH"

    # 4. De-escalate HIGH -> WATCH (20mm) even with same issue_time
    r4 = engine.evaluate(cell, _fc(next_24h=20.0, peak_1h=4.0, issue_time="2026-11-27T01:00:00Z"), now_utc=t0 + timedelta(minutes=25))
    assert r4["alerts_updated"] == 1
    assert store.get_alert(aid)["severity"] == "WATCH"

    # 5. Forecast becomes STALE or UNAVAILABLE -> skipped, active alert NOT silently resolved!
    for bad in ("STALE", "UNAVAILABLE"):
        r_bad = engine.evaluate(cell, _fc(freshness=bad, next_24h=0.0, peak_1h=0.0), now_utc=t0 + timedelta(minutes=30))
        assert r_bad["status"] == "SKIPPED_STALE_OR_UNAVAILABLE"
        assert store.get_alert(aid)["lifecycle_state"] == "ACTIVE"

    # 6. Server restart during ACTIVE alert preserves state
    store.close()
    store2 = AlertStore(db_path)
    engine2 = OperationalAlertEngine(store2, config=cfg)
    assert store2.get_alert(aid)["lifecycle_state"] == "ACTIVE"

    # 7. Forecast returns after outage with dry conditions (2mm) -> auto-resolves ACTIVE alert
    r_dry = engine2.evaluate(cell, _fc(freshness="LIVE", next_24h=2.0, peak_1h=0.5, issue_time="2026-11-27T02:00:00Z"), now_utc=t0 + timedelta(minutes=45))
    assert r_dry["alerts_auto_resolved"] == 1
    assert store2.get_alert(aid)["lifecycle_state"] == "RESOLVED"
    store2.close()


def test_api_exposes_spatial_scope_metadata():
    srv = run_dashboard(host="127.0.0.1", port=0, blocking=False)
    port = srv.server_address[1]
    try:
        summary = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/alerts/summary", timeout=5).read())
        assert summary["spatial_forcing_scope"] == "REGIONAL_SINGLE_ANCHOR_BENGALURU"
        assert "not 1,170 independent local forecasts" in summary["spatial_coverage_note"]
        listing = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/alerts", timeout=5).read())
        assert listing["spatial_forcing_scope"] == "REGIONAL_SINGLE_ANCHOR_BENGALURU"
    finally:
        srv.shutdown()
        srv.server_close()
