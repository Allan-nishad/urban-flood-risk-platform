# Phase 4.7.5 — Scientific Audit: Flood Event Lifecycles & Historical Archive Separation

**Platform:** Bengaluru Urban Flood Risk Intelligence Platform  
**Component:** Flood-Event Monitoring Engine ([`src/floodrisk/processing/monitoring.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/monitoring.py))  
**Audited Dataset:** [`data/processed/flood_event_monitoring_log.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/flood_event_monitoring_log.parquet)  
**Audit Classification:** **REQUIRES_CORRECTION (Corrected & Documented with Limitations)**

---

## 1. Audit Context & Scientific Objective

In Phase 4.4, the platform established a flood-event monitoring engine tracking six discrete episodes across an event lifecycle state machine.

The scientific objective of this audit is to determine:
1. Whether historical retrospective episodes are cleanly segregated from the active forecast monitoring episode.
2. Whether a forward-looking Numerical Weather Prediction (NWP) `WATCH` state risks being misinterpreted as an ongoing, active flood disaster.
3. Whether crowd/media incident reports are distinguished from independently verified hydrological ground truth.

---

## 2. Event Log Analysis & Episode Separation

Inspection of [`src/floodrisk/processing/monitoring.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/monitoring.py) and [`data/processed/flood_event_monitoring_log.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/flood_event_monitoring_log.parquet) confirms the presence of six discrete episodes:

| Episode ID | Episode Designation | Time Window | Peak 24h Rain | Linked Incidents | Lifecycle State | Historical Archive? |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `EP-2022-08-W1` | Pre-Monsoon Soil Priming | 2022-08-25 - 2022-08-29 | $22.3\text{ mm}$ | 0 | `CLOSED` | **YES** |
| `EP-2022-08-STORM1` | Intense Convective Storm | 2022-08-30 | $75.3\text{ mm}$ | 5 | `CLOSED` | **YES** |
| `EP-2022-09-INTER` | Inter-Storm Saturation Maintenance | 2022-08-31 - 2022-09-03 | $23.9\text{ mm}$ | 0 | `CLOSED` | **YES** |
| `EP-2022-09-DELUGE` | Catastrophic Monsoonal Deluge | 2022-09-04 - 2022-09-05 | $131.2\text{ mm}$ | 13 | `CLOSED` | **YES** |
| `EP-2022-09-RECEDE` | Post-Event Drainage Phase | 2022-09-06 - 2022-09-10 | $21.9\text{ mm}$ | 0 | `CLOSED` | **YES** |
| `EP-LIVE-FCST` | 72h Continuous NWP Surveillance | *Active Forecast Horizon* | $24.5\text{ mm}$ | 0 | `WATCH` | **NO (Forecast)** |

### Critical Findings:
1. **The Danger of Conflating Forecast with Active Inundation:**  
   In operational disaster response, an episode labelled `WATCH` driven by NWP forecast rainfall must **never** be visualized or communicated as a confirmed flood event. Heavy rainfall exposure is a meteorological hazard; flood inundation requires hydraulic runoff, micro-drainage congestion, and surface pooling.
2. **Missing Distinction in Initial Implementation:**  
   The initial Phase 4.4 monitoring log presented all six episodes in a single uniform table without an explicit schema flag separating closed historical archives from forward-looking forecast surveillance.
3. **Evidence Verification Granularity:**  
   The 18 incidents linked to `EP-2022-08-STORM1` and `EP-2022-09-DELUGE` represent citizen and media reports compiled by BBMP and KSNDMC. While 10 are corroborated by multiple photographs and press videos (`Confirmed Inundation`), 7 represent `Reported Waterlogging` and 4 represent general `Flood Disruption`. They do not possess calibrated gauge water-depth recordings.

---

## 3. Targeted Lifecycle Corrections

The monitoring engine ([`src/floodrisk/processing/monitoring.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/monitoring.py)) has been updated with the following structural partitions:

1. **Explicit Archive Partitioning (`is_historical_archive`):**
   - Episodes 1 through 5 are explicitly flagged as `is_historical_archive: True` and frozen in the `CLOSED` state.
   - Episode 6 (`EP-LIVE-FCST`) is flagged as `is_historical_archive: False` with `evidence_verification_type: "FORWARD_NWP_METEOROLOGICAL_WATCH"`.
2. **Hazard Classification Disclaimers:**
   - The hazard classification for `EP-LIVE-FCST` has been renamed to:  
     `"METEOROLOGICAL_WATCH_ONLY_NOT_ACTIVE_FLOOD"`.
   - The operational note explicitly records:  
     *"Open-Meteo ECMWF/GFS forecast surveillance. Meteorological WATCH state only; NOT a confirmed active flood or ground inundation event."*
3. **Web Dashboard Partitioning:**
   - The dashboard tab separates the **Historical Event Archive (2022 Monsoonal Disaster)** from the **Active Forward Forecast Horizon (2026 Surveillance)**.

