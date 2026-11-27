"""Stage 4 Operational Alert Engine, Lifecycle, Persistence, Scheduler, and API Tests.

All fixtures in this test module are explicitly synthetic test fixtures isolated in tmp_path.
"""

from datetime import datetime, timedelta, timezone
import json
import urllib.error
import urllib.request

import pytest


def _synth_cells():
    return [
        {
            "grid_id": "TEST_CELL_HIGH",
            "latitude": 12.95,
            "longitude": 77.65,
            "static_susceptibility_score": 0.72,
            "elevation_mean_m": 885.0,
            "mean_twi": 14.2,
        },
        {
            "grid_id": "TEST_CELL_MOD",
            "latitude": 12.97,
            "longitude": 77.60,
            "static_susceptibility_score": 0.50,
            "elevation_mean_m": 905.0,
            "mean_twi": 11.5,
        },
        {
            "grid_id": "TEST_CELL_LOW",
            "latitude": 13.00,
            "longitude": 77.55,
            "static_susceptibility_score": 0.25,
            "elevation_mean_m": 930.0,
            "mean_twi": 9.0,
        },
    ]


def _synth_forecast(freshness="LIVE", next_24h=40.0, peak_1h=10.0, issue_time="2026-11-27T00:00:00Z"):
    return {
        "provider": "open_meteo",
        "model": "ecmwf_ifs025",
        "freshness": freshness,
        "status": freshness,
        "issue_time_utc": issue_time,
        "retrieval_time_utc": "2026-11-27T05:00:00Z",
        "valid_from_utc": "2026-11-27T06:00:00Z",
        "valid_to_utc": "2026-11-28T06:00:00Z",
        "next_24h_precipitation_mm": next_24h,
        "peak_hourly_precipitation_mm": peak_1h,
        "hourly_forecast": [{"valid_time_utc": "2026-11-27T06:00:00Z", "precipitation": peak_1h}],
    }


def test_alert_generation_severity_and_ml_gate(tmp_path):
    from floodrisk.alerts import AlertStore, OperationalAlertEngine

    store = AlertStore(tmp_path / "alerts.db")
    engine = OperationalAlertEngine(store)
    assert engine.public_dispatch_enabled is False

    # 1. ML score alone (0.99) with dry forecast (2.0 mm) MUST NOT trigger an alert
    run_dry = engine.evaluate(
        cells=_synth_cells(),
        forecast_payload=_synth_forecast(next_24h=2.0, peak_1h=0.5),
        ml_support_by_grid={"TEST_CELL_HIGH": {"experimental_score": 0.99, "qualification_status": "EXPERIMENTAL_UNVALIDATED"}},
    )
    assert run_dry["alerts_created"] == 0

    # 2. Heavy forecast (70.0 mm) triggers HIGH on TEST_CELL_HIGH and ADVISORY on TEST_CELL_MOD; TEST_CELL_LOW stays below
    run_heavy = engine.evaluate(
        cells=_synth_cells(),
        forecast_payload=_synth_forecast(next_24h=70.0, peak_1h=16.0),
        ml_support_by_grid={"TEST_CELL_HIGH": {"experimental_score": 0.88, "qualification_status": "EXPERIMENTAL_UNVALIDATED"}},
    )
    assert run_heavy["alerts_created"] == 2
    alerts = store.list_alerts(lifecycle_state="ACTIVE")
    by_grid = {a["grid_id"]: a for a in alerts}
    assert by_grid["TEST_CELL_HIGH"]["severity"] == "HIGH"
    assert by_grid["TEST_CELL_HIGH"]["qualification_status"] == "PROVISIONAL_RULE_BASED"
    assert by_grid["TEST_CELL_HIGH"]["experimental_ml_score"] == 0.88
    assert by_grid["TEST_CELL_HIGH"]["experimental_ml_status"] == "EXPERIMENTAL_UNVALIDATED"
    assert "NOT A PUBLIC EMERGENCY WARNING" in by_grid["TEST_CELL_HIGH"]["warning_disclaimer"]
    assert by_grid["TEST_CELL_MOD"]["severity"] == "ADVISORY"
    assert "TEST_CELL_LOW" not in by_grid
    store.close()


def test_stale_and_missing_inputs_never_generate_alerts(tmp_path):
    from floodrisk.alerts import AlertStore, OperationalAlertEngine

    store = AlertStore(tmp_path / "stale.db")
    engine = OperationalAlertEngine(store)

    for bad_state in ("STALE", "UNAVAILABLE", "INVALID"):
        run = engine.evaluate(
            cells=_synth_cells(),
            forecast_payload=_synth_forecast(freshness=bad_state, next_24h=90.0, peak_1h=25.0),
        )
        assert run["status"] == "SKIPPED_STALE_OR_UNAVAILABLE"
        assert run["alerts_created"] == 0

    assert store.list_alerts() == []
    store.close()


def test_duplicate_suppression_cooldown_lifecycle_expiry_and_restart(tmp_path):
    from floodrisk.alerts import (
        AlertNotFoundError,
        AlertRuleConfig,
        AlertStore,
        InvalidLifecycleTransitionError,
        OperationalAlertEngine,
    )

    db_path = tmp_path / "lifecycle.db"
    cfg = AlertRuleConfig(cooldown_minutes=60, default_ttl_hours=4.0)
    store = AlertStore(db_path)
    engine = OperationalAlertEngine(store, config=cfg)

    t0 = datetime(2026, 11, 27, 5, 0, tzinfo=timezone.utc)
    # Create WATCH alert (20.0 mm on HIGH cell)
    r1 = engine.evaluate(_synth_cells(), _synth_forecast(next_24h=20.0, peak_1h=4.0), now_utc=t0)
    assert r1["alerts_created"] == 1
    alert_id = store.list_alerts(lifecycle_state="ACTIVE")[0]["alert_id"]

    # Duplicate suppression on identical forecast
    r2 = engine.evaluate(_synth_cells(), _synth_forecast(next_24h=20.0, peak_1h=4.0), now_utc=t0 + timedelta(minutes=10))
    assert r2["alerts_created"] == 0
    assert r2["alerts_suppressed"] == 1

    # Escalation updates existing alert (20mm -> 70mm)
    r3 = engine.evaluate(_synth_cells(), _synth_forecast(next_24h=70.0, peak_1h=12.0, issue_time="2026-11-27T01:00:00Z"), now_utc=t0 + timedelta(minutes=15))
    assert r3["alerts_updated"] >= 1

    # Acknowledge -> Resolve lifecycle
    ack = engine.acknowledge_alert(alert_id, actor="tester", note="Checking cell")
    assert ack["lifecycle_state"] == "ACKNOWLEDGED"
    with pytest.raises(InvalidLifecycleTransitionError):
        engine.acknowledge_alert(alert_id, actor="tester")

    res = engine.resolve_alert(alert_id, actor="tester", note="Verified clear", now_utc=t0 + timedelta(minutes=20))
    assert res["lifecycle_state"] == "RESOLVED"
    assert res["qualification_status"] == "RESOLVED"
    with pytest.raises(InvalidLifecycleTransitionError):
        engine.resolve_alert(alert_id, actor="tester")
    with pytest.raises(AlertNotFoundError):
        engine.acknowledge_alert("ALT-DOESNOTEXIST")

    # Cooldown suppression within 60 minutes for resolved alert
    r4 = engine.evaluate(
        [_synth_cells()[0]],
        _synth_forecast(next_24h=70.0, peak_1h=12.0, issue_time="2026-11-27T02:00:00Z"),
        now_utc=t0 + timedelta(minutes=30),
    )
    assert r4["alerts_created"] == 0
    assert r4["alerts_suppressed"] == 1

    # Restart recovery check: close and reopen AlertStore on same db_path
    store.close()
    store2 = AlertStore(db_path)
    engine2 = OperationalAlertEngine(store2, config=cfg)
    persisted = store2.get_alert(alert_id)
    assert persisted is not None
    assert persisted["lifecycle_state"] == "RESOLVED"
    assert len(persisted["audit_trail"]) >= 3

    # Expiry check after TTL
    r5 = engine2.evaluate(
        [_synth_cells()[0]],
        _synth_forecast(next_24h=70.0, peak_1h=12.0, issue_time="2026-11-27T03:00:00Z"),
        now_utc=t0 + timedelta(hours=2),
    )
    assert r5["alerts_created"] == 1
    active_id = store2.list_alerts(lifecycle_state="ACTIVE")[0]["alert_id"]
    expired_cnt = engine2.expire_stale_alerts(now_dt=t0 + timedelta(hours=7))
    assert expired_cnt == 1
    assert store2.get_alert(active_id)["lifecycle_state"] == "EXPIRED"
    store2.close()


def test_scheduler_integration_triggers_alert_evaluation(tmp_path):
    from floodrisk.alerts import AlertStore, OperationalAlertEngine
    from floodrisk.live.scheduler import LiveWeatherRefresher
    from floodrisk.live.storage import LiveWeatherStore

    class _FakeAdapter:
        preferred_model = "ecmwf_ifs025"

        def fetch_forecast(self):
            return {
                "provider": "open_meteo",
                "model_id": "ecmwf_ifs025",
                "retrieval_time_utc": "2026-11-27T05:00:00Z",
                "records": [
                    {
                        "provider": "open_meteo",
                        "location_ref": "bengaluru_center",
                        "latitude": 12.9716,
                        "longitude": 77.5946,
                        "data_type": "FORECAST",
                        "variable": "precipitation",
                        "value": 25.0,
                        "unit": "mm",
                        "issue_time_utc": "2026-11-27T00:00:00Z",
                        "valid_time_utc": "2026-11-27T06:00:00Z",
                        "retrieval_time_utc": "2026-11-27T05:00:00Z",
                        "model_id": "ecmwf_ifs025",
                        "quality_status": "AVAILABLE",
                    }
                ],
            }

    db_path = tmp_path / "sched.db"
    wstore = LiveWeatherStore(db_path)
    astore = AlertStore(db_path)
    engine = OperationalAlertEngine(astore)
    triggered = []

    def _on_success(_summary):
        run = engine.evaluate(
            cells=_synth_cells(),
            forecast_payload=_synth_forecast(next_24h=25.0, peak_1h=5.0),
        )
        triggered.append(run)

    refresher = LiveWeatherRefresher(wstore, adapter=_FakeAdapter(), on_refresh_success=_on_success)
    res = refresher.refresh_once()
    assert res["success"] is True
    assert len(triggered) == 1
    assert triggered[0]["alerts_created"] == 1
    assert len(astore.list_alerts(lifecycle_state="ACTIVE")) == 1
    astore.close()
    wstore.close()


def test_api_alerts_endpoints_and_validation(tmp_path):
    from floodrisk.alerts import AlertStore, OperationalAlertEngine
    from floodrisk.dashboard.server import get_datastore, run_dashboard

    srv = run_dashboard(host="127.0.0.1", port=0, blocking=False)
    port = srv.server_address[1]
    base_url = f"http://127.0.0.1:{port}"
    ds = get_datastore()
    orig_store, orig_engine = ds.alert_store, ds.alert_engine
    test_store = AlertStore(tmp_path / "api_alerts.db")
    ds.alert_store = test_store
    ds.alert_engine = OperationalAlertEngine(test_store)

    try:
        # Summary & list
        with urllib.request.urlopen(f"{base_url}/api/alerts/summary", timeout=5) as resp:
            assert resp.status == 200
            summary = json.loads(resp.read().decode("utf-8"))
        assert summary["public_dispatch_enabled"] is False
        assert summary["ml_qualification_gate"] == "BLOCKED_EXPERIMENTAL_MODEL"

        with urllib.request.urlopen(f"{base_url}/api/alerts", timeout=5) as resp:
            assert resp.status == 200
            listing = json.loads(resp.read().decode("utf-8"))
        assert listing["public_dispatch_enabled"] is False

        # Invalid state parameter -> 400
        with pytest.raises(urllib.error.HTTPError) as exc_400:
            urllib.request.urlopen(f"{base_url}/api/alerts?state=BOGUS", timeout=5)
        assert exc_400.value.code == 400

        # Unknown alert ID -> 404
        with pytest.raises(urllib.error.HTTPError) as exc_404:
            urllib.request.urlopen(f"{base_url}/api/alerts/ALT-UNKNOWN999", timeout=5)
        assert exc_404.value.code == 404

        # Unsupported POST route -> 405
        req_405 = urllib.request.Request(f"{base_url}/api/alerts/broadcast_public", data=b"{}", method="POST")
        with pytest.raises(urllib.error.HTTPError) as exc_405:
            urllib.request.urlopen(req_405, timeout=5)
        assert exc_405.value.code == 405

        # Evaluate via synthetic forecast injection into isolated test store & test ack/resolve API
        run_res = ds.alert_engine.evaluate(
            cells=[_synth_cells()[0]],
            forecast_payload=_synth_forecast(next_24h=70.0, peak_1h=15.0, issue_time="2026-11-27T09:00:00Z"),
        )
        assert run_res["alerts_created"] == 1
        test_alerts = ds.alert_store.list_alerts(lifecycle_state="ACTIVE", grid_id="TEST_CELL_HIGH")
        assert len(test_alerts) == 1
        aid = test_alerts[0]["alert_id"]
        req_ack = urllib.request.Request(
            f"{base_url}/api/alerts/{aid}/acknowledge",
            data=json.dumps({"actor": "api_test"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_ack, timeout=5) as r_ack:
            assert r_ack.status == 200
            ack_body = json.loads(r_ack.read().decode("utf-8"))
        assert ack_body["alert"]["lifecycle_state"] == "ACKNOWLEDGED"

        # 409 on duplicate acknowledge
        with pytest.raises(urllib.error.HTTPError) as exc_409:
            urllib.request.urlopen(req_ack, timeout=5)
        assert exc_409.value.code == 409

        req_res = urllib.request.Request(
            f"{base_url}/api/alerts/{aid}/resolve",
            data=json.dumps({"actor": "api_test", "note": "Cleanup synthetic test alert"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req_res, timeout=5) as r_res:
            assert r_res.status == 200
            res_body = json.loads(r_res.read().decode("utf-8"))
        assert res_body["alert"]["lifecycle_state"] == "RESOLVED"
    finally:
        ds.alert_store = orig_store
        ds.alert_engine = orig_engine
        test_store.close()
        srv.shutdown()
        srv.server_close()
