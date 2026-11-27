"""Reproducible forecast-driven grid-level flood-risk prioritisation engine.

Combines multi-zone ECMWF IFS forecast rainfall windows (1h–72h) with
static terrain, TWI, drainage/flow accumulation, land cover, and historical
flood evidence. Scores are non-probabilistic prioritisation indices in [0, 1]
and are NEVER presented as calibrated flood probabilities.
"""

from typing import Any, Dict, Iterable, List, Optional

from ..live.forecast_metrics import HORIZON_HOURS, compute_rainfall_windows
from .spatial import assign_cell_to_forecast_zone

RISK_METHODOLOGY_DOC = (
    "Exploratory multi-criteria forecast prioritisation index [0, 1] combining "
    "static terrain/MCDA susceptibility (35%), D8 TWI/drainage factor (20%), "
    "impervious land-cover factor (15%), and forecast rainfall exposure (30%), "
    "with historical flood evidence retained as non-circular context. "
    "Not a calibrated flood probability; missing/stale inputs yield INSUFFICIENT_DATA."
)


def _clamp01(val: float) -> float:
    return max(0.0, min(1.0, float(val)))


def _classify_risk_index(score: float) -> str:
    if score >= 0.70:
        return "CRITICAL"
    if score >= 0.55:
        return "HIGH"
    if score >= 0.40:
        return "MODERATE"
    if score >= 0.25:
        return "ELEVATED"
    return "LOW"


def _compute_static_factors(cell: Dict[str, Any]) -> Dict[str, Any]:
    missing: List[str] = []

    static_susc = cell.get("static_susceptibility_score")
    if static_susc is None:
        static_susc = cell.get("composite_risk_score")
    if static_susc is None:
        missing.append("static_susceptibility_score")
        terrain_factor = None
    else:
        terrain_factor = round(_clamp01(float(static_susc)), 4)

    twi = cell.get("topographic_wetness_index")
    if twi is None:
        twi = cell.get("mean_twi")
    upa = cell.get("upstream_contributing_area_km2")
    if twi is not None:
        # TWI in Bengaluru typically spans ~5 to ~20
        twi_norm = _clamp01((float(twi) - 5.0) / 15.0)
        upa_norm = _clamp01(float(upa) / 50.0) if upa is not None else 0.0
        drainage_factor = round(_clamp01(0.75 * twi_norm + 0.25 * upa_norm), 4)
    elif terrain_factor is not None:
        drainage_factor = terrain_factor
        missing.append("topographic_wetness_index")
    else:
        drainage_factor = None
        missing.append("topographic_wetness_index")

    built = cell.get("built_up_fraction")
    water = cell.get("water_fraction")
    tree = cell.get("tree_cover_fraction")
    if built is not None:
        b_val = float(built)
        w_val = float(water) if water is not None else 0.0
        t_val = float(tree) if tree is not None else 0.0
        landcover_factor = round(_clamp01(0.75 * b_val + 0.25 * w_val - 0.15 * t_val), 4)
    else:
        landcover_factor = None
        missing.append("built_up_fraction")

    return {
        "terrain_factor": terrain_factor,
        "drainage_factor": drainage_factor,
        "landcover_factor": landcover_factor,
        "missing_static": missing,
    }


def _forecast_rain_factor(cum_mm: Optional[float], peak_1h_mm: Optional[float], horizon_hours: int) -> Optional[float]:
    if cum_mm is None and peak_1h_mm is None:
        return None
    # Scale reference by horizon (64.5 mm / 24h IMD heavy rain reference, capped for shorter/longer horizons)
    ref_mm = max(15.0, 64.5 * (horizon_hours / 24.0)) if horizon_hours <= 24 else 64.5 + 30.0 * ((horizon_hours - 24.0) / 48.0)
    cum_norm = _clamp01(float(cum_mm or 0.0) / ref_mm)
    peak_norm = _clamp01(float(peak_1h_mm or 0.0) / 25.0)
    return round(_clamp01(0.65 * cum_norm + 0.35 * peak_norm), 4)


def assess_cell_for_horizon(
    cell: Dict[str, Any],
    zone_forecasts: Dict[str, Dict[str, Any]],
    horizon_hours: int = 24,
    max_distance_km: float = 25.0,
) -> Dict[str, Any]:
    """Produce a reproducible forecast-driven risk-prioritisation assessment for one cell and horizon."""
    gid = str(cell.get("grid_id", ""))
    static = _compute_static_factors(cell)
    warnings: List[str] = list(static["missing_static"])

    assigned_fc, cov_meta = assign_cell_to_forecast_zone(cell, zone_forecasts, max_distance_km=max_distance_km)
    cov_status = cov_meta.get("coverage_status", "INSUFFICIENT_SPATIAL_COVERAGE")

    if assigned_fc is None:
        warnings.append(cov_meta.get("reason", "No fresh forecast anchor within coverage limit"))
        return {
            "grid_id": gid,
            "horizon_hours": int(horizon_hours),
            "valid_from_utc": None,
            "valid_to_utc": None,
            "forecast_zone_id": None,
            "distance_to_anchor_km": None,
            "native_resolution_deg": 0.25,
            "rainfall_accumulation_mm": None,
            "max_hourly_rainfall_mm": None,
            "risk_prioritization_index": None,
            "risk_category": "INSUFFICIENT_DATA",
            "is_calibrated_probability": False,
            "data_freshness": "UNAVAILABLE",
            "spatial_coverage_status": cov_status,
            "contributing_factors": {
                "terrain_susceptibility": static["terrain_factor"],
                "twi_drainage": static["drainage_factor"],
                "land_cover_imperviousness": static["landcover_factor"],
                "forecast_rainfall_exposure": None,
                "historical_flood_evidence": bool(cell.get("has_ground_flood_evidence", False)),
                "historical_incident_count": int(cell.get("historical_incident_count", 0) or 0),
            },
            "missing_data_warnings": warnings,
        }

    freshness = assigned_fc.get("freshness") or assigned_fc.get("status") or "UNAVAILABLE"
    windows = compute_rainfall_windows(assigned_fc.get("hourly_forecast") or [], horizons=(horizon_hours,))
    win = windows[f"{int(horizon_hours)}h"]
    if win["quality_status"] == "PARTIAL":
        warnings.append(f"Partial forecast window: {win['available_hours']}/{win['expected_hours']} hours available")
    elif win["quality_status"] == "UNAVAILABLE":
        warnings.append(f"No forecast hours available for {horizon_hours}h window")

    rain_factor = _forecast_rain_factor(win["cumulative_mm"], win["max_hourly_mm"], int(horizon_hours))

    # Missing terrain or missing/stale forecast -> never classify as LOW/safe
    if (
        freshness not in ("LIVE", "RECENT")
        or static["terrain_factor"] is None
        or rain_factor is None
    ):
        if freshness not in ("LIVE", "RECENT"):
            warnings.append(f"Forecast freshness is {freshness}")
        return {
            "grid_id": gid,
            "horizon_hours": int(horizon_hours),
            "valid_from_utc": win["valid_from_utc"],
            "valid_to_utc": win["valid_to_utc"],
            "forecast_zone_id": cov_meta.get("forecast_zone_id"),
            "distance_to_anchor_km": cov_meta.get("distance_to_anchor_km"),
            "native_resolution_deg": cov_meta.get("native_resolution_deg", 0.25),
            "rainfall_accumulation_mm": win["cumulative_mm"],
            "max_hourly_rainfall_mm": win["max_hourly_mm"],
            "risk_prioritization_index": None,
            "risk_category": "INSUFFICIENT_DATA",
            "is_calibrated_probability": False,
            "data_freshness": freshness,
            "spatial_coverage_status": cov_status,
            "contributing_factors": {
                "terrain_susceptibility": static["terrain_factor"],
                "twi_drainage": static["drainage_factor"],
                "land_cover_imperviousness": static["landcover_factor"],
                "forecast_rainfall_exposure": rain_factor,
                "historical_flood_evidence": bool(cell.get("has_ground_flood_evidence", False)),
                "historical_incident_count": int(cell.get("historical_incident_count", 0) or 0),
            },
            "missing_data_warnings": warnings,
        }

    lc_val = static["landcover_factor"] if static["landcover_factor"] is not None else static["terrain_factor"]
    dr_val = static["drainage_factor"] if static["drainage_factor"] is not None else static["terrain_factor"]
    score = round(
        _clamp01(
            0.35 * static["terrain_factor"]
            + 0.20 * dr_val
            + 0.15 * lc_val
            + 0.30 * rain_factor
        ),
        4,
    )

    return {
        "grid_id": gid,
        "horizon_hours": int(horizon_hours),
        "valid_from_utc": win["valid_from_utc"],
        "valid_to_utc": win["valid_to_utc"],
        "forecast_zone_id": cov_meta.get("forecast_zone_id"),
        "distance_to_anchor_km": cov_meta.get("distance_to_anchor_km"),
        "native_resolution_deg": cov_meta.get("native_resolution_deg", 0.25),
        "rainfall_accumulation_mm": win["cumulative_mm"],
        "max_hourly_rainfall_mm": win["max_hourly_mm"],
        "risk_prioritization_index": score,
        "risk_category": _classify_risk_index(score),
        "is_calibrated_probability": False,
        "data_freshness": freshness,
        "spatial_coverage_status": cov_status,
        "contributing_factors": {
            "terrain_susceptibility": static["terrain_factor"],
            "twi_drainage": static["drainage_factor"],
            "land_cover_imperviousness": static["landcover_factor"],
            "forecast_rainfall_exposure": rain_factor,
            "historical_flood_evidence": bool(cell.get("has_ground_flood_evidence", False)),
            "historical_incident_count": int(cell.get("historical_incident_count", 0) or 0),
        },
        "missing_data_warnings": warnings,
    }


def evaluate_cell_risk_timeline(
    cell: Dict[str, Any],
    zone_forecasts: Dict[str, Dict[str, Any]],
    horizons: Iterable[int] = HORIZON_HOURS,
) -> List[Dict[str, Any]]:
    """Evaluate a single grid cell across all forecast horizons (1h–72h)."""
    return [
        assess_cell_for_horizon(cell, zone_forecasts, horizon_hours=int(h))
        for h in horizons
    ]


def evaluate_forecast_risk_grid(
    cells: Iterable[Dict[str, Any]],
    zone_forecasts: Dict[str, Dict[str, Any]],
    horizon_hours: int = 24,
    limit: int = 200,
) -> Dict[str, Any]:
    """Evaluate all grid cells for a given forecast horizon and return sorted assessments + summary."""
    assessments = [
        assess_cell_for_horizon(c, zone_forecasts, horizon_hours=horizon_hours)
        for c in cells
    ]
    by_cat: Dict[str, int] = {}
    for a in assessments:
        cat = a["risk_category"]
        by_cat[cat] = by_cat.get(cat, 0) + 1

    assessments.sort(
        key=lambda a: (
            a["risk_prioritization_index"] is not None,
            a["risk_prioritization_index"] if a["risk_prioritization_index"] is not None else -1.0,
        ),
        reverse=True,
    )
    return {
        "status": "AVAILABLE",
        "horizon_hours": int(horizon_hours),
        "is_calibrated_probability": False,
        "methodology": RISK_METHODOLOGY_DOC,
        "total_cells": len(assessments),
        "category_counts": by_cat,
        "assessments": assessments[:limit],
    }
