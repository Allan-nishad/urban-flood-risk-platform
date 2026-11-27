# V8 Final Implementation & Limitations Report

**Branch:** `upgrade/v8-operational-ai`  
**Scope:** Private, research-stage forecast-driven urban flood-risk decision-support platform for Bengaluru Urban District (1,170 equal-area 1 km cells, EPSG:6933).

---

## 1. Implemented Capabilities

1. **72-Hour Rainfall Forecasting (`src/floodrisk/live/forecast_metrics.py`, `open_meteo.py`, `scheduler.py`, `storage.py`):**
   - Live batched 5-anchor ECMWF IFS (`ecmwf_ifs025`, 0.25° native grid) ingestion via Open-Meteo.
   - Cumulative and peak hourly rainfall windows for `1h, 3h, 6h, 12h, 24h, 48h, 72h` with explicit `AVAILABLE` / `PARTIAL` / `UNAVAILABLE` quality tracking.
   - SQLite WAL-mode persistence (`PRAGMA user_version = 2`), `forecast_refresh_history` audit table, and automated backup retention (`cleanup_old_backups`).
2. **Forecast-Driven Flood-Risk Prioritisation (`src/floodrisk/alerts/risk_engine.py`):**
   - Integrates static terrain susceptibility, D8 TWI/flow accumulation, WorldCover land cover, historical flood evidence (non-circular context), and multi-zone 1h–72h forecast rainfall.
   - Produces reproducible non-probabilistic `risk_prioritization_index` `[0, 1]` and `risk_category` (`LOW`–`CRITICAL`, or `INSUFFICIENT_DATA` when stale/missing/out-of-coverage).
3. **Experimental ML Integration (`src/floodrisk/ml/train.py`, `infer.py`):**
   - Preserves spatial-block 5-fold CV and temporal holdout evaluation with `data_version`, calibration/uncertainty assessment, and top contributing feature explanations.
   - Remains strictly `EXPERIMENTAL_UNVALIDATED` and `BLOCKED_EXPERIMENTAL_MODEL`.
4. **REST API & Dashboard (`src/floodrisk/dashboard/server.py`, `static/index.html`):**
   - Added `/api/weather/history` and `/api/risk/forecast` (grid-level and per-cell 1h–72h timeline), plus `rainfall_windows` in `/api/weather/forecast`.
   - Cached ML inference and Phase 6/7 hydrology lookups in `DashboardDataStore` to eliminate per-request disk/model reloads.
   - Updated dashboard UI with TWI/UPA metrics, 1h–72h live risk timeline, refresh history table, and `X-Admin-Token` support.
5. **Security, Reliability & Deployment (`server.py`, `alerts/storage.py`, `Dockerfile`, `docker-compose.yml`, `.env.example`):**
   - `hmac.compare_digest()` token verification, fail-closed non-loopback startup check (`FLOODRISK_ADMIN_TOKEN`), restricted CORS, HTTP security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Cache-Control: no-store`), `Content-Length` validation, structured logging, `SIGTERM` graceful shutdown, and `AlertStore` column allowlist.

---

## 2. Documented Limitations

- **Native Weather Resolution:** Open-Meteo `ecmwf_ifs025` operates on a ~27.8 km (0.25°) grid; Bengaluru's 5 sector anchors snap to 2 distinct native model nodes. It does not provide 1,170 independent local forecasts.
- **Live Ground Gauges Unavailable:** KSNDMC and IMD live telemetry feeds remain `UNAVAILABLE`; historical Phase 4.3 baseline is marked `STALE`.
- **Unvalidated Thresholds & ML:** Provisional alert thresholds and the 48-record Random Forest model are not scientifically validated for public emergency warnings (`public_dispatch_enabled = False`).
