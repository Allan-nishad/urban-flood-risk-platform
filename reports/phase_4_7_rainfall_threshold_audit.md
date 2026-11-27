# Phase 4.7.3 — Scientific Audit: Rainfall Categories vs. Official Warnings & Accumulation Windows

**Platform:** Bengaluru Urban Flood Risk Intelligence Platform  
**Component:** Rainfall Classification Engine ([`src/floodrisk/ingestion/forecast.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/ingestion/forecast.py))  
**Audited Datasets:**
- [`data/processed/forecast_exposure_indicators_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/forecast_exposure_indicators_bengaluru.parquet)
- [`data/processed/dynamic_risk_intelligence_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/dynamic_risk_intelligence_bengaluru.parquet)  
**Audit Classification:** **REQUIRES_CORRECTION (Corrected & Documented with Limitations)**

---

## 1. Audit Context & Scientific Objective

In the Phase 4.2 report and dashboard, forecasted precipitation values were classified into categories labelled `HEAVY_RAIN_ADVISORY`, `MODERATE_RAIN_WATCH`, and `VERY_HEAVY_RAIN_WARNING`, with accompanying claims of "WMO and IMD alert compliance".

The scientific objective of this audit is to determine:
1. The exact meteorological origin and legal status of the numerical thresholds ($15.6\text{ mm}$, $64.5\text{ mm}$, $115.5\text{ mm}$).
2. Whether the platform has legal or scientific authority to issue "warnings" or "advisories".
3. Whether the rolling 24-hour accumulation window in the forecast pipeline matches the official standard reporting window used by the India Meteorological Department (IMD).

---

## 2. Threshold Origin & Classification Analysis

### 2.1 The India Meteorological Department (IMD) Classification
The numeric thresholds used in [`src/floodrisk/ingestion/forecast.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/ingestion/forecast.py) originate from the official India Meteorological Department (IMD) 24-hour precipitation depth classification standards:

| IMD Rainfall Classification | 24-Hour Accumulated Depth ($P_{24\text{h}}$) | Standard Color Code |
| :--- | :---: | :---: |
| **No Rain / Dry** | $0.0\text{ mm}$ | White |
| **Very Light Rain** | $0.1 - 2.4\text{ mm}$ | Light Green |
| **Light Rain** | $2.5 - 15.5\text{ mm}$ | Green |
| **Moderate Rain** | $15.6 - 64.4\text{ mm}$ | Yellow |
| **Heavy Rain** | $64.5 - 115.5\text{ mm}$ | Orange |
| **Very Heavy Rain** | $115.6 - 204.4\text{ mm}$ | Red |
| **Extremely Heavy Rain** | $\ge 204.5\text{ mm}$ | Maroon / Purple |

### 2.2 Critical Distinction: Rainfall Category vs. Official Warning
1. **Rainfall Depth Category (Physical Parameter):**  
   Measuring or forecasting that a location may receive $68.2\text{ mm}$ of rain in 24 hours places it objectively in the **Heavy Rainfall Category** ($64.5 - 115.5\text{ mm}$).
2. **Official Emergency Warning (Statutory Administrative Product):**  
   An official **Advisory**, **Watch**, or **Warning** (such as an IMD Red Alert or Karnataka State Natural Disaster Monitoring Centre - KSNDMC Flash Flood Bulletin) is an authoritative administrative document issued by statutory authorities based on synoptic expertise, vulnerability assessments, and multi-agency coordination.
3. **Scientific Invariant:**  
   An academic or automated software platform has **no authority** to declare an "IMD Warning" or "WMO Advisory". Presenting internal threshold logic as an official government alert risks severe public confusion and legal liability.

---

## 3. Accumulation Window Discrepancy

A critical temporal mismatch was identified during code audit:

$$\begin{aligned}
\text{Official IMD Observation Window:} & \quad \mathbf{08:30\text{ IST to 08:30\text{ IST}}} \text{ (03:00 UTC to 03:00 UTC next day)} \\
\text{Platform Forecast Accumulation:} & \quad \mathbf{\text{Rolling 24-Hour Horizon}} \text{ (e.g., valid at 14:00 UTC = 14:00 UTC yesterday to 14:00 UTC today)}
\end{aligned}$$

### Scientific Consequences:
- A cloudburst occurring between $20:00\text{ IST}$ and $02:00\text{ IST}$ produces a localized $80\text{ mm}$ total.
- In the platform's rolling 24-hour forecast, this is captured cleanly as an $80\text{ mm}$ 24-hour accumulation (`HEAVY_RAINFALL_CATEGORY`).
- In official IMD historical records, this same downpour is recorded entirely on a single observational day (08:30 to 08:30 IST).
- Conversely, a rain event spanning from $06:00\text{ IST}$ to $12:00\text{ IST}$ is split across **two separate IMD reporting days**, whereas the rolling window captures the unified $24\text{h}$ burst.
- **Audit Requirement:** The platform must document that its forecast accumulation interval is a rolling hydrological exposure metric, not an official daily synoptic gauge total.

---

## 4. Code & Nomenclature Corrections

The following terminology corrections have been made across [`src/floodrisk/ingestion/forecast.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/ingestion/forecast.py), [`src/floodrisk/processing/dynamic_risk.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/dynamic_risk.py), and the dashboard:

| Previous Label | Corrected Label | Status & Meaning |
| :--- | :--- | :--- |
| `HEAVY_RAIN_ADVISORY` | `HEAVY_RAINFALL_CATEGORY` | Internal threshold classification ($\ge 64.5\text{ mm / 24h}$). |
| `MODERATE_RAIN_WATCH` | `MODERATE_RAINFALL_CATEGORY` | Internal threshold classification ($15.6 - 64.4\text{ mm / 24h}$). |
| `LIGHT_RAIN` | `LIGHT_RAINFALL_CATEGORY` | Internal threshold classification ($< 15.6\text{ mm / 24h}$). |
| *Missing* | `official_warning_status` | Added column: `"INTERNAL_METEOROLOGICAL_CLASSIFICATION_NOT_OFFICIAL_GOVERNMENT_ALERT"`. |
| *Missing* | `accumulation_interval_note` | Added column: `"Rolling 24h accumulation ending at forecast valid time; differs from official IMD 08:30-08:30 IST window."` |

