# Phase 7.2 Final Audit: Hydrological Modeling Claims Audit

**Auditor:** Urban Hydrologist & Statistical Validation Specialist  
**Document Identifier:** `reports/phase_7_final/final_hydrology_claims_audit.md`  
**Dataset Evaluated:** `data/processed/phase7/hydrology/phase7_hydrology_comparison.parquet` (1,170 cells)  
**Status:** **`VERIFIED_WITH_DOCUMENTED_LIMITATIONS`**  

---

## 1. Topographic Routing & Depression Metric Verification

All static terrain and depression metrics were independently audited:

| Hydrological Metric | Reported Value | Recalculated Audit Value | Discrepancy | Verification Status |
| :--- | :---: | :---: | :---: | :---: |
| **Grid Dimensions** | 30 cols $\times$ 39 rows | 30 cols $\times$ 39 rows | 0 | `VERIFIED` |
| **Flow Accumulation Range** | $1.0 - 186.0\text{ km}^2$ | $1.0 - 186.0\text{ km}^2$ | 0 | `VERIFIED` |
| **Topographic Wetness Index** | $10.08 - 19.04$ | $10.080 - 19.041$ | $< 0.001$ | `VERIFIED` |
| **Identified Sink Cells** | 19 cells | 19 cells | 0 | `VERIFIED` |
| **Maximum Depression Depth**| $4.85\text{ m}$ | $4.850\text{ m}$ | Exact | `VERIFIED` |
| **Downstream Area Alteration**| Up to $12.0\text{ km}^2$ | $12.00\text{ km}^2$ | Exact | `VERIFIED` |
| **Dynamic HIPI ROC-AUC** | **$0.5604$** | **$0.5604$** | Exact | `VERIFIED` |

---

## 2. Statistical Deconstruction of ROC-AUC = 0.560

The evaluation of the Hydrological Inundation Potential Index (HIPI) was audited:
- **Evaluation Sample Size:** $N = 20$ cells (13 verified positives, 7 verified monitored negatives).
- **Point Estimate:** $\text{ROC-AUC} = \mathbf{0.5604}$.

### Evaluation of Hanley & McNeil (1982) Standard Error:
- The Hanley & McNeil formulation computes the variance of the Mann-Whitney $U$ statistic:
  $$\text{SE}(\text{AUC}) = \sqrt{\frac{\theta(1-\theta) + (n_1 - 1)(Q_1 - \theta^2) + (n_2 - 1)(Q_2 - \theta^2)}{n_1 n_2}}$$
  where $\theta = 0.5604$, $n_1 = 13$, $n_2 = 7$, $Q_1 = \theta / (2 - \theta) = 0.3893$, $Q_2 = 2\theta^2 / (1 + \theta) = 0.4025$.
- Calculated Standard Error: **$\text{SE} = \mathbf{0.1288} \approx \mathbf{0.13}$**.
- Approximate 95% Confidence Interval ($Z = 1.96$):
  $$0.5604 \pm 1.96 \times 0.1288 \implies \mathbf{[0.308, 0.813]}$$

### Precise Academic Interpretation:
- With $N=20$, the standard error is large ($\approx 0.13$).
- Because the 95% confidence interval $[0.308, 0.813]$ **completely encompasses 0.500 (the null hypothesis of random guessing)**, the available sample **does not establish discrimination clearly above chance** ($p > 0.05$).
- It is scientifically incorrect to claim that the score "proves equivalence to chance"; rather, the correct formulation is: *the available ground truth sample is too small and the 1-km macro-elevation features are too coarse to demonstrate statistically significant flood discrimination*.

---

## 3. Depression Filling: Algorithmic Effect vs. Physical Reality

- **Algorithmic Effect:** Priority-flood pit filling modifies the DEM by elevating 19 sink cells to their spill rim. This guarantees that every cell has a continuous flow path to the domain boundary, altering downstream contributing area by up to $12.0\text{ km}^2$.
- **Physical Reality in Bengaluru:** These 19 depressions correspond to urban tanks (lakes), wetlands, and quarry pits. In reality, they possess finite storage retention. During early storm stages, they absorb runoff; during late storm stages (when full), they overtop.
- **Audit Conclusion:** Priority-flood filling accurately approximates the overtopping behavior of already-full lakes during the peak deluge of September 5, 2022, but overestimates downstream discharge during dry antecedent conditions.

