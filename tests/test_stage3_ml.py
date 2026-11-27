"""Stage 3 Experimental AI/ML Pipeline & API Tests."""

import json
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def test_event_group_independence_and_leakage_guard():
    from floodrisk.ml.features import (
        EVENT_GROUP_MAP,
        FEATURE_COLUMNS,
        FORBIDDEN_LEAKAGE_COLS,
        prepare_ml_dataset,
    )

    assert EVENT_GROUP_MAP["EP_2022_08_30"] == "EG_2022_08_09_MONSOON"
    assert EVENT_GROUP_MAP["EP_2022_09_05"] == "EG_2022_08_09_MONSOON"
    assert set(FEATURE_COLUMNS).isdisjoint(FORBIDDEN_LEAKAGE_COLS)

    df = pd.read_parquet("data/phase8/flood_event_grid_dataset.parquet")
    X_all, y_all, meta_all = prepare_ml_dataset(df, subset="all_labeled")
    assert len(X_all) == 48
    assert int((y_all == 1).sum()) == 34
    assert int((y_all == 0).sum()) == 14
    assert list(X_all.columns) == FEATURE_COLUMNS
    assert set(X_all.columns).isdisjoint(FORBIDDEN_LEAKAGE_COLS)
    assert meta_all["event_group_id"].nunique() == 6

    # Verify UNOBSERVED rows are never coerced to 0
    df_with_unobs = pd.concat(
        [
            df,
            pd.DataFrame(
                [
                    {
                        **df.iloc[0].to_dict(),
                        "event_id": "EP_2024_10_15",
                        "grid_id": "SYNTH_UNOBS",
                        "flood_label": np.nan,
                        "evidence_status": "UNOBSERVED",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    X_unobs, y_unobs, meta_unobs = prepare_ml_dataset(df_with_unobs, subset="all_labeled")
    assert len(X_unobs) == 48
    assert "SYNTH_UNOBS" not in set(meta_unobs["grid_id"])


def test_prepare_ml_dataset_subsets_and_invalid():
    from floodrisk.ml.features import prepare_ml_dataset

    df = pd.read_parquet("data/phase8/flood_event_grid_dataset.parquet")
    X_conf, y_conf, _ = prepare_ml_dataset(df, subset="confirmed_only")
    assert len(X_conf) == 44
    assert int((y_conf == 1).sum()) == 30
    assert int((y_conf == 0).sum()) == 14

    X_dedup, y_dedup, _ = prepare_ml_dataset(df, subset="dedup_event_group")
    assert len(X_dedup) == 37
    assert int((y_dedup == 1).sum()) == 30
    assert int((y_dedup == 0).sum()) == 7

    with pytest.raises(ValueError, match="Unknown subset"):
        prepare_ml_dataset(df, subset="invalid_subset")


def test_train_serialize_and_inference_in_tmp_path(tmp_path):
    from floodrisk.ml.features import prepare_ml_dataset
    from floodrisk.ml.infer import ExperimentalFloodInference
    from floodrisk.ml.train import train_and_evaluate_experimental_models

    out_dir = tmp_path / "models"
    meta = train_and_evaluate_experimental_models(
        dataset_path=Path("data/phase8/flood_event_grid_dataset.parquet"),
        model_dir=out_dir,
        seed=42,
    )

    assert (out_dir / "flood_risk_model_v8_exp.joblib").is_file()
    assert (out_dir / "model_metadata.json").is_file()
    assert meta["qualification_status"] == "EXPERIMENTAL_UNVALIDATED"
    assert meta["warning_gate"] == "BLOCKED_EXPERIMENTAL_MODEL"
    assert meta["event_group_summary"]["loeo_feasible"] is False
    assert meta["event_group_summary"]["negative_control_event_groups"] == 1
    assert set(meta["baselines"].keys()) == {"static_mcda_baseline", "era5_rain_ge_15_6mm_baseline"}
    assert set(meta["candidate_models"].keys()) == {
        "logistic_regression",
        "random_forest",
        "hist_gradient_boosting",
        "xgboost",
    }

    infer = ExperimentalFloodInference(
        model_path=out_dir / "flood_risk_model_v8_exp.joblib",
        metadata_path=out_dir / "model_metadata.json",
    )

    df = pd.read_parquet("data/phase8/flood_event_grid_dataset.parquet")
    X, _, meta_df = prepare_ml_dataset(df, subset="all_labeled")
    rec_valid = X.iloc[0].to_dict()
    rec_valid["grid_id"] = str(meta_df.iloc[0]["grid_id"])

    rec_missing = dict(rec_valid)
    rec_missing["grid_id"] = "CELL_WITH_NAN"
    rec_missing["era5_rain_24h_pre_mm"] = np.nan

    res = infer.predict_records([rec_valid, rec_missing])
    assert res["status"] == "AVAILABLE"
    assert res["qualification_status"] == "EXPERIMENTAL_UNVALIDATED"
    assert res["warning_gate"] == "BLOCKED_EXPERIMENTAL_MODEL"
    assert len(res["predictions"]) == 2
    assert res["predictions"][0]["is_calibrated_probability"] is False
    assert 0.0 <= res["predictions"][0]["experimental_score"] <= 1.0
    assert res["predictions"][0]["missing_inputs"] == []
    assert "era5_rain_24h_pre_mm" in res["predictions"][1]["missing_inputs"]

    with pytest.raises(ValueError, match="cannot be empty"):
        infer.predict_records([])

    with pytest.raises(ValueError, match="Missing required feature columns"):
        infer.predict_records([{"elevation_m": 900.0}])

    missing_infer = ExperimentalFloodInference(
        model_path=tmp_path / "missing.joblib",
        metadata_path=tmp_path / "missing.json",
    )
    unavail = missing_infer.predict_records([rec_valid])
    assert unavail["status"] == "UNAVAILABLE"
    assert unavail["warning_gate"] == "BLOCKED_MISSING_MODEL"


def test_api_ml_experimental_endpoint():
    from floodrisk.dashboard.server import run_dashboard

    srv = run_dashboard(host="127.0.0.1", port=0, blocking=False)
    port = srv.server_address[1]
    base_url = f"http://127.0.0.1:{port}"

    try:
        with urllib.request.urlopen(f"{base_url}/api/ml/experimental", timeout=5) as resp:
            assert resp.status == 200
            payload = json.loads(resp.read().decode("utf-8"))
        assert payload["status"] == "AVAILABLE"
        assert payload["qualification_status"] == "EXPERIMENTAL_UNVALIDATED"
        assert payload["warning_gate"] == "BLOCKED_EXPERIMENTAL_MODEL"
        assert payload["model_name"] == "random_forest"
        assert "candidate_models" in payload

        # Valid grid_id inference
        valid_grid_id = "g1000_7472_1625"
        with urllib.request.urlopen(f"{base_url}/api/ml/experimental?grid_id={valid_grid_id}", timeout=5) as resp:
            assert resp.status == 200
            cell_payload = json.loads(resp.read().decode("utf-8"))
        assert cell_payload["qualification_status"] == "EXPERIMENTAL_UNVALIDATED"
        pred0 = cell_payload["predictions"][0]
        assert pred0["grid_id"] == valid_grid_id
        assert pred0["is_calibrated_probability"] is False
        assert 0.0 <= pred0["experimental_score"] <= 1.0

        # Invalid grid_id -> 404
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(f"{base_url}/api/ml/experimental?grid_id=INVALID_CELL_999", timeout=5)
        assert exc_info.value.code == 404

        # Empty grid_id -> 400
        with pytest.raises(urllib.error.HTTPError) as exc_info_400:
            urllib.request.urlopen(f"{base_url}/api/ml/experimental?grid_id=", timeout=5)
        assert exc_info_400.value.code == 400
    finally:
        srv.shutdown()
        srv.server_close()
