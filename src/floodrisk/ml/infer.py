"""Experimental ML inference interface with strict qualification gating."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import pandas as pd

from .features import FEATURE_COLUMNS


class ExperimentalFloodInference:
    """Loads serialized experimental ML model and generates gated research scores."""

    def __init__(
        self,
        model_path: Path | str = Path("models/v8_experimental/flood_risk_model_v8_exp.joblib"),
        metadata_path: Path | str = Path("models/v8_experimental/model_metadata.json"),
    ):
        self.model_path = Path(model_path)
        self.metadata_path = Path(metadata_path)
        self.model = None
        self.metadata: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if not self.model_path.is_file() or not self.metadata_path.is_file():
            self.model = None
            self.metadata = {"qualification_status": "UNAVAILABLE", "warning_gate": "BLOCKED_MISSING_MODEL"}
            return
        self.model = joblib.load(self.model_path)
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def predict_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run inference on prepared feature records; never exposes scores as calibrated probabilities."""
        ts_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if self.model is None:
            return {
                "status": "UNAVAILABLE",
                "qualification_status": "UNAVAILABLE",
                "warning_gate": "BLOCKED_MISSING_MODEL",
                "prediction_timestamp_utc": ts_utc,
                "predictions": [],
            }
        if not records:
            raise ValueError("Input records list cannot be empty")

        df_in = pd.DataFrame(records)
        missing_cols = [c for c in FEATURE_COLUMNS if c not in df_in.columns]
        if missing_cols:
            raise ValueError(f"Missing required feature columns: {missing_cols}")

        X = df_in[FEATURE_COLUMNS].copy()
        raw_scores = self.model.predict_proba(X)[:, 1]
        qual = self.metadata.get("qualification_status", "EXPERIMENTAL_UNVALIDATED")

        preds = []
        for idx, score in enumerate(raw_scores):
            row = df_in.iloc[idx]
            missing_inputs = [c for c in FEATURE_COLUMNS if pd.isna(row[c])]
            preds.append({
                "grid_id": str(row.get("grid_id", f"row_{idx}")),
                "experimental_score": round(float(score), 4),
                "is_calibrated_probability": False,
                "qualification_status": qual,
                "warning_gate": self.metadata.get("warning_gate", "BLOCKED_EXPERIMENTAL_MODEL"),
                "missing_inputs": missing_inputs,
                "uncertainty_note": "Experimental uncalibrated score trained on 48 records; not a flood probability.",
            })

        return {
            "status": "AVAILABLE",
            "model_name": self.metadata.get("model_name"),
            "model_version": self.metadata.get("model_version"),
            "qualification_status": qual,
            "warning_gate": self.metadata.get("warning_gate", "BLOCKED_EXPERIMENTAL_MODEL"),
            "prediction_timestamp_utc": ts_utc,
            "predictions": preds,
        }
