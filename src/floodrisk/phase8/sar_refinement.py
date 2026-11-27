"""Sentinel-1 multi-scene CDSE catalog query & permanent-water-masked classification."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd


def _default_cdse_get(url: str, timeout: float = 12.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "urban-flood-risk-platform-v8/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def query_cdse_episode_scenes(
    df_catalog: pd.DataFrame,
    window_days: int = 7,
    out_path: Path | str = Path("data/phase8/sentinel1_multi_scene_catalog.parquet"),
    http_get: Optional[Callable[[str, float], bytes]] = None,
) -> pd.DataFrame:
    """Query Copernicus CDSE OData per episode window (metadata only; no blind downloads)."""
    fetcher = http_get or _default_cdse_get
    rows: List[Dict[str, Any]] = []
    seen_names = set()

    for _, ep in df_catalog.iterrows():
        ev_id = str(ep["event_id"])
        ev_dt = datetime.fromisoformat(str(ep["event_start_utc"]).replace("Z", "+00:00")).astimezone(timezone.utc)
        s_iso = (ev_dt - timedelta(days=window_days)).strftime("%Y-%m-%dT00:00:00.000Z")
        e_iso = (ev_dt + timedelta(days=window_days)).strftime("%Y-%m-%dT23:59:59.999Z")

        flt = (
            "Collection/Name eq 'SENTINEL-1' "
            "and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/Value eq 'GRD') "
            "and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'operationalMode' and att/Value eq 'IW') "
            "and OData.CSC.Intersects(area=geography'SRID=4326;POINT(77.5946 12.9716)') "
            f"and ContentDate/Start ge {s_iso} and ContentDate/Start le {e_iso}"
        )
        url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?" + urllib.parse.urlencode({
            "$filter": flt, "$top": 20, "$orderby": "ContentDate/Start asc"
        })
        try:
            raw = fetcher(url, 15.0)
            data = json.loads(raw.decode("utf-8"))
            for item in data.get("value", []):
                name = item.get("Name", "")
                acq = item.get("ContentDate", {}).get("Start", "")
                size_mb = round(float(item.get("ContentLength", 0)) / (1024 ** 2), 2)
                sat = "Sentinel-1A" if name.startswith("S1A") else ("Sentinel-1B" if name.startswith("S1B") else "Sentinel-1C")
                pol = "VV+VH" if "_1SDV_" in name else ("VV" if "_1SSV_" in name else "UNKNOWN")
                key = (ev_id, name)
                if key in seen_names:
                    continue
                seen_names.add(key)
                rows.append({
                    "event_id": ev_id,
                    "scene_id": name,
                    "satellite": sat,
                    "beam_mode": "IW",
                    "product_type": "GRD",
                    "polarisation": pol,
                    "acquisition_utc": acq,
                    "size_mb": size_mb,
                    "cdse_product_uuid": item.get("Id", ""),
                    "download_status": "CATALOG_METADATA_ONLY",
                })
        except Exception as e:
            rows.append({
                "event_id": ev_id,
                "scene_id": f"QUERY_ERROR_{ev_id}",
                "satellite": "UNKNOWN",
                "beam_mode": "IW",
                "product_type": "GRD",
                "polarisation": "UNKNOWN",
                "acquisition_utc": None,
                "size_mb": None,
                "cdse_product_uuid": "",
                "download_status": f"QUERY_FAILED: {type(e).__name__}: {str(e)[:80]}",
            })

    df_scenes = pd.DataFrame(rows)
    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    df_scenes.to_parquet(out_p, index=False)
    return df_scenes


def classify_sar_cell_state(
    sar_delta_vv_db: Optional[float],
    water_fraction: float,
    built_up_fraction: float,
    tree_cover_fraction: float,
    is_permanent_water_conflated: bool = False,
) -> str:
    """Distinguish permanent water, temporary inundation, urban double-bounce, canopy/shadow, or no valid obs."""
    if sar_delta_vv_db is None or pd.isna(sar_delta_vv_db):
        return "NO_VALID_OBSERVATION"
    if is_permanent_water_conflated or water_fraction >= 0.40:
        return "PERMANENT_WATER"
    if built_up_fraction >= 0.70 and sar_delta_vv_db > 0.0:
        return "URBAN_DOUBLE_BOUNCE_ARTIFACT"
    if sar_delta_vv_db <= -0.05:
        return "TEMPORARY_INUNDATION"
    if tree_cover_fraction >= 0.40 and abs(sar_delta_vv_db) < 0.05:
        return "SHADOW_OR_CANOPY"
    return "UNCERTAIN"
