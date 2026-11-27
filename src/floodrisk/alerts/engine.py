"""Operational flood-risk alert engine with lifecycle, cooldown, and qualification gates."""

from datetime import datetime, timedelta, timezone
import threading
from typing import Any, Dict, Iterable, List, Optional
import uuid

from .clustering import cluster_alerts
from .rules import (
    RESEARCH_DISCLAIMER,
    SEVERITY_RANK,
    AlertRuleConfig,
    evaluate_cell_candidate,
)
from .spatial import assign_cell_to_forecast_zone, summarize_spatial_coverage
from .storage import AlertStore


class AlertNotFoundError(KeyError):
    """Raised when an alert ID does not exist."""


class InvalidLifecycleTransitionError(ValueError):
    """Raised when an alert lifecycle state transition is invalid."""


def _parse_iso_utc(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _fmt_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class OperationalAlertEngine:
    """Evaluates grid cells against fresh forecasts and manages persistent alert lifecycles.

    Safety invariants:
      - Public emergency notifications are permanently disabled (public_dispatch_enabled=False).
      - Experimental ML scores are supporting metadata only and cannot trigger alerts.
      - Stale, unavailable, or invalid forecast inputs never generate fresh alerts.
    """

    public_dispatch_enabled: bool = False

    def __init__(
        self,
        store: AlertStore,
        config: Optional[AlertRuleConfig] = None,
    ):
        self.store = store
        self.config = config or AlertRuleConfig()
        self._eval_lock = threading.Lock()

    def _enrich_forecast_summary(self, forecast_payload: Dict[str, Any], now_dt: datetime) -> Dict[str, Any]:
        summary = dict(forecast_payload or {})
        hourly = summary.get("hourly_forecast") or []
        if summary.get("peak_hourly_precipitation_mm") is None and hourly:
            peaks = [h.get("precipitation") for h in hourly[:24] if h.get("precipitation") is not None]
            summary["peak_hourly_precipitation_mm"] = round(max(peaks), 2) if peaks else None

        if summary.get("lead_time_hours") is None:
            valid_from = _parse_iso_utc(summary.get("valid_from_utc"))
            if valid_from is not None:
                lead_h = max(0.0, (valid_from - now_dt).total_seconds() / 3600.0)
                summary["lead_time_hours"] = round(lead_h, 2)
        return summary

    def expire_stale_alerts(self, now_dt: Optional[datetime] = None) -> int:
        """Expire ACTIVE or ACKNOWLEDGED alerts whose expires_at_utc has passed."""
        ref = now_dt or datetime.now(timezone.utc)
        now_str = _fmt_utc(ref)
        expired_count = 0
        for state in ("ACTIVE", "ACKNOWLEDGED"):
            for alert in self.store.list_alerts(lifecycle_state=state, limit=1000):
                exp_dt = _parse_iso_utc(alert.get("expires_at_utc"))
                if exp_dt is not None and exp_dt <= ref:
                    self.store.update_alert_fields(
                        alert["alert_id"],
                        {
                            "lifecycle_state": "EXPIRED",
                            "qualification_status": "EXPIRED",
                            "updated_at_utc": now_str,
                        },
                    )
                    self.store.append_audit(
                        alert_id=alert["alert_id"],
                        event_type="EXPIRED",
                        actor="system:alert_engine",
                        previous_state=state,
                        new_state="EXPIRED",
                        detail={"expires_at_utc": alert.get("expires_at_utc")},
                        timestamp_utc=now_str,
                    )
                    expired_count += 1
        return expired_count

    def evaluate(
        self,
        cells: Iterable[Dict[str, Any]],
        forecast_payload: Dict[str, Any],
        observed_payload: Optional[Dict[str, Any]] = None,
        ml_support_by_grid: Optional[Dict[str, Dict[str, Any]]] = None,
        now_utc: Optional[datetime] = None,
        zone_forecasts: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Run one full alert evaluation cycle over all provided grid cells."""
        with self._eval_lock:
            now_dt = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
            now_str = _fmt_utc(now_dt)
            run_id = f"RUN-{uuid.uuid4().hex[:10].upper()}"

            expired_count = self.expire_stale_alerts(now_dt=now_dt)
            fc = self._enrich_forecast_summary(forecast_payload, now_dt)
            fc_freshness = fc.get("freshness") or fc.get("status") or "UNAVAILABLE"
            fc_ret_utc = fc.get("retrieval_time_utc")

            enriched_zones: Optional[Dict[str, Dict[str, Any]]] = None
            if zone_forecasts is not None:
                enriched_zones = {
                    zid: self._enrich_forecast_summary(zfc, now_dt)
                    for zid, zfc in zone_forecasts.items()
                }
                has_any_fresh_zone = any(
                    (zfc.get("freshness") or zfc.get("status")) in ("LIVE", "RECENT") and zfc.get("hourly_forecast")
                    for zfc in enriched_zones.values()
                )
            else:
                has_any_fresh_zone = fc_freshness in ("LIVE", "RECENT") and bool(fc.get("hourly_forecast"))

            # Safety gate: never generate fresh-looking alerts from stale or unavailable data
            if not has_any_fresh_zone:
                run_rec = {
                    "run_id": run_id,
                    "started_at_utc": now_str,
                    "completed_at_utc": _fmt_utc(datetime.now(timezone.utc)),
                    "forecast_freshness": str(fc_freshness),
                    "forecast_retrieval_time_utc": fc_ret_utc,
                    "cells_evaluated": 0,
                    "alerts_created": 0,
                    "alerts_updated": 0,
                    "alerts_suppressed": 0,
                    "alerts_expired": expired_count,
                    "alerts_auto_resolved": 0,
                    "status": "SKIPPED_STALE_OR_UNAVAILABLE",
                    "note": (
                        f"Skipped candidate generation because forecast freshness is '{fc_freshness}' "
                        "or hourly_forecast is empty. Stale data is never treated as fresh or safe."
                    ),
                }
                self.store.record_evaluation_run(run_rec)
                return run_rec

            cell_list = list(cells)
            ml_map = ml_support_by_grid or {}
            created = 0
            updated = 0
            suppressed = 0
            auto_resolved = 0
            insufficient_coverage_cells = 0

            # Index open alerts by grid_id (one open candidate alert per grid cell)
            open_alerts: Dict[str, Dict[str, Any]] = {}
            for st in ("ACTIVE", "ACKNOWLEDGED"):
                for a in self.store.list_alerts(lifecycle_state=st, limit=2000):
                    open_alerts[a["grid_id"]] = a

            triggered_grids = set()
            expires_str = _fmt_utc(now_dt + timedelta(hours=self.config.default_ttl_hours))

            for cell in cell_list:
                gid = str(cell.get("grid_id", ""))
                cell_fc = fc
                cov_meta: Optional[Dict[str, Any]] = None
                if enriched_zones is not None:
                    assigned_fc, cov_meta = assign_cell_to_forecast_zone(cell, enriched_zones)
                    if assigned_fc is None:
                        insufficient_coverage_cells += 1
                        continue
                    cell_fc = assigned_fc

                cand = evaluate_cell_candidate(
                    cell=cell,
                    forecast_summary=cell_fc,
                    observed_summary=observed_payload,
                    ml_support=ml_map.get(gid),
                    config=self.config,
                )
                if cand is None:
                    continue
                if cov_meta is not None:
                    cand["triggering_inputs"]["forecast_zone_id"] = cov_meta.get("forecast_zone_id")
                    cand["triggering_inputs"]["distance_to_anchor_km"] = cov_meta.get("distance_to_anchor_km")
                    cand["triggering_inputs"]["assignment_method"] = cov_meta.get("assignment_method")
                    cand["triggering_inputs"]["spatial_forcing_scope"] = "MULTI_ANCHOR_SECTOR_0_25_DEG"

                triggered_grids.add(cand["grid_id"])
                existing = open_alerts.get(cand["grid_id"])

                if existing is not None:
                    # Update if severity changed (escalation or de-escalation) or forecast issue time changed
                    old_rank = SEVERITY_RANK.get(existing["severity"], 0)
                    new_rank = SEVERITY_RANK.get(cand["severity"], 0)
                    same_issue = existing.get("forecast_issue_time_utc") == cand.get("forecast_issue_time_utc")
                    if new_rank != old_rank or not same_issue:
                        new_count = int(existing.get("evaluation_count", 1)) + 1
                        self.store.update_alert_fields(
                            existing["alert_id"],
                            {
                                "rule_id": cand["rule_id"],
                                "severity": cand["severity"],
                                "title": cand["title"],
                                "explanation": cand["explanation"],
                                "triggering_inputs": cand["triggering_inputs"],
                                "data_freshness": cand["data_freshness"],
                                "forecast_issue_time_utc": cand.get("forecast_issue_time_utc"),
                                "forecast_valid_from_utc": cand.get("forecast_valid_from_utc"),
                                "forecast_valid_to_utc": cand.get("forecast_valid_to_utc"),
                                "lead_time_hours": cand.get("lead_time_hours"),
                                "experimental_ml_score": cand.get("experimental_ml_score"),
                                "experimental_ml_status": cand.get("experimental_ml_status", "UNAVAILABLE"),
                                "updated_at_utc": now_str,
                                "expires_at_utc": expires_str,
                                "evaluation_count": new_count,
                            },
                        )
                        self.store.append_audit(
                            alert_id=existing["alert_id"],
                            event_type="UPDATED",
                            actor="system:alert_engine",
                            previous_state=existing["lifecycle_state"],
                            new_state=existing["lifecycle_state"],
                            detail={"rule_id": cand["rule_id"], "severity": cand["severity"], "evaluation_count": new_count},
                            timestamp_utc=now_str,
                        )
                        updated += 1
                    else:
                        suppressed += 1
                    continue

                # Cooldown check against recently resolved/expired alert for same (grid_id, rule_id)
                recent_closed = self.store.get_recent_closed_alert(cand["grid_id"], cand["rule_id"])
                if recent_closed is not None:
                    closed_dt = _parse_iso_utc(
                        recent_closed.get("resolved_at_utc") or recent_closed.get("updated_at_utc")
                    )
                    if closed_dt is not None:
                        elapsed_min = (now_dt - closed_dt).total_seconds() / 60.0
                        if 0 <= elapsed_min < self.config.cooldown_minutes:
                            suppressed += 1
                            continue

                alert_id = f"ALT-{uuid.uuid4().hex[:12].upper()}"
                new_alert = {
                    **cand,
                    "alert_id": alert_id,
                    "lifecycle_state": "ACTIVE",
                    "created_at_utc": now_str,
                    "updated_at_utc": now_str,
                    "expires_at_utc": expires_str,
                    "evaluation_count": 1,
                }
                self.store.insert_alert(new_alert)
                self.store.append_audit(
                    alert_id=alert_id,
                    event_type="CREATED",
                    actor="system:alert_engine",
                    previous_state=None,
                    new_state="ACTIVE",
                    detail={"rule_id": cand["rule_id"], "severity": cand["severity"]},
                    timestamp_utc=now_str,
                )
                created += 1

            # Auto-resolve ACTIVE alerts whose conditions dropped below provisional thresholds on fresh data
            for gid, existing in open_alerts.items():
                if existing["lifecycle_state"] == "ACTIVE" and gid not in triggered_grids:
                    self.store.update_alert_fields(
                        existing["alert_id"],
                        {
                            "lifecycle_state": "RESOLVED",
                            "qualification_status": "RESOLVED",
                            "updated_at_utc": now_str,
                            "resolved_by": "system:alert_engine",
                            "resolved_at_utc": now_str,
                            "resolution_note": "Forecast conditions dropped below provisional thresholds.",
                        },
                    )
                    self.store.append_audit(
                        alert_id=existing["alert_id"],
                        event_type="RESOLVED",
                        actor="system:alert_engine",
                        previous_state="ACTIVE",
                        new_state="RESOLVED",
                        detail={"reason": "below_provisional_threshold"},
                        timestamp_utc=now_str,
                    )
                    auto_resolved += 1

            run_rec = {
                "run_id": run_id,
                "started_at_utc": now_str,
                "completed_at_utc": _fmt_utc(datetime.now(timezone.utc)),
                "forecast_freshness": str(fc_freshness),
                "forecast_retrieval_time_utc": fc_ret_utc,
                "cells_evaluated": len(cell_list),
                "alerts_created": created,
                "alerts_updated": updated,
                "alerts_suppressed": suppressed,
                "alerts_expired": expired_count,
                "alerts_auto_resolved": auto_resolved,
                "status": "COMPLETED",
                "note": "Evaluated with provisional thresholds; public dispatch disabled.",
            }
            self.store.record_evaluation_run(run_rec)
            return run_rec

    def acknowledge_alert(self, alert_id: str, actor: str = "operator", note: Optional[str] = None) -> Dict[str, Any]:
        alert = self.store.get_alert(alert_id)
        if alert is None:
            raise AlertNotFoundError(f"Alert '{alert_id}' not found")
        state = alert["lifecycle_state"]
        if state != "ACTIVE":
            raise InvalidLifecycleTransitionError(
                f"Cannot acknowledge alert '{alert_id}' from state '{state}'; must be ACTIVE."
            )
        now_str = _fmt_utc(datetime.now(timezone.utc))
        self.store.update_alert_fields(
            alert_id,
            {
                "lifecycle_state": "ACKNOWLEDGED",
                "acknowledged_by": actor or "operator",
                "acknowledged_at_utc": now_str,
                "updated_at_utc": now_str,
            },
        )
        self.store.append_audit(
            alert_id=alert_id,
            event_type="ACKNOWLEDGED",
            actor=actor or "operator",
            previous_state=state,
            new_state="ACKNOWLEDGED",
            detail={"note": note} if note else {},
            timestamp_utc=now_str,
        )
        return self.store.get_alert(alert_id)  # type: ignore[return-value]

    def resolve_alert(
        self,
        alert_id: str,
        actor: str = "operator",
        note: Optional[str] = None,
        now_utc: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        alert = self.store.get_alert(alert_id)
        if alert is None:
            raise AlertNotFoundError(f"Alert '{alert_id}' not found")
        state = alert["lifecycle_state"]
        if state not in ("ACTIVE", "ACKNOWLEDGED"):
            raise InvalidLifecycleTransitionError(
                f"Cannot resolve alert '{alert_id}' from state '{state}'; must be ACTIVE or ACKNOWLEDGED."
            )
        now_str = _fmt_utc(now_utc or datetime.now(timezone.utc))
        self.store.update_alert_fields(
            alert_id,
            {
                "lifecycle_state": "RESOLVED",
                "qualification_status": "RESOLVED",
                "resolved_by": actor or "operator",
                "resolved_at_utc": now_str,
                "resolution_note": note or "Resolved by operator.",
                "updated_at_utc": now_str,
            },
        )
        self.store.append_audit(
            alert_id=alert_id,
            event_type="RESOLVED",
            actor=actor or "operator",
            previous_state=state,
            new_state="RESOLVED",
            detail={"note": note} if note else {},
            timestamp_utc=now_str,
        )
        return self.store.get_alert(alert_id)  # type: ignore[return-value]

    def get_clusters(self, max_clusters: int = 50) -> List[Dict[str, Any]]:
        open_alerts = self.store.list_alerts(lifecycle_state="ACTIVE", limit=2000) + self.store.list_alerts(
            lifecycle_state="ACKNOWLEDGED", limit=2000
        )
        return cluster_alerts(open_alerts, max_clusters=max_clusters)

    def acknowledge_cluster(self, cluster_id: str, actor: str = "operator", note: Optional[str] = None) -> Dict[str, Any]:
        clusters = self.get_clusters(max_clusters=500)
        target = next((c for c in clusters if c["cluster_id"] == cluster_id), None)
        if target is None:
            raise AlertNotFoundError(f"Cluster '{cluster_id}' not found or has no open alerts")
        acked = []
        for aid in target["alert_ids"]:
            a = self.store.get_alert(aid)
            if a and a["lifecycle_state"] == "ACTIVE":
                acked.append(self.acknowledge_alert(aid, actor=actor, note=note or f"Cluster ack: {cluster_id}"))
        return {"cluster_id": cluster_id, "acknowledged_count": len(acked), "alert_ids": [a["alert_id"] for a in acked]}

    def resolve_cluster(self, cluster_id: str, actor: str = "operator", note: Optional[str] = None) -> Dict[str, Any]:
        clusters = self.get_clusters(max_clusters=500)
        target = next((c for c in clusters if c["cluster_id"] == cluster_id), None)
        if target is None:
            raise AlertNotFoundError(f"Cluster '{cluster_id}' not found or has no open alerts")
        resolved = []
        for aid in target["alert_ids"]:
            a = self.store.get_alert(aid)
            if a and a["lifecycle_state"] in ("ACTIVE", "ACKNOWLEDGED"):
                resolved.append(self.resolve_alert(aid, actor=actor, note=note or f"Cluster resolve: {cluster_id}"))
        return {"cluster_id": cluster_id, "resolved_count": len(resolved), "alert_ids": [a["alert_id"] for a in resolved]}

    def get_summary(self) -> Dict[str, Any]:
        counts = self.store.get_summary_counts()
        latest_run = self.store.get_latest_evaluation_run()
        return {
            "status": "AVAILABLE",
            "public_dispatch_enabled": self.public_dispatch_enabled,
            "spatial_forcing_scope": "REGIONAL_SINGLE_ANCHOR_BENGALURU",
            "multi_zone_spatial_scope": "MULTI_ANCHOR_SECTOR_0_25_DEG",
            "spatial_coverage_note": (
                "Forecast forcing is assigned from Bengaluru sector anchors (snapping to 2 distinct "
                "native 0.25-deg ECMWF IFS nodes) combined with cell-level static terrain susceptibility; "
                "not 1,170 independent local forecasts."
            ),
            "warning_disclaimer": RESEARCH_DISCLAIMER,
            "ml_qualification_gate": "BLOCKED_EXPERIMENTAL_MODEL",
            **counts,
            "latest_evaluation_run": latest_run,
        }
