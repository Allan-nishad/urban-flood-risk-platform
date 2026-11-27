# Phase 6.1 — Independent Scientific Audit: Audit B (Ground Rainfall Verification)

**Auditor:** Independent Scientific Acceptance Inspector  
**Campaign Baseline:** Phase 6 Master Execution Baseline (`reports/phase_6/`)  
**Audit Target:** Ground Rain Gauge Ingestion, 256 Paired Records, Spatial Clustering, and Forecast Skill Metrics  
**Classification:** `VERIFIED_WITH_LIMITATIONS`  

---

## 1. Executive Summary & Audit Mandate

In the Phase 6 Executive Report, Workstream 6B reported:
- 21 stations catalogued and 357 observations
- 256 paired forecast-observation records
- $\text{MAE} = 18.64\text{ mm}$, $\text{RMSE} = 33.19\text{ mm}$, $\text{Pearson } r = 0.142$
- Heavy rainfall ($\ge 64.5\text{ mm}$) Probability of Detection: $\text{POD} = 0.00$

The audit investigated:
1. The discrepancy between 357 reported observations and actual hydrological observations in `ground_rainfall_observations.parquet`.
2. The exact construction of the 256 paired records.
3. The spatial dependence and effective degrees of freedom across stations sharing GFS grid nodes.
4. The recalculation of continuous and categorical verification metrics, and the physical reason for $\text{POD} = 0.00$.

---

## 2. Rain Gauge Network Audit & Observation Count Discrepancy

Inspection of `rain_gauge_station_registry.parquet` revealed **21 catalogued stations** across three distinct networks:

| Network | Station Count | Primary Hydrological Gauge? | Siting & Operational Context |
| :--- | :---: | :---: | :--- |
| **IMD Primary Observatories** | 3 | `True` | WMO-standard surface meteorological observatories (Bengaluru City, HAL Airport, Kempegowda International Airport). High accuracy, calibrated daily at 03:00 UTC (08:30 IST). |
| **KSNDMC BBMP TRG** | 13 | `True` | Telemetric Rain Gauges (tipping bucket 0.5mm resolution) deployed across municipal ward offices and lake catchment basins (Mahadevapura, Bellandur, Varthur, Koramangala, etc.). |
| **CPCB CAAQM Stations** | 5 | `False` | Continuous Ambient Air Quality Monitoring stations (BTM, Kadabesanahalli, City Railway, Peenya, Saneguruvanahalli). Sited on municipal rooftops; non-standard exposure for hydrological monitoring. |

### Observation Count Discrepancy Clarification:
- The Phase 6 Executive Report stated "357 observations".
- Nominal calculation: $21 \text{ stations} \times 17 \text{ calendar days} = 357 \text{ station-days}$.
- However, inspection of `ground_rainfall_observations.parquet` revealed **exactly 272 rows**.
- **Reason:** The 5 CPCB CAAQM stations were audited and correctly excluded from hydrological rainfall observations because they are air quality monitoring stations, not primary meteorological gauges.
- The 16 primary hydrological stations (3 IMD + 13 KSNDMC) across 17 days yielded exactly:
  $$16 \text{ primary stations} \times 17 \text{ days} = 272 \text{ authentic hydrological observations}$$
- **Audit Conclusion:** The 357 figure was an uncurated nominal count; the actual authentic observation dataset contains **272 validated hydrological observations**.

---

## 3. Structure and Clustering of the 256 Paired Records

Inspection of `gfs_vs_gauge_validation_metrics.parquet` established how the 256 paired samples were generated:
- Evaluated against the **16 primary hydrological stations**.
- Over **16 paired 24-hour forecast cycles**: initialization dates 2022-08-25 through 2022-09-09 (forecast lead time = 24h, verifying against ground observations for target dates 2022-08-26 through 2022-09-10).
- $16 \text{ stations} \times 16 \text{ dates} = 256 \text{ paired records}$.

### Spatial Clustering Analysis:
Crucially, all 16 stations are located within only **three native GFS $0.25^\circ$ grid cells**:

| GFS Grid Node | Stations Mapped to Node | Stations List | Total Paired Records |
| :---: | :---: | :--- | :---: |
| **(13.00°N, 77.50°E)** | 8 | IMD Bengaluru City, KSNDMC BTM Layout, Hebbal, Kengeri, Koramangala, Peenya, Vidyapeetha, Yelahanka | 128 |
| **(13.00°N, 77.75°E)** | 7 | IMD HAL Airport, KSNDMC Bellandur, Doddanekkundi, Mahadevapura, Marathahalli, Varthur, Whitefield | 112 |
| **(13.25°N, 77.75°E)** | 1 | IMD Kempegowda International Airport (Devanahalli) | 16 |
| **Total** | **16** | — | **256** |

### Statistical Implication:
- On any given calendar day, **all 8 stations mapped to (13.00°N, 77.50°E) receive the exact same GFS forecast value**.
- Similarly, **all 7 stations mapped to (13.00°N, 77.75°E) receive the exact same GFS forecast value**.
- Therefore, the 256 pairs do **NOT** represent 256 independent forecast instances.
- The maximum number of independent atmospheric forecast realizations evaluated is:
  $$\text{Effective Forecast Realizations} = 3 \text{ GFS nodes} \times 16 \text{ verification dates} = 48 \text{ instances}$$
- Treating the 256 pairs as independent samples would overstate the statistical degrees of freedom by a factor of $5.33\times$.

---

## 4. Verification Metrics Recalculation

All metrics were independently recalculated across the 256 pairs:

### A. Continuous Metrics (Pooled vs. Grouped)

| Evaluation Group | Sample Size ($N$) | Mean Forecast (mm) | Mean Observed (mm) | Mean Bias (mm) | MAE (mm) | RMSE (mm) | Pearson $r$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **All Pooled Pairs** | **256** | **13.14** | **24.01** | **-10.87** | **18.64** | **33.19** | **0.142** |
| GFS Node (13.00, 77.50) | 128 | 12.70 | 19.18 | -6.48 | 13.96 | 22.53 | 0.228 |
| GFS Node (13.00, 77.75) | 112 | 13.88 | 31.73 | -17.85 | 25.10 | 43.71 | 0.081 |
| GFS Node (13.25, 77.75) | 16 | 11.49 | 8.73 | +2.76 | 10.85 | 13.76 | 0.174 |
| **16-Date Spatial Mean** | **16** | **13.14** | **24.01** | **-10.87** | **14.86** | **25.29** | **0.285** |

### Key Observations:
1. The reported continuous metrics ($\text{MAE} = 18.64\text{ mm}$, $\text{RMSE} = 33.19\text{ mm}$, $r = 0.142$) are mathematically reproducible and correct on the pooled 256 pairs.
2. The GFS model exhibited severe negative bias ($\text{Bias} = -10.87\text{ mm}$ overall; $-17.85\text{ mm}$ in East Bengaluru), under-predicting the intense monsoon pulse.
3. Pearson correlation is weak ($r = 0.142$), reflecting that coarse GFS forecasts could not track day-to-day convective spikes at individual stations.

---

## 5. Contingency Table & Analysis of Heavy Rainfall Skill ($\text{POD} = 0.00$)

The contingency analysis for heavy rainfall ($\ge 64.5\text{ mm}$, the IMD threshold for Heavy Rainfall) was audited:

```
                  Contingency Table at Threshold >= 64.5 mm
                                Observed Heavy (Yes)    Observed Heavy (No)
Forecast Heavy (Yes)                    0 (Hits)            0 (False Alarms)
Forecast Heavy (No)                    23 (Misses)        233 (Correct Negatives)
```

- $\text{Hits} = 0$
- $\text{Misses} = 23$
- $\text{False Alarms} = 0$
- $\text{Correct Negatives} = 233$
- **Probability of Detection (POD):**
  $$\text{POD} = \frac{\text{Hits}}{\text{Hits} + \text{Misses}} = \frac{0}{0 + 23} = \mathbf{0.0000}$$
- **False Alarm Ratio (FAR):** Undefined / 0.0 (no alarms issued).
- **Critical Success Index (CSI):** $0 / (0 + 23 + 0) = \mathbf{0.0000}$.

### Contingency at Moderate Rainfall Threshold ($\ge 15.6\text{ mm}$):
At the lower IMD moderate rainfall threshold ($\ge 15.6\text{ mm}$):
- $\text{Hits} = 60$, $\text{Misses} = 65$, $\text{False Alarms} = 27$, $\text{Correct Negatives} = 104$
- $\text{POD} = 60 / (60 + 65) = \mathbf{0.4800}$ ($48.0\%$)
- $\text{FAR} = 27 / (60 + 27) = \mathbf{0.3103}$ ($31.0\%$)
- $\text{CSI} = 60 / (60 + 65 + 27) = \mathbf{0.3947}$ ($39.5\%$)

### Physical Explanation for $\text{POD} = 0.00$ at Heavy Rainfall:
- **Spatial Averaging Effect:** A single GFS grid cell covers $\approx 750\text{ km}^2$. The model simulates an areal average depth over this entire footprint.
- During the August 30 and September 4–5 events, convective storm cells were localized ($2 - 5\text{ km}$ diameter), producing intense point totals at individual TRGs ($162\text{ mm}$ at Mahadevapura on Aug 30; $131\text{ mm}$ at Doddanekkundi on Sept 5).
- However, the regional grid-cell average in GFS reached a maximum of only **$38.70\text{ mm}$** on August 27 and **$34.50\text{ mm}$** on September 7.
- Because the coarse grid-cell forecast never exceeded $64.5\text{ mm}$ anywhere in the domain, the model could mathematically never trigger a heavy rainfall event, yielding exactly 0 hits and 23 misses ($\text{POD} = 0.00$).

---

## 6. Audit Classification & Conclusions

| Audit Metric | Status | Note |
| :--- | :--- | :--- |
| **Observation Registry** | `VERIFIED_WITH_LIMITATIONS` | 272 authentic primary observations (not 357, as CPCB stations were correctly filtered). |
| **Continuous Verification** | `VERIFIED` | MAE ($18.64\text{ mm}$), RMSE ($33.19\text{ mm}$), $r$ ($0.142$) mathematically exact. |
| **Heavy Rainfall POD** | `VERIFIED` | $\text{POD} = 0.00$ verified; caused by spatial scale mismatch between GFS $0.25^\circ$ footprint and convective storm cores. |
| **Sample Independence** | `VERIFIED_WITH_LIMITATIONS` | 256 pairs clustered into 3 GFS cells; maximum 48 independent forecast instances. |

