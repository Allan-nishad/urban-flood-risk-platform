"""Operational flood-risk alert engine (internal, research-qualified)."""

from .clustering import cluster_alerts
from .engine import (
    AlertNotFoundError,
    InvalidLifecycleTransitionError,
    OperationalAlertEngine,
)
from .risk_engine import (
    RISK_METHODOLOGY_DOC,
    assess_cell_for_horizon,
    evaluate_cell_risk_timeline,
    evaluate_forecast_risk_grid,
)
from .rules import (
    LIFECYCLE_STATES,
    QUALIFICATION_STATES,
    RESEARCH_DISCLAIMER,
    SEVERITY_RANK,
    AlertRuleConfig,
    evaluate_cell_candidate,
)
from .spatial import assign_cell_to_forecast_zone, summarize_spatial_coverage
from .storage import AlertStore

__all__ = [
    "AlertNotFoundError",
    "AlertRuleConfig",
    "AlertStore",
    "InvalidLifecycleTransitionError",
    "LIFECYCLE_STATES",
    "OperationalAlertEngine",
    "QUALIFICATION_STATES",
    "RESEARCH_DISCLAIMER",
    "RISK_METHODOLOGY_DOC",
    "SEVERITY_RANK",
    "assess_cell_for_horizon",
    "assign_cell_to_forecast_zone",
    "cluster_alerts",
    "evaluate_cell_candidate",
    "evaluate_cell_risk_timeline",
    "evaluate_forecast_risk_grid",
    "summarize_spatial_coverage",
]
