"""Scheduled live weather refresher with exponential backoff and freshness evaluation."""

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

from .open_meteo import OpenMeteoForecastAdapter, ProviderError
from .storage import LiveWeatherStore

logger = logging.getLogger(__name__)


def compute_freshness(
    retrieval_time_utc: Optional[str],
    now_utc: Optional[datetime] = None,
    live_hours: float = 3.0,
    recent_hours: float = 12.0,
) -> str:
    """Classify retrieval timestamp into LIVE, RECENT, STALE, or UNAVAILABLE."""
    if not retrieval_time_utc:
        return "UNAVAILABLE"
    try:
        dt = datetime.fromisoformat(retrieval_time_utc.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return "INVALID"
    ref = now_utc or datetime.now(timezone.utc)
    age_hours = (ref - dt.astimezone(timezone.utc)).total_seconds() / 3600.0
    if age_hours < 0:
        return "LIVE"
    if age_hours <= live_hours:
        return "LIVE"
    if age_hours <= recent_hours:
        return "RECENT"
    return "STALE"


class LiveWeatherRefresher:
    """Background scheduler for refreshing Open-Meteo forecasts into SQLite."""

    def __init__(
        self,
        store: LiveWeatherStore,
        adapter: Optional[OpenMeteoForecastAdapter] = None,
        refresh_interval_s: float = 1800.0,
        freshness_live_hours: float = 3.0,
        freshness_recent_hours: float = 12.0,
        max_retries: int = 3,
        backoff_base_s: float = 1.0,
        sleep_fn: Callable[[float], None] = time.sleep,
        on_refresh_success: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.store = store
        self.adapter = adapter or OpenMeteoForecastAdapter()
        self.refresh_interval_s = float(refresh_interval_s)
        self.freshness_live_hours = float(freshness_live_hours)
        self.freshness_recent_hours = float(freshness_recent_hours)
        self.max_retries = int(max_retries)
        self.backoff_base_s = float(backoff_base_s)
        self._sleep = sleep_fn
        self.on_refresh_success = on_refresh_success
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def refresh_once(self) -> Dict[str, Any]:
        """Attempt forecast retrieval with exponential backoff; never hides failures."""
        attempt_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        last_err: Optional[str] = None

        for attempt in range(self.max_retries):
            try:
                res = self.adapter.fetch_forecast()
                written = self.store.upsert_weather_records(res["records"], freshness_status="LIVE")
                self.store.update_provider_health(
                    provider=res["provider"],
                    model_id=res["model_id"],
                    attempt_utc=res["retrieval_time_utc"],
                    success=True,
                    status="LIVE",
                    error=None,
                    records_written=written,
                )
                summary = {
                    "success": True,
                    "provider": res["provider"],
                    "model_id": res["model_id"],
                    "retrieval_time_utc": res["retrieval_time_utc"],
                    "records_written": written,
                    "status": "LIVE",
                }
                if self.on_refresh_success is not None:
                    try:
                        self.on_refresh_success(summary)
                    except Exception:
                        logger.exception("on_refresh_success callback failed")
                return summary
            except ProviderError as e:
                last_err = str(e)
                logger.warning("Open-Meteo refresh attempt %d/%d failed: %s", attempt + 1, self.max_retries, last_err)
                if attempt < self.max_retries - 1:
                    self._sleep(self.backoff_base_s * (2 ** attempt))
            except Exception as e:
                last_err = f"Unexpected error: {type(e).__name__}: {e}"
                logger.exception("Unexpected error during weather refresh")
                break

        # On failure, preserve existing records and compute current freshness if any exist
        existing_health = self.store.get_provider_health("open_meteo")
        prev_success = existing_health[0]["last_success_utc"] if existing_health else None
        status = compute_freshness(
            prev_success,
            live_hours=self.freshness_live_hours,
            recent_hours=self.freshness_recent_hours,
        )
        self.store.update_provider_health(
            provider="open_meteo",
            model_id=self.adapter.preferred_model,
            attempt_utc=attempt_utc,
            success=False,
            status=status,
            error=last_err,
            records_written=0,
        )
        return {
            "success": False,
            "provider": "open_meteo",
            "model_id": self.adapter.preferred_model,
            "attempt_utc": attempt_utc,
            "status": status,
            "error": last_err,
        }

    def start(self, run_initial: bool = True) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()

        def _loop():
            if run_initial:
                self.refresh_once()
            while not self._stop_event.wait(self.refresh_interval_s):
                self.refresh_once()

        self._thread = threading.Thread(target=_loop, name="live-weather-refresher", daemon=True)
        self._thread.start()

    def stop(self, timeout_s: float = 2.0) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout_s)

    @property
    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())
