"""Deterministic tests for V8 Stage 2 multi-event flood catalog, ERA5-Land alignment, SAR & grid dataset."""

import json
from pathlib import Path

import pandas as pd

from floodrisk.live.open_meteo import OpenMeteoArchiveAdapter
from floodrisk.phase8 import (
    HistoricalWeatherReconstructor,
    build_flood_event_catalog,
    build_integrated_event_grid_dataset,
    classify_sar_cell_state,
)


def test_event_catalog_dedup_and_unmapped_locality(tmp_path):
    df_cat, meta = build_flood_event_catalog(out_dir=tmp_path)
    assert len(df_cat) == 8
    assert meta["p2_4_incident_rows"] == 21
    assert meta["p6_incident_rows"] == 24
    assert meta["overlapping_grid_id_count"] > 0

    # Broad locality report must remain unmapped
    ep_2025_10 = df_cat[df_cat["event_id"] == "EP_2025_10_09"].iloc[0]
    assert ep_2025_10["verification_status"] == "REPORTED"
    assert ep_2025_10["linked_grid_ids"] == ""
    assert (tmp_path / "flood_event_catalog.csv").is_file()
    assert (tmp_path / "flood_event_catalog.parquet").is_file()


def test_historical_weather_zero_future_leakage(tmp_path):
    # Mock archive returning 10mm BEFORE event_start and 999mm AT/AFTER event_start
    def _mock_http(url, timeout):
        payload = {
            "latitude": 12.97,
            "longitude": 77.59,
            "hourly_units": {"time": "iso8601", "precipitation": "mm"},
            "hourly": {
                "time": [
                    "2023-05-21T06:00",  # 3h pre-event
                    "2023-05-21T07:00",  # 2h pre-event
                    "2023-05-21T08:00",  # 1h pre-event (None -> missing)
                    "2023-05-21T09:00",  # AT event_start -> must NOT leak into pre_mm!
                    "2023-05-21T10:00",  # AFTER event_start -> must NOT leak!
                ],
                "precipitation": [4.0, 6.0, None, 500.0, 499.0],
            },
        }
        return 200, json.dumps(payload).encode("utf-8")

    df_mini_cat = pd.DataFrame([{
        "event_id": "EP_2023_05_21",
        "event_start_utc": "2023-05-21T09:00:00Z",
        "event_end_utc": "2023-05-21T20:00:00Z",
    }])
    arch = OpenMeteoArchiveAdapter(http_get=_mock_http)
    recon = HistoricalWeatherReconstructor(adapter=arch)
    df_h, df_ep = recon.reconstruct_for_catalog(df_mini_cat, out_path=tmp_path / "era5.parquet")

    row = df_ep.iloc[0]
    assert row["rainfall_classification"] == "HISTORICAL_REANALYSIS"
    assert row["era5_rain_24h_pre_mm"] == 10.0  # 4.0 + 6.0 only; 500+499 excluded!
    assert row["era5_missing_pre_hours"] == 1
    assert row["era5_rain_during_event_mm"] == 999.0


def test_sar_multi_scene_classification_distinctions():
    assert classify_sar_cell_state(None, 0.0, 0.5, 0.1) == "NO_VALID_OBSERVATION"
    assert classify_sar_cell_state(-0.2, 0.5, 0.1, 0.1) == "PERMANENT_WATER"
    assert classify_sar_cell_state(-0.2, 0.05, 0.5, 0.1, is_permanent_water_conflated=True) == "PERMANENT_WATER"
    assert classify_sar_cell_state(0.05, 0.0, 0.80, 0.05) == "URBAN_DOUBLE_BOUNCE_ARTIFACT"
    assert classify_sar_cell_state(-0.25, 0.0, 0.40, 0.10) == "TEMPORARY_INUNDATION"
    assert classify_sar_cell_state(0.01, 0.0, 0.20, 0.55) == "SHADOW_OR_CANOPY"


def test_integrated_dataset_preserves_unobserved_and_grid_counts(tmp_path):
    df_cat, meta = build_flood_event_catalog(out_dir=tmp_path)
    df_ep_rain = pd.DataFrame([
        {
            "event_id": eid,
            "era5_rain_24h_pre_mm": 10.0,
            "era5_rain_72h_pre_mm": 20.0,
            "era5_rain_7d_pre_mm": 30.0,
            "era5_rain_14d_pre_mm": 40.0,
            "era5_api_7d_pre_mm": 15.0,
            "rainfall_classification": "HISTORICAL_REANALYSIS",
        }
        for eid in df_cat["event_id"]
    ])
    df_scenes = pd.DataFrame(columns=["event_id", "scene_id"])
    df_ds, qa = build_integrated_event_grid_dataset(df_cat, df_ep_rain, df_scenes, meta, out_dir=tmp_path)

    assert len(df_ds) == 8 * 1170
    assert df_ds["grid_id"].nunique() == 1170
    # Unobserved & Unknown must NEVER be labeled 0
    unobs = df_ds[df_ds["evidence_status"].isin(["UNOBSERVED", "UNKNOWN"])]
    assert len(unobs) > 9000
    assert unobs["flood_label"].isna().all()
    assert qa["1_independent_events_identified"] == 8
    assert qa["ml_validation_readiness"]["loeo_feasible"] is False
