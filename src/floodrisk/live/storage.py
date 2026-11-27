"""SQLite persistence layer for live weather forecasts and provider health."""

import json
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, List, Optional


class LiveWeatherStore:
    """Thread-safe SQLite store for meteorological records and provider health."""

    def __init__(self, db_path: Path | str = Path("data/state/floodrisk_v8.db")):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weather_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    location_ref TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    data_type TEXT NOT NULL,
                    variable TEXT NOT NULL,
                    value REAL,
                    unit TEXT NOT NULL,
                    issue_time_utc TEXT NOT NULL,
                    valid_time_utc TEXT NOT NULL,
                    retrieval_time_utc TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    source_metadata_json TEXT NOT NULL,
                    quality_status TEXT NOT NULL,
                    freshness_status TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_weather_unique
                ON weather_records (provider, location_ref, data_type, variable, valid_time_utc, model_id)
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_weather_type_valid ON weather_records (data_type, valid_time_utc)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_weather_provider_ret ON weather_records (provider, retrieval_time_utc)"
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS provider_health (
                    provider TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    last_attempt_utc TEXT,
                    last_success_utc TEXT,
                    status TEXT NOT NULL,
                    last_error TEXT,
                    consecutive_failures INTEGER NOT NULL DEFAULT 0,
                    records_written INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    def upsert_weather_records(self, records: List[Dict[str, Any]], freshness_status: str = "LIVE") -> int:
        if not records:
            return 0
        rows = [
            (
                r["provider"],
                r["location_ref"],
                float(r["latitude"]),
                float(r["longitude"]),
                r["data_type"],
                r["variable"],
                r["value"],
                r["unit"],
                r["issue_time_utc"],
                r["valid_time_utc"],
                r["retrieval_time_utc"],
                r["model_id"],
                json.dumps(r.get("source_metadata", {})),
                r["quality_status"],
                r.get("freshness_status", freshness_status),
            )
            for r in records
        ]
        with self._lock, self._conn:
            self._conn.executemany(
                """
                INSERT INTO weather_records (
                    provider, location_ref, latitude, longitude, data_type, variable,
                    value, unit, issue_time_utc, valid_time_utc, retrieval_time_utc,
                    model_id, source_metadata_json, quality_status, freshness_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, location_ref, data_type, variable, valid_time_utc, model_id)
                DO UPDATE SET
                    value = excluded.value,
                    unit = excluded.unit,
                    issue_time_utc = excluded.issue_time_utc,
                    retrieval_time_utc = excluded.retrieval_time_utc,
                    source_metadata_json = excluded.source_metadata_json,
                    quality_status = excluded.quality_status,
                    freshness_status = excluded.freshness_status
                """,
                rows,
            )
        return len(rows)

    def update_provider_health(
        self,
        provider: str,
        model_id: str,
        attempt_utc: str,
        success: bool,
        status: str,
        error: Optional[str] = None,
        records_written: int = 0,
    ) -> None:
        with self._lock, self._conn:
            existing = self._conn.execute(
                "SELECT last_success_utc, consecutive_failures FROM provider_health WHERE provider = ?",
                (provider,),
            ).fetchone()
            prev_success = existing["last_success_utc"] if existing else None
            prev_fails = existing["consecutive_failures"] if existing else 0
            new_success = attempt_utc if success else prev_success
            new_fails = 0 if success else (prev_fails + 1)
            self._conn.execute(
                """
                INSERT INTO provider_health (
                    provider, model_id, last_attempt_utc, last_success_utc,
                    status, last_error, consecutive_failures, records_written
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider) DO UPDATE SET
                    model_id = excluded.model_id,
                    last_attempt_utc = excluded.last_attempt_utc,
                    last_success_utc = excluded.last_success_utc,
                    status = excluded.status,
                    last_error = excluded.last_error,
                    consecutive_failures = excluded.consecutive_failures,
                    records_written = excluded.records_written
                """,
                (provider, model_id, attempt_utc, new_success, status, error, new_fails, records_written),
            )

    def get_provider_health(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if provider:
                rows = self._conn.execute("SELECT * FROM provider_health WHERE provider = ?", (provider,)).fetchall()
            else:
                rows = self._conn.execute("SELECT * FROM provider_health ORDER BY provider").fetchall()
            return [dict(r) for r in rows]

    def get_latest_forecast(self, provider: str = "open_meteo", location_ref: str = "bengaluru_centroid") -> List[Dict[str, Any]]:
        with self._lock:
            latest = self._conn.execute(
                """
                SELECT MAX(retrieval_time_utc) AS max_ret
                FROM weather_records
                WHERE provider = ? AND location_ref = ? AND data_type = 'FORECAST'
                """,
                (provider, location_ref),
            ).fetchone()
            if not latest or not latest["max_ret"]:
                return []
            rows = self._conn.execute(
                """
                SELECT * FROM weather_records
                WHERE provider = ? AND location_ref = ? AND data_type = 'FORECAST' AND retrieval_time_utc = ?
                ORDER BY valid_time_utc ASC, variable ASC
                """,
                (provider, location_ref, latest["max_ret"]),
            ).fetchall()
            return [dict(r) for r in rows]

    def count_records(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) AS cnt FROM weather_records").fetchone()
            return int(row["cnt"]) if row else 0

    def close(self) -> None:
        with self._lock:
            self._conn.close()
