# V8 STAGE 4: OPERATIONAL ALERT ENGINE REPORT

**Branch:** `upgrade/v8-operational-ai`  
**Baseline Commit:** `85180c8` (Stage 3)  
**Public Dispatch Status:** `DISABLED` (`public_dispatch_enabled = False`)  
**ML Qualification Gate:** `EXPERIMENTAL_UNVALIDATED` / `BLOCKED_EXPERIMENTAL_MODEL`

---

## 1. Architecture & Implemented Modules

Stage 4 implemented an internal, persistent, scheduler-driven operational flood-risk alert engine under `src/floodrisk/alerts/`:

- **`src/floodrisk/alerts/rules.py`:** Configurable provisional thresholds (`AlertRuleConfig`), qualification states (`QUALIFICATION_STATES`), lifecycle states (`LIFECYCLE_STATES`), mandatory `RESEARCH_DISCLAIMER`, and `evaluate_cell_candidate(...)` with separate handling for observed rainfall, forecast rainfall, static terrain susceptibility, and experimental ML scores.
- **`src/floodrisk/alerts/storage.py`:** Thread-safe SQLite persistence (`AlertStore`) sharing `data/state/floodrisk_v8.db` with `LiveWeatherStore`.
- **`src/floodrisk/alerts/engine.py`:** `OperationalAlertEngine` implementing cell evaluation, duplicate suppression, cooldown windows, severity escalation updates, auto-resolution, TTL expiry, lifecycle transitions (`acknowledge_alert`, `resolve_alert`), and audit logging.
- **`src/floodrisk/live/scheduler.py`:** Added `on_refresh_success` callback on `LiveWeatherRefresher` so successful forecast refreshes automatically trigger alert evaluation.
- **`src/floodrisk/dashboard/server.py` & `src/floodrisk/dashboard/static/index.html`:** Wired `AlertStore`, `OperationalAlertEngine`, REST endpoints (`/api/alerts`, `/api/alerts/summary`, `/api/alerts/{id}`, `/api/alerts/{id}/acknowledge`, `/api/alerts/{id}/resolve`, `/api/alerts/evaluate`), and the **Operational Alerts (Research-Only)** dashboard tab.

---

## 2. Database Schema & Alert Lifecycle

Three SQLite tables in `data/state/floodrisk_v8.db`:
1. **`alerts`:** Stores `alert_id`, `grid_id`, `latitude`, `longitude`, `rule_id`, `severity`, `qualification_status`, `lifecycle_state` (`ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`, `EXPIRED`), `title`, `explanation`, `triggering_inputs_json`, `data_source`, `data_freshness`, `forecast_issue_time_utc`, `forecast_valid_from_utc`, `forecast_valid_to_utc`, `lead_time_hours`, `experimental_ml_score`, `experimental_ml_status`, `warning_disclaimer`, `created_at_utc`, `updated_at_utc`, `expires_at_utc`, `acknowledged_by`, `acknowledged_at_utc`, `resolved_by`, `resolved_at_utc`, `resolution_note`, and `evaluation_count`.
2. **`alert_audit_log`:** Append-only lifecycle audit trail (`CREATED`, `UPDATED`, `ACKNOWLEDGED`, `RESOLVED`, `EXPIRED`).
3. **`alert_evaluation_runs`:** Records every evaluation cycle (`run_id`, timestamps, `forecast_freshness`, `cells_evaluated`, `alerts_created`, `alerts_updated`, `alerts_suppressed`, `alerts_expired`, `alerts_auto_resolved`, `status`, `note`).

### Lifecycle & Safety Invariants
- **Duplicate Suppression:** At most one open (`ACTIVE` or `ACKNOWLEDGED`) alert per `grid_id`. Identical forecast issue times and non-escalating severity suppress duplicate creation.
- **Escalation / Refresh Update:** Higher severity or newer `forecast_issue_time_utc` updates the existing alert in place and logs `UPDATED`.
- **Cooldown:** Re-triggering the same `(grid_id, rule_id)` within `cooldown_minutes` (`120` min default) of a `RESOLVED`/`EXPIRED` alert is suppressed.
- **Auto-Resolution & Expiry:** `ACTIVE` alerts whose fresh forecast conditions drop below provisional thresholds are auto-resolved; any `ACTIVE`/`ACKNOWLEDGED` alert past `expires_at_utc` (`12.0` h default) is marked `EXPIRED`.
- **Stale/Unavailable Gate:** If forecast `freshness` is not `LIVE` or `RECENT` (or `hourly_forecast` is empty), candidate generation is skipped (`SKIPPED_STALE_OR_UNAVAILABLE`), preventing stale inputs from generating fresh-looking alerts.
- **ML Gate:** Stage 3 ML scores (`EXPERIMENTAL_UNVALIDATED`) are stored only as supporting metadata and can never independently trigger an alert.

---

## 3. Rules & Provisional Threshold Sources

All thresholds in `AlertRuleConfig` are explicitly marked **PROVISIONAL** and require local IDF / rain-gauge calibration:
- **`WATCH` (`RULE_PROVISIONAL_WATCH_RAIN_HIGH_SUSCEPTIBILITY`):** `forecast_24h_mm >= 15.6 mm` (Stage 3 ERA5 reference baseline) AND `static_susceptibility_score >= 0.60`.
- **`ADVISORY` (`RULE_PROVISIONAL_ADVISORY_RAIN_MODERATE_SUSCEPTIBILITY`):** (`forecast_24h_mm >= 35.0 mm` OR `peak_hourly_mm >= 15.0 mm`) AND `static_susceptibility_score >= 0.45`.
- **`HIGH` (`RULE_PROVISIONAL_HEAVY_RAIN_HIGH_SUSCEPTIBILITY`):** `forecast_24h_mm >= 64.5 mm` (IMD 24h heavy rainfall reference, provisional for 1 km urban grid) AND `static_susceptibility_score >= 0.60`.

Observed rainfall is handled separately (`UNAVAILABLE` for live gauges; Phase 4.3 `12.5 mm` baseline is `STALE` and never substituted as live telemetry).

---

## 4. Scheduler Behaviour & API Endpoints

- **Scheduler:** `LiveWeatherRefresher.refresh_once()` invokes `on_refresh_success` upon successful Open-Meteo retrieval, automatically running `DashboardDataStore.evaluate_alerts()`. On startup/restart, `DashboardDataStore` also evaluates any fresh stored forecast and recovers persisted alerts from SQLite.
- **Endpoints:**
  - `GET /api/alerts` (optional `?state=`, `?grid_id=`, `?limit=`)
  - `GET /api/alerts/summary`
  - `GET /api/alerts/{id}` (includes full `audit_trail`)
  - `POST /api/alerts/{id}/acknowledge` (`404` unknown ID, `409` invalid transition)
  - `POST /api/alerts/{id}/resolve` (`404` unknown ID, `409` invalid transition)
  - `POST /api/alerts/evaluate` (internal evaluation trigger)
  - Unsupported POST routes (e.g. public dispatch) return `405 Method Not Allowed`.

---

## 5. Dashboard Integration

Added **Operational Alerts (Research-Only)** tab (`#alertsTab`) in `src/floodrisk/dashboard/static/index.html` with:
- Prominent red **INTERNAL RESEARCH-ONLY CANDIDATE ALERTS — NOT A PUBLIC EMERGENCY WARNING** banner (`Public Dispatch: DISABLED`).
- Summary bar (`Active`, `Ack`, `Resolved`, `Expired`, `Latest Run`), `Re-evaluate Alerts` button, active/acknowledged table with `Ack`/`Resolve` actions, and resolved/expired history table.

---

## 6. Test Results

- **New Stage 4 Tests (`tests/test_stage4_alerts.py`):** 5 test functions using isolated synthetic fixtures in `tmp_path` covering severity & ML qualification gate, stale/missing input rejection, duplicate suppression, cooldown, escalation, ack/resolve transitions, TTL expiry, SQLite restart recovery, scheduler callback integration, and API validation (`200`, `400`, `404`, `405`, `409`).
- **Full Regression Suite (`.venv\Scripts\python.exe -m pytest tests/ -q`):** **154 passed, 0 failed** (149 baseline + 5 Stage 4 tests).

---

## 7. Operational Demonstration Results

1. **Actual Open-Meteo Provider Run (`enable_live_refresh=True`):**
   - Retrieved live `open_meteo` / `ecmwf_ifs025` forecast (`freshness: LIVE`, `next_24h_precipitation_mm: 1.8 mm`, `retrieval_time_utc: 2026-11-27T05:14:24Z`).
   - Evaluated all `1,170` Bengaluru grid cells (`RUN-335E0F50AA`, `status: COMPLETED`, `alerts_created: 0` due to dry conditions, `public_dispatch_enabled: false`).
2. **Isolated Synthetic Fixture Lifecycle + UI + Restart Persistence (`70.0 mm` / `18.0 mm` 1h peak fixture):**
   - Evaluated all `1,170` cells (`RUN-78477B042C`), creating `633` candidate alerts (e.g., `ALT-066E0E42B408` on `g1000_7472_1625`, `ADVISORY`, `PROVISIONAL_RULE_BASED`).
   - Verified in headless Edge Playwright that `#alertsTab` rendered `alertTabCount = 633` and `200` visible table rows.
   - Acknowledged and resolved `ALT-066E0E42B408` via `POST /api/alerts/{id}/acknowledge` and `POST /api/alerts/{id}/resolve`.
   - Restarted the server against the same SQLite database and verified `GET /api/alerts/ALT-066E0E42B408` returned `lifecycle_state: "RESOLVED"` with `audit_trail` `['RESOLVED', 'ACKNOWLEDGED', 'CREATED']`.

---

## 8. Known Limitations & What Remains Before Deployment

- **Provisional Thresholds:** Rainfall thresholds (`15.6`, `35.0`, `64.5`, `15.0 mm/h`) are uncalibrated for Bengaluru's 1 km urban drainage response.
- **No Live Ground Gauges:** KSNDMC/IMD live telemetry remains `UNAVAILABLE`; alerts rely solely on NWP forecasts + static terrain.
- **ML Blocked:** Stage 3 ML remains `EXPERIMENTAL_UNVALIDATED` until multi-year verified dry controls and independent flood events are collected.
- **Public Notifications Disabled:** External alerting (SMS/email/CAP) must remain disabled until independent validation and authorized agency integration.
