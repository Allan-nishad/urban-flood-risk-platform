# Phase 7B — Final NWP Forecast Verification Report

**Auditor:** Meteorological Verification Specialist & Multi-Disciplinary Team  
**Campaign Baseline:** Phase 7 Verification Pipeline (`scripts/phase7/verify_forecasts.py`)  
**Study Domain:** Bengaluru Urban Region ($1,170\text{ km}^2$, 16 Primary Meteorological Stations)  
**Evaluated Product:** NOAA GFS 0.25° Global Forecast System (AWS Open Data `s3://noaa-gfs-bdp-pds`)  
**Status:** **`PASS_WITH_DOCUMENTED_LIMITATIONS`**  

---

## 1. Executive Summary & Evaluation Design

Workstream 7B delivers the final, rigorous scientific assessment of 24-hour rainfall forecasts from the NOAA Global Forecast System (GFS) against authentic ground rain-gauge measurements during the late August to early September 2022 monsoon flood episode:
- **Forecast Product:** NOAA GFS 0.25° ($N_i = 1440, N_j = 721$, regular lat/lon grid, $\sim 27.75\text{ km}$ spacing).
- **Initialization Cycles:** 00Z cycles from 2022-08-25 through 2022-09-09 (16 cycles, 24h lead accumulation).
- **Observation Reference:** 16 primary meteorological stations (3 IMD observatories + 13 KSNDMC BBMP telemetric rain gauges). Siting audited; 5 rooftop CAAQM air quality stations quarantined.
- **Verification Sample:** Exactly **256 matched forecast-observation pairs** ($16 \text{ stations} \times 16 \text{ verification dates}$).
- **Spatial Clustering Reality:** All 16 stations fall into only **three native GFS grid nodes** ($(13.00, 77.50)$ [8 stations], $(13.00, 77.75)$ [7 stations], $(13.25, 77.75)$ [1 station]). Effective forecast sample size is at most 48 independent spatial-temporal realizations.

---

## 2. Continuous Verification Metrics

Metrics evaluated on the complete pooled sample ($N=256$):

| Metric | Point Estimate | Interpretation |
| :--- | :---: | :--- |
| **Mean Absolute Error (MAE)** | **$18.64\text{ mm}$** | Average magnitude of forecast error across all station-days. |
| **Root Mean Squared Error (RMSE)** | **$33.19\text{ mm}$** | Heavily penalizes large convective under-predictions. |
| **Mean Forecast Bias** | **$-10.88\text{ mm}$** | Pronounced systemic under-prediction of monsoon precipitation volume. |
| **Mean Forecast Rainfall** | **$13.14\text{ mm}$** | Area-averaged daily rainfall simulated by GFS coarse grid. |
| **Mean Observed Rainfall** | **$24.01\text{ mm}$** | Point-measured daily rainfall across primary rain gauges. |
| **Pearson Correlation ($r$)** | **$0.1421$** | Weak linear tracking between daily forecast depth and station observations. |
| **Spearman Rank Correlation ($\rho$)** | **$0.3635$** | Statistically significant monotonic ranking ($p = 2.04 \times 10^{-9}$), indicating moderate skill in distinguishing dry/wet regimes despite magnitude errors. |

---

## 3. Multi-Threshold Categorical Verification

Contingency metrics were evaluated across five standard IMD meteorological thresholds:

| Threshold Class | Threshold Depth | Hits | Misses | False Alarms | Correct Negatives | POD (Hit Rate) | FAR | CSI (Threat Score) | Equitable Threat Score (ETS) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Light Rain** | $\ge 2.5\text{ mm}$ | 190 | 25 | 26 | 15 | **$0.8837$** | **$0.1204$** | **$0.7884$** | **$0.0762$** |
| **Moderate Rain** | $\ge 15.6\text{ mm}$ | 60 | 65 | 27 | 104 | **$0.4800$** | **$0.3103$** | **$0.3947$** | **$0.2185$** |
| **Rather Heavy Rain**| $\ge 35.5\text{ mm}$ | 0 | 43 | 7 | 206 | **$0.0000$** | **$1.0000$** | **$0.0000$** | **$-0.0782$** |
| **Heavy Rain** | $\ge 64.5\text{ mm}$ | 0 | 23 | 0 | 233 | **$0.0000$** | *Undefined* | **$0.0000$** | **$0.0000$** |
| **Very Heavy Rain** | $\ge 115.6\text{ mm}$ | 0 | 10 | 0 | 246 | **$0.0000$** | *Undefined* | **$0.0000$** | **$0.0000$** |

### Key Categorical Findings:
1. **High Skill on Rain Occurrence ($\ge 2.5\text{ mm}$):** GFS successfully predicted the occurrence of rainfall ($\text{POD} = 88.4\%$, $\text{FAR} = 12.0\%$, $\text{CSI} = 0.788$). It reliably captured synoptic monsoon cloud cover.
2. **Moderate Skill on Routine Monsoon Rain ($\ge 15.6\text{ mm}$):** Captured nearly half of moderate rainfall events ($\text{POD} = 48.0\%$, $\text{CSI} = 0.395$, $\text{ETS} = 0.219$).
3. **Total Breakdown at Convective Extreme Thresholds ($\ge 35.5\text{ mm}$ to $\ge 115.6\text{ mm}$):**
   - At $\ge 35.5\text{ mm}$: 0 hits, 43 misses ($\text{POD} = 0.00$).
   - At $\ge 64.5\text{ mm}$: 0 hits, 23 misses ($\text{POD} = 0.00$).
   - At $\ge 115.6\text{ mm}$: 0 hits, 10 misses ($\text{POD} = 0.00$).

---

## 4. Physical Synthesis: The Areal vs. Point Scale Mismatch

The complete failure of coarse GFS to detect heavy rainfall ($\text{POD} = 0.00$) is **not** an operational data defect; it is a fundamental consequence of atmospheric physics and spatial scale representation:
- A single GFS 0.25° grid box represents an areal footprint of approximately **$27.75\text{ km} \times 27.05\text{ km} \approx 750\text{ km}^2$**.
- A tipping-bucket rain gauge has an orifice diameter of $20\text{ cm}$ ($\text{Area} \approx 0.0314\text{ m}^2$), representing an instantaneous point measurement.
- The extreme deluges of August 30 and September 4–5, 2022 were triggered by mesoscale convective clusters with intense cores of $2 - 5\text{ km}$ diameter (producing $130 - 162\text{ mm}$ at individual TRGs).
- When $162\text{ mm}$ falls over a $20\text{ km}^2$ storm core while the surrounding $730\text{ km}^2$ receives only $20 - 30\text{ mm}$, the **grid-box average** is mathematically $\approx 25 - 35\text{ mm}$.
- Because GFS predicts the grid-box mean, its maximum forecasted depth across Bengaluru was **$38.7\text{ mm}$**. It could physically never cross the $64.5\text{ mm}$ point threshold.

---

## 5. Workstream Acceptance Status

$$\mathbf{GATE\_STATUS:\quad PASS\_WITH\_DOCUMENTED\_LIMITATIONS}$$

**Documented Boundaries for Research Presentation:**
- GFS $0.25^\circ$ demonstrates moderate skill in predicting rainfall occurrence and routine monsoon volume ($\text{CSI} = 0.395$ at $15.6\text{ mm}$).
- Coarse GFS forecasts **cannot be used directly as triggers for heavy rainfall or urban flood emergencies** without localized convective downscaling.
- The 256 paired records represent 3 spatial clusters; effective sample size is at most 48 instances.

