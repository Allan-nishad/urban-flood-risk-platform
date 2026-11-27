# V8 STAGE 5: SPATIAL OPERATIONALIZATION, DEPLOYMENT & OPERATIONAL READINESS REPORT

**Branch:** `upgrade/v8-operational-ai`  
**Baseline Commit:** `d804512` (Stage 4.1)  
**ML Qualification Gate:** `EXPERIMENTAL_UNVALIDATED` / `BLOCKED_EXPERIMENTAL_MODEL`  
**Public Emergency Dispatch:** `DISABLED` (`public_dispatch_enabled = False`)

---

## 1. Deployment Architecture

The platform runs as a self-contained, multi-threaded Python HTTP service (`ThreadedHTTPServer`) with an in-process background weather refresher (`LiveWeatherRefresher`), an event-driven alert evaluation engine (`OperationalAlertEngine`), and a WAL-mode SQLite persistence store (`data/state/floodrisk_v8.db`):

- **HTTP & Static Console:** `src/floodrisk/dashboard/server.py` + `src/floodrisk/dashboard/static/index.html`
- **Multi-Zone Ingestion:** `src/floodrisk/live/open_meteo.py` (`OpenMeteoForecastAdapter.fetch_multi_zone_forecast`) + `src/floodrisk/live/scheduler.py` (`LiveWeatherRefresher`)
- **Spatial Assignment & Clustering:** `src/floodrisk/alerts/spatial.py` & `src/floodrisk/alerts/clustering.py`
- **Alert Lifecycle & Persistence:** `src/floodrisk/alerts/engine.py`, `rules.py`, `storage.py`, `src/floodrisk/live/storage.py`

---

## 2. Spatial Forecast Coverage & Honest Limitations

- **Multi-Anchor Batched Ingestion:** `OpenMeteoForecastAdapter` (`use_multi_zone=True`) queries **5 Bengaluru sector anchors** (`bengaluru_centroid`, `blr_north_west`, `blr_north_east`, `blr_south_west`, `blr_south_east`) in **1 single HTTP request** to respect Open-Meteo API quotas.
- **Observed Native Model Resolution:** Open-Meteo `ecmwf_ifs025` has a **0.25° (~27.8 km)** native grid. Across Bengaluru (`12.8462°–13.1517°N`, `77.4462°–77.7468°E`), the 5 sector anchors snap to **2 distinct native ECMWF IFS model nodes** (`[13.0, 77.5]` West Bengaluru and `[13.0, 77.75]` East Bengaluru).
- **Defensible Cell Assignment (`assign_cell_to_forecast_zone`):** Each 1 km cell is assigned to its nearest fresh (`LIVE`/`RECENT`) sector anchor within `25.0 km` (`NEAREST_SECTOR_ANCHOR_NO_INTERPOLATION`), with zero invented spatial downscaling. Cells outside range or without fresh anchors are marked **`INSUFFICIENT_SPATIAL_COVERAGE`**.
- **Coverage API:** `GET /api/spatial/coverage` reports `covered_cells`, `insufficient_spatial_coverage_cells`, `cells_by_zone`, `distinct_native_model_nodes`, and `native_resolution_deg`.

---

## 3. Alert Aggregation & Fatigue Controls

- **Spatial Clustering (`cluster_alerts` in `src/floodrisk/alerts/clustering.py`):** Groups open (`ACTIVE` / `ACKNOWLEDGED`) alerts by `(forecast_zone_id, ~5.5 km spatial tile)` without inventing administrative ward boundaries.
- **Full Traceability:** Each cluster summary (`GET /api/alerts/clusters`) retains every underlying `alert_id` and `grid_id`, `max_severity`, `active_count`, and `acknowledged_count`.
- **Cluster Operations:** `POST /api/alerts/clusters/{cluster_id}/acknowledge` and `POST /api/alerts/clusters/{cluster_id}/resolve` transition all eligible underlying alerts with per-alert audit-trail entries.
- **Dashboard Integration:** `#alertsTab` displays the Spatial Alert Clusters table alongside individual alerts, spatial coverage, and system health.

---

## 4. Database, Security, Monitoring & Deployment Configuration

### SQLite WAL & Online Backups
- Enabled `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA busy_timeout=5000;` in both `LiveWeatherStore` and `AlertStore`.
- Implemented `backup_database()` via `sqlite3.Connection.backup()` (exposed at `POST /api/system/backup`), plus pre-Stage 5 backup at `data/state/backups/floodrisk_v8_pre_stage5.db`.

### Security & Input Controls
- **Authentication:** Setting `FLOODRISK_ADMIN_TOKEN` enforces `Authorization: Bearer <token>` or `X-Admin-Token: <token>` on all mutating `POST` endpoints (`401` missing, `403` invalid).
- **Request Limits:** `MAX_POST_BODY_BYTES = 65536` (`413 Payload Too Large`), strict query-parameter allowlisting (`400`), and `405` on unsupported POST routes.
- **HTTPS Assumption:** Designed to sit behind a TLS-terminating reverse proxy (e.g., Nginx/Caddy) in production; no secrets committed to Git.

### Continuous Monitoring
- `GET /api/health` reports `HEALTHY`, `DEGRADED`, or `UNHEALTHY` based on SQLite health, forecast freshness (`LIVE`/`RECENT`/`STALE`/`UNAVAILABLE`), `provider_consecutive_failures`, `scheduler_running`, `spatial_coverage_status`, `ml_artifact_status` (`AVAILABLE_BLOCKED`), `active_alerts`, and `public_dispatch_enabled: false`.
- `GET /api/ready` returns `200` when DB and all 1,170 grid cells are loaded (`503` otherwise).

### Environment Variables & Startup
- `FLOODRISK_DB_PATH` (default: `data/state/floodrisk_v8.db`)
- `FLOODRISK_BACKUP_DIR` (default: `data/state/backups`)
- `FLOODRISK_REFRESH_INTERVAL_S` (default: `1800`)
- `FLOODRISK_ADMIN_TOKEN` (required for authenticated `POST` controls in deployment)
- **Run command:** `.venv\Scripts\python.exe -m floodrisk.dashboard.server --host 0.0.0.0 --port 8501` (or `floodrisk dashboard`).

---

## 5. Automated Test & Live Demonstration Results

- **New Stage 5 Tests (`tests/test_stage5_deployment.py`):** 5 test functions covering multi-zone Open-Meteo ingestion & mismatch handling, `INSUFFICIENT_SPATIAL_COVERAGE`, alert clustering & cluster ack/resolve, SQLite WAL + online backup + outage/recovery, and API auth (`401`/`403`/`200`), `/api/health`, `/api/ready`, `/api/spatial/coverage`, `/api/alerts/clusters`.
- **Live End-to-End Demonstration (`task-4521`):**
  - **Live Open-Meteo Multi-Zone Startup:** `status=HEALTHY`, `journal_mode=wal`, `forecast_freshness=LIVE`, `scheduler_running=True`, `ready=True`, `covered_cells=1170/1170`, `zones_configured=5`, `distinct_native_model_nodes=[[13.0, 77.5], [13.0, 77.75]]`.
  - **Isolated `70.0 mm` Fixture Clustering & UI:** `633` raw cell alerts aggregated into **`39` spatial clusters** (top cluster `CLU-bengaluru_centroid-TILE_12.950_77.550` with `34` alerts); headless Edge Playwright verified `39` cluster rows and `HEALTHY (Fcst=LIVE, ML=AVAILABLE_BLOCKED)` badge; authenticated `POST` acknowledged all `34` alerts in the top cluster and created an online SQLite backup (`BACKUP: True`).

---

## 6. Remaining Scientific & Pre-Public-Warning Requirements

- **Not Yet Validated for Public Warnings:** Rainfall thresholds remain provisional (`15.6`, `35.0`, `64.5`, `15.0 mm/h`), live KSNDMC/IMD ground gauges are `UNAVAILABLE`, and Stage 3 ML remains `EXPERIMENTAL_UNVALIDATED` / `BLOCKED_EXPERIMENTAL_MODEL`.
- **Before Any Authorized Public Warning Deployment:**
  1. Integrate authenticated live ground rain-gauge telemetry (KSNDMC/IMD).
  2. Calibrate thresholds and validate ML models against multi-year independent flood & verified dry-control events.
  3. Obtain institutional authorization and implement governed CAP/agency notification channels.
