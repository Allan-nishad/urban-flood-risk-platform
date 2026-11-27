# v7.3 Reliability Recovery Log

**Baseline Note:** `v7.2.0-FREEZE` (`1e63101` on `main`) is a reconstructed Git baseline of the pre-repair project (originally uncommitted/untagged), including `FULL_SYSTEM_AUDIT_REPORT.md` and excluding `.venv`, caches, and `scratch/`. Full pre-repair backup saved to `C:\Users\allan\AppData\Local\Temp\backup_v7_2_0_freeze`.

---

## Defect 1: `DATA-STATE` (Tier 1 — Data-State Contract, Stale Rainfall, Manifests, Incidents, Dead Paths)
- **Root Cause:** No shared data-state vocabulary; `server.py` coerced missing `research_monitoring_level` to `"NORMAL"`; `dynamic_risk_intelligence_bengaluru.parquet` (Phase 4.3 constant `12.5` mm observed rainfall) lacked `STALE` provenance; Phase 7 73-entry manifest and Phase 6 24-record incident inventory were unexposed; `cli.py:process-rainfall` exited with code 1 without `UNAVAILABLE` state message on missing directory; `configs/datasets.yaml` lacked `UNAVAILABLE` status for missing curated/quarantine CSVs.
- **Files Changed:** `src/floodrisk/state_contract.py` (new), `src/floodrisk/dashboard/server.py`, `src/floodrisk/cli.py`, `configs/datasets.yaml`, `tests/test_server.py` (new).
- **Before Evidence:** `pytest tests/test_server.py` -> 3 failed (`ModuleNotFoundError`, `AttributeError`, `exit_code == 1`).
- **After Evidence:** `pytest tests/test_server.py` -> 3 passed; full suite passing (`112 passed`).

## Defect 2: `API-01` (Tier 2 — API Error Schemas, Query Param Validation, Method Handling)
- **Root Cause:** `DashboardRequestHandler.do_GET` stripped query strings (`self.path.split("?")[0]`) and ignored invalid `grid_id` or unknown params, returning `200` with all 1,170 cells; unsupported HTTP methods (`POST`, etc.) fell back to `BaseHTTPRequestHandler` HTML `501`; `404` error JSON lacked `code` and `detail` fields.
- **Files Changed:** `src/floodrisk/dashboard/server.py`, `tests/test_server.py`.
- **Before Evidence:** `pytest tests/test_server.py` -> 4 failed (`200 == 404`, `200 == 400`, `501 == 405`, missing `code`/`detail`).
- **After Evidence:** `pytest tests/test_server.py` -> 8 passed; full suite passing (`117 passed`).

## Defect 3: `UI-01` (Tier 3 — Dashboard Integration, Hardcoded Tables, Duplicate DOM IDs, Null Fallbacks)
- **Root Cause:** `index.html` contained 5 duplicate `<div id="phase6Tab">` blocks (one nested inside `inspectorTab`), hardcoded fake KPI values (`266 Cells`, `68.20 mm`), hardcoded `phase6GroundTruthTbody` ignoring `/api/phase6/flood-evidence`, 6 unfetched Phase 6/7 endpoints, `"NORMAL"`/`0.0` fallbacks, and swallowed `fetch` errors.
- **Files Changed:** `src/floodrisk/dashboard/static/index.html`, `tests/test_server.py`.
- **Before Evidence:** `pytest tests/test_server.py::test_frontend_html_integration_and_no_duplicates` -> FAILED (`assert 5 == 1`).
- **After Evidence:** `pytest tests/test_server.py` -> 9 passed; headless Edge DOM verification confirmed 24 Phase 6 incident rows, 73 Phase 7 manifest rows, `STALE` badge, and real KPI values (`0 Cells` heavy rain, `6.10 mm` max 24h); screenshot saved to `C:\Users\allan\AppData\Local\Temp\audit_20261127_092600\dashboard_headless.png`.

## Defect 4: `SAR-METRIC-AND-TIER4` (Tier 4 — SAR 76.9% Overclaim Repair, Data Integrity & Playwright Tests)
- **Root Cause:** `server.py:351` and `index.html` Stage 6D card prominently displayed `76.9% Sensitivity` (`10/13`), which Phase 7 (`phase7_sar_evidence_comparison.parquet`) revealed included `4/13` pre-existing permanent-lake conflations and `1/13` unvalidated double-bounce; true specular flood expansion detection is `5/13 (38.5%)`. Additionally, `tests/` lacked `test_data_integrity.py` and interactive browser tests.
- **Files Changed:** `src/floodrisk/dashboard/server.py`, `src/floodrisk/dashboard/static/index.html`, `tests/test_data_integrity.py` (new), `tests/test_server.py`.
- **Before Evidence:** `p6SarVal` displayed `76.9% Sensitivity`; 0 data integrity or Playwright tests.
- **After Evidence:** `p6SarVal` displays `5/13 True Specular (38.5%)` with `EXPLORATORY_UNVALIDATED` status and lake-conflation breakdown; `pytest tests/test_data_integrity.py tests/test_server.py -v` -> `20 passed in 15.34s` (including Playwright Edge desktop/mobile interactive test).
