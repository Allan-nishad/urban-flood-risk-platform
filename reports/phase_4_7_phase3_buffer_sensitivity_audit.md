# Phase 4.7.7 — Scientific Audit: Phase 3 Spatial-Buffer Sensitivity & Autocorrelation Invariants

**Platform:** Bengaluru Urban Flood Risk Intelligence Platform  
**Component:** Spatial Validation Engine ([`src/floodrisk/processing/spatial_validation.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/spatial_validation.py))  
**Audited Datasets:**
- [`data/processed/phase3_model_features.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/phase3_model_features.parquet)
- [`reports/phase_3_spatial_validation_report.md`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/phase_3_spatial_validation_report.md)  
**Audit Classification:** **VERIFIED_WITH_LIMITATIONS (Empirical Numbers Recovered & Limitations Documented)**

---

## 1. Audit Context & Scientific Objective

In Phase 3.2, the platform implemented spatial block cross-validation with a 5-km buffer to prevent spatial data leakage between training and evaluation partitions. However, semi-variogram analysis revealed empirical spatial dependence ranges of $12\text{ km}$ for built-up fraction and $16\text{ km}$ for elevation.

The scientific objective of this audit is to:
1. Recover the exact numerical results of the 5 km, 10 km, and 15 km buffer sensitivity experiments.
2. Determine how many cells are purged and retained at each buffer distance.
3. Quantify ranking stability (Spearman's $\rho$) across increasing buffer sizes.
4. Assess whether a 15-km buffer leaves sufficient data for statistically valid model training.
5. Clarify that a 5-km buffer mitigates immediate contiguity but does **not** eliminate spatial dependence when variogram ranges exceed $12\text{ km}$.

---

## 2. Semi-Variogram Ranges & Empirical Spatial Autocorrelation

Empirical semi-variograms $\gamma(h) = \frac{1}{2N(h)} \sum (z_i - z_j)^2$ evaluated across all pairs of the 1,170 master cells establish the physical spatial structure of the Bengaluru Urban domain:

| Spatial Feature | Sample Variance (Sill $\sigma^2$) | 95% Sill Threshold | Estimated Correlation Range | Physical Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **SRTM Elevation ($m$)** | $1,175.07\text{ m}^2$ | $1,116.32\text{ m}^2$ | **$16.0\text{ km}$** | Topographic gradient from western ridges ($950\text{ m}$) to eastern valleys ($840\text{ m}$) spans half the domain. |
| **Built-Up Fraction** | $0.0907$ | $0.0862$ | **$12.0\text{ km}$** | Core urban agglomeration transitions gradually into peri-urban agriculture over $12\text{ km}$. |

Because the domain spans approximately $30\text{ km}$ east-west by $39\text{ km}$ north-south, a spatial range of $12 - 16\text{ km}$ represents between $35\%$ and $50\%$ of the entire study area width.

---

## 3. Buffer Sensitivity Experimental Results

Using $5\text{ km} \times 5\text{ km}$ blocks ($25$ grid cells per block; 48 spatial blocks total), leave-one-block-out validation was executed across 5 km, 10 km, and 15 km buffer zones:

| Buffer Distance | Mean Purged Cells | Mean Retained Cells | Mean Purged % | Min Train Cells | Mean Spearman $\rho$ | Median Spearman $\rho$ | Std Dev $\rho$ | Top-10% Overlap |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$5\text{ km}$ (Baseline)** | $127.5$ cells | $1,042.5$ cells | **$10.9\%$** | $985$ cells | **$0.9351$** | **$0.9463$** | $0.0498$ | $68.4\%$ |
| **$10\text{ km}$** | $328.3$ cells | $841.7$ cells | **$28.1\%$** | $669$ cells | **$0.9202$** | **$0.9449$** | $0.0612$ | $64.1\%$ |
| **$15\text{ km}$** | $559.0$ cells | $611.0$ cells | **$47.8\%$** | $284$ cells | **$0.8661$** | **$0.9126$** | $0.0984$ | $56.7\%$ |

```
[Buffer Purging Breakdown across 1,170 Cells]
  0 km (No buffer): [========================================] 1,170 cells (100% retained)
  5 km buffer:     [===================================.....] 1,043 cells (89.1% retained)
 10 km buffer:     [============================............]   842 cells (71.9% retained)
 15 km buffer:     [====================....................]   611 cells (52.2% retained)
```

---

## 4. Methodological Interpretation & Limitations

### 4.1 Does a 5-km Buffer Eliminate Spatial Dependence?
**NO.**
- At $h = 5\text{ km}$, semi-variance $\gamma(5)$ for elevation is $382.1\text{ m}^2$, which is only $32.5\%$ of the sill ($1,175.1\text{ m}^2$).
- The residual spatial covariance at $5\text{ km}$ remains substantial ($\sim 67.5\%$).
- Therefore, a 5-km buffer **mitigates contiguous cell adjacency**, but does **not** produce statistically independent spatial samples.
- The platform report must not claim that spatial autocorrelation was eliminated.

### 4.2 Why Was a 15-km Buffer Not Selected as the Default?
1. **Severe Training Sample Depletion:**  
   Enforcing a 15-km buffer purges an average of $47.8\%$ of the entire study area ($559$ cells). In edge blocks (e.g., corner blocks near Sarjapur or Peenya), the buffer eliminates over $75\%$ of the domain, leaving as few as $284$ training cells.
2. **Geographical Edge Effects:**  
   In a $30 \times 39\text{ km}$ domain, a 15-km buffer surrounding a central block removes the entire core city, forcing models to train exclusively on peripheral rural fringes and evaluate on the high-density urban center.
3. **Robustness of Ranking Invariant:**  
   Remarkably, even under a 15-km buffer with nearly half the domain purged, the mean rank stability remains $\rho = 0.8661$ (median $\rho = 0.9126$). This proves that the multi-criteria physical ranking is structurally robust and not an artifact of spatial over-fitting.

### 4.3 Scientific Conclusion
The 5-km buffer represents an optimal engineering trade-off: it purges immediate contiguous neighbors while preserving sufficient sample size ($89\%$ of domain) for stable estimation. The existence of residual spatial dependence is an inherent property of regional urban topographies and is documented as an explicit limitation.

