# v7.3 RELIABILITY RECOVERY REPORT: `urban-flood-risk-platform`

**Branch:** `recovery/v7.3` (branched from reconstructed baseline tag `v7.2.0-FREEZE` at `1e63101`)  
**Baseline Backup:** `C:\Users\allan\AppData\Local\Temp\backup_v7_2_0_freeze` (801 files)  
**Date:** 2026-11-27  

---

## 1. Defects Identified, Root Causes & Repairs Completed

| Defect ID | Severity | Root Cause | Files Changed | Fix Summary |
|---|---|---|---|---|
| **`DATA-STATE`** | P1 (Major) | No shared state vocabulary; `server.py` coerced missing `research_monitoring_level` to `"NORMAL"`; Phase 4.3 constant `12.5` mm observed rainfall lacked `STALE` provenance; Phase 7 73-entry manifest & Phase 6 24-record inventory unexposed; `cli.py:process-rainfall` crashed (`exit 1`) without `UNAVAILABLE` message on missing dir; `configs/datasets.yaml` lacked missing-path status. | `src/floodrisk/state_contract.py` (new), `src/floodrisk/dashboard/server.py`, `src/floodrisk/cli.py`, `configs/datasets.yaml`, `tests/test_server.py` | Added `DATA_STATES` contract (`AVAILABLE`, `PARTIAL`, `UNAVAILABLE`, `UNOBSERVED`, `UNVALIDATED`, `STALE`), tagged `observed_rainfall_state="STALE"`, exposed `/api/phase7/manifest` (73 entries) and 24-row Phase 6 records in `/api/phase6/flood-evidence` (keeping `/api/incidents` 21-row legacy intact). |
| **`API-01`** | P2 (Moderate) | `do_GET` stripped query strings and returned all 1,170 cells on `grid_id=INVALID_999` (`200`); unknown params ignored (`200`); `POST` returned HTML `501`; `404` lacked `code`/`detail`. | `src/floodrisk/dashboard/server.py`, `tests/test_server.py` | Added unified `{error, code, detail}` JSON error schema, `404` on unknown `grid_id`, `400` on unknown query params, `405` JSON on unsupported HTTP methods, and filtered `FeatureCollection` on valid `grid_id`. |
| **`UI-01`** | P1 (Major) | `index.html` contained 5 duplicate `<div id="phase6Tab">` blocks (one nested inside `inspectorTab`), hardcoded fake KPIs (`266 Cells`, `68.20 mm`), hardcoded `phase6GroundTruthTbody` ignoring API, 6 unfetched Phase 6/7 routes, `"NORMAL"`/`0.0` fallbacks, and swallowed `fetch` errors. | `src/floodrisk/dashboard/static/index.html`, `tests/test_server.py` | Removed 4 duplicate blocks (`2284` → `1699` lines), wired dynamic KPIs + all Phase 6/7 endpoints, replaced hardcoded table with 24-row API rendering, added `#apiErrorBanner`, replaced null fallbacks with `UNAVAILABLE`/`UNOBSERVED`/`STALE`, and styled `"incidents"` layer. |
| **`SAR-METRIC`** | P1 (Major) | Dashboard Stage 6D card and `server.py:351` prominently displayed `76.9% Sensitivity` (`10/13`), which Phase 7 (`phase7_sar_evidence_comparison.parquet`) showed included `4/13` pre-existing permanent-lake conflations and `1/13` double-bounce. | `src/floodrisk/dashboard/server.py`, `src/floodrisk/dashboard/static/index.html`, `tests/test_server.py`, `tests/test_data_integrity.py` (new) | Replaced `76.9% Sensitivity` KPI with audited `5/13 True Specular (38.5%)` and `EXPLORATORY_UNVALIDATED` breakdown (`4` lake-conflated, `3` urban-canyon missed, `6/7` dry specificity). |

---

## 2. API Route Inventory & Verification

All **20** registered `/api/*` routes in `src/floodrisk/dashboard/server.py` were enumerated dynamically and verified against a live `ThreadedHTTPServer` (`test_all_registered_routes_inventory_and_valid_json`):
- **Core:** `/api/summary`, `/api/cells` (supports `?grid_id=<id>`, `404` on invalid ID), `/api/incidents` (21 legacy records), `/api/episodes` (6 records), `/api/manifest` (33 legacy entries), `/api/health`
- **Phase 5:** `/api/phase5/verification-metrics`, `/api/phase5/flood-validation`, `/api/phase5/sar-manifest`, `/api/phase5/readiness-gates`
- **Phase 6:** `/api/phase6/summary`, `/api/phase6/nwp`, `/api/phase6/ground-rainfall`, `/api/phase6/flood-evidence` (24 Phase 6 records + 13+/7-/1,150U), `/api/phase6/sar`, `/api/phase6/hydrology`, `/api/phase6/manifest` (16 entries)
- **Phase 7:** `/api/phase7/summary`, `/api/phase7/uncertainty`, `/api/phase7/manifest` (73 entries, newly added)
- **Error Handling:** `400 INVALID_PARAMETER`, `404 CELL_NOT_FOUND` / `ENDPOINT_NOT_FOUND`, `405 METHOD_NOT_ALLOWED` (all verified JSON `{error, code, detail}`).

---

## 3. Dataset Integrity & Baseline Diff Proof

- **Grid & Joins (`tests/test_data_integrity.py`):** `1,170` cells, unique `g1000_{col}_{row}` IDs, `EPSG:6933`, exact 1:1 `grid_id` match across all static/risk/hydrology/ground-truth parquets.
- **Null & Censorship Preservation:** `1,150` (`98.29%`) `UNOBSERVED_DOMAIN_CELL` cells retain `binary_flood_target = -1` and `NaN` `water_depth_est_m` (never converted to `0` or dry).
- **Manifests & Incidents Separation:** `33`-entry legacy, `16`-entry Phase 6, and `73`-entry Phase 7.2 manifests verified separate with all 73 frozen file paths and byte sizes matching on disk; `21`-record legacy and `24`-record Phase 6 incident inventories remain cleanly separated.
- **Formula/Weight/Threshold Diff Proof vs `v7.2.0-FREEZE`:**
  - Command: `git diff v7.2.0-FREEZE --stat -- src/floodrisk/processing/ src/floodrisk/validation/ src/floodrisk/spatial/`
  - Result: **Empty diff (`0` files changed)** — zero unauthorized modifications to scientific formulas, weights, thresholds, or source datasets.

---

## 4. Test & Browser Verification Results

- **Before Recovery (`v7.2.0-FREEZE` baseline):** `109 passed, 0 failed` (0 API, 0 data-integrity, 0 browser tests).
- **After Recovery (`recovery/v7.3`):** **`129 passed, 0 failed, 0 skipped`** (`109` baseline + `7` in `tests/test_data_integrity.py` + `13` in `tests/test_server.py`).
- **Playwright Interactive Browser Test (`test_playwright_interactive_dashboard`, Microsoft Edge headless):**
  - Verified initial load (`1,170 km²`, `0 Cells` heavy rain, `6.10 mm` max 24h, `STALE` observed badge, `5/13 True Specular (38.5%)` SAR).
  - Switched all 3 top-right tabs and all 5 bottom analytics tabs; verified 24 rows in `#phase6GroundTruthTbody` and 73 rows in `#phase7ManifestTbody`.
  - Clicked a live Leaflet grid cell polygon and verified `#inspCellId` update.
  - Tested mobile viewport (`375×812`) with `0` JS `pageerror`s and `0` failed `/api/*` requests.
  - Simulated `/api/cells` network abort and verified `#apiErrorBanner` became visible.

---

## 5. Remaining Defects & Known Scientific Limitations

1. **LOW — Stale Uniform Observed Rainfall (`12.5` mm):** `/api/cells` still serves the Phase 4.3 `dynamic_risk_intelligence_bengaluru.parquet` snapshot (`max dynamic score = 0.3500`, `observed_rainfall_24h_mm = 12.5` constant). Now explicitly badged `STALE` in both API and UI.
2. **SCIENTIFIC LIMITATION — Coarse GFS Heavy-Rain Skill (`POD = 0.0`):** NOAA GFS 0.25° (`27.75` km) missed `23/23` heavy-rain events ($\ge 64.5\text{ mm}$) across `256` station-day pairs (`MAE = 18.64 mm`, `r = 0.1421`).
3. **SCIENTIFIC LIMITATION — Uncalibrated Index & ML Gate:** `98.29%` of the domain (`1,150/1,170` cells) is unobserved; supervised ML remains `BLOCKED_BY_INSUFFICIENT_EVIDENCE`; scores are uncalibrated prioritisation rankings, not flood probabilities.
4. **LOW — External Map Tiles CDN:** Leaflet CSS/JS and OpenStreetMap tiles require internet access; offline environments will not render the basemap tiles.

---

## 6. Exact Launch Instructions & Readiness Status

```powershell
.venv\Scripts\python.exe -m floodrisk.cli dashboard --port 8000
# Open http://127.0.0.1:8000/
```

**Final Readiness Status:** **`READY_FOR_RESEARCH_DEMO_WITH_DOCUMENTED_LIMITATIONS`**  
*(Not ready for operational emergency deployment due to `STALE` Phase 4.3 map rainfall, `POD = 0.0` GFS heavy-rain skill, and `98.29%` domain observational censorship.)*
