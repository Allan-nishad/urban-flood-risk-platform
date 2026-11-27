"""Live weather ingestion, SQLite persistence, and refresh scheduling."""

from .forecast_metrics import HORIZON_HOURS, compute_rainfall_windows
from .open_meteo import OpenMeteoArchiveAdapter, OpenMeteoForecastAdapter, ProviderError
from .scheduler import LiveWeatherRefresher, compute_freshness
from .storage import LiveWeatherStore, cleanup_old_backups

__all__ = [
    "HORIZON_HOURS",
    "OpenMeteoForecastAdapter",
    "OpenMeteoArchiveAdapter",
    "ProviderError",
    "LiveWeatherStore",
    "LiveWeatherRefresher",
    "cleanup_old_backups",
    "compute_freshness",
    "compute_rainfall_windows",
]
