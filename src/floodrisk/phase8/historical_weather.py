"""Historical ERA5-Land weather reconstruction around candidate flood episodes."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..live.open_meteo import OpenMeteoArchiveAdapter


class HistoricalWeatherReconstructor:
    """Retrieves and aligns ERA5-Land reanalysis strictly prior to each episode start."""

    def __init__(
        self,
        adapter: Optional[OpenMeteoArchiveAdapter] = None,
        pre_days: int = 14,
        post_days: int = 1,
    ):
        self.adapter = adapter or OpenMeteoArchiveAdapter()
        self.pre_days = int(pre_days)
        self.post_days = int(post_days)

    @staticmethod
    def _parse_utc(ts: str) -> datetime:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

    def reconstruct_for_catalog(
        self,
        df_catalog: pd.DataFrame,
        out_path: Path | str = Path("data/phase8/historical_weather_era5_land.parquet"),
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Fetch hourly ERA5-Land windows and compute strictly pre-event rainfall features."""
        hourly_rows: List[Dict[str, Any]] = []
        episode_features: List[Dict[str, Any]] = []

        for _, ep in df_catalog.iterrows():
            ev_id = str(ep["event_id"])
            ev_start = self._parse_utc(str(ep["event_start_utc"]))
            ev_end = self._parse_utc(str(ep["event_end_utc"]))
            s_date = (ev_start - timedelta(days=self.pre_days)).strftime("%Y-%m-%d")
            e_date = (ev_end + timedelta(days=self.post_days)).strftime("%Y-%m-%d")

            res = self.adapter.fetch_historical(s_date, e_date)
            recs = res["records"]
            for r in recs:
                r_copy = dict(r)
                r_copy["event_id"] = ev_id
                hourly_rows.append(r_copy)

            # Strictly pre-event slice: valid_time_utc < event_start_utc (zero future leakage)
            df_h = pd.DataFrame(recs)
            df_h["valid_dt"] = pd.to_datetime(df_h["valid_time_utc"], utc=True)
            pre = df_h[df_h["valid_dt"] < pd.Timestamp(ev_start)].sort_values("valid_dt")
            # Also capture event-window accumulation [event_start, event_end] separately as event context
            during = df_h[(df_h["valid_dt"] >= pd.Timestamp(ev_start)) & (df_h["valid_dt"] <= pd.Timestamp(ev_end))]

            def _sum_last_hours(h_df: pd.DataFrame, hours: int) -> Optional[float]:
                cutoff = pd.Timestamp(ev_start - timedelta(hours=hours))
                sub = h_df[h_df["valid_dt"] >= cutoff]["value"].dropna()
                return round(float(sub.sum()), 2) if len(sub) > 0 else None

            # 7-day antecedent precipitation decay API (k=0.85 per day)
            api_7d = None
            if len(pre) > 0:
                pre_7 = pre[pre["valid_dt"] >= pd.Timestamp(ev_start - timedelta(days=7))].copy()
                if len(pre_7) > 0:
                    pre_7["days_ago"] = (pd.Timestamp(ev_start) - pre_7["valid_dt"]).dt.total_seconds() / 86400.0
                    vals = pre_7["value"].fillna(0.0).values
                    weights = 0.85 ** pre_7["days_ago"].values
                    api_7d = round(float(np.sum(vals * weights)), 2)

            during_vals = during["value"].dropna()
            episode_features.append({
                "event_id": ev_id,
                "predictor_cutoff_utc": ep["event_start_utc"],
                "era5_rain_24h_pre_mm": _sum_last_hours(pre, 24),
                "era5_rain_72h_pre_mm": _sum_last_hours(pre, 72),
                "era5_rain_7d_pre_mm": _sum_last_hours(pre, 168),
                "era5_rain_14d_pre_mm": _sum_last_hours(pre, 336),
                "era5_api_7d_pre_mm": api_7d,
                "era5_rain_during_event_mm": round(float(during_vals.sum()), 2) if len(during_vals) > 0 else None,
                "era5_missing_pre_hours": int(pre["value"].isna().sum()),
                "rainfall_provider": "open_meteo_archive",
                "rainfall_model_id": "era5_land",
                "rainfall_classification": "HISTORICAL_REANALYSIS",
            })

        df_hourly_all = pd.DataFrame(hourly_rows)
        # Drop source_metadata dict before parquet or serialize to JSON string
        if "source_metadata" in df_hourly_all.columns:
            df_hourly_all["source_metadata_json"] = df_hourly_all["source_metadata"].apply(json.dumps)
            df_hourly_all = df_hourly_all.drop(columns=["source_metadata"])

        out_p = Path(out_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_hourly_all.to_parquet(out_p, index=False)

        df_ep_feat = pd.DataFrame(episode_features)
        df_ep_feat.to_parquet(out_p.parent / "historical_episode_rainfall_features.parquet", index=False)
        return df_hourly_all, df_ep_feat
