# Phase 4.4 — Flood-Event Monitoring & Lifecycle Tracking Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban (1,170 Cells, 1-km Grid)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Reporting Date:** 2026-11-05  
**Deliverable Dataset:** [`data/processed/flood_event_monitoring_log.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/flood_event_monitoring_log.parquet) (6 discrete episodes logged)  

---

## 1. Executive Summary & Event Monitoring Architecture

Phase 4.4 establishes an operational event-monitoring framework to track rainfall episodes across time, manage empirical ground incident evidence, and monitor event lifecycle progressions without conflating atmospheric rainfall with verified terrestrial flooding.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        EVENT MONITORING STATE MACHINE WORKFLOW                         │
├───────────────┬────────────────────────────────────────────────────────────────────────┤
│ State         │ Trigger Criteria & Operational Meaning                                 │
├───────────────┼────────────────────────────────────────────────────────────────────────┤
│ WATCH         │ Significant rainfall forecast detected in NWP stream (e.g. > 35 mm/24h)│
│ ACTIVE_EVENT  │ Heavy observed precipitation detected in progress across domain cells  │
│ FLOOD_REPORTED│ Independent citizen or municipal inundation report received in zone    │
│ UNDER_REVIEW  │ Scientific review of incident coordinates, photographs, and satellite   │
│ CLOSED        │ Event terminated; rainfall receded; final retrospective audit logged   │
└───────────────┴────────────────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Operational Boundary Clarification:**
> The lifecycle states (`WATCH`, `ACTIVE_RAINFALL_EVENT`, etc.) are **internal decision-support workflow classifications** of the research platform.
> They are **NOT official meteorological or disaster management warnings**. Official warnings in Karnataka are issued exclusively by the India Meteorological Department (IMD) and the Karnataka State Natural Disaster Monitoring Centre (KSNDMC).

---

## 2. Catalog of Monsoonal & Forecast Monitoring Episodes

The monitoring engine identifies and tracks six discrete episodes:

| Episode Identifier | Episode Name | Temporal Window | Peak Date | Domain Peak Rainfall | Total Volume | Incidents | Lifecycle State | Operational Classification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`EP-2022-08-W1`** | Late August Soil Priming | 2022-08-25 to 2022-08-29 | 2022-08-29 | $22.32\text{ mm}$ | $81.62\text{ mm}$ | 0 | `CLOSED` | Soil Moisture Priming |
| **`EP-2022-08-STORM1`** | August 30 First Storm Peak | 2022-08-30 to 2022-08-30 | 2022-08-30 | $75.25\text{ mm}$ | $75.25\text{ mm}$ | 5 | `CLOSED` | Flash Ponding & Arterial Disruption |
| **`EP-2022-09-INTER`** | Inter-Storm Saturation Maintenance | 2022-08-31 to 2022-09-03 | 2022-08-31 | $23.92\text{ mm}$ | $70.47\text{ mm}$ | 0 | `CLOSED` | Drainage Bottleneck Maintenance |
| **`EP-2022-09-DELUGE`** | September 4–5 Catastrophic Deluge | 2022-09-04 to 2022-09-05 | 2022-09-05 | $131.16\text{ mm}$ | $199.33\text{ mm}$ | 13 | `CLOSED` | Catastrophic Urban Inundation |
| **`EP-2022-09-RECEDE`** | Post-Disaster Recession Phase | 2022-09-06 to 2022-09-10 | 2022-09-06 | $21.93\text{ mm}$ | $52.52\text{ mm}$ | 0 | `CLOSED` | Post-Disaster Dewatering & Drainage |
| **`EP-LIVE-FCST`** | Current 72-Hour NWP Forecast Window| Active Forecast Window | Current +1d | $24.50\text{ mm}$ | $46.80\text{ mm}$ | 0 | `WATCH` | Live Forward-Looking Watch |

---

## 3. Evidence Audit Trail & Management

For each registered flood incident, the monitoring engine maintains immutable audit metadata:
1. **Source Provenance:** Linking to verified publisher records in [`flood_source_registry_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/flood_source_registry_bengaluru.parquet).
2. **Spatial Uncertainty Radius:** Explicitly encoding geocoding uncertainty circles ($\pm 250\text{ m}$ for underpasses, $\pm 500\text{ m}$ for residential layouts, $\pm 1,500\text{ m}$ for arterial transit corridors).
3. **Review & Corroboration Status:** Flagging duplicate social media complaints to prevent artificial amplification of single localized puddle events.

