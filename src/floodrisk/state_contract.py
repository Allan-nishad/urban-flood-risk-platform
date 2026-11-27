"""Shared Data-State Contract for backend, API, and frontend."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

DATA_STATES = (
    "AVAILABLE",
    "PARTIAL",
    "UNAVAILABLE",
    "UNOBSERVED",
    "UNVALIDATED",
    "STALE",
)


def make_state_field(
    value: Any,
    status: str,
    source: str,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Wrap a nullable metric with explicit state, source, and timestamp metadata."""
    if status not in DATA_STATES:
        raise ValueError(f"Invalid data state '{status}'. Must be one of {DATA_STATES}")
    return {
        "value": value,
        "status": status,
        "source": source,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }
