"""Open-Meteo forecast and historical reanalysis adapters with strict validation."""

from datetime import datetime, timezone
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple


class ProviderError(RuntimeError):
    """Raised when an external weather provider fails or returns invalid data."""


def _default_http_get(url: str, timeout: float) -> Tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "urban-flood-risk-platform-v8/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        raise ProviderError(f"HTTP {e.code} from provider: {e.reason}") from e
    except Exception as e:
        raise ProviderError(f"Network/timeout error: {type(e).__name__}: {e}") from e


def _validate_coords(lat: float, lon: float) -> None:
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        raise ProviderError(f"Invalid geographic coordinates: lat={lat}, lon={lon}")


def _parse_iso_utc(ts: str) -> str:
    if not isinstance(ts, str) or not ts.strip():
        raise ProviderError(f"Empty or non-string timestamp: {ts!r}")
    norm = ts.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(norm)
    except ValueError as e:
        raise ProviderError(f"Invalid ISO-8601 timestamp: {ts!r}") from e
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class OpenMeteoForecastAdapter:
    """Adapter for Open-Meteo Forecast API preferring ECMWF IFS (`ecmwf_ifs025`)."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    NATIVE_RESOLUTION_DEG = 0.25
    REQUIRED_VARS = ("precipitation", "rain", "temperature_2m", "relative_humidity_2m")
    EXPECTED_UNITS = {
        "precipitation": "mm",
        "rain": "mm",
        "temperature_2m": "°C",
        "relative_humidity_2m": "%",
    }
    BENGALURU_FORECAST_ZONES = (
        {"zone_id": "bengaluru_centroid", "latitude": 12.9716, "longitude": 77.5946, "label": "Central Bengaluru"},
        {"zone_id": "blr_north_west", "latitude": 13.0800, "longitude": 77.5000, "label": "North-West (Yelahanka/Peenya)"},
        {"zone_id": "blr_north_east", "latitude": 13.0800, "longitude": 77.6900, "label": "North-East (Mahadevapura/KR Puram)"},
        {"zone_id": "blr_south_west", "latitude": 12.9000, "longitude": 77.5000, "label": "South-West (Kengeri/RR Nagar)"},
        {"zone_id": "blr_south_east", "latitude": 12.9000, "longitude": 77.6900, "label": "South-East (Bellandur/HSR)"},
    )

    def __init__(
        self,
        latitude: float = 12.9716,
        longitude: float = 77.5946,
        location_ref: str = "bengaluru_centroid",
        preferred_model: str = "ecmwf_ifs025",
        forecast_days: int = 3,
        timeout_s: float = 10.0,
        http_get: Optional[Callable[[str, float], Tuple[int, bytes]]] = None,
        use_multi_zone: bool = False,
    ):
        _validate_coords(latitude, longitude)
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.location_ref = location_ref
        self.preferred_model = preferred_model
        self.forecast_days = int(forecast_days)
        self.timeout_s = float(timeout_s)
        self._http_get = http_get or _default_http_get
        self.use_multi_zone = bool(use_multi_zone)

    def build_url(self, model: Optional[str] = None, zones: Optional[List[Dict[str, Any]]] = None) -> str:
        if zones:
            lats = ",".join(str(z["latitude"]) for z in zones)
            lons = ",".join(str(z["longitude"]) for z in zones)
        else:
            lats = str(self.latitude)
            lons = str(self.longitude)
        params = urllib.parse.urlencode({
            "latitude": lats,
            "longitude": lons,
            "hourly": ",".join(self.REQUIRED_VARS),
            "models": model or self.preferred_model,
            "forecast_days": self.forecast_days,
            "timezone": "UTC",
        })
        return f"{self.BASE_URL}?{params}"

    def _parse_zone_payload(
        self,
        payload: Dict[str, Any],
        location_ref: str,
        req_lat: float,
        req_lon: float,
        retrieval_utc: str,
        issue_utc: str,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Tuple[float, float]]:
        if not isinstance(payload, dict) or payload.get("error"):
            raise ProviderError(f"Open-Meteo API error payload: {payload}")

        ret_lat = payload.get("latitude")
        ret_lon = payload.get("longitude")
        if ret_lat is None or ret_lon is None:
            raise ProviderError("Missing latitude/longitude in Open-Meteo response")
        _validate_coords(float(ret_lat), float(ret_lon))
        if abs(float(ret_lat) - req_lat) > 1.0 or abs(float(ret_lon) - req_lon) > 1.0:
            raise ProviderError(f"Returned coordinates ({ret_lat}, {ret_lon}) out of Bengaluru tolerance")

        hourly = payload.get("hourly")
        units = payload.get("hourly_units")
        if not isinstance(hourly, dict) or not isinstance(units, dict):
            raise ProviderError("Missing 'hourly' or 'hourly_units' block in Open-Meteo response")

        times = hourly.get("time")
        if not isinstance(times, list) or len(times) == 0:
            raise ProviderError("Missing or empty 'hourly.time' array")

        for var in self.REQUIRED_VARS:
            if var not in hourly or not isinstance(hourly[var], list):
                raise ProviderError(f"Missing required variable '{var}' in Open-Meteo response")
            if len(hourly[var]) != len(times):
                raise ProviderError(f"Length mismatch for '{var}': {len(hourly[var])} != {len(times)}")
            if units.get(var) != self.EXPECTED_UNITS[var]:
                raise ProviderError(f"Unexpected unit for '{var}': got {units.get(var)!r}, expected {self.EXPECTED_UNITS[var]!r}")

        parsed_times = [_parse_iso_utc(t) for t in times]
        meta = {
            "provider_url": self.BASE_URL,
            "requested_model": self.preferred_model,
            "requested_latitude": float(req_lat),
            "requested_longitude": float(req_lon),
            "returned_latitude": float(ret_lat),
            "returned_longitude": float(ret_lon),
            "native_resolution_deg": self.NATIVE_RESOLUTION_DEG,
            "elevation_m": payload.get("elevation"),
            "timezone": payload.get("timezone", "UTC"),
            "generationtime_ms": payload.get("generationtime_ms"),
            "issue_time_note": "Nominal 6h UTC cycle derived from retrieval time (Open-Meteo omits exact NWP init time).",
        }

        records: List[Dict[str, Any]] = []
        for idx, valid_utc in enumerate(parsed_times):
            for var in self.REQUIRED_VARS:
                val = hourly[var][idx]
                q_status = "AVAILABLE" if val is not None else "UNAVAILABLE"
                records.append({
                    "provider": "open_meteo",
                    "location_ref": location_ref,
                    "latitude": float(ret_lat),
                    "longitude": float(ret_lon),
                    "data_type": "FORECAST",
                    "variable": var,
                    "value": float(val) if val is not None else None,
                    "unit": units[var],
                    "issue_time_utc": issue_utc,
                    "valid_time_utc": valid_utc,
                    "retrieval_time_utc": retrieval_utc,
                    "model_id": self.preferred_model,
                    "source_metadata": meta,
                    "quality_status": q_status,
                })
        return records, meta, (round(float(ret_lat), 4), round(float(ret_lon), 4))

    def fetch_forecast(self) -> Dict[str, Any]:
        """Fetch, validate, and normalize hourly forecast records for the single anchor."""
        retrieval_dt = datetime.now(timezone.utc)
        retrieval_utc = retrieval_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        cycle_hour = (retrieval_dt.hour // 6) * 6
        issue_utc = retrieval_dt.replace(hour=cycle_hour, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")

        url = self.build_url(self.preferred_model)
        status_code, raw_bytes = self._http_get(url, self.timeout_s)
        if status_code != 200:
            raise ProviderError(f"Unexpected HTTP status {status_code} from Open-Meteo")

        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            raise ProviderError(f"Invalid JSON from Open-Meteo: {e}") from e

        records, meta, native_node = self._parse_zone_payload(
            payload, self.location_ref, self.latitude, self.longitude, retrieval_utc, issue_utc
        )
        return {
            "provider": "open_meteo",
            "model_id": self.preferred_model,
            "issue_time_utc": issue_utc,
            "retrieval_time_utc": retrieval_utc,
            "metadata": meta,
            "records": records,
            "zones_fetched": 1,
            "distinct_native_nodes": [native_node],
        }

    def fetch_multi_zone_forecast(self, zones: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Fetch batched multi-coordinate forecasts for Bengaluru sector anchors in one HTTP call."""
        zone_list = list(zones or self.BENGALURU_FORECAST_ZONES)
        retrieval_dt = datetime.now(timezone.utc)
        retrieval_utc = retrieval_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        cycle_hour = (retrieval_dt.hour // 6) * 6
        issue_utc = retrieval_dt.replace(hour=cycle_hour, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")

        url = self.build_url(self.preferred_model, zones=zone_list)
        status_code, raw_bytes = self._http_get(url, self.timeout_s)
        if status_code != 200:
            raise ProviderError(f"Unexpected HTTP status {status_code} from Open-Meteo")

        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            raise ProviderError(f"Invalid JSON from Open-Meteo: {e}") from e

        items = payload if isinstance(payload, list) else [payload]
        if len(items) != len(zone_list):
            raise ProviderError(f"Multi-zone length mismatch: expected {len(zone_list)}, got {len(items)}")

        all_records: List[Dict[str, Any]] = []
        native_nodes = set()
        for zone, item in zip(zone_list, items):
            recs, _meta, node = self._parse_zone_payload(
                item,
                zone["zone_id"],
                float(zone["latitude"]),
                float(zone["longitude"]),
                retrieval_utc,
                issue_utc,
            )
            all_records.extend(recs)
            native_nodes.add(node)

        return {
            "provider": "open_meteo",
            "model_id": self.preferred_model,
            "issue_time_utc": issue_utc,
            "retrieval_time_utc": retrieval_utc,
            "records": all_records,
            "zones_fetched": len(zone_list),
            "distinct_native_nodes": sorted(native_nodes),
        }


class OpenMeteoArchiveAdapter:
    """Separate adapter for Open-Meteo Historical Reanalysis (ERA5-Land).

    Always tagged `HISTORICAL_REANALYSIS`; never live observation or flood ground truth.
    """

    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
    DATA_CLASSIFICATION = "HISTORICAL_REANALYSIS"

    def __init__(
        self,
        latitude: float = 12.9716,
        longitude: float = 77.5946,
        location_ref: str = "bengaluru_centroid",
        timeout_s: float = 10.0,
        http_get: Optional[Callable[[str, float], Tuple[int, bytes]]] = None,
    ):
        _validate_coords(latitude, longitude)
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.location_ref = location_ref
        self.timeout_s = float(timeout_s)
        self._http_get = http_get or _default_http_get

    def fetch_historical(self, start_date: str, end_date: str) -> Dict[str, Any]:
        params = urllib.parse.urlencode({
            "latitude": self.latitude,
            "longitude": self.longitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": "precipitation,rain",
            "timezone": "UTC",
        })
        url = f"{self.BASE_URL}?{params}"
        status_code, raw_bytes = self._http_get(url, self.timeout_s)
        if status_code != 200:
            raise ProviderError(f"Unexpected HTTP {status_code} from Open-Meteo Archive")
        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            raise ProviderError(f"Invalid JSON from Open-Meteo Archive: {e}") from e
        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        units = payload.get("hourly_units") or {}
        if not times or "precipitation" not in hourly:
            raise ProviderError("Incomplete Open-Meteo Archive response")

        retrieval_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        records: List[Dict[str, Any]] = []
        for idx, t in enumerate(times):
            valid_utc = _parse_iso_utc(t)
            val = hourly["precipitation"][idx]
            records.append({
                "provider": "open_meteo_archive",
                "location_ref": self.location_ref,
                "latitude": float(payload.get("latitude", self.latitude)),
                "longitude": float(payload.get("longitude", self.longitude)),
                "data_type": self.DATA_CLASSIFICATION,
                "variable": "precipitation",
                "value": float(val) if val is not None else None,
                "unit": units.get("precipitation", "mm"),
                "issue_time_utc": valid_utc,
                "valid_time_utc": valid_utc,
                "retrieval_time_utc": retrieval_utc,
                "model_id": "era5_land",
                "source_metadata": {"classification": self.DATA_CLASSIFICATION, "not_ground_truth": True},
                "quality_status": "HISTORICAL" if val is not None else "UNAVAILABLE",
            })
        return {"classification": self.DATA_CLASSIFICATION, "records": records}
