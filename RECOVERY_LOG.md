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
- **After Evidence:** `pytest tests/test_server.py` -> 8 passed; full suite passing.
