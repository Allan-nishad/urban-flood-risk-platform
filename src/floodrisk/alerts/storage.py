"""SQLite persistence layer for operational alert lifecycle and audit trail."""

import json
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, List, Optional


class AlertStore:
    """Thread-safe SQLite store for internal candidate alerts, audit logs, and evaluation runs."""

    def __init__(self, db_path: Path | str = Path("data/state/floodrisk_v8.db")):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock, self._conn:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute("PRAGMA busy_timeout=5000")
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    grid_id TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    rule_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    qualification_status TEXT NOT NULL,
                    lifecycle_state TEXT NOT NULL,
                    title TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    triggering_inputs_json TEXT NOT NULL,
                    data_source TEXT NOT NULL,
                    data_freshness TEXT NOT NULL,
                    forecast_issue_time_utc TEXT,
                    forecast_valid_from_utc TEXT,
                    forecast_valid_to_utc TEXT,
                    lead_time_hours REAL,
                    experimental_ml_score REAL,
                    experimental_ml_status TEXT NOT NULL,
                    warning_disclaimer TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL,
                    expires_at_utc TEXT NOT NULL,
                    acknowledged_by TEXT,
                    acknowledged_at_utc TEXT,
                    resolved_by TEXT,
                    resolved_at_utc TEXT,
                    resolution_note TEXT,
                    evaluation_count INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_alerts_state_grid ON alerts (lifecycle_state, grid_id, rule_id)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_alerts_updated ON alerts (updated_at_utc DESC)"
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alert_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    previous_state TEXT,
                    new_state TEXT,
                    detail_json TEXT NOT NULL,
                    timestamp_utc TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_alert_id ON alert_audit_log (alert_id, id DESC)"
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alert_evaluation_runs (
                    run_id TEXT PRIMARY KEY,
                    started_at_utc TEXT NOT NULL,
                    completed_at_utc TEXT NOT NULL,
                    forecast_freshness TEXT NOT NULL,
                    forecast_retrieval_time_utc TEXT,
                    cells_evaluated INTEGER NOT NULL,
                    alerts_created INTEGER NOT NULL,
                    alerts_updated INTEGER NOT NULL,
                    alerts_suppressed INTEGER NOT NULL,
                    alerts_expired INTEGER NOT NULL,
                    alerts_auto_resolved INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    note TEXT
                )
                """
            )

    def _row_to_alert(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        raw_inputs = d.pop("triggering_inputs_json", "{}")
        try:
            d["triggering_inputs"] = json.loads(raw_inputs)
        except Exception:
            d["triggering_inputs"] = {}
        return d

    def insert_alert(self, alert: Dict[str, Any]) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO alerts (
                    alert_id, grid_id, latitude, longitude, rule_id, severity,
                    qualification_status, lifecycle_state, title, explanation,
                    triggering_inputs_json, data_source, data_freshness,
                    forecast_issue_time_utc, forecast_valid_from_utc, forecast_valid_to_utc,
                    lead_time_hours, experimental_ml_score, experimental_ml_status,
                    warning_disclaimer, created_at_utc, updated_at_utc, expires_at_utc,
                    acknowledged_by, acknowledged_at_utc, resolved_by, resolved_at_utc,
                    resolution_note, evaluation_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert["alert_id"],
                    alert["grid_id"],
                    alert.get("latitude"),
                    alert.get("longitude"),
                    alert["rule_id"],
                    alert["severity"],
                    alert["qualification_status"],
                    alert["lifecycle_state"],
                    alert["title"],
                    alert["explanation"],
                    json.dumps(alert.get("triggering_inputs", {})),
                    alert["data_source"],
                    alert["data_freshness"],
                    alert.get("forecast_issue_time_utc"),
                    alert.get("forecast_valid_from_utc"),
                    alert.get("forecast_valid_to_utc"),
                    alert.get("lead_time_hours"),
                    alert.get("experimental_ml_score"),
                    alert.get("experimental_ml_status", "UNAVAILABLE"),
                    alert["warning_disclaimer"],
                    alert["created_at_utc"],
                    alert["updated_at_utc"],
                    alert["expires_at_utc"],
                    alert.get("acknowledged_by"),
                    alert.get("acknowledged_at_utc"),
                    alert.get("resolved_by"),
                    alert.get("resolved_at_utc"),
                    alert.get("resolution_note"),
                    int(alert.get("evaluation_count", 1)),
                ),
            )

    def update_alert_fields(self, alert_id: str, fields: Dict[str, Any]) -> None:
        if not fields:
            return
        mapped = dict(fields)
        if "triggering_inputs" in mapped:
            mapped["triggering_inputs_json"] = json.dumps(mapped.pop("triggering_inputs"))
        cols = ", ".join(f"{k} = ?" for k in mapped.keys())
        vals = list(mapped.values()) + [alert_id]
        with self._lock, self._conn:
            self._conn.execute(f"UPDATE alerts SET {cols} WHERE alert_id = ?", vals)

    def append_audit(
        self,
        alert_id: str,
        event_type: str,
        actor: str,
        previous_state: Optional[str],
        new_state: Optional[str],
        detail: Dict[str, Any],
        timestamp_utc: str,
    ) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO alert_audit_log (
                    alert_id, event_type, actor, previous_state, new_state, detail_json, timestamp_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (alert_id, event_type, actor, previous_state, new_state, json.dumps(detail), timestamp_utc),
            )

    def record_evaluation_run(self, run: Dict[str, Any]) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO alert_evaluation_runs (
                    run_id, started_at_utc, completed_at_utc, forecast_freshness,
                    forecast_retrieval_time_utc, cells_evaluated, alerts_created,
                    alerts_updated, alerts_suppressed, alerts_expired, alerts_auto_resolved,
                    status, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run["run_id"],
                    run["started_at_utc"],
                    run["completed_at_utc"],
                    run["forecast_freshness"],
                    run.get("forecast_retrieval_time_utc"),
                    int(run["cells_evaluated"]),
                    int(run["alerts_created"]),
                    int(run["alerts_updated"]),
                    int(run["alerts_suppressed"]),
                    int(run["alerts_expired"]),
                    int(run.get("alerts_auto_resolved", 0)),
                    run["status"],
                    run.get("note"),
                ),
            )

    def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,)).fetchone()
            if not row:
                return None
            alert = self._row_to_alert(row)
            audit_rows = self._conn.execute(
                "SELECT id, event_type, actor, previous_state, new_state, detail_json, timestamp_utc "
                "FROM alert_audit_log WHERE alert_id = ? ORDER BY id DESC",
                (alert_id,),
            ).fetchall()
            alert["audit_trail"] = [
                {**dict(a), "detail": json.loads(a["detail_json"])}
                for a in audit_rows
            ]
            for a in alert["audit_trail"]:
                a.pop("detail_json", None)
            return alert

    def list_alerts(
        self,
        lifecycle_state: Optional[str] = None,
        grid_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []
        if lifecycle_state:
            clauses.append("lifecycle_state = ?")
            params.append(lifecycle_state)
        if grid_id:
            clauses.append("grid_id = ?")
            params.append(grid_id)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM alerts {where} ORDER BY updated_at_utc DESC LIMIT ?"
        params.append(int(limit))
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_alert(r) for r in rows]

    def get_recent_closed_alert(self, grid_id: str, rule_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT * FROM alerts
                WHERE grid_id = ? AND rule_id = ? AND lifecycle_state IN ('RESOLVED', 'EXPIRED')
                ORDER BY updated_at_utc DESC LIMIT 1
                """,
                (grid_id, rule_id),
            ).fetchone()
        return self._row_to_alert(row) if row else None

    def get_latest_evaluation_run(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM alert_evaluation_runs ORDER BY completed_at_utc DESC LIMIT 1"
            ).fetchone()
        return dict(row) if row else None

    def get_summary_counts(self) -> Dict[str, Any]:
        with self._lock:
            by_state = {
                r["lifecycle_state"]: r["cnt"]
                for r in self._conn.execute(
                    "SELECT lifecycle_state, COUNT(*) AS cnt FROM alerts GROUP BY lifecycle_state"
                ).fetchall()
            }
            by_severity_active = {
                r["severity"]: r["cnt"]
                for r in self._conn.execute(
                    "SELECT severity, COUNT(*) AS cnt FROM alerts "
                    "WHERE lifecycle_state IN ('ACTIVE', 'ACKNOWLEDGED') GROUP BY severity"
                ).fetchall()
            }
            total = sum(by_state.values())
        return {
            "total_alerts": total,
            "by_lifecycle_state": by_state,
            "active_or_acknowledged_by_severity": by_severity_active,
        }

    def close(self) -> None:
        with self._lock:
            self._conn.close()
