"""Stage 5 Spatial Operationalization, Clustering, Security, Health, Backup, and Outage Tests.

All synthetic fixtures are isolated in tmp_path.
"""

import json
from pathlib import Path
import sqlite3
import urllib.error
import urllib.request

import pytest

from floodrisk.alerts import (
    AlertStore,
    OperationalAlertEngine,
    assign_cell_to_forecast_zone,
    cluster_alerts,
    summarize_spatial_coverage,
)
from floodrisk.dashboard.server import get_datastore, run_dashboard
from floodrisk.live.open_meteo import OpenMeteoForecastAdapter, ProviderError
from floodrisk.live.scheduler import LiveWeatherRefresher
from floodrisk.live.storage import LiveWeatherStore


def test_multi_zone_open_meteo_ingestion_and_mismatch():
    def _fake_get(url, timeout):
        items = []
        for z in OpenMeteoForecastAdapter.BENGALURU_FORECAST_ZONES:
            items.append({
                "latitude": 13.0 if z["latitude"] > 12.95 else 12.75,
                "longitude": 77.75 if z["longitude"] > 77.62 else 77.5,
                "timezone": "UTC",
                "hourly_units": {
                    "precipitation": "mm",
                    "rain": "mm",
                    "temperature_2m": "°C",
                    "relative_humidity_2m": "%",
                },
                "hourly": {
                    "time": ["2026-11-27T06:00"],
                    "precipitation": [5.0],
                    "rain": [5.0],
                    "temperature_2m": [24.0],
                    "relative_humidity_2m": [80.0],
                },
            })
        return 200, json.dumps(items).encode("utf-8")

    adapter = OpenMeteoForecastAdapter(http_get=_fake_get)
    res = adapter.fetch_multi_zone_forecast()
    assert res["zones_fetched"] == 5
    assert len(res["records"]) == 5 * 4
    assert len(res["distinct_native_nodes"]) >= 2

    def _bad_len_get(url, timeout):
        return 200, json.dumps([{"latitude": 13.0, "longitude": 77.5}]).encode("utf-8")

    bad_adapter = OpenMeteoForecastAdapter(http_get=_bad_len_get)
    with pytest.raises(ProviderError, match="Multi-zone length mismatch"):
        bad_adapter.fetch_multi_zone_forecast()


def test_spatial_assignment_and_insufficient_coverage():
    zones = {
        "blr_center": {
            "freshness": "LIVE",
            "requested_latitude": 12.9716,
            "requested_longitude": 77.5946,
            "latitude": 13.0,
            "longitude": 77.5,
            "native_resolution_deg": 0.25,
            "hourly_forecast": [{"valid_time_utc": "2026-11-27T06:00:00Z", "precipitation": 2.0}],
        }
    }
    fc_ok, meta_ok = assign_cell_to_forecast_zone(
        {"grid_id": "IN_RANGE", "latitude": 12.98, "longitude": 77.60},
        zones,
        max_distance_km=25.0,
    )
    assert fc_ok is not None
    assert meta_ok["coverage_status"] == "COVERED_BY_SECTOR_ANCHOR"
    assert meta_ok["assignment_method"] == "NEAREST_SECTOR_ANCHOR_NO_INTERPOLATION"

    fc_far, meta_far = assign_cell_to_forecast_zone(
        {"grid_id": "OUT_OF_RANGE", "latitude": 14.5, "longitude": 79.0},
        zones,
        max_distance_km=25.0,
    )
    assert fc_far is None
    assert meta_far["coverage_status"] == "INSUFFICIENT_SPATIAL_COVERAGE"

    summary = summarize_spatial_coverage(
        [
            {"grid_id": "IN_RANGE", "latitude": 12.98, "longitude": 77.60},
            {"grid_id": "OUT_OF_RANGE", "latitude": 14.5, "longitude": 79.0},
        ],
        zones,
    )
    assert summary["status"] == "PARTIAL"
    assert summary["covered_cells"] == 1
    assert summary["insufficient_spatial_coverage_cells"] == 1


def test_alert_clustering_and_cluster_lifecycle(tmp_path):
    store = AlertStore(tmp_path / "cluster.db")
    engine = OperationalAlertEngine(store)
    cells = [
        {"grid_id": "C1", "latitude": 12.951, "longitude": 77.651, "static_susceptibility_score": 0.70},
        {"grid_id": "C2", "latitude": 12.952, "longitude": 77.652, "static_susceptibility_score": 0.50},
    ]
    fc = {
        "provider": "test",
        "model": "ecmwf_ifs025",
        "freshness": "LIVE",
        "location_ref": "blr_south_east",
        "requested_latitude": 12.90,
        "requested_longitude": 77.69,
        "latitude": 13.0,
        "longitude": 77.75,
        "issue_time_utc": "2026-11-27T00:00:00Z",
        "retrieval_time_utc": "2026-11-27T05:00:00Z",
        "next_24h_precipitation_mm": 70.0,
        "peak_hourly_precipitation_mm": 18.0,
        "hourly_forecast": [{"valid_time_utc": "2026-11-27T06:00:00Z", "precipitation": 18.0}],
    }
    run = engine.evaluate(cells, fc, zone_forecasts={"blr_south_east": fc})
    assert run["alerts_created"] == 2

    clusters = engine.get_clusters()
    assert len(clusters) == 1
    cid = clusters[0]["cluster_id"]
    assert clusters[0]["alert_count"] == 2
    assert set(clusters[0]["grid_ids"]) == {"C1", "C2"}

    ack = engine.acknowledge_cluster(cid, actor="ops")
    assert ack["acknowledged_count"] == 2
    res = engine.resolve_cluster(cid, actor="ops")
    assert res["resolved_count"] == 2
    assert engine.get_clusters() == []
    store.close()


def test_sqlite_wal_backup_and_outage_recovery(tmp_path):
    db_path = tmp_path / "wal_test.db"
    wstore = LiveWeatherStore(db_path)
    health = wstore.check_db_health()
    assert health["status"] == "HEALTHY"
    assert health["journal_mode"].lower() == "wal"

    class _FlakyAdapter:
        preferred_model = "ecmwf_ifs025"
        use_multi_zone = True
        fail = True

        def fetch_multi_zone_forecast(self):
            if self.fail:
                raise ProviderError("Simulated provider outage")
            return {
                "provider": "open_meteo",
                "model_id": "ecmwf_ifs025",
                "retrieval_time_utc": "2026-11-27T06:00:00Z",
                "records": [
                    {
                        "provider": "open_meteo",
                        "location_ref": "blr_center",
                        "latitude": 13.0,
                        "longitude": 77.5,
                        "data_type": "FORECAST",
                        "variable": "precipitation",
                        "value": 3.0,
                        "unit": "mm",
                        "issue_time_utc": "2026-11-27T06:00:00Z",
                        "valid_time_utc": "2026-11-27T07:00:00Z",
                        "retrieval_time_utc": "2026-11-27T06:00:00Z",
                        "model_id": "ecmwf_ifs025",
                        "quality_status": "AVAILABLE",
                    }
                ],
            }

    adapter = _FlakyAdapter()
    refresher = LiveWeatherRefresher(wstore, adapter=adapter, max_retries=1, backoff_base_s=0.0)
    r_fail = refresher.refresh_once()
    assert r_fail["success"] is False
    assert wstore.get_provider_health("open_meteo")[0]["consecutive_failures"] == 1

    adapter.fail = False
    r_ok = refresher.refresh_once()
    assert r_ok["success"] is True
    assert wstore.get_provider_health("open_meteo")[0]["consecutive_failures"] == 0

    bpath = wstore.backup_database(tmp_path / "backups" / "snap.db")
    assert Path(bpath).is_file()
    bconn = sqlite3.connect(bpath)
    cnt = bconn.execute("SELECT COUNT(*) FROM weather_records").fetchone()[0]
    bconn.close()
    assert cnt == 1
    wstore.close()


def test_api_auth_health_ready_spatial_clusters_and_backup(tmp_path):
    srv = run_dashboard(host="127.0.0.1", port=0, blocking=False)
    port = srv.server_address[1]
    base_url = f"http://127.0.0.1:{port}"
    ds = get_datastore()
    orig_token = ds.admin_token
    orig_bdir = ds.backup_dir
    ds.admin_token = "stage5-secret-token"
    ds.backup_dir = tmp_path / "backups"

    try:
        # Readiness & Health & Spatial & Clusters GET endpoints
        with urllib.request.urlopen(f"{base_url}/api/ready", timeout=5) as r:
            assert r.status == 200
            assert json.loads(r.read())["ready"] is True

        with urllib.request.urlopen(f"{base_url}/api/health", timeout=5) as r:
            h = json.loads(r.read())
        assert h["status"] in ("HEALTHY", "DEGRADED")
        assert h["public_dispatch_enabled"] is False

        with urllib.request.urlopen(f"{base_url}/api/spatial/coverage", timeout=5) as r:
            cov = json.loads(r.read())
        assert cov["total_cells"] == 1170

        with urllib.request.urlopen(f"{base_url}/api/alerts/clusters", timeout=5) as r:
            clu = json.loads(r.read())
        assert clu["public_dispatch_enabled"] is False

        # Auth checks on POST /api/system/backup
        req_no_auth = urllib.request.Request(f"{base_url}/api/system/backup", data=b"{}", method="POST")
        with pytest.raises(urllib.error.HTTPError) as e401:
            urllib.request.urlopen(req_no_auth, timeout=5)
        assert e401.value.code == 401

        req_bad_auth = urllib.request.Request(
            f"{base_url}/api/system/backup",
            data=b"{}",
            headers={"Authorization": "Bearer wrong-token"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as e403:
            urllib.request.urlopen(req_bad_auth, timeout=5)
        assert e403.value.code == 403

        req_ok_auth = urllib.request.Request(
            f"{base_url}/api/system/backup",
            data=b"{}",
            headers={"Authorization": "Bearer stage5-secret-token"},
            method="POST",
        )
        with urllib.request.urlopen(req_ok_auth, timeout=5) as r_bak:
            assert r_bak.status == 200
            bak_body = json.loads(r_bak.read())
        assert Path(bak_body["backup_path"]).is_file()
    finally:
        ds.admin_token = orig_token
        ds.backup_dir = orig_bdir
        srv.shutdown()
        srv.server_close()
