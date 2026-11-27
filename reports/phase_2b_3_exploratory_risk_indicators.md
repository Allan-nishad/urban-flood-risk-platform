# Phase 2B.3 — Exploratory Flood-Risk Indicators & Sensitivity Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban Provisional Development Domain (1,170 Cells, 1-km Grid)  
**Execution Environment:** Python 3.11.15 (`.venv`)  
**Deliverable Parquet File:** [`data/processed/exploratory_risk_indicators_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/exploratory_risk_indicators_bengaluru.parquet) (19,890 rows, 663,821 bytes)  
**Associated Artifact:** [`reports/figures/phase_2b/exploratory_risk_indicators_map.png`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase_2b/exploratory_risk_indicators_map.png)

---

## 1. Executive Summary

Phase 2B.3 formulates and evaluates transparent, un-trained multi-criteria flood susceptibility and dynamic exposure indicators across the 1,170 1-km grid cells of the Bengaluru Urban domain. 

**Strict Separation of Concepts:**
- This phase **does not train supervised machine learning models**. Training is explicitly deferred because ground-truth labels remain incomplete and unrepresentative.
- Instead, transparent physical scoring equations were designed using verified observational inputs (SRTM 30m DEM, ESA WorldCover 10m, and staged GPM IMERG V07B precipitation).
- Pending layers (`MERIT Hydro UPA`) and simulation fixtures (`Sentinel-1A SAR`) are explicitly preserved as `NaN` / `UNAVAILABLE` and excluded from risk scoring.

**Core Findings:**
1. **Indicator Discriminative Power:** Cell-dates containing verified historical flood incidents exhibit dramatically higher exposure:
   - Land cover runoff potential indicator ($I_{\text{landcover}}$): **0.709** for incident cells vs **0.475** for non-incident cells.
   - Dynamic rainfall exposure indicator ($I_{\text{rainfall}}$): **0.680** on incident dates vs **0.314** on non-incident dates.
   - Runoff-dominant composite risk: **0.656** for incidents vs **0.409** for background cells.
2. **Weighting Scheme Robustness:** Sensitivity analysis across three diverse weighting schemes (Equal, Terrain-Dominant, Runoff-Dominant) reveals high rank stability (Spearman $\rho \ge 0.884$, Pearson $r \ge 0.884$). The mean spread across schemes is modest ($0.056 \pm 0.041$), confirming that spatial risk hotspots are consistently identified regardless of specific parameter tuning.

![Exploratory Flood Risk Indicators](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase_2b/exploratory_risk_indicators_map.png)

---

## 2. Mathematical Formulation of Component Indicators

All component indicators are normalized strictly to the unit interval $[0.0, 1.0]$:

### 1. Topographic Susceptibility Indicator ($I_{\text{terrain}}$)
Topographic depressions with low surface roughness trap overland flow and impede natural runoff:
$$\text{elev\_norm}_i = \frac{e_i - \min(e)}{\max(e) - \min(e)}, \quad \text{rough\_norm}_i = \frac{\sigma_{e, i} - \min(\sigma_e)}{\max(\sigma_e) - \min(\sigma_e)}$$
$$I_{\text{terrain}, i} = 0.60 \cdot (1 - \text{elev\_norm}_i) + 0.40 \cdot (1 - \text{rough\_norm}_i)$$
where $e_i$ is `elevation_mean_m` and $\sigma_{e, i}$ is `elevation_std_m`.

### 2. Land Cover Runoff Potential Indicator ($I_{\text{landcover}}$)
Impervious surfaces accelerate surface discharge and eliminate infiltration, while vegetative cover provides natural interception and storage:
$$I_{\text{raw}, i} = 0.75 \cdot f_{\text{built}, i} + 0.25 \cdot f_{\text{water}, i} - 0.20 \cdot (f_{\text{tree}, i} + f_{\text{crop}, i})$$
$$I_{\text{landcover}, i} = \text{clip}\left(\frac{I_{\text{raw}, i} - \min(I_{\text{raw}})}{\max(I_{\text{raw}}) - \min(I_{\text{raw}})}, 0.0, 1.0\right)$$

### 3. Dynamic Meteorological Exposure Indicator ($I_{\text{rainfall}}$)
Meteorological flood triggering depends jointly on short-term storm intensity ($P_{\text{daily}}$) and antecedent saturation ($API$):
$$\text{rain\_norm}_{i, t} = \text{clip}\left(\frac{P_{i, t}}{150.0}, 0.0, 1.0\right), \quad \text{api\_norm}_{i, t} = \text{clip}\left(\frac{API_{i, t}}{250.0}, 0.0, 1.0\right)$$
$$I_{\text{rainfall}, i, t} = 0.55 \cdot \text{rain\_norm}_{i, t} + 0.45 \cdot \text{api\_norm}_{i, t}$$

### 4. Hydrology & SAR Status Disclosure
- $I_{\text{hydro}}$: Marked as `NaN` (`indicator_hydro_status="UNAVAILABLE_PENDING_MERIT_HYDRO"`).
- $I_{\text{sar}}$: Marked as `NaN` (`indicator_sar_status="UNAVAILABLE_SAR_SYNTHETIC_ONLY"`).

---

## 3. Weighting Schemes & Sensitivity Analysis

Three transparent composite formulations were evaluated across all 19,890 cell-days:

1. **Equal Weighting (Balanced Scheme):**
   $$I_{\text{equal}} = \frac{1}{3} I_{\text{terrain}} + \frac{1}{3} I_{\text{landcover}} + \frac{1}{3} I_{\text{rainfall}}$$
2. **Terrain-Dominant Scheme (Topographic Sink Focus):**
   $$I_{\text{terrain\_dom}} = 0.50 \cdot I_{\text{terrain}} + 0.25 \cdot I_{\text{landcover}} + 0.25 \cdot I_{\text{rainfall}}$$
3. **Runoff-Dominant Scheme (Urban Flash-Flood Focus):**
   $$I_{\text{runoff\_dom}} = 0.20 \cdot I_{\text{terrain}} + 0.40 \cdot I_{\text{landcover}} + 0.40 \cdot I_{\text{rainfall}}$$

### Pairwise Scheme Correlation Matrix

| Scheme Pair | Pearson $r$ | Spearman Rank $\rho$ | Diagnostic Conclusion |
| :--- | :---: | :---: | :--- |
| **Equal vs. Runoff-Dominant** | **0.9857** | **0.9854** | Near-perfect linear and rank agreement |
| **Equal vs. Terrain-Dominant** | **0.9499** | **0.9498** | High consistency across relative rankings |
| **Terrain vs. Runoff-Dominant** | **0.8838** | **0.8840** | Strong concordance; differences confined to steep ridges |

### Indicator Distribution Statistics ($N = 19,890$)

| Indicator Metric | Mean | Std Dev | Min | 25th % | Median | 75th % | Max |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| $I_{\text{terrain}}$ | 0.4681 | 0.1081 | 0.1940 | 0.3981 | 0.4561 | 0.5184 | 0.8827 |
| $I_{\text{landcover}}$ | 0.4750 | 0.2875 | 0.0000 | 0.2021 | 0.4761 | 0.7368 | 1.0000 |
| $I_{\text{rainfall}}$ | 0.3142 | 0.1628 | 0.0914 | 0.1692 | 0.2924 | 0.4088 | 0.8583 |
| $I_{\text{equal}}$ | 0.4191 | 0.1066 | 0.1389 | 0.3363 | 0.4178 | 0.4984 | 0.7768 |
| $I_{\text{terrain\_dom}}$ | 0.4314 | 0.0863 | 0.1527 | 0.3682 | 0.4309 | 0.4927 | 0.7490 |
| $I_{\text{runoff\_dom}}$ | 0.4093 | 0.1282 | 0.1167 | 0.3069 | 0.4064 | 0.5062 | 0.8290 |
| Sensitivity Spread ($\Delta_{\max - \min}$) | 0.0560 | 0.0410 | 0.0000 | 0.0234 | 0.0484 | 0.0804 | 0.2317 |

---

## 4. Empirical Incident Evaluation

Comparing indicator values on cell-dates with verified flood incidents ($N = 18$) against background cell-dates ($N = 19,872$) validates the physical representation of the indicators:

| Indicator / Index | Incident Cells Mean | Non-Incident Cells Mean | Absolute Difference ($\Delta$) | Relative Contrast Ratio |
| :--- | :---: | :---: | :---: | :---: |
| $I_{\text{terrain}}$ | **0.5028** | 0.4681 | +0.0347 | 1.07× |
| $I_{\text{landcover}}$ | **0.7094** | 0.4748 | **+0.2346** | **1.49×** |
| $I_{\text{rainfall}}$ | **0.6799** | 0.3139 | **+0.3660** | **2.17×** |
| $I_{\text{equal}}$ | **0.6307** | 0.4189 | **+0.2118** | **1.51×** |
| $I_{\text{terrain\_dom}}$ | **0.5988** | 0.4312 | +0.1676 | 1.39× |
| $I_{\text{runoff\_dom}}$ | **0.6563** | 0.4091 | **+0.2472** | **1.60×** |

### Key Takeaway:
The Runoff-Dominant scheme achieves the greatest discriminative separation (1.60× contrast ratio), confirming that extreme rainfall over dense impervious urban surfaces is the primary driver of Bengaluru's reported flood emergencies. Topography acts as an important secondary localization factor (directing overland runoff into underpasses, lake cascades, and valley bottoms).

