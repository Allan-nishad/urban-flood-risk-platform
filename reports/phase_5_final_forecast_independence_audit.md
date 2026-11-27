# Phase 5 Final — Forecast Sample Independence & Pseudo-Replication Audit Report

**Milestone:** Phase 5 Final Acceptance Campaign — Step 5: Information Content & Degrees of Freedom Audit  
**Author:** Antigravity Autonomous Agent (Google DeepMind Advanced Agentic Coding)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Study Domain:** Bengaluru Urban provisional study domain (1,170 equal-area 1-km cells, EPSG:6933, bounded provisionally by $77.45^\circ - 77.75^\circ\text{E}, 12.85^\circ - 13.15^\circ\text{N}$)  

---

## 1. Executive Summary & The Problem of Pseudo-Replication

The initial Phase 5 report claimed an evaluation sample size of **183,690 matched forecast-observation pairs**. 

In rigorous inferential statistics, calculating sample variance, standard errors, confidence intervals, or $p$-values based on raw row counts when observations share identical underlying model inputs constitutes **pseudo-replication** (Hurlbert, 1984). If a regional NWP model has a native grid resolution of $10\text{ km}$, sampling 130 contiguous 1-km grid cells within that single model pixel does not produce 130 independent meteorological predictions. It produces 1 physical prediction duplicated 130 times.

Workstream 5C conducts a rigorous degrees-of-freedom audit of the matched dataset, calculating the exact independent information content, quantifying the spatial replication factor, and re-evaluating forecast error metrics at the authentic regional anchor level ($N_{\text{eff}}$).

---

## 2. Independent Information Content Census

A comprehensive accounting of the unique dimensions in [`forecast_observation_matched_pairs.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/phase5_final/forecast_observation_matches/forecast_observation_matched_pairs.parquet) reveals:

| Dimension Evaluated | Census Value | Independent Information Interpretation |
| :--- | :---: | :--- |
| **Raw Matched Pairs ($N_{\text{raw}}$)** | **183,690** | Total row count across all cells, lead times, and cycles. |
| **Unique Forecast Models** | 1 | ECMWF IFS High-Resolution Atmospheric Model (HRES). |
| **Unique Synoptic Cycle Run Times ($T_{\text{init}}$)** | 34 | 17 calendar days $\times$ 2 daily initialization runs (00:00 UTC and 12:00 UTC). |
| **Unique Daily Forecast Cycles** | 2 | 00Z and 12Z model runs. |
| **Unique Forecast Source-Pixel IDs (NWP Anchors)** | **9** | Coarse regional anchors (`NWP_ANCHOR_0_0` to `NWP_ANCHOR_2_2`). |
| **Unique Forecast Lead Times** | 5 | $6\text{h}, 12\text{h}, 24\text{h}, 48\text{h}, 72\text{h}$. |
| **Unique Valid Timestamps ($T_{\text{valid}}$)** | 67 | Discrete accumulation termination timestamps across the event window. |
| **Unique Valid Dates (`valid_date`)** | 17 | August 25, 2022 through September 10, 2022. |
| **Unique Spatial Analytical Units (`grid_id`)** | 1,170 | Equal-area 1-km analytical grid cells. |
| **Independent Synoptic Storm Episodes** | 2 | Episode 1: Aug 29–30; Episode 2: Sep 4–6 (the historic Bellandur/Yamalur deluge). |

---

## 3. Spatial Replication Factor & Anchor Mapping

The 1,170 analytical grid cells inherit their atmospheric state from the 9 regional NWP anchors as follows:

| NWP Anchor Node | Coordinates | Geographic Coverage Sector | Number of Mapped 1-km Cells |
| :--- | :---: | :--- | :---: |
| `NWP_ANCHOR_0_0` | $12.88^\circ\text{N}, 77.48^\circ\text{E}$ | South-West Peri-Urban Fringe | 120 |
| `NWP_ANCHOR_0_1` | $12.88^\circ\text{N}, 77.60^\circ\text{E}$ | South Urban Core / Bannerghatta Corridor | 132 |
| `NWP_ANCHOR_0_2` | $12.88^\circ\text{N}, 77.72^\circ\text{E}$ | South-East Tech / Electronic City Corridor | 108 |
| `NWP_ANCHOR_1_0` | $13.00^\circ\text{N}, 77.48^\circ\text{E}$ | West Rural / Kengeri Fringe | 150 |
| `NWP_ANCHOR_1_1` | $13.00^\circ\text{N}, 77.60^\circ\text{E}$ | Central Metropolitan / BBMP Core | 165 |
| `NWP_ANCHOR_1_2` | $13.00^\circ\text{N}, 77.72^\circ\text{E}$ | East Tech Corridor / Mahadevapura / Bellandur | 135 |
| `NWP_ANCHOR_2_0` | $13.12^\circ\text{N}, 77.48^\circ\text{E}$ | North-West Peri-Urban Fringe | 120 |
| `NWP_ANCHOR_2_1` | $13.12^\circ\text{N}, 77.60^\circ\text{E}$ | North Ridge / Yelahanka / Hebbal Basin | 132 |
| `NWP_ANCHOR_2_2` | $13.12^\circ\text{N}, 77.72^\circ\text{E}$ | North-East Airport Corridor / Devanahalli Fringe | 108 |
| **Total / Mean** | — | — | **1,170 Total (Mean: 130.0 cells/anchor)** |

$$\text{Spatial Replication Factor} = \frac{1,170\text{ cells}}{9\text{ anchors}} = 130.0$$

Every atmospheric state simulated at an anchor is replicated across an average of **130 contiguous analytical cells**. Consequently, calculating standard errors using $N = 183,690$ underestimates sampling error by a factor of $\sqrt{130} \approx 11.4$, producing artificially collapsed confidence intervals.

---

## 4. Recalculation at Authentic Regional Anchor Scale ($N_{\text{eff}}$)

To eliminate pseudo-replication, forecast and observed values were aggregated to the authentic regional anchor scale (9 spatial nodes $\times$ 17 event dates = $711$ total independent spatiotemporal units). 

Below is the side-by-side comparison between the cell-replicated metrics ($N_{\text{raw}}$) and the authentic anchor-level metrics ($N_{\text{eff}}$):

| Lead Time | Cell $N_{\text{raw}}$ | Cell MAE (mm) | Cell RMSE (mm) | Cell Pearson $r$ | Anchor $N_{\text{eff}}$ | Anchor MAE (mm) | Anchor RMSE (mm) | Anchor Pearson $r$ | Anchor $p$-value |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **6h** | 39,780 | 5.973 | 10.219 | **0.7196** | **153** | **5.203** | **9.512** | **0.8566** | $3.1 \times 10^{-45}$ |
| **12h** | 38,610 | 11.503 | 17.820 | **0.5892** | **153** | **9.146** | **15.410** | **0.7833** | $5.4 \times 10^{-33}$ |
| **24h** | 37,440 | 20.805 | 28.623 | **0.5350** | **144** | **19.967** | **27.777** | **0.5621** | $2.3 \times 10^{-13}$ |
| **48h** | 35,100 | 30.993 | 45.124 | **-0.2053** | **135** | **28.930** | **43.886** | **-0.2331** | $0.0065$ |
| **72h** | 32,760 | 32.826 | 44.364 | **-0.1143** | **126** | **30.275** | **41.984** | **-0.1460** | **0.1028 (Not Sig.)** |

---

## 5. Critical Statistical Insights & Corrective Principles

1. **Skill Trajectory Confirmed:** The fundamental physical trajectory of NWP skill decay is confirmed at both scales. Short-range correlation is strong ($r = 0.56 - 0.86$ at anchor level), decaying to negative correlation at 48h ($r = -0.23$) and 72h ($r = -0.15$).
2. **False Significance at 72 Hours Corrected:** 
   - Under naive cell-level pseudo-replication ($N = 32,760$), the 72h correlation appeared "highly statistically significant" ($p = 1.04 \times 10^{-95}$) simply due to artificial sample size inflation.
   - At the authentic anchor scale ($N_{\text{eff}} = 126$), the 72h correlation has $p = 0.1028$, establishing that **72-hour forecast skill is statistically indistinguishable from zero**.
3. **Mandatory Reporting Requirement:** All official platform reports must explicitly present both $N_{\text{raw}}$ (the analytical grid mapping count) and $N_{\text{eff}}$ (the effective regional degrees of freedom) to ensure full scientific transparency.

