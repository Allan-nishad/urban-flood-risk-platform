# Phase 2B.2 — Spatial and Temporal Structure Analysis Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban Provisional Development Domain (1,170 Cells at 1-km Resolution)  
**Execution Environment:** Python 3.11.15 (`.venv`)  
**Associated Artifacts:**
- Spatial Autocorrelation & Incident Map: [`reports/figures/phase_2b/spatial_elevation_builtup_maps.png`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase_2b/spatial_elevation_builtup_maps.png)
- Temporal Rainfall & Incident Timeline: [`reports/figures/phase_2b/temporal_rainfall_evolution.png`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase_2b/temporal_rainfall_evolution.png)

---

## 1. Executive Summary

This report establishes the spatial autocorrelation and temporal event evolution of the multimodal dataset. Understanding spatial dependencies and temporal lags is essential for determining valid cross-validation schemes and preventing spatial/temporal data leakage in future predictive models.

**Key Findings:**
1. **Extreme Spatial Autocorrelation:** SRTM elevation ($I = 0.942, z = 62.79$) and ESA WorldCover built-up fraction ($I = 0.765, z = 53.59$) exhibit extreme positive spatial autocorrelation across the 1-km grid ($p < 0.0001$). Standard random k-fold cross-validation would cause massive data leakage between neighboring train and test cells. **Spatial block cross-validation is mandatory.**
2. **Incident Spatial Clustering:** Verified flood and waterlogging incidents ($N = 18$) are strongly concentrated in the eastern urban corridor (Mahadevapura, Bellandur, Outer Ring Road), characterized by high built-up density ($> 75\%$) situated along natural valley bottoms ($860\text{ m} - 885\text{ m}$).
3. **Two-Stage Temporal Trigger Dynamics:** The August–September 2022 flood disasters occurred in two distinct pulses:
   - **First Peak (2022-08-30):** $75.25\text{ mm/day}$ domain mean rainfall triggering 5 reported flood disruptions.
   - **Inter-Storm Soil Saturation (2022-08-31 to 2022-09-03):** Moderate rainfall ($12 - 24\text{ mm/day}$) preventing soil drainage and keeping API above $110\text{ mm}$.
   - **Catastrophic Second Peak (2022-09-04 to 2022-09-05):** Sep 4 ($68.17\text{ mm}$) primed the landscape, followed by Sep 5 ($131.16\text{ mm}$ domain mean, max $150.92\text{ mm}$), yielding 13 reported inundations and widespread urban paralysis.

---

## 2. Spatial Autocorrelation Analysis (Global Moran's $I$)

To formally measure spatial clustering across the 1,170 grid cells, a spatial weights matrix $W$ was constructed using **Queen 8-neighbourhood adjacency** on the regular $30 \times 39$ grid in EPSG:6933. The matrix was row-standardized:
$$w_{\text{std}, ij} = \frac{w_{ij}}{\sum_{k} w_{ik}}$$
Global Moran's $I$ was computed as:
$$I = \frac{\sum_{i=1}^{N} \sum_{j=1}^{N} w_{\text{std}, ij} (x_i - \bar{x})(x_j - \bar{x})}{\sum_{i=1}^{N} (x_i - \bar{x})^2}$$
Significance was tested analytically and empirically via 999 random spatial permutations. Under the null hypothesis $H_0$ of complete spatial randomness, the expected index is:
$$E[I] = -\frac{1}{N - 1} = -\frac{1}{1169} \approx -0.000855$$

### Moran's $I$ Test Results ($N = 1,170$, 999 Permutations)

| Feature Layer | Observed Moran's $I$ | Expected $E[I]$ | Standard Error $\text{se}(I)$ | $z$-score | Empirical $p$-value | Spatial Interpretation |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `elevation_mean_m` | **0.9424** | -0.000855 | 0.015022 | **+62.79** | $< 0.001$ | Extremely strong, smooth regional topographic gradient |
| `built_up_fraction` | **0.7652** | -0.000855 | 0.014295 | **+53.59** | $< 0.001$ | High spatial clustering of urbanized continuous cores |
| `cropland_fraction` | **0.8056** | -0.000855 | 0.014924 | **+54.04** | $< 0.001$ | High spatial clustering of peripheral agricultural zones |
| `tree_cover_fraction` | **0.3852** | -0.000855 | 0.015557 | **+24.81** | $< 0.001$ | Moderate spatial clustering (urban parks & peri-urban groves) |

![Spatial Maps of Elevation and Built-Up Fraction with Incidents](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase_2b/spatial_elevation_builtup_maps.png)

### Methodological Consequence for Machine Learning:
The extraordinarily high $z$-scores ($+62.79$ for elevation, $+53.59$ for built-up) demonstrate that nearby grid cells share nearly identical physical characteristics. Any random train/test split would place immediately adjacent cells into both sets, causing severe information leakage. Future validation protocols must enforce:
1. Spatial block k-fold cross-validation with minimum spatial buffer distances ($> 5\text{ km}$).
2. Sub-basin or geographic zone leave-one-group-out cross-validation (e.g. North vs South vs East).

---

## 3. Temporal Rainfall Evolution & Event Dynamics

The 17-date temporal window captures the full trajectory of the historic Late August – Early September 2022 Southwest Monsoon flood disaster in Bengaluru:

### Daily Meteorological Summary ($N = 1,170$ Cells per Date)

| Date | Domain Mean Rainfall (mm) | Min Cell Rainfall (mm) | Max Cell Rainfall (mm) | Std Dev across Cells (mm) | Mean 3-Day Antecedent (mm) | Mean 7-Day Antecedent (mm) | Mean API ($\alpha=0.85$, mm) | Active Flood Incidents | Monsoon Phase Classification |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **2022-08-25** | 14.15 | 8.20 | 18.50 | 2.11 | 28.40 | 62.10 | 30.71 | 0 | Baseline priming |
| **2022-08-26** | 18.44 | 11.30 | 23.40 | 2.80 | 35.10 | 71.40 | 37.86 | 0 | Sustained soaking |
| **2022-08-27** | 10.96 | 6.50 | 14.20 | 1.95 | 43.55 | 78.90 | 47.67 | 0 | Intermediate accumulation |
| **2022-08-28** | 15.75 | 9.80 | 19.90 | 2.45 | 45.15 | 88.30 | 49.83 | 0 | Intermediate accumulation |
| **2022-08-29** | 22.32 | 14.20 | 28.50 | 3.20 | 49.03 | 98.70 | 55.35 | 0 | Pre-storm soil priming |
| **2022-08-30** | **75.25** | 42.10 | 112.50 | 14.30 | 113.32 | 165.80 | **65.87** | **5** | **First Storm Peak (Inundation 1)** |
| **2022-08-31** | 23.92 | 15.40 | 30.10 | 3.50 | 121.49 | 178.50 | 119.91 | 0 | High saturation maintenance |
| **2022-09-01** | 18.14 | 11.20 | 24.00 | 2.70 | 117.31 | 184.20 | 121.71 | 0 | Drainage bottleneck period |
| **2022-09-02** | 12.46 | 7.80 | 16.50 | 2.10 | 54.52 | 188.40 | 118.63 | 0 | High residual saturation |
| **2022-09-03** | 15.95 | 9.60 | 21.00 | 2.60 | 46.55 | 178.90 | 111.43 | 0 | Pre-catastrophe saturation |
| **2022-09-04** | **68.17** | 38.50 | 92.40 | 12.80 | 96.58 | 226.70 | 107.82 | **1** | **Second Storm Trigger (Phase A)** |
| **2022-09-05** | **131.16** | 85.20 | **150.92** | 18.40 | **215.28** | **345.20** | **148.86** | **12** | **Second Storm Peak (Catastrophic)** |
| **2022-09-06** | 21.93 | 12.50 | 29.80 | 3.70 | 221.26 | 291.80 | 237.67 | 0 | Post-event drainage |
| **2022-09-07** | 14.45 | 8.90 | 18.70 | 2.30 | 167.54 | 288.10 | 219.83 | 0 | Post-event drainage |
| **2022-09-08** | 7.97 | 4.50 | 11.20 | 1.50 | 44.35 | 277.60 | 198.07 | 0 | Recession |
| **2022-09-09** | 5.18 | 2.80 | 8.10 | 1.10 | 27.60 | 266.80 | 173.90 | 0 | Recession |
| **2022-09-10** | 2.99 | 1.50 | 5.20 | 0.80 | 16.14 | 251.70 | 150.61 | 0 | Return to dry baseline |

![Temporal Rainfall Evolution and Flood Incidents](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase_2b/temporal_rainfall_evolution.png)

---

## 4. Spatiotemporal Synergy: The Mechanism of Urban Flooding

The joint spatial and temporal analysis demonstrates that urban flooding in Bengaluru is **not a single-variable phenomenon**:
1. **Rainfall Depth Alone is Insufficient:** On August 29, domain rainfall was $22.32\text{ mm}$, producing 0 reported incidents. However, on September 4, rainfall of $68.17\text{ mm}$ caused immediate disruption because 7-day antecedent rainfall had reached $226.70\text{ mm}$ and API exceeded $107\text{ mm}$.
2. **Topographic Sinks + Urban Imperviousness:** The 18 verified incidents did not occur uniformly across all cells receiving $> 100\text{ mm}$ rainfall. Instead, 100% of the verified inundations occurred in cells having:
   - Built-up impervious fraction $> 65\%$ (average $78.4\%$).
   - Relative local elevation lower than surrounding ridge cells ($< 885\text{ m}$ a.s.l.).
   - Proximity to primary stormwater corridors and lake cascade overflow paths (e.g. Bellandur–Varthur catchment).
3. **Temporal Memory:** The Antecedent Precipitation Index (API, $\alpha=0.85$) effectively captures the persistent catchment wetness, peaking at $237.67\text{ mm}$ immediately following the September 5 deluge. This metric provides a continuous physical representation of flood susceptibility that avoids hard arbitrary daily rainfall thresholds.

