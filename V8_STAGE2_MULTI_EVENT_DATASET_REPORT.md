# V8 STAGE 2: MULTI-EVENT FLOOD DATASET & SAR REFINEMENT REPORT

**Branch:** `upgrade/v8-operational-ai` (starting from `4541068`)  
**Date:** 2026-11-27  

---

## 1. Events Discovered & Audited (2020–2025)

Existing inventories (`21` Phase 2/4 rows + `24` Phase 6 rows) were audited and consolidated into independent episodes by `(episode_window, grid_id)` (`5` overlapping `grid_id`s merged), then expanded across **2020–2025** using verifiable municipal/IMD/news archives:

| Event ID | Start (UTC) | Status | Confidence | Linked Cells | Evidence Source |
|---|---|---|---|---|---|
| `EP_2020_10_23` | `2020-10-23T11:00:00Z` | `CORROBORATED` | HIGH | `1` (`g1000_7481_1635`) | The News Minute / The Hindu / FloodList / Citizen Matters |
| `EP_2022_05_18` | `2022-05-17T18:00:00Z` | `CORROBORATED` | HIGH | `1` (`g1000_7493_1647`) | The New Indian Express (IMD 114.6 mm, Horamavu 155 mm) |
| `EP_2022_08_30` | `2022-08-30T12:00:00Z` | `CONFIRMED` | HIGH | `6` cells | Consolidated P2/4 + P6 field & media records |
| `EP_2022_09_05` | `2022-09-04T18:00:00Z` | `CONFIRMED` | HIGH | `23` cells (+ `7` dry proxies) | Consolidated P2/4 + P6 + BBMP + Sentinel-1A |
| `EP_2023_05_21` | `2023-05-21T09:00:00Z` | `CONFIRMED` | HIGH | `1` (`g1000_7486_1641`) | The Hindu / BBMP-IISc Hotspot Audit (KR Circle) |
| `EP_2024_10_15` | `2024-10-15T00:00:00Z` | `CORROBORATED` | HIGH | `1` (`g1000_7486_1657`) | The Hindu / New Indian Express / ATREE (Yelahanka 157 mm/6h) |
| `EP_2025_05_18` | `2025-05-18T12:00:00Z` | `CORROBORATED` | HIGH | `1` (`g1000_7489_1636`) | New Indian Express / Watchers.news (IMD 105.5 mm 24h) |
| `EP_2025_10_09` | `2025-10-09T00:00:00Z` | `REPORTED` | LOW | `0` (unmapped locality) | The Hindu (broad locality report; kept unmapped) |

---

## 2. Historical Weather Reconstruction (`ERA5-Land`)

* **Adapter:** `OpenMeteoArchiveAdapter` (`HISTORICAL_REANALYSIS`, `era5_land`) — strictly separated from live observations and flood ground truth.
* **Records Retrieved:** **`3,408` hourly rows** across `[event_start - 14d, event_end + 1d]` for all 8 episodes (`0` future leakage: `valid_time_utc < event_start_utc`).
* **Limitation Observed:** Coarse ~11 km ERA5-Land captures synoptic events (`116.1 mm` during `EP_2024_10_15`), but underestimates localized convective cloudbursts (`4.2 mm` during `EP_2023_05_21`).

---

## 3. Sentinel-1 Multi-Scene Catalog & Classification Refinement

* **CDSE Query Results:** **`9` Sentinel-1 IW GRD scenes** catalogued across the 8 episode windows (`±7d`, metadata only — no blind multi-GB downloads).
* **Refined Classification (`classify_sar_cell_state`):** Distinguishes `PERMANENT_WATER`, `TEMPORARY_INUNDATION`, `URBAN_DOUBLE_BOUNCE_ARTIFACT`, `SHADOW_OR_CANOPY`, `UNCERTAIN`, and `NO_VALID_OBSERVATION`.
* **SAR Missing Rate:** `99.79%` across `9,360` event-grid rows because only `EP_2022_09_05` has processed pixel-level $\Delta\gamma^0_{\text{VV}}$ in the repo (`20` cells).

---

## 4. 15-Point Evidence-Quality & Independence Audit (`data/phase8/evidence_quality_audit.json`)

1. Independent events identified: **`8`** (`2020`, `2022`, `2023`, `2024`, `2025`)
2. Confirmed events: **`3`**
3. Corroborated events: **`4`**
4. Reported (unverified/unmapped) events: **`1`**
5. Distinct affected positive grid cells: **`29`**
6. Confirmed/corroborated flood-positive grid/event records: **`34`**
7. Verified negative records: **`0`**
8. Proxy-negative records: **`14`** (from the 7 monitored control sites in `2022-08-30` & `2022-09-05`)
9. Unknown/unobserved records: **`9,312`** (strictly preserved as `NaN` `flood_label`)
10. Temporal coverage: **`2020, 2022, 2023, 2024, 2025`**
11. Spatial domain per event: **`1,170`** `EPSG:6933` cells
12. Satellite scenes catalogued: **`9`**
13. Historical rainfall episodes covered: **`8 / 8`**
14. SAR missing-data rate: **`99.79%`**
15. Overlapping P2/4–P6 grid IDs deduplicated: **`5`**

---

## 5. ML Validation Readiness Assessment & Remaining Blockers

* **Positive Events:** `7` episodes (`34` cell-event positives).
* **Negative Control Events:** Only **`2`** episodes (`2022-08-30` and `2022-09-05`, `14` proxy-negative records) have non-flood control labels; `2020`, `2023`, `2024`, and `2025` have **zero** non-flood controls.
* **`loeo_feasible`: `False`** (threshold: $\ge 5$ positive episodes AND $\ge 3$ negative-control episodes).
* **Scientific Conclusion:** While positive flood coverage expanded from `1` to `7` episodes, supervised LOEO training across 2020–2025 requires **monitored non-flood control records for the 2020, 2023, 2024, and 2025 episodes** (or an explicit Stage 3 decision on pairing non-flood dates at the 7 verified control stations with strict `PROXY_NEGATIVE` disclosure).

---

## 6. Files Created, Storage & Test Results

* **Code (`src/floodrisk/phase8/`):** `__init__.py`, `event_catalog.py`, `historical_weather.py`, `sar_refinement.py`, `dataset_builder.py`
* **Datasets (`data/phase8/`):** `flood_event_catalog.csv`, `flood_event_catalog.parquet`, `flood_event_grid_dataset.parquet`, `historical_weather_era5_land.parquet`, `historical_episode_rainfall_features.parquet`, `sentinel1_multi_scene_catalog.parquet`, `source_evidence_registry.json`, `evidence_quality_audit.json`
* **Tests (`tests/test_stage2_dataset.py`):** `4 passed` (zero-leakage ERA5 alignment, catalog dedup, SAR class distinctions, unobserved preservation).
* **Full Test Suite:** Executed via `pytest tests/ -q` (`145` total tests).
