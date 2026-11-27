# Phase 5.2 — Track G: Dashboard Claims & UI Truthfulness Audit

## 1. Executive Summary

This report documents the UI and REST API audit conducted on the operational flood risk intelligence console ([`src/floodrisk/dashboard/server.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/dashboard/server.py) and [`static/index.html`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/dashboard/static/index.html)).

The user interface has been updated to ensure complete scientific truthfulness:
* All references to "Verified Forecast Skill" have been replaced with **`RETROSPECTIVE_RECONSTRUCTED_SERIES — NOT VERIFIED NWP SKILL`**.
* The sample size indicator clarifies that **711 represents anchor-time-lead groups, with statistically effective degrees of freedom not established**.
* Gate A is displayed as **`BLOCKED BY PROVENANCE`** for operational alerting.
* Gate B is displayed as **`BLOCKED BY DATA ACCESS`** for supervised machine learning flood prediction.
* The 4-layer distinction between static vulnerability, observed rainfall, forecast exposure, and ground evidence is strictly maintained.

---

## 2. Six-Pillar Terminology Alignment

The dashboard now strictly separates the following six distinct physical concepts:

```
┌───────────────────────────────────────┬────────────────────────────────────────────────────────┐
│ UI Concept                            │ Strict Physical Meaning & Source                      │
├───────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ 1. Static Flood Susceptibility        │ Intrinsic terrain & land cover vulnerability (SRTM     │
│                                       │ DEM slope, TWI, elevation, ESA WorldCover imperviousness│
├───────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ 2. Observed Rainfall                  │ Historical precipitation depth recorded by ground     │
│                                       │ rain gauges and calibrated IMERG satellite sensors     │
├───────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ 3. Forecast Rainfall                  │ Exploratory simulated atmospheric guidance with lead   │
│                                       │ times (6h to 72h). NOT verified operational NWP skill. │
├───────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ 4. Independent Flood Evidence         │ Qualitative and semi-quantitative records of reported  │
│                                       │ waterlogging or inundation from civic disaster logs    │
├───────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ 5. Dynamic Risk Prioritization Index  │ Multi-criteria heuristic rank combining static and     │
│                                       │ dynamic exposure. NOT a supervised ML probability.     │
├───────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ 6. Verified Flood Inundation          │ Direct ground-truth measurement of standing water depth│
│                                       │ (>0.5m) at a specific instrumented grid cell.          │
└───────────────────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 3. UI Changes & Truthfulness Updates

### A. Readiness Gate Cards
* **Gate A Card:** Color-coded amber/orange (`#ea580c`). Badge reads `BLOCKED BY PROVENANCE`. Rationale states: *"Forecast series was reconstructed from historical observed rainfall synoptic curves rather than authentic archived NWP model output (e.g., ECMWF/GFS GRIB2). Genuine NWP verification not established. Automated alerts barred."*
* **Gate B Card:** Color-coded red (`#dc2626`). Badge reads `BLOCKED BY DATA ACCESS`. Rationale states: *"Domain Censorship: 98.13% Unobserved (1,148 cells). Positive flood scarcity (13 cells). Negative locations are high-ground ridge weather stations, not verified dry valley truth. Supervised ML modeling is strictly blocked."*

### B. Track A Table Header
* Previous Header: *"Archived NWP Forecast Verification Across Lead Times (183,690 Matched Pairs)"*
* Reconciled Header: *"Retrospective Reconstructed Series vs Observations (183,690 Raw Pairs across 711 Anchor-Time Groups — NOT Verified NWP Skill)"*

### C. Watch vs Flood Distinction
The live map legend and tooltips maintain a strict boundary between meteorological hazard and ground inundation:
* A cell with forecast rainfall $\ge 64.5\text{ mm}$ triggers a **`HEAVY_RAIN_ADVISORY`**, indicating potential atmospheric forcing.
* It is **never rendered as an active flood** unless independent ground flood evidence exists for that cell.

---

## 4. API Contract Preservation

To avoid breaking regression tests or client applications, all nine REST API endpoints remain active with backward-compatible payloads:

```
Endpoint                         HTTP Status   Primary JSON Payload
-------------------------------------------------------------------------------------------------------
/api/health                      200 OK        {"status": "healthy"}
/api/summary                     200 OK        Platform domain cell counts, active event counts
/api/cells                       200 OK        GeoJSON FeatureCollection (1,170 enriched cells)
/api/incidents                   200 OK        Historical incident point inventory (21 records)
/api/episodes                    200 OK        Event monitoring state log (Phase 4 monitoring)
/api/manifest                    200 OK        Baseline dataset manifest
/api/phase5/verification-metrics 200 OK        15-row lead-time metric array
/api/phase5/flood-validation     200 OK        7-class taxonomy distribution, bootstrap CIs
/api/phase5/sar-manifest         200 OK        Authentic CDSE scene inventory (3 records)
/api/phase5/readiness-gates      200 OK        Reconciled Gate A-E status dictionary
```

