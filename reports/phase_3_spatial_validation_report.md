# Phase 3 — Spatial Validation & Model Stability Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban Provisional Development Domain (1,170 Cells at 1,000 m Resolution)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Associated Artifacts:**
- Spatial Block Validation Map: [`reports/figures/phase3/fig06_spatial_block_buffer_validation.png`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase3/fig06_spatial_block_buffer_validation.png)
- Model Ranking Stability Heatmap: [`reports/figures/phase3/fig07_model_ranking_stability_comparison.png`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase3/fig07_model_ranking_stability_comparison.png)

---

## 1. Executive Summary

This report establishes the spatial validation methodology, empirical spatial dependence analysis, stability evaluations, and leakage audits for the exploratory flood-risk models. 

**Core Scientific Findings:**
1. **Empirical Spatial Correlation Range:** Empirical semi-variogram analysis demonstrates that the spatial autocorrelation range reaches **16 km for elevation** and **12 km for built-up fraction**. This validates that spatial dependence far exceeds standard cell neighborhoods, proving that naive random cross-validation would suffer from extreme spatial autocorrelation leakage.
2. **Spatial Block Cross-Validation with Buffer:** A spatial block cross-validation scheme using **$5\text{ km} \times 5\text{ km}$ blocks** with an enforced **5-km spatial exclusion buffer** was evaluated across 48 spatial blocks. The average purged buffer zone comprises **10.9% of domain cells** per test fold.
3. **High Spatial Rank Generalization:** Despite purging all cells within 5 km of the test block, the leave-one-block-out Isolation Forest models achieved a **mean Spearman rank stability of $\rho = 0.9351 \pm 0.0498$** (median $\rho = 0.9463$) relative to full-domain models, confirming that feature representations capture general physical relationships rather than memorizing localized spatial pockets.
4. **Leakage Audit Clearance:** The feature pipeline passed 100% of target leakage, synthetic SAR leakage, and spatiotemporal duplicate record checks.

![Spatial Block & Buffer Validation Architecture](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase3/fig06_spatial_block_buffer_validation.png)

---

## 2. Empirical Spatial Dependence Analysis (Semi-Variograms)

To establish an empirically grounded buffer distance rather than relying on arbitrary assumptions, empirical semi-variograms $\gamma(h)$ were computed across lag distances from $1\text{ km}$ to $20\text{ km}$:
$$\gamma(h) = \frac{1}{2 N(h)} \sum_{(i,j): d(i,j) \approx h} (z_i - z_j)^2$$
The spatial correlation range is estimated as the lag distance where $\gamma(h)$ reaches $95\%$ of the total sample variance sill ($\sigma^2$).

### Variogram Table: Elevation & Built-Up Fraction ($N = 1,170$ Cells)

| Lag Distance $h$ (km) | Pair Count $N(h)$ | Elevation Semi-Variance $\gamma_e(h)$ ($\text{m}^2$) | Elevation Sill Fraction | Built-Up Semi-Variance $\gamma_b(h)$ | Built-Up Sill Fraction | Spatial Interpretation |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1 km** | 8,950 | 65.35 | 5.6% | 0.0216 | 23.8% | Immediate adjacent cell continuity |
| **2 km** | 12,952 | 135.59 | 11.5% | 0.0322 | 35.5% | Strong neighborhood dependence |
| **3 km** | 16,690 | 203.68 | 17.3% | 0.0394 | 43.4% | Continuous urban fabric & ridge slopes |
| **5 km** | 26,766 | 382.13 | 32.5% | 0.0519 | 57.2% | **Enforced Minimum Buffer Threshold** |
| **7 km** | 35,122 | 563.56 | 48.0% | 0.0638 | 70.3% | Intermediate sub-basin scale |
| **10 km** | 42,664 | 841.10 | 71.6% | 0.0815 | 89.9% | Major watershed boundary |
| **12 km** | 46,940 | 981.68 | 83.5% | **0.0884** | **97.5% (SILL REACHED)** | **Built-Up Spatial Range ($12\text{ km}$)** |
| **14 km** | 54,156 | 1071.24 | 91.2% | 0.0940 | > 100% | Agricultural-urban transition |
| **16 km** | 61,340 | **1133.68** | **96.5% (SILL REACHED)** | 0.1006 | > 100% | **Elevation Spatial Range ($16\text{ km}$)** |
| **20 km** | 47,132 | 1267.23 | > 100% | 0.1066 | > 100% | Regional plateau boundaries |

### Justification of Buffer Design:
The empirical semi-variogram proves that spatial dependence in topography extends up to $16\text{ km}$, and urban built-up density extends up to $12\text{ km}$. While an ideal theoretical buffer would span $12 - 16\text{ km}$, the total study domain width is $30\text{ km} \times 39\text{ km}$. A 16-km buffer around a 5-km test block would purge $> 75\%$ of the domain, leaving insufficient training samples.
Therefore, the **5-km buffer** represents a principled operational compromise: it eliminates $57.2\%$ of the spatial covariance in built-up density and $32.5\%$ in elevation, purging an average of **$10.9\%$ of domain cells** per validation fold while preserving sufficient training mass.

---

## 3. Spatial Block Cross-Validation Evaluation

The master grid ($30 \times 39$ cells) was partitioned into **$5\text{ km} \times 5\text{ km}$ blocks** (48 total blocks, $6 \text{ cols} \times 8 \text{ rows}$). In each validation fold:
1. One block $B_{\text{test}}$ was held out.
2. All cells within a Euclidean distance $\le 5\text{ km}$ of any test cell were purged into a quarantine buffer.
3. The model was trained exclusively on the remaining distant cells ($d > 5\text{ km}$).
4. Anomaly rankings on $B_{\text{test}}$ were compared against the unpartitioned domain baseline using Spearman rank correlation ($\rho$).

### Spatial Block CV Stability Results (Sensitivity Across 5, 10, and 15 km Buffers)

To evaluate spatial dependence beyond the initial 5-km buffer, systematic buffer sensitivity experiments were executed across 5 km, 10 km, and 15 km quarantine distances across all 48 spatial blocks ($5\text{ km} \times 5\text{ km}$):

| Exclusion Buffer Distance | Valid Folds ($\ge 50$ Train Cells) | Mean Test Cells | Mean Purged Buffer Cells | Mean Purged Domain Fraction | Mean Train Cells | Min Train Cells in Fold | Mean Spearman Rank Stability ($\rho$) | Median Spearman Stability ($\rho$) | Std Dev $\sigma_\rho$ | Methodological Assessment |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **5 km Buffer** | **48 / 48 (100%)** | 24.4 | 127.5 | 10.9% | 1,018.1 | 985 | **0.9351** | **0.9463** | 0.0498 | Conservative initial design; retains 87% training data; reduces local autocorrelation. |
| **10 km Buffer** | **48 / 48 (100%)** | 24.4 | 328.3 | 28.1% | 817.3 | 669 | **0.9202** | **0.9449** | 0.0768 | Matches built-up variogram range ($12\text{ km}$); purges 28% of cells; rank stability remains $> 0.92$. |
| **15 km Buffer** | **48 / 48 (100%)** | 24.4 | 559.0 | 47.8% | 586.6 | 284 | **0.8661** | **0.9126** | 0.1145 | Matches elevation variogram range ($16\text{ km}$); purges nearly half the domain; rank stability remains $> 0.86$. |

> [!WARNING]
> **Scientific Qualification on Buffer Distance:**
> Spatial block validation with a 5-km exclusion buffer reduces local spatial dependence and provides a far more conservative assessment than random cross-validation. However, the estimated empirical spatial dependence ranges of 12–16 km indicate that **residual spatial dependence may remain under a 5-km buffer**. As demonstrated above, expanding the buffer to 10 km and 15 km purges up to $47.8\%$ of the entire regional domain (leaving as few as 284 training cells in central test blocks). The fact that rank stability remains high ($\rho = 0.8661 - 0.9202$) even under 10–15 km buffers confirms that model feature representations capture generalized regional relationships rather than memorizing local geography, though residual spatial covariance cannot be completely eliminated in a finite $30\text{ km} \times 39\text{ km}$ domain.

---

## 4. Feature Ablation & Sensitivity Analysis

To quantify model dependence on specific predictor subsets and diagnose collinearity vulnerabilities, systematic feature ablations were performed using Isolation Forest ($N = 19,890$ observations). Each ablated model was compared against the full baseline (8 features) via Spearman rank correlation ($\rho$) and Top-10% Jaccard index overlap ($J_{10} = |A \cap B| / |A \cup B|$):

| Ablation Configuration | Retained Features | Spearman $\rho$ vs. Full Baseline | Top-10% Jaccard Overlap ($J_{10}$) | Sensitivity Impact & Physical Insight |
| :--- | :---: | :---: | :---: | :--- |
| **Full Baseline Model** | 8 | 1.0000 | 1.0000 | All verified static terrain, landcover, and dynamic rainfall predictors. |
| **Ablate Terrain** | 6 | **0.7575** | **0.3933** | **High Impact.** Removing elevation and slope proxy dramatically alters the top-decile risk zones ($60.7\%$ turnover). Topography is essential for localizing depressions. |
| **Ablate Land Cover** | 4 | **0.7076** | **0.3708** | **Highest Impact.** Removing built-up and vegetation fractions causes $62.9\%$ turnover in top-decile anomalies. Surface impermeability is the primary driver of urban anomaly detection. |
| **Ablate Rainfall** | 6 | **0.7922** | **0.4832** | **Moderate-High Impact.** Removing daily depth and API eliminates temporal storm dynamics, collapsing models into static susceptibility maps. |
| **Drop Built-Up Only** | 7 | 0.9401 | 0.6679 | **Low Impact.** High collinearity with cropland ($r = -0.786$) allows cropland and tree cover to act as effective surrogates. |
| **Drop Cropland Only** | 7 | 0.8870 | 0.6364 | **Moderate Impact.** Built-up fraction retains primary urban signal. |

![Model Ranking Stability Comparison](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase3/fig07_model_ranking_stability_comparison.png)

---

## 5. Algorithmic Random Seed Stability (Isolation Forest)

Isolation Forest constructs random axis-aligned partition trees. To ensure reproducibility and guard against stochastic instability, the model was evaluated across three distinct random seeds (42, 100, 2022) with 100 estimators and contamination $c = 0.05$:

### Pairwise Seed Rank Correlation Matrix ($N = 19,890$)

| Random Seed Comparison | Spearman Rank Correlation ($\rho$) | Top-10% Anomaly Agreement | Stochastic Verdict |
| :--- | :---: | :---: | :--- |
| **Seed 42 vs. Seed 100** | **0.9984** | 98.7% | Near-identical anomaly rankings |
| **Seed 42 vs. Seed 2022** | **0.9982** | 98.5% | Robust to pseudo-random initialization |
| **Seed 100 vs. Seed 2022** | **0.9986** | 98.8% | High ensemble stability with $n=100$ trees |

---

## 6. Comprehensive Leakage Audit

A three-point forensic leakage verification was executed across the model feature dataset:
1. **Target Leakage Check:** Verified that no historical incident identifiers (`incident_ids`), category tags (`evidence_category`), or occurrence flags (`has_reported_incident_on_date`) are present in predictor feature lists. Status: **PASS**.
2. **Synthetic Fixture Leakage Check:** Verified that no synthetic Sentinel-1 SAR simulation features (e.g. `sar_backscatter_intensity`, `candidate_water_mask`) exist in predictor arrays. Status: **PASS**.
3. **Spatiotemporal Duplicate Check:** Verified that the $(1,170 \times 17 = 19,890)$ panel contains zero duplicate `(grid_id, date)` combinations. Status: **PASS**.

