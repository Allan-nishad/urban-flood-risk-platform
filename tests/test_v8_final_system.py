"""Tests for V8 Final Execution: 72h rainfall windows, risk engine, ML, security, and packaging."""

import json
from pathlib import Path
import time
import urllib.error
import urllib.request

import pytest

from floodrisk.alerts import (
    AlertStore,
    assess_cell_for_horizon,
    evaluate_cell_risk_timeline,
    evaluate_forecast_risk_grid,
)
from floodrisk.dashboard.server import get_datastore, run_dashboard
from floodrisk.live import (
    HORIZON_HOURS,
    LiveWeatherRefresher,
    LiveWeatherStore,
    cleanup_old_backups,
    compute_rainfall_windows,
)
from floodrisk.ml import ExperimentalFloodInference


def test_compute_rainfall_windows_72h_and_partial():
    hourly = [
        {"valid_time_utc": f"2026-11-27T{h % 24:02d}:00:00Z", "precipitation": 2.0 if h != 5 else None}
        for h in range(72)
    ]
    # Give unique monotonic timestamps
    for idx, row in enumerate(hourly):
        day = 27 + idx // 24
        hr = idx % 24
        row["valid_time_utc"] = f"2026-11-{day:02d}T{hr:02d}:00:00Z"

    wins = compute_rainfall_windows(hourly)
    assert tuple(int(k[:-1]) for k in wins.keys()) == HORIZON_HOURS
    assert wins["1h"]["cumulative_mm"] == 2.0
    assert wins["1h"]["quality_status"] == "AVAILABLE"
    assert wins["3h"]["cumulative_mm"] == 6.0
    assert wins["6h"]["missing_hours"] == 1
    assert wins["6h"]["quality_status"] == "PARTIAL"
    assert wins["72h"]["available_hours"] == 71
    assert wins["72h"]["cumulative_mm"] == 142.0

    empty_wins = compute_rainfall_windows([])
    assert empty_wins["24h"]["quality_status"] == "UNAVAILABLE"
    assert empty_wins["24h"]["cumulative_mm"] is None


def test_weather_store_schema_version_history_and_backup_retention(tmp_path):
    store = LiveWeatherStore(tmp_path / "v8.db")
    health = store.check_db_health()
    assert health["schema_version"] == LiveWeatherStore.SCHEMA_VERSION

    class _FakeAdapter:
        preferred_model = "ecmwf_ifs025"
        use_multi_zone = False

        def fetch_forecast(self):
            return {
                "provider": "open_meteo",
                "model_id": "ecmwf_ifs025",
                "issue_time_utc": "2026-11-27T06:00:00Z",
                "retrieval_time_utc": "2026-11-27T07:00:00Z",
                "zones_fetched": 1,
                "records": [
                    {
                        "provider": "open_meteo",
                        "location_ref": "bengaluru_centroid",
                        "latitude": 13.0,
                        "longitude": 77.5,
                        "data_type": "FORECAST",
                        "variable": "precipitation",
                        "value": 4.5,
                        "unit": "mm",
                        "issue_time_utc": "2026-11-27T06:00:00Z",
                        "valid_time_utc": "2026-11-27T08:00:00Z",
                        "retrieval_time_utc": "2026-11-27T07:00:00Z",
                        "model_id": "ecmwf_ifs025",
                        "quality_status": "AVAILABLE",
                    }
                ],
            }

    ref = LiveWeatherRefresher(store, adapter=_FakeAdapter(), max_retries=1)
    res = ref.refresh_once()
    assert res["success"] is True

    hist = store.get_refresh_history(limit=10)
    assert len(hist) == 1
    assert hist[0]["success"] is True
    assert hist[0]["records_written"] == 1

    bdir = tmp_path / "backups"
    bdir.mkdir()
    for i in range(5):
        p = bdir / f"floodrisk_v8_20261127T00000{i}Z.db"
        p.write_bytes(b"sqlite")
        time.sleep(0.01)
    removed = cleanup_old_backups(bdir, keep=3)
    assert removed == 2
    assert len(list(bdir.glob("floodrisk_v8_*.db"))) == 3
    store.close()


def test_forecast_risk_engine_and_insufficient_data_handling():
    zones = {
        "blr_center": {
            "freshness": "LIVE",
            "requested_latitude": 12.9716,
            "requested_longitude": 77.5946,
            "latitude": 13.0,
            "longitude": 77.5,
            "native_resolution_deg": 0.25,
            "hourly_forecast": [
                {"valid_time_utc": f"2026-11-{27 + i // 24:02d}T{i % 24:02d}:00:00Z", "precipitation": 3.0}
                for i in range(72)
            ],
        }
    }
    good_cell = {
        "grid_id": "CELL_1",
        "latitude": 12.98,
        "longitude": 77.60,
        "static_susceptibility_score": 0.72,
        "topographic_wetness_index": 14.5,
        "upstream_contributing_area_km2": 12.0,
        "built_up_fraction": 0.80,
        "water_fraction": 0.05,
        "tree_cover_fraction": 0.10,
        "has_ground_flood_evidence": True,
        "historical_incident_count": 2,
    }
    a24 = assess_cell_for_horizon(good_cell, zones, horizon_hours=24)
    assert a24["is_calibrated_probability"] is False
    assert a24["rainfall_accumulation_mm"] == 72.0
    assert a24["risk_category"] in ("HIGH", "CRITICAL")
    assert a24["spatial_coverage_status"] == "COVERED_BY_SECTOR_ANCHOR"
    assert a24["contributing_factors"]["historical_flood_evidence"] is True

    tl = evaluate_cell_risk_timeline(good_cell, zones)
    assert len(tl) == len(HORIZON_HOURS)

    # Out-of-range cell -> never classified as LOW/safe
    far_cell = {"grid_id": "FAR_1", "latitude": 15.0, "longitude": 79.0, "static_susceptibility_score": 0.2}
    far_a = assess_cell_for_horizon(far_cell, zones, horizon_hours=24)
    assert far_a["risk_category"] == "INSUFFICIENT_DATA"
    assert far_a["risk_prioritization_index"] is None

    # Stale forecast -> INSUFFICIENT_DATA
    stale_zones = {"blr_center": {**zones["blr_center"], "freshness": "STALE"}}
    stale_a = assess_cell_for_horizon(good_cell, stale_zones, horizon_hours=24)
    assert stale_a["risk_category"] == "INSUFFICIENT_DATA"

    grid_res = evaluate_forecast_risk_grid([good_cell, far_cell], zones, horizon_hours=24)
    assert grid_res["total_cells"] == 2
    assert grid_res["is_calibrated_probability"] is False


def test_experimental_ml_explanations_and_gates():
    inf = ExperimentalFloodInference()
    if inf.model is None:
        pytest.skip("Experimental ML model artifact not present")
    res = inf.predict_records([
        {
            "grid_id": "g1000_7476_1635",
            "elevation_m": 811.0,
            "slope_deg": 1.5,
            "upstream_contributing_area_km2": 5.0,
            "topographic_wetness_index": 13.0,
            "depression_depth_m": 0.0,
            "is_closed_sink": 0,
            "built_up_fraction": 0.85,
            "tree_cover_fraction": 0.12,
            "cropland_fraction": 0.0,
            "water_fraction": 0.0,
            "era5_rain_24h_pre_mm": 10.0,
            "era5_rain_72h_pre_mm": 20.0,
            "era5_api_7d_pre_mm": 30.0,
            "era5_pre_missing_flag": 0,
        }
    ])
    assert res["qualification_status"] == "EXPERIMENTAL_UNVALIDATED"
    assert res["warning_gate"] == "BLOCKED_EXPERIMENTAL_MODEL"
    pred = res["predictions"][0]
    assert pred["is_calibrated_probability"] is False
    assert len(pred["top_contributing_features"]) > 0


def test_alert_store_column_allowlist(tmp_path):
    store = AlertStore(tmp_path / "allow.db")
    with pytest.raises(ValueError, match="Disallowed alert update column"):
        store.update_alert_fields("ALT-1", {"lifecycle_state = 'ACTIVE'; --": "x"})
    store.close()


def test_security_headers_cors_fail_closed_and_new_endpoints(monkeypatch):
    monkeypatch.delenv("FLOODRISK_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("FLOODRISK_ALLOW_UNAUTH_NONLOOPBACK", raising=False)
    with pytest.raises(RuntimeError, match="FLOODRISK_ADMIN_TOKEN must be configured"):
        run_dashboard(host="0.0.0.0", port=0, blocking=False)

    srv = run_dashboard(host="127.0.0.1", port=0, blocking=False)
    port = srv.server_address[1]
    base = f"http://127.0.0.1:{port}"
    ds = get_datastore()
    orig_token = ds.admin_token
    ds.admin_token = "v8-sec-token"

    try:
        with urllib.request.urlopen(f"{base}/api/weather/forecast", timeout=5) as r:
            assert r.headers.get("X-Content-Type-Options") == "nosniff"
            assert r.headers.get("X-Frame-Options") == "SAMEORIGIN"
            assert r.headers.get("Cache-Control") == "no-store"
            fc = json.loads(r.read())
        assert "rainfall_windows" in fc
        assert "72h" in fc["rainfall_windows"]

        with urllib.request.urlopen(f"{base}/api/weather/history?limit=10", timeout=5) as r:
            hist = json.loads(r.read())
        assert hist["status"] == "AVAILABLE"

        with urllib.request.urlopen(f"{base}/api/risk/forecast?horizon=24&limit=5", timeout=5) as r:
            rf = json.loads(r.read())
        assert rf["is_calibrated_probability"] is False
        assert rf["horizon_hours"] == 24

        with urllib.request.urlopen(f"{base}/api/health", timeout=5) as r:
            h = json.loads(r.read())
        assert "database_path" not in h
        assert h["public_dispatch_enabled"] is False

        # Malformed Content-Length -> 400
        req_bad_len = urllib.request.Request(
            f"{base}/api/alerts/ALT-1/acknowledge",
            data=b"{}",
            headers={"Authorization": "Bearer v8-sec-token", "Content-Length": "not-an-int"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as e400:
            urllib.request.urlopen(req_bad_len, timeout=5)
        assert e400.value.code == 400
    finally:
        ds.admin_token = orig_token
        srv.shutdown()
        srv.server_close()
