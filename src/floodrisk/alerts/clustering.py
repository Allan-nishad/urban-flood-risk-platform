"""Alert clustering and fatigue controls with full underlying-cell traceability."""

from typing import Any, Dict, List

from .rules import RESEARCH_DISCLAIMER, SEVERITY_RANK


def _tile_id(lat: Any, lon: Any, step_deg: float = 0.05) -> str:
    if lat is None or lon is None:
        return "TILE_UNKNOWN"
    t_lat = round(round(float(lat) / step_deg) * step_deg, 3)
    t_lon = round(round(float(lon) / step_deg) * step_deg, 3)
    return f"TILE_{t_lat:.3f}_{t_lon:.3f}"


def cluster_alerts(alerts: List[Dict[str, Any]], max_clusters: int = 50) -> List[Dict[str, Any]]:
    """Group open alerts by (forecast_zone_id, ~5.5 km spatial tile) without hiding cells.

    Does not invent administrative ward boundaries; uses explicit deterministic spatial tiles
    and retains every underlying alert_id and grid_id for traceability.
    """
    groups: Dict[tuple, List[Dict[str, Any]]] = {}
    for a in alerts:
        inputs = a.get("triggering_inputs") or {}
        zone_id = str(inputs.get("forecast_zone_id") or inputs.get("forecast_anchor", {}).get("location_ref") or "bengaluru_centroid")
        tile = _tile_id(a.get("latitude"), a.get("longitude"))
        groups.setdefault((zone_id, tile), []).append(a)

    clusters: List[Dict[str, Any]] = []
    for (zone_id, tile), items in groups.items():
        items_sorted = sorted(
            items,
            key=lambda x: (-SEVERITY_RANK.get(x["severity"], 0), x["grid_id"]),
        )
        max_sev = items_sorted[0]["severity"]
        lats = [float(x["latitude"]) for x in items_sorted if x.get("latitude") is not None]
        lons = [float(x["longitude"]) for x in items_sorted if x.get("longitude") is not None]
        clusters.append({
            "cluster_id": f"CLU-{zone_id}-{tile}",
            "cluster_method": "FORECAST_ZONE_AND_5_5KM_SPATIAL_TILE",
            "forecast_zone_id": zone_id,
            "spatial_tile_id": tile,
            "max_severity": max_sev,
            "alert_count": len(items_sorted),
            "active_count": sum(1 for x in items_sorted if x["lifecycle_state"] == "ACTIVE"),
            "acknowledged_count": sum(1 for x in items_sorted if x["lifecycle_state"] == "ACKNOWLEDGED"),
            "centroid_lat": round(sum(lats) / len(lats), 5) if lats else None,
            "centroid_lon": round(sum(lons) / len(lons), 5) if lons else None,
            "rule_ids": sorted({x["rule_id"] for x in items_sorted}),
            "grid_ids": [x["grid_id"] for x in items_sorted],
            "alert_ids": [x["alert_id"] for x in items_sorted],
            "qualification_status": items_sorted[0]["qualification_status"],
            "warning_disclaimer": RESEARCH_DISCLAIMER,
        })

    clusters.sort(key=lambda c: (-SEVERITY_RANK.get(c["max_severity"], 0), -c["alert_count"], c["cluster_id"]))
    return clusters[:max_clusters]
