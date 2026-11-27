"""Configurable provisional alert rules, qualification states, and safety gates."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

RESEARCH_DISCLAIMER = (
    "INTERNAL RESEARCH-ONLY CANDIDATE ALERT — NOT A PUBLIC EMERGENCY WARNING. "
    "Provisional uncalibrated thresholds; human verification required."
)

SEVERITY_RANK = {
    "INFO": 0,
    "WATCH": 1,
    "ADVISORY": 2,
    "HIGH": 3,
}

QUALIFICATION_STATES = (
    "EXPERIMENTAL",
    "PROVISIONAL_RULE_BASED",
    "INSUFFICIENT_DATA",
    "EXPIRED",
    "RESOLVED",
)

LIFECYCLE_STATES = (
    "ACTIVE",
    "ACKNOWLEDGED",
    "RESOLVED",
    "EXPIRED",
)


@dataclass(frozen=True)
class AlertRuleConfig:
    """Provisional, configurable rule thresholds for Bengaluru grid-cell evaluation.

    All rainfall thresholds are marked PROVISIONAL and require local IDF / gauge
    calibration before any operational or public deployment.
    """

    # Provisional 24h forecast rainfall thresholds (mm)
    forecast_watch_24h_mm: float = 15.6      # Stage 3 ERA5 reference baseline (provisional)
    forecast_advisory_24h_mm: float = 35.0   # Provisional moderate-heavy urban rain
    forecast_high_24h_mm: float = 64.5       # IMD 24h heavy rainfall reference (provisional for 1km grid)
    forecast_peak_hourly_mm: float = 15.0    # Provisional 1h intense convective rain rate

    # Static terrain susceptibility thresholds (from Phase 4 MCDA grid)
    static_moderate_susceptibility: float = 0.45
    static_high_susceptibility: float = 0.60

    # Lifecycle & suppression controls
    cooldown_minutes: int = 120
    default_ttl_hours: float = 12.0


def evaluate_cell_candidate(
    cell: Dict[str, Any],
    forecast_summary: Dict[str, Any],
    observed_summary: Optional[Dict[str, Any]] = None,
    ml_support: Optional[Dict[str, Any]] = None,
    config: Optional[AlertRuleConfig] = None,
) -> Optional[Dict[str, Any]]:
    """Evaluate a single grid cell using separate handling for observed, forecast, terrain, and ML.

    Returns an alert candidate dict if a rule triggers, or None if conditions are below
    provisional thresholds. Never generates a flood alert from stale/unavailable forecasts,
    and never allows the EXPERIMENTAL_UNVALIDATED ML score to trigger an alert alone.
    """
    cfg = config or AlertRuleConfig()
    grid_id = str(cell.get("grid_id", ""))
    if not grid_id:
        return None

    # 1. Observed rainfall handling (never substitute forecast or stale baseline as live obs)
    obs_status = (observed_summary or {}).get("status", "UNAVAILABLE")
    obs_rain = (observed_summary or {}).get("observed_rainfall_mm")
    if obs_status not in ("LIVE", "RECENT"):
        obs_rain = None

    # 2. Forecast rainfall handling (must be LIVE or RECENT)
    fc_freshness = forecast_summary.get("freshness") or forecast_summary.get("status") or "UNAVAILABLE"
    if fc_freshness not in ("LIVE", "RECENT"):
        return None

    fc_24h = forecast_summary.get("next_24h_precipitation_mm")
    fc_peak_1h = forecast_summary.get("peak_hourly_precipitation_mm")
    if fc_24h is None and fc_peak_1h is None:
        return None

    fc_24h_val = float(fc_24h) if fc_24h is not None else 0.0
    fc_peak_val = float(fc_peak_1h) if fc_peak_1h is not None else 0.0

    # 3. Static terrain susceptibility (missing terrain cannot be treated as safe)
    static_susc = cell.get("static_susceptibility_score")
    if static_susc is None:
        static_susc = cell.get("composite_risk_score")
    if static_susc is None:
        return None
    static_val = float(static_susc)

    # 4. Experimental ML score (supporting info only; NEVER triggers an alert independently)
    ml_score = None
    ml_status = "UNAVAILABLE"
    if ml_support is not None:
        ml_score = ml_support.get("experimental_score")
        ml_status = ml_support.get("qualification_status", "EXPERIMENTAL_UNVALIDATED")

    # Provisional rule evaluation
    rule_id: Optional[str] = None
    severity: Optional[str] = None
    explanation: Optional[str] = None

    if fc_24h_val >= cfg.forecast_high_24h_mm and static_val >= cfg.static_high_susceptibility:
        rule_id = "RULE_PROVISIONAL_HEAVY_RAIN_HIGH_SUSCEPTIBILITY"
        severity = "HIGH"
        explanation = (
            f"Provisional 24h forecast ({fc_24h_val:.1f} mm >= {cfg.forecast_high_24h_mm} mm) "
            f"over high static susceptibility cell ({static_val:.2f} >= {cfg.static_high_susceptibility})."
        )
    elif (
        fc_24h_val >= cfg.forecast_advisory_24h_mm or fc_peak_val >= cfg.forecast_peak_hourly_mm
    ) and static_val >= cfg.static_moderate_susceptibility:
        rule_id = "RULE_PROVISIONAL_ADVISORY_RAIN_MODERATE_SUSCEPTIBILITY"
        severity = "ADVISORY"
        explanation = (
            f"Provisional forecast rain (24h={fc_24h_val:.1f} mm, peak 1h={fc_peak_val:.1f} mm) "
            f"over moderate/high static susceptibility cell ({static_val:.2f} >= {cfg.static_moderate_susceptibility})."
        )
    elif fc_24h_val >= cfg.forecast_watch_24h_mm and static_val >= cfg.static_high_susceptibility:
        rule_id = "RULE_PROVISIONAL_WATCH_RAIN_HIGH_SUSCEPTIBILITY"
        severity = "WATCH"
        explanation = (
            f"Provisional 24h forecast ({fc_24h_val:.1f} mm >= {cfg.forecast_watch_24h_mm} mm) "
            f"over high static susceptibility cell ({static_val:.2f} >= {cfg.static_high_susceptibility})."
        )

    if rule_id is None or severity is None:
        return None

    return {
        "grid_id": grid_id,
        "latitude": cell.get("latitude"),
        "longitude": cell.get("longitude"),
        "rule_id": rule_id,
        "severity": severity,
        "qualification_status": "PROVISIONAL_RULE_BASED",
        "title": f"{severity} Candidate: {grid_id}",
        "explanation": explanation,
        "triggering_inputs": {
            "forecast_24h_mm": round(fc_24h_val, 2),
            "forecast_peak_1h_mm": round(fc_peak_val, 2),
            "observed_rainfall_mm": obs_rain,
            "observed_rainfall_status": obs_status,
            "static_susceptibility_score": round(static_val, 4),
            "elevation_mean_m": cell.get("elevation_mean_m"),
            "mean_twi": cell.get("mean_twi"),
            "thresholds_provisional": True,
        },
        "data_source": f"{forecast_summary.get('provider', 'unknown')}/{forecast_summary.get('model', 'unknown')}",
        "data_freshness": fc_freshness,
        "forecast_issue_time_utc": forecast_summary.get("issue_time_utc"),
        "forecast_valid_from_utc": forecast_summary.get("valid_from_utc"),
        "forecast_valid_to_utc": forecast_summary.get("valid_to_utc"),
        "lead_time_hours": forecast_summary.get("lead_time_hours"),
        "experimental_ml_score": ml_score,
        "experimental_ml_status": ml_status,
        "warning_disclaimer": RESEARCH_DISCLAIMER,
    }
