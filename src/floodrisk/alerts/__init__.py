"""Operational flood-risk alert engine (internal, research-qualified)."""

from .clustering import cluster_alerts
from .engine import (
    AlertNotFoundError,
    InvalidLifecycleTransitionError,
    OperationalAlertEngine,
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
    "SEVERITY_RANK",
    "assign_cell_to_forecast_zone",
    "cluster_alerts",
    "evaluate_cell_candidate",
    "summarize_spatial_coverage",
]
