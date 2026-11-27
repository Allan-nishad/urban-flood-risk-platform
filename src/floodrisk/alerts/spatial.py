"""Defensible spatial forecast assignment and coverage auditing (no invented downscaling)."""

import math
from typing import Any, Dict, Iterable, List, Optional, Tuple


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometers between two WGS84 coordinates."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    return 2.0 * r * math.asin(math.sqrt(a))


def assign_cell_to_forecast_zone(
    cell: Dict[str, Any],
    zone_forecasts: Dict[str, Dict[str, Any]],
    max_distance_km: float = 25.0,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """Assign a 1 km grid cell to the nearest fresh forecast zone anchor without interpolation.

    Returns (assigned_forecast_payload_or_None, coverage_metadata).
    Cells without coordinates or without a fresh zone within max_distance_km are marked
    INSUFFICIENT_SPATIAL_COVERAGE and never receive fabricated local forecasts.
    """
    lat = cell.get("latitude") if cell.get("latitude") is not None else cell.get("centroid_lat")
    lon = cell.get("longitude") if cell.get("longitude") is not None else cell.get("centroid_lon")
    if lat is None or lon is None:
        return None, {
            "coverage_status": "INSUFFICIENT_SPATIAL_COVERAGE",
            "reason": "Missing cell centroid coordinates",
            "assignment_method": "NONE",
        }

    c_lat, c_lon = float(lat), float(lon)
    best_zone_id: Optional[str] = None
    best_fc: Optional[Dict[str, Any]] = None
    best_dist = float("inf")

    for zid, fc in zone_forecasts.items():
        freshness = fc.get("freshness") or fc.get("status") or "UNAVAILABLE"
        if freshness not in ("LIVE", "RECENT") or not fc.get("hourly_forecast"):
            continue
        z_lat = fc.get("requested_latitude") if fc.get("requested_latitude") is not None else fc.get("latitude")
        z_lon = fc.get("requested_longitude") if fc.get("requested_longitude") is not None else fc.get("longitude")
        if z_lat is None or z_lon is None:
            continue
        d = haversine_km(c_lat, c_lon, float(z_lat), float(z_lon))
        if d < best_dist:
            best_dist = d
            best_zone_id = zid
            best_fc = fc

    if best_fc is None or best_dist > max_distance_km:
        return None, {
            "coverage_status": "INSUFFICIENT_SPATIAL_COVERAGE",
            "reason": (
                "No fresh forecast zone anchor available"
                if best_fc is None
                else f"Nearest anchor ({best_zone_id}) is {best_dist:.2f} km > {max_distance_km} km limit"
            ),
            "assignment_method": "NONE",
        }

    return best_fc, {
        "coverage_status": "COVERED_BY_SECTOR_ANCHOR",
        "forecast_zone_id": best_zone_id,
        "native_grid_latitude": best_fc.get("latitude"),
        "native_grid_longitude": best_fc.get("longitude"),
        "native_resolution_deg": best_fc.get("native_resolution_deg", 0.25),
        "distance_to_anchor_km": round(best_dist, 2),
        "assignment_method": "NEAREST_SECTOR_ANCHOR_NO_INTERPOLATION",
    }


def summarize_spatial_coverage(
    cells: Iterable[Dict[str, Any]],
    zone_forecasts: Dict[str, Dict[str, Any]],
    max_distance_km: float = 25.0,
) -> Dict[str, Any]:
    """Summarize spatial forecast coverage across all grid cells."""
    total = 0
    covered = 0
    insufficient = 0
    by_zone: Dict[str, int] = {}
    native_nodes = set()

    for cell in cells:
        total += 1
        fc, meta = assign_cell_to_forecast_zone(cell, zone_forecasts, max_distance_km=max_distance_km)
        if fc is None:
            insufficient += 1
        else:
            covered += 1
            zid = str(meta["forecast_zone_id"])
            by_zone[zid] = by_zone.get(zid, 0) + 1
            if meta.get("native_grid_latitude") is not None and meta.get("native_grid_longitude") is not None:
                native_nodes.add((round(float(meta["native_grid_latitude"]), 4), round(float(meta["native_grid_longitude"]), 4)))

    status = "COVERED" if (total > 0 and insufficient == 0) else ("PARTIAL" if covered > 0 else "INSUFFICIENT_SPATIAL_COVERAGE")
    return {
        "status": status,
        "total_cells": total,
        "covered_cells": covered,
        "insufficient_spatial_coverage_cells": insufficient,
        "zones_configured": len(zone_forecasts),
        "cells_by_zone": by_zone,
        "distinct_native_model_nodes": [list(n) for n in sorted(native_nodes)],
        "native_resolution_deg": 0.25,
        "assignment_method": "NEAREST_SECTOR_ANCHOR_NO_INTERPOLATION",
        "limitation_note": (
            "1 km grid cells are assigned to nearest Open-Meteo ECMWF IFS 0.25 deg (~27.8 km) "
            "sector anchor without spatial downscaling; not 1,170 independent local forecasts."
        ),
    }
