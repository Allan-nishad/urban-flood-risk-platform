"""Reproducible multi-horizon rainfall window calculations (1h to 72h)."""

from typing import Any, Dict, Iterable, List, Tuple

HORIZON_HOURS: Tuple[int, ...] = (1, 3, 6, 12, 24, 48, 72)


def compute_rainfall_windows(
    hourly_forecast: List[Dict[str, Any]],
    horizons: Iterable[int] = HORIZON_HOURS,
) -> Dict[str, Dict[str, Any]]:
    """Compute cumulative and peak hourly rainfall for standard forecast windows.

    Never fabricates values for missing hours: tracks ``available_hours`` vs
    ``expected_hours`` and marks each window ``AVAILABLE``, ``PARTIAL``, or
    ``UNAVAILABLE``.
    """
    ordered = sorted(hourly_forecast or [], key=lambda h: str(h.get("valid_time_utc") or ""))
    windows: Dict[str, Dict[str, Any]] = {}

    for h in horizons:
        h_int = int(h)
        key = f"{h_int}h"
        slice_rows = ordered[:h_int]
        if not slice_rows:
            windows[key] = {
                "horizon_hours": h_int,
                "expected_hours": h_int,
                "available_hours": 0,
                "missing_hours": h_int,
                "cumulative_mm": None,
                "max_hourly_mm": None,
                "valid_from_utc": None,
                "valid_to_utc": None,
                "quality_status": "UNAVAILABLE",
            }
            continue

        vals = [
            float(r["precipitation"])
            for r in slice_rows
            if r.get("precipitation") is not None
        ]
        avail = len(vals)
        missing = max(0, h_int - avail)
        if avail == 0:
            q_status = "UNAVAILABLE"
        elif avail < h_int:
            q_status = "PARTIAL"
        else:
            q_status = "AVAILABLE"

        windows[key] = {
            "horizon_hours": h_int,
            "expected_hours": h_int,
            "available_hours": avail,
            "missing_hours": missing,
            "cumulative_mm": round(sum(vals), 2) if vals else None,
            "max_hourly_mm": round(max(vals), 2) if vals else None,
            "valid_from_utc": slice_rows[0].get("valid_time_utc"),
            "valid_to_utc": slice_rows[-1].get("valid_time_utc"),
            "quality_status": q_status,
        }

    return windows
