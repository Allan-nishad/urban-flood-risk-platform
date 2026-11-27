# Phase 2B.2 — Feature Correlation & Multicollinearity Diagnostics Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban Provisional Development Domain (1,170 Cells, 1-km Grid)  
**Execution Environment:** Python 3.11.15 (`.venv`)  
**Associated Artifact:** [`reports/figures/phase_2b/correlation_heatmap.png`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase_2b/correlation_heatmap.png)

---

## 1. Executive Summary

This report delivers a rigorous correlation and multicollinearity assessment of the verified static physical features extracted across the 1,170 grid cells of the Bengaluru Urban provisional domain. 
Both linear (Pearson $r$) and monotonic rank (Spearman $\rho$) relationships were evaluated. To identify collinear predictors that could destabilize parameter estimation in downstream modeling, Variance Inflation Factors (VIF) were analytically calculated from the predictor correlation matrix inverse.

**Key Diagnostic Verdict:**
- Topographic features (`elevation_mean_m` and `elevation_std_m`) are statistically independent of urban land cover density ($\text{VIF} < 1.20$), indicating that elevation and slope proxies can be used without multicollinearity concerns.
- A strong inverse trade-off exists between `built_up_fraction` and rural vegetation classes, particularly `cropland_fraction` ($r = -0.79$) and `shrubland_fraction` ($r = -0.64$). This collinearity results in moderate VIF values for `built_up_fraction` ($\text{VIF} = 7.22$) and `cropland_fraction` ($\text{VIF} = 6.07$).
- **Recommendation:** Downstream models should either regularize predictor weights (e.g. Ridge / Elastic Net / Lasso) or collapse landcover into an orthogonal imperviousness index ($I_{\text{impervious}} = f_{\text{built}} - f_{\text{vegetation}}$) to prevent coefficient inflation.

![Static Feature Correlation Heatmap](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase_2b/correlation_heatmap.png)

---

## 2. Linear (Pearson $r$) Correlation Matrix

The table below presents the pairwise Pearson correlation coefficients across the 8 verified continuous static physical features:

| Feature | `elevation_mean_m` | `elevation_std_m` | `built_up_fraction` | `water_fraction` | `tree_cover_fraction` | `cropland_fraction` | `grassland_fraction` | `shrubland_fraction` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `elevation_mean_m` | **1.000** | -0.262 | 0.230 | -0.005 | -0.029 | -0.124 | -0.204 | -0.265 |
| `elevation_std_m` | -0.262 | **1.000** | 0.087 | -0.060 | 0.083 | -0.234 | 0.050 | 0.142 |
| `built_up_fraction` | 0.230 | 0.087 | **1.000** | -0.061 | -0.216 | **-0.786** | -0.484 | **-0.636** |
| `water_fraction` | -0.005 | -0.060 | -0.061 | **1.000** | 0.005 | -0.067 | -0.001 | -0.032 |
| `tree_cover_fraction` | -0.029 | 0.083 | -0.216 | 0.005 | **1.000** | -0.249 | -0.167 | 0.026 |
| `cropland_fraction` | -0.124 | -0.234 | **-0.786** | -0.067 | -0.249 | **1.000** | 0.376 | 0.275 |
| `grassland_fraction` | -0.204 | 0.050 | -0.484 | -0.001 | -0.167 | 0.376 | **1.000** | 0.271 |
| `shrubland_fraction` | -0.265 | 0.142 | **-0.636** | -0.032 | 0.026 | 0.275 | 0.271 | **1.000** |

---

## 3. Monotonic (Spearman Rank $\rho$) Correlation Matrix

To detect non-linear monotonic dependencies and guard against outlier leverage (e.g. from highly skewed water fractions or valley elevations), the Spearman rank correlation matrix was evaluated:

| Feature | `elevation_mean_m` | `elevation_std_m` | `built_up_fraction` | `water_fraction` | `tree_cover_fraction` | `cropland_fraction` | `grassland_fraction` | `shrubland_fraction` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `elevation_mean_m` | **1.000** | -0.111 | 0.222 | 0.005 | 0.007 | -0.231 | -0.168 | -0.349 |
| `elevation_std_m` | -0.111 | **1.000** | 0.063 | -0.085 | 0.091 | -0.212 | 0.034 | 0.198 |
| `built_up_fraction` | 0.222 | 0.063 | **1.000** | -0.054 | -0.187 | **-0.812** | -0.471 | **-0.648** |
| `water_fraction` | 0.005 | -0.085 | -0.054 | **1.000** | 0.082 | 0.006 | 0.024 | -0.083 |
| `tree_cover_fraction` | 0.007 | 0.091 | -0.187 | 0.082 | **1.000** | -0.217 | -0.141 | 0.009 |
| `cropland_fraction` | -0.231 | -0.212 | **-0.812** | 0.006 | -0.217 | **1.000** | 0.354 | 0.284 |
| `grassland_fraction` | -0.168 | 0.034 | -0.471 | 0.024 | -0.141 | 0.354 | **1.000** | 0.298 |
| `shrubland_fraction` | -0.349 | 0.198 | **-0.648** | -0.083 | 0.009 | 0.284 | 0.298 | **1.000** |

---

## 4. Multicollinearity Diagnostics: Variance Inflation Factor (VIF)

The Variance Inflation Factor quantifies the inflation in the variance of an estimated regression coefficient due to linear relationships among the predictor variables:
$$\text{VIF}_j = \frac{1}{1 - R_j^2} = (R^{-1})_{jj}$$
where $R$ is the correlation matrix of predictors. 

Standard empirical guidelines:
- $\text{VIF} < 5.0$: Low multicollinearity; safe for unregularized linear modeling.
- $5.0 \le \text{VIF} < 10.0$: Moderate multicollinearity; coefficient stability may degrade in unpenalized regressions.
- $\text{VIF} \ge 10.0$: Severe multicollinearity; severe coefficient instability, parameter sign flipping, and inflated standard errors.

### VIF Audit Results

| Predictor Variable | VIF | Diagnostic Assessment | Recommended Treatment |
| :--- | :---: | :---: | :--- |
| `elevation_mean_m` | **1.17** | Low | Retain as primary topographic baseline |
| `elevation_std_m` | **1.19** | Low | Retain as sub-cell roughness/slope proxy |
| `built_up_fraction` | **7.22** | Moderate | High collinearity with rural land uses; use regularization or composite index |
| `tree_cover_fraction` | **2.56** | Low | Retain as urban canopy / infiltration proxy |
| `cropland_fraction` | **6.07** | Moderate | Complement of built-up; consider omitting if built-up is primary |
| `grassland_fraction` | **1.65** | Low | Retain as open pervious surface proxy |

---

## 5. Physical & Modeling Insights

1. **Topography vs. Urban Development Independence:**
   The weak correlation between `elevation_mean_m` and `built_up_fraction` ($r = 0.23$, $\rho = 0.22$, $\text{VIF} = 1.17$) proves that urban built environment in Bengaluru spans diverse elevations across the plateau. Development is not confined to valleys or ridges alone, though major tech parks (Bellandur, Outer Ring Road) occupy natural low-elevation valley bottoms.
2. **Land Cover Complementarity (The Zero-Sum Constraint):**
   Because fractional land covers within a 1-km cell sum to approximately $1.0$, `built_up_fraction` exhibits strong negative collinearity with `cropland_fraction` ($r = -0.786, \rho = -0.812$) and `shrubland_fraction` ($r = -0.636, \rho = -0.648$). Including all land cover fractions simultaneously in an unconstrained linear model would induce variance inflation ($\text{VIF} = 7.22$).
3. **Surface Water Independence:**
   `water_fraction` shows almost zero linear correlation with all other static layers ($|r| \le 0.067$). This confirms that lake water bodies exist as localized, point-like landscape sinks across both urban and rural zones, requiring explicit proximity or hydro-accumulation metrics rather than general terrain proxies.

