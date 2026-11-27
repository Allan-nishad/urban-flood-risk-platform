"""Operational flood-risk alert engine (internal, research-qualified)."""

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
    "evaluate_cell_candidate",
]
