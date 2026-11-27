# Phase 7.2 Final Audit: Forecast Verification & NWP Claims Audit

**Auditor:** Meteorological Verification Specialist & Independent Scientific Reviewer  
**Document Identifier:** `reports/phase_7_final/final_forecast_claims_audit.md`  
**Dataset Evaluated:** `data/processed/phase7/nwp/phase7_forecast_error_registry.parquet` (256 pairs)  
**Status:** **`VERIFIED_WITH_DOCUMENTED_LIMITATIONS`**  

---

## 1. Audited Forecast Metrics & Reproduction

Every numerical claim in the Phase 7 forecast reports was verified against the underlying 256 paired evaluation records:

| Numerical Metric | Reported Value | Recalculated Audit Value | Discrepancy | Verification Status |
| :--- | :---: | :---: | :---: | :---: |
| **Matched Evaluation Pairs** | 256 | 256 | 0 | `VERIFIED` |
| **Primary Rain Gauge Stations**| 16 | 16 | 0 | `VERIFIED` |
| **Represented Native GFS Nodes**| 3 | 3 | 0 | `VERIFIED` |
| **Evaluation Calendar Dates** | 16 | 16 | 0 | `VERIFIED` |
| **Mean Absolute Error (MAE)** | $18.64\text{ mm}$ | $18.642\text{ mm}$ | $< 0.001\text{ mm}$ | `VERIFIED` |
| **Root Mean Squared Error (RMSE)**| $33.19\text{ mm}$ | $33.189\text{ mm}$ | $< 0.001\text{ mm}$ | `VERIFIED` |
| **Mean Forecast Bias** | $-10.88\text{ mm}$ | $-10.876\text{ mm}$ | $< 0.001\text{ mm}$ | `VERIFIED` |
| **Pearson Correlation ($r$)** | $0.1421$ | $0.1421$ | Exact | `VERIFIED` |
| **Spearman Rank Correlation ($\rho$)**| $0.3635$ | $0.3635$ | Exact | `VERIFIED` |
| **Light Rain ($\ge 2.5\text{ mm}$) POD**| $0.8837$ | $0.8837$ ($190/215$) | Exact | `VERIFIED` |
| **Moderate Rain ($\ge 15.6\text{ mm}$) POD**| $0.4800$ | $0.4800$ ($60/125$) | Exact | `VERIFIED` |
| **Heavy Rain ($\ge 64.5\text{ mm}$) POD**| **$0.0000$** | **$0.0000$** ($0/23$) | Exact | `VERIFIED` |
| **Heavy Rain Hits / Misses** | 0 / 23 | 0 / 23 | Exact | `VERIFIED` |

---

## 2. Statistical Uncertainty Audit (The 2,000-Iteration Clustered Bootstrap)

The audit inspected `scripts/phase7/grouped_uncertainty.py` and `phase7B_grouped_uncertainty_results.json`:
- **Cluster Definition:** The 16 calendar dates (each date contains observations from all 16 primary rain gauges).
- **Resampling Unit:** Daily cycles. When a date is resampled, all 16 stations on that date are sampled together as an intact block, preserving the simultaneous spatial covariance.
- **Monte Carlo Iterations:** 2,000 iterations using fixed NumPy seed 42.
- **Percentile Confidence Intervals:** Empirical 2.5th and 97.5th percentiles.

### Comparison of Naive vs. Clustered Bootstrap Uncertainty:
| Metric | Point Estimate | Naive i.i.d. 95% CI | Date-Clustered 95% CI | Width Inflation Ratio |
| :--- | :---: | :---: | :---: | :---: |
| **MAE** | $18.64\text{ mm}$ | $[15.34, 22.31]\text{ mm}$ | **$[8.71, 30.64]\text{ mm}$** | **$3.1\times$** ($21.93\text{ mm}$ vs $6.97\text{ mm}$) |
| **RMSE** | $33.19\text{ mm}$ | $[26.94, 39.35]\text{ mm}$ | **$[11.40, 49.57]\text{ mm}$** | **$3.1\times$** ($38.17\text{ mm}$ vs $12.41\text{ mm}$) |
| **Bias** | $-10.88\text{ mm}$ | $[-15.14, -7.22]\text{ mm}$ | **$[-24.89, +1.27]\text{ mm}$** | **$3.3\times$** ($26.16\text{ mm}$ vs $7.92\text{ mm}$) |
| **Pearson $r$**| $0.1421$ | $[0.08, 0.22]$ | **$[-0.07, +0.50]$** | **$4.2\times$** ($0.58$ vs $0.14$) |

### Interpretation of Pearson Correlation CI `[-0.07, +0.50]`:
- Because the date-clustered 95% confidence interval spans across zero into negative correlation, the available sample **does not establish a statistically significant positive linear correlation** at the 95% confidence level.
- The appearance of statistical significance under naive i.i.d. assumption ($p < 0.05$) is an artifact of treating spatially and temporally correlated records as independent samples.

---

## 3. Spatial Resolution Attribution Clarification

- **Native Grid Spacing:** NOAA GFS 0.25° has a native grid spacing of $\approx 27.75\text{ km}$ latitude by $\approx 27.05\text{ km}$ longitude.
- **Domain Coverage:** The $1,170\text{ km}^2$ study area is covered by **exactly 6 native GFS grid nodes**:
  - Two central nodes ($(13.00, 77.50)$ and $(13.00, 77.75)$) account for 930 out of 1,170 cells ($79.49\%$).
- **Rain Gauge Nodes:** All 16 primary rain gauges map to only **3 native GFS nodes** ($(13.00, 77.50)$ [8 stations], $(13.00, 77.75)$ [7 stations], $(13.25, 77.75)$ [1 station]).
- **Degrees of Freedom:** The effective sample size of atmospheric simulations evaluated is:
  $$K \le 3 \text{ GFS nodes} \times 16 \text{ dates} = 48 \text{ forecast realizations}$$
  Never describe the 256 pairs or 198,900 rows as independent forecast realizations.

