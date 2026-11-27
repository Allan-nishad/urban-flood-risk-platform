"""Deterministic unit & integration tests for V8 Stage 1 live weather ingestion & SQLite store."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import urllib.error

import pytest

from floodrisk.live import (
    LiveWeatherRefresher,
    LiveWeatherStore,
    OpenMeteoArchiveAdapter,
    OpenMeteoForecastAdapter,
    ProviderError,
    compute_freshness,
)


def _valid_open_meteo_payload():
    return {
        "latitude": 12.97,
        "longitude": 77.59,
        "generationtime_ms": 0.12,
        "utc_offset_seconds": 0,
        "timezone": "UTC",
        "elevation": 920.0,
        "hourly_units": {
            "time": "iso8601",
            "precipitation": "mm",
            "rain": "mm",
            "temperature_2m": "°C",
            "relative_humidity_2m": "%",
        },
        "hourly": {
            "time": ["2026-11-27T06:00", "2026-11-27T07:00", "2026-11-27T08:00"],
            "precipitation": [0.0, 2.4, 5.1],
            "rain": [0.0, 2.4, 5.1],
            "temperature_2m": [24.1, 25.0, 25.5],
            "relative_humidity_2m": [78, 82, 85],
        },
    }


def test_1_successful_provider_response():
    payload = json.dumps(_valid_open_meteo_payload()).encode("utf-8")
    adapter = OpenMeteoForecastAdapter(http_get=lambda url, t: (200, payload))
    res = adapter.fetch_forecast()
    assert res["provider"] == "open_meteo"
    assert res["model_id"] == "ecmwf_ifs025"
    assert len(res["records"]) == 12  # 3 timestamps * 4 vars
    precip = [r for r in res["records"] if r["variable"] == "precipitation"]
    assert [r["value"] for r in precip] == [0.0, 2.4, 5.1]
    assert all(r["unit"] == "mm" and r["data_type"] == "FORECAST" for r in precip)


def test_2_provider_timeout():
    def _timeout(url, t):
        raise ProviderError("Network/timeout error: TimeoutError: timed out")

    adapter = OpenMeteoForecastAdapter(http_get=_timeout)
    with pytest.raises(ProviderError, match="timeout"):
        adapter.fetch_forecast()


def test_3_http_failure():
    adapter = OpenMeteoForecastAdapter(http_get=lambda url, t: (503, b"Service Unavailable"))
    with pytest.raises(ProviderError, match="503"):
        adapter.fetch_forecast()


def test_4_invalid_json():
    adapter = OpenMeteoForecastAdapter(http_get=lambda url, t: (200, b"{not valid json"))
    with pytest.raises(ProviderError, match="Invalid JSON"):
        adapter.fetch_forecast()


def test_5_missing_variables():
    bad = _valid_open_meteo_payload()
    del bad["hourly"]["rain"]
    adapter = OpenMeteoForecastAdapter(http_get=lambda url, t: (200, json.dumps(bad).encode("utf-8")))
    with pytest.raises(ProviderError, match="Missing required variable 'rain'"):
        adapter.fetch_forecast()


def test_6_invalid_timestamps():
    bad = _valid_open_meteo_payload()
    bad["hourly"]["time"] = ["not-a-timestamp", "2026-11-27T07:00", "2026-11-27T08:00"]
    adapter = OpenMeteoForecastAdapter(http_get=lambda url, t: (200, json.dumps(bad).encode("utf-8")))
    with pytest.raises(ProviderError, match="Invalid ISO-8601 timestamp"):
        adapter.fetch_forecast()


def test_7_unit_validation():
    bad = _valid_open_meteo_payload()
    bad["hourly_units"]["precipitation"] = "inch"
    adapter = OpenMeteoForecastAdapter(http_get=lambda url, t: (200, json.dumps(bad).encode("utf-8")))
    with pytest.raises(ProviderError, match="Unexpected unit"):
        adapter.fetch_forecast()


def test_8_9_10_sqlite_persistence_dedup_and_restart_recovery(tmp_path):
    db_file = tmp_path / "weather_test.db"
    payload = json.dumps(_valid_open_meteo_payload()).encode("utf-8")
    adapter = OpenMeteoForecastAdapter(http_get=lambda url, t: (200, payload))

    store1 = LiveWeatherStore(db_file)
    refresher = LiveWeatherRefresher(store1, adapter=adapter, sleep_fn=lambda _: None)
    r1 = refresher.refresh_once()
    assert r1["success"] is True
    assert store1.count_records() == 12

    # Upsert again -> duplicate prevention keeps count == 12
    r2 = refresher.refresh_once()
    assert r2["success"] is True
    assert store1.count_records() == 12
    store1.close()

    # Reopen from disk -> restart recovery preserves records and provider health
    store2 = LiveWeatherStore(db_file)
    assert store2.count_records() == 12
    health = store2.get_provider_health("open_meteo")
    assert len(health) == 1
    assert health[0]["status"] == "LIVE"
    assert len(store2.get_latest_forecast()) == 12
    store2.close()


def test_11_stale_data_detection():
    now = datetime(2026, 11, 27, 12, 0, 0, tzinfo=timezone.utc)
    assert compute_freshness(None, now_utc=now) == "UNAVAILABLE"
    assert compute_freshness((now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"), now_utc=now) == "LIVE"
    assert compute_freshness((now - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ"), now_utc=now) == "RECENT"
    assert compute_freshness((now - timedelta(hours=20)).strftime("%Y-%m-%dT%H:%M:%SZ"), now_utc=now) == "STALE"


def test_12_failed_refresh_backoff_and_health_tracking(tmp_path):
    db_file = tmp_path / "fail_test.db"
    store = LiveWeatherStore(db_file)
    sleeps = []

    def _always_fail(url, t):
        raise ProviderError("HTTP 502 Bad Gateway")

    adapter = OpenMeteoForecastAdapter(http_get=_always_fail)
    refresher = LiveWeatherRefresher(
        store, adapter=adapter, max_retries=3, backoff_base_s=2.0, sleep_fn=lambda s: sleeps.append(s)
    )
    res = refresher.refresh_once()
    assert res["success"] is False
    assert sleeps == [2.0, 4.0]  # Exponential backoff across 3 attempts
    health = store.get_provider_health("open_meteo")[0]
    assert health["consecutive_failures"] == 1
    assert "502" in health["last_error"]
    assert health["status"] == "UNAVAILABLE"
    store.close()


def test_13_archive_adapter_separated_as_historical_reanalysis():
    arch_payload = json.dumps({
        "latitude": 12.97,
        "longitude": 77.59,
        "hourly_units": {"time": "iso8601", "precipitation": "mm"},
        "hourly": {"time": ["2022-09-05T00:00"], "precipitation": [42.0]},
    }).encode("utf-8")
    arch = OpenMeteoArchiveAdapter(http_get=lambda url, t: (200, arch_payload))
    res = arch.fetch_historical("2022-09-05", "2022-09-05")
    assert res["classification"] == "HISTORICAL_REANALYSIS"
    assert res["records"][0]["data_type"] == "HISTORICAL_REANALYSIS"
    assert res["records"][0]["quality_status"] == "HISTORICAL"


def test_14_stage1_api_endpoints_schemas(tmp_path):
    # Tested against an isolated DashboardDataStore with populated live SQLite
    from floodrisk.dashboard.server import DashboardDataStore

    ds = DashboardDataStore(data_dir=tmp_path, reports_dir=tmp_path)
    payload = json.dumps(_valid_open_meteo_payload()).encode("utf-8")
    ds.refresher = LiveWeatherRefresher(
        ds.weather_store,
        adapter=OpenMeteoForecastAdapter(http_get=lambda url, t: (200, payload)),
        sleep_fn=lambda _: None,
    )
    # Before refresh: UNAVAILABLE
    wf0 = ds.get_weather_forecast_payload()
    assert wf0["status"] == "UNAVAILABLE"
    assert wf0["next_24h_precipitation_mm"] is None

    # After refresh: LIVE with real units & timestamp
    ds.refresher.refresh_once()
    wf1 = ds.get_weather_forecast_payload()
    assert wf1["status"] == "LIVE"
    assert wf1["model"] == "ecmwf_ifs025"
    assert wf1["next_24h_precipitation_mm"] == 7.5
    assert len(wf1["hourly_forecast"]) == 3

    wc = ds.get_weather_current_payload()
    assert wc["status"] == "UNAVAILABLE"
    assert wc["observed_rainfall_mm"] is None
    assert wc["historical_baseline"]["status"] == "STALE"

    srcs = ds.get_sources_payload()["sources"]
    om_src = [s for s in srcs if s["source_id"] == "open_meteo_forecast"][0]
    assert om_src["status"] == "LIVE"
    hp = ds.get_health_payload()
    assert hp["database_status"] == "AVAILABLE"
    assert hp["stored_weather_records"] == 12
    ds.weather_store.close()
