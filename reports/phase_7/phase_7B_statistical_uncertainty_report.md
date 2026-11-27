# Phase 7B — Dependence-Aware Statistical Uncertainty Report

**Auditor:** Statistical Validation Specialist & Research Lead  
**Campaign Baseline:** `scripts/phase7/grouped_uncertainty.py` & `phase7B_grouped_uncertainty_results.json`  
**Sample Evaluated:** 256 Paired Records (16 Stations $\times$ 16 Dates $\times$ 3 GFS Nodes)  
**Methodology:** Clustered Block Bootstrap (2,000 Iterations by Forecast Cycle / Date) vs. Naive i.i.d. Bootstrap  
**Status:** **`PASS_WITH_DOCUMENTED_LIMITATIONS`**  

---

## 1. Executive Summary & Core Statistical Question

In standard meteorological verification, evaluating paired records as identically and independently distributed (i.i.d.) observations is a widespread flaw. In an urban domain:
1. Multiple stations on the same calendar day experience identical synoptic forcing.
2. Stations mapped to the same GFS grid node receive identical forecast numerical values.
3. Errors across stations on extreme days (such as Sept 4–5) are strongly correlated.

Treating $N=256$ paired records as 256 independent samples drastically underestimates the standard error of metrics. This audit implemented a rigorous **date-clustered bootstrap** (resampling entire daily cycles with all 16 stations together) across 2,000 iterations to quantify the true sampling uncertainty.

---

## 2. Empirical 95% Confidence Intervals: Naive vs. Clustered Bootstrap

Across 2,000 Monte Carlo bootstrap iterations, empirical 95% confidence intervals (2.5th to 97.5th percentiles) were derived:

| Verification Metric | Point Estimate | Naive i.i.d. 95% CI | Date-Clustered 95% CI | CI Width (Naive) | CI Width (Clustered) | Uncertainty Inflation Factor |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mean Absolute Error (MAE)** | **$18.64\text{ mm}$** | $[15.34, 22.31]\text{ mm}$ | **$[8.71, 30.64]\text{ mm}$** | $6.97\text{ mm}$ | $21.93\text{ mm}$ | **$3.1\times$** |
| **Root Mean Squared Error (RMSE)** | **$33.19\text{ mm}$** | $[26.94, 39.35]\text{ mm}$ | **$[11.40, 49.57]\text{ mm}$** | $12.41\text{ mm}$ | $38.17\text{ mm}$ | **$3.1\times$** |
| **Mean Forecast Bias** | **$-10.88\text{ mm}$** | $[-15.14, -7.22]\text{ mm}$ | **$[-24.89, +1.27]\text{ mm}$**| $7.92\text{ mm}$ | $26.16\text{ mm}$ | **$3.3\times$** |
| **Pearson Correlation ($r$)** | **$0.1421$** | $[0.08, 0.22]$ | **$[-0.07, +0.50]$** | $0.14$ | $0.58$ | **$4.2\times$** |

---

## 3. Critical Academic Insights from Clustered Analysis

### 1. Artificial Certainty of Naive i.i.d. Resampling
- Under naive resampling, the confidence interval for Pearson $r$ is $[0.08, 0.22]$, which would tempt an analyst to claim a "statistically significant positive correlation ($p < 0.05$)".
- Under date-clustered resampling, however, the 95% confidence interval widens by **$4.2\times$** to **$[-0.07, +0.50]$**.
- Because the date-clustered interval **encompasses zero (negative correlation)**, the linear correlation between GFS daily forecasts and ground observations is **not statistically significant at the $\alpha = 0.05$ level**.

### 2. Extreme Outlier Sensitivity of MAE and RMSE
- The date-clustered 95% CI for MAE spans from **$8.71\text{ mm}$ to $30.64\text{ mm}$**.
- This massive spread reflects that the platform's overall MAE is dominated by just two severe convective days (August 30 and September 5), where daily station errors reached $80 - 130\text{ mm}$.
- On routine days, MAE is below $10\text{ mm}$; on extreme days, MAE exceeds $70\text{ mm}$.
- A sample of 16 dates is too small to establish an invariant MAE for all future monsoon seasons.

### 3. Mean Bias Spans Zero Under Clustered Uncertainty
- The date-clustered 95% CI for mean bias is **$[-24.89\text{ mm}, +1.27\text{ mm}]$**.
- While the point estimate is negative ($-10.88\text{ mm}$), the upper confidence limit crosses zero ($+1.27\text{ mm}$), indicating that while GFS systematically under-predicted during the convective flood peak, on non-convective monsoon days it occasionally slightly over-predicted light rainfall.

---

## 4. Formal Statistical Recommendation for Final Presentation

1. **Never Report Naive Standard Errors:** In academic papers or project vivas, the 256 samples must never be presented as 256 independent observations.
2. **Explicitly State the Effective Degrees of Freedom:** The dataset consists of 16 daily atmospheric cycles across 3 spatial grid nodes ($K \le 48$).
3. **Report the Clustered Confidence Intervals:** Always report metrics with their date-clustered bounds:
   - $\text{MAE} = 18.64\text{ mm} \quad [8.71, 30.64]\text{ mm}$
   - $\text{RMSE} = 33.19\text{ mm} \quad [11.40, 49.57]\text{ mm}$
   - $\text{Bias} = -10.88\text{ mm} \quad [-24.89, +1.27]\text{ mm}$
   - $\text{Pearson } r = 0.14 \quad [-0.07, +0.50]$

