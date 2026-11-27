# Phase 5 Final — Continuous Forecast Error & Lead-Time Decay Verification Report

**Milestone:** Phase 5 Final Acceptance Campaign — Step 6: Continuous NWP Forecast Verification  
**Author:** Antigravity Autonomous Agent (Google DeepMind Advanced Agentic Coding)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Study Domain:** Bengaluru Urban provisional study domain (1,170 equal-area 1-km cells, EPSG:6933, bounded provisionally by $77.45^\circ - 77.75^\circ\text{E}, 12.85^\circ - 13.15^\circ\text{N}$)  

---

## 1. Executive Summary & Verification Protocol

Workstream 5C evaluates the continuous quantitative error characteristics of Numerical Weather Prediction (NWP) forecasts against independent ground and satellite rainfall observations. 

To eliminate confusion between forecast lead time and precipitation accumulation duration, we formally establish:
- **Lead Time Horizon ($\Delta t_{\text{lead}}$):** The temporal separation between model initialization ($T_{\text{init}}$) and verification valid time ($T_{\text{valid}}$), evaluated at $6\text{h}, 12\text{h}, 24\text{h}, 48\text{h}, 72\text{h}$.
- **Accumulation Duration ($\Delta t_{\text{accum}}$):** The physical integration interval over which rainfall depth is accumulated.
  - For $6\text{h}$ lead time: $\Delta t_{\text{accum}} = 6\text{ hours}$.
  - For $12\text{h}$ lead time: $\Delta t_{\text{accum}} = 12\text{ hours}$.
  - For $24\text{h}, 48\text{h}, 72\text{h}$ lead times: $\Delta t_{\text{accum}} = 24\text{ hours}$ (the 24-hour rainfall depth ending at the valid horizon).
  - **Explicit Clarification:** The $48\text{h}$ and $72\text{h}$ evaluations represent **24-hour accumulated rainfall forecasted 2 and 3 days in advance**, NOT 48-hour or 72-hour total cumulative rainfall.

---

## 2. Quantitative Continuous Verification Results

The continuous error metrics evaluated across all 183,690 cell-level matched pairs and 711 anchor-level independent units are detailed below:

### 2.1 Cell-Level Verification Metrics ($N_{\text{raw}}$):

| Lead Time ($\Delta t_{\text{lead}}$) | Accum. Duration | Sample Count ($N_{\text{raw}}$) | Mean Observed (mm) | Mean Forecast (mm) | Mean Bias (mm) | Rel. Bias (%) | MAE (mm) | RMSE (mm) | Pearson $r$ | Spearman $\rho$ |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **6 Hours** | 6 Hours | 39,780 | 11.275 | 6.945 | -4.330 | -38.41% | **5.973** | **10.219** | **+0.7196** | **+0.6749** |
| **12 Hours** | 12 Hours | 38,610 | 18.600 | 13.915 | -4.685 | -25.19% | **11.503** | **17.820** | **+0.5892** | **+0.5493** |
| **24 Hours** | 24 Hours | 37,440 | 29.070 | 27.695 | -1.375 | -4.73% | **20.805** | **28.623** | **+0.5350** | **+0.4610** |
| **48 Hours** | 24 Hours | 35,100 | 29.770 | 27.338 | -2.432 | -8.17% | **30.993** | **45.124** | **-0.2053** | **+0.1343** |
| **72 Hours** | 24 Hours | 32,760 | 31.110 | 27.224 | -3.886 | -12.49% | **32.826** | **44.364** | **-0.1143** | **-0.1752** |

### 2.2 Effective Anchor-Level Metrics ($N_{\text{eff}}$):

| Lead Time ($\Delta t_{\text{lead}}$) | Effective Units ($N_{\text{eff}}$) | Anchor Mean Obs (mm) | Anchor Mean Fcst (mm) | Anchor MAE (mm) | Anchor RMSE (mm) | Anchor Pearson $r$ | Anchor $p$-value | 95% Confidence Interval ($r$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **6 Hours** | 153 | 11.275 | 6.945 | **5.203** | **9.512** | **+0.8566** | $3.1 \times 10^{-45}$ | $[+0.806, \; +0.895]$ |
| **12 Hours** | 153 | 18.600 | 13.915 | **9.146** | **15.410** | **+0.7833** | $5.4 \times 10^{-33}$ | $[+0.712, \; +0.838]$ |
| **24 Hours** | 144 | 29.070 | 27.695 | **19.967** | **27.777** | **+0.5621** | $2.3 \times 10^{-13}$ | $[+0.437, \; +0.665]$ |
| **48 Hours** | 135 | 29.770 | 27.338 | **28.930** | **43.886** | **-0.2331** | $0.0065$ | $[-0.387, \; -0.066]$ |
| **72 Hours** | 126 | 31.110 | 27.224 | **30.275** | **41.984** | **-0.1460** | **0.1028 (Not Sig.)** | $[-0.313, \; +0.030]$ |

---

## 3. Physical Analysis of Error Growth & Convective Decay

```mermaid
flowchart TD
    subgraph Decay["Predictive Correlation Trajectory (Pearson r)"]
        R6["6h Horizon: r = +0.857 (p < 10^-44)"] --> R12["12h Horizon: r = +0.783 (p < 10^-32)"]
        R12 --> R24["24h Horizon: r = +0.562 (p < 10^-12)"]
        R24 --> R48["48h Horizon: r = -0.233 (p = 0.006)"]
        R48 --> R72["72h Horizon: r = -0.146 (p = 0.103, Zero Skill)"]
    end

    style R6 fill:#dcfce7,stroke:#16a34a,stroke-width:2px
    style R12 fill:#dcfce7,stroke:#16a34a,stroke-width:2px
    style R24 fill:#fef9c3,stroke:#ca8a04,stroke-width:2px
    style R48 fill:#fee2e2,stroke:#dc2626,stroke-width:2px
    style R72 fill:#fee2e2,stroke:#dc2626,stroke-width:2px
```

### 3.1 Why Forecast Error Grows Non-Linearly in Tropical Urban Regimes:
1. **Short-Range Coherence ($\le 24\text{h}$):** 
   Within 24 hours, the NWP model accurately tracks broad synoptic depressions, monsoon trough positioning, and low-level jet moisture convergence across Southern Karnataka, producing strong positive correlation ($r > 0.55$).
2. **Convective Phase & Spatial Errors ($\ge 48\text{h}$):** 
   Urban pluvial downpours in Bengaluru are triggered by mesoscale convective complexes (intense localized afternoon thunderstorm cells). Beyond 24 to 36 hours, NWP models exhibit severe spatial displacement errors: predicting extreme convective rainfall 30 km to the west or east of where storms actually form.
3. **Double Penalty Effect:** 
   Spatial misplacement of an intense convective storm creates a double penalty in continuous verification: a false alarm where the rain was forecast but did not fall, and a miss where the rain fell but was not forecast. This drives RMSE to $45\text{ mm}$ and causes Pearson $r$ to turn negative ($-0.20$ to $-0.23$).
4. **Statistical Insignificance at 72h:** 
   At the authentic regional anchor scale ($N_{\text{eff}} = 126$), the 72h correlation confidence interval includes zero ($[-0.313, \; +0.030]$, $p = 0.1028$). Numerical predictions at 72 hours have zero statistically defensible correlation with observed ground rainfall.

---

## 4. Scientific Conclusion & Operational Rule

1. **Defensible Warning Window:** Quantitative NWP forecasts are scientifically validated and approved for automated early detection **strictly for lead times $\le 24\text{ hours}$**.
2. **Unfavourable Results Retained:** The negative correlations at 48h ($r = -0.21$) and 72h ($r = -0.11$) are explicitly preserved and highlighted in all system documentation to prevent over-reliance on medium-range model runs.

