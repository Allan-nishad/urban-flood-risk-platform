# V8 STAGE 4.1: ALERT ENGINE SCIENTIFIC AND SPATIAL AUDIT

**Branch:** `upgrade/v8-operational-ai`  
**Audited Baseline:** `46f0be6` (Stage 4)  
**Qualification Status:** `PROVISIONAL_RULE_BASED` (software milestone) / `EXPERIMENTAL_UNVALIDATED` (ML gate)  
**Public Dispatch:** `DISABLED` (`public_dispatch_enabled = False`)

---

## 1. Spatial Forecast Coverage Audit

- **Single-Anchor Forcing Verified:** `OpenMeteoForecastAdapter` (`src/floodrisk/live/open_meteo.py`) queries one coordinate pair (`latitude=12.9716, longitude=77.5946`, `location_ref="bengaluru_centroid"`).
- **How Cell Evaluation Works:** `DashboardDataStore.evaluate_alerts()` passes that single forecast payload identically to all `1,170` grid cells. Cells do **not** receive 1,170 independent NWP forecasts.
- **Terrain Differentiation:** Cell-level `static_susceptibility_score` (from SRTM 30m elevation/roughness + ESA WorldCover) genuinely differentiates which cells trigger and at what severity.
- **Observed Rainfall:** Local live gauges (`KSNDMC / IMD`) remain `UNAVAILABLE`; `observed_rainfall_status` is explicitly `"UNAVAILABLE"`, and forecasts are never substituted as local observations.

---

## 2. Explanation of the 633-Alert Fixture Result

Reproducing the `70.0 mm` 24h / `18.0 mm/h` peak fixture across all `1,170` Bengaluru cells in an isolated SQLite DB:

| Static Susceptibility Band | Cell Count | Rule Triggered | Severity |
|---|---:|---|---|
| `static_susceptibility_score >= 0.60` | `270` | `RULE_PROVISIONAL_HEAVY_RAIN_HIGH_SUSCEPTIBILITY` | `HIGH` (`270`) |
| `0.45 <= static_susceptibility_score < 0.60` | `363` | `RULE_PROVISIONAL_ADVISORY_RAIN_MODERATE_SUSCEPTIBILITY` | `ADVISORY` (`363`) |
| `static_susceptibility_score < 0.45` | `537` | None (below provisional thresholds) | `0` alerts |
| **Total** | **1,170** | **2 provisional rules** | **633 alerts** |

**Conclusion:** The `633` alerts are mathematically expected under the current provisional rules because identical `70.0 mm` single-anchor rainfall forcing is applied city-wide, causing every cell with `static_susceptibility_score >= 0.45` (`270 + 363 = 633`) to trigger simultaneously while `537` low-susceptibility cells stay silent. No artificial cap was added; instead, the API, alert payloads, and UI now explicitly label this as **`REGIONAL_SINGLE_ANCHOR_BENGALURU`**.

---

## 3. Threshold Provenance Table

| Parameter (`AlertRuleConfig`) | Value | Variable & Unit | Accumulation / Interval | Provenance & Classification | Suitable for Operational Bengaluru Warnings? |
|---|---:|---|---|---|---|
| `forecast_watch_24h_mm` | `15.6` | Forecast precipitation (`mm`) | Next 24h | **Project-derived provisional baseline** (used in Stage 3 `train.py` as simple ERA5 24h threshold baseline). | **No — provisional & configurable; requires local IDF calibration.** |
| `forecast_advisory_24h_mm` | `35.0` | Forecast precipitation (`mm`) | Next 24h | **Experimental/provisional configuration** (no external Bengaluru validation). | **No — provisional & configurable; requires local calibration.** |
| `forecast_peak_hourly_mm` | `15.0` | Forecast peak hourly rain (`mm/h`) | 1 hour | **Experimental/provisional configuration** (no external Bengaluru drainage calibration). | **No — provisional & configurable; requires local calibration.** |
| `forecast_high_24h_mm` | `64.5` | Forecast precipitation (`mm`) | Next 24h | **External synoptic reference** (IMD 24h "Heavy Rainfall" >= 64.5 mm), applied **provisionally** to 1 km urban grid. | **No — synoptic reference only; urban flash flooding depends on sub-hourly intensity & drainage.** |
| `static_moderate_susceptibility` | `0.45` | `static_susceptibility_score` (`[0,1]`) | Static terrain | **Project-derived provisional cutoff** on Phase 4 MCDA terrain/landcover score. | **Provisional screening only; uncalibrated against multi-year flood frequency.** |
| `static_high_susceptibility` | `0.60` | `static_susceptibility_score` (`[0,1]`) | Static terrain | **Project-derived provisional cutoff** on Phase 4 MCDA terrain/landcover score. | **Provisional screening only; uncalibrated against multi-year flood frequency.** |

---

## 4. Code Hardening & Lifecycle Audit Fixes

1. **De-escalation Fix (`src/floodrisk/alerts/engine.py`):** Changed severity comparison from `new_rank > old_rank` to `new_rank != old_rank` so both escalation (`WATCH -> HIGH`) and de-escalation (`HIGH -> WATCH`) update active alerts cleanly even within the same forecast issue timestamp.
2. **Explicit Spatial Scope Metadata (`rules.py`, `engine.py`, `server.py`, `index.html`):** Added `spatial_forcing_scope: "REGIONAL_SINGLE_ANCHOR_BENGALURU"` and `spatial_coverage_note` to alert `triggering_inputs`, `/api/alerts`, `/api/alerts/summary`, `/api/weather/forecast`, and the `#alertsTab` banner.
3. **Outage Safety:** Verified that `STALE` and `UNAVAILABLE` forecasts return `SKIPPED_STALE_OR_UNAVAILABLE` and never auto-resolve active alerts or fabricate safety.

---

## 5. Audit & Regression Test Results

- **New Audit Tests (`tests/test_stage4_1_audit.py`):** Verified 633-alert breakdown (`270 HIGH + 363 ADVISORY`, `537` silent), `REGIONAL_SINGLE_ANCHOR_BENGALURU` metadata, repeated identical refresh suppression, escalation + de-escalation, `STALE`/`UNAVAILABLE` outage preservation, restart during `ACTIVE` alert, and auto-resolution when fresh dry forecast returns.
- **Full Suite (`.venv\Scripts\python.exe -m pytest tests/ -q`):** Executed post-edit (see Stage 4.1 completion summary).

---

## 6. Remaining Operational Restrictions

- Single-anchor NWP forcing cannot resolve localized convective cells across Bengaluru without gridded NWP or multi-station live gauge telemetry.
- All thresholds remain provisional; Stage 3 ML remains `EXPERIMENTAL_UNVALIDATED`; public emergency dispatch remains `DISABLED`.
