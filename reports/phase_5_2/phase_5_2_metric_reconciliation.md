# Phase 5.2 — Track C: Forecast Metric Reconciliation & Aggregation Analysis

## 1. Executive Summary

This report performs a side-by-side reconciliation between the initial Phase 5 verification metrics and the Phase 5 final metrics, resolving why certain numbers changed while others remained identical.

* **Raw Error Equivalence:** Raw cell-level continuous errors ($\text{MAE}$ and $\text{RMSE}$) are **100% identical** between the initial and final datasets across all lead times. The underlying data rows ($183,690$ pairs) did not become more accurate.
* **Correlation Divergence:** The correlation differences reported between Phase 5 and Phase 5 Final are entirely due to **evaluating at the anchor-mean level ($N = 711$) versus the raw cell level ($N = 183,690$)**. Grouping and averaging cells across 9 anchors attenuates sub-grid cell noise, which mathematically increases correlation for coherent signals ($r = 0.7196 \to 0.8566$ at 6h) and sharpens negative correlations at degraded lead times ($r = -0.1143 \to -0.1460$ at 72h).
* **Accumulation Duration vs Lead Time:** All 24h, 48h, and 72h lead times evaluate **24-hour rainfall accumulation windows**, NOT multi-day accumulation depths.

---

## 2. Comprehensive Reconciliation Table

The following table presents the complete side-by-side comparison across all five lead times:

| Lead Time | Accum. Duration | Raw Sample ($N_{\text{raw}}$) | Raw MAE (mm) | Raw RMSE (mm) | Raw Pearson $r$ | Anchor Groups ($N_{\text{grp}}$) | Anchor MAE (mm) | Anchor RMSE (mm) | Anchor Pearson $r$ | Anchor $p$-value | Scientific Interpretation |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **6 Hours** | 6 Hours | 39,780 | 5.973 | 10.219 | 0.7196 | 153 | 5.203 | 9.512 | **0.8566** | $3.09 \times 10^{-45}$ | Strong synoptic curve match; anchor averaging smooths cell-level noise. |
| **12 Hours** | 12 Hours | 38,610 | 11.503 | 17.820 | 0.5892 | 153 | 9.146 | 15.410 | **0.7833** | $5.43 \times 10^{-33}$ | Coherent diurnal convective phase; errors increase with lead time. |
| **24 Hours** | 24 Hours | 37,440 | 20.805 | 28.623 | 0.5350 | 144 | 19.967 | 27.777 | **0.5621** | $2.30 \times 10^{-13}$ | Daily volume alignment; anchor correlation moderately exceeds raw cell $r$. |
| **48 Hours** | 24 Hours | 35,100 | 30.993 | 45.124 | -0.2053 | 135 | 28.930 | 43.886 | **-0.2331** | $6.51 \times 10^{-3}$ | Negative spatial or temporal association observed; physical displacement mechanism not independently established. |
| **72 Hours** | 24 Hours | 32,760 | 32.826 | 44.364 | -0.1143 | 126 | 30.275 | 41.984 | **-0.1460** | $0.1028$ | Skill collapses; anchor correlation is statistically indistinguishable from zero. |

---

## 3. Mathematical Mechanism of the Correlation Change

Why did correlation change between Phase 5 and Phase 5 Final while raw MAE and RMSE remained unchanged?

### A. Raw Metrics Were Calculated on Identical Data
Both initial Phase 5 and Phase 5 Final used the identical underlying matched pairs file (`forecast_observation_matched_pairs.parquet`, 183,690 rows, SHA-256: `458a5c09bcc8...`). Because the individual cell pairs were untouched, the raw MAE:
$$\text{MAE}_{\text{raw}} = \frac{1}{N} \sum_{i=1}^{N} |y_{\text{fcst}, i} - y_{\text{obs}, i}|$$
evaluated to $5.973\text{ mm}$ (at 6h), $11.503\text{ mm}$ (at 12h), and $20.805\text{ mm}$ (at 24h) in both reports.

### B. The Ecological Fallacy & Spatial Averaging Effect
In initial Phase 5, Pearson $r$ was calculated across all 39,780 individual grid cell rows ($r = 0.7196$).
In Phase 5 Final, `scratch/generate_final_metrics.py` calculated correlation across the 153 anchor-level means:
$$\bar{y}_{\text{anchor}} = \frac{1}{K} \sum_{k \in \text{Anchor}} y_k$$
Because individual grid cells had random perturbations around their anchor mean, averaging over the $K \approx 130$ cells per anchor canceled out high-frequency spatial variance (uncorrelated error):
$$\operatorname{Var}(\bar{\epsilon}) \approx \frac{\operatorname{Var}(\epsilon)}{K}$$
This reduction in noise variance increased the signal-to-noise ratio, inflating the Pearson correlation coefficient from $0.7196$ to $0.8566$.
This is a standard statistical property known as **aggregation inflation** (related to the Modifiable Areal Unit Problem, MAUP). It does **not** signify improved forecast quality.

---

## 4. Accumulation Duration Clarification

It is essential to distinguish between **forecast lead time** and **precipitation accumulation duration**:

```
+------------+--------------------+---------------------+-------------------------------------------------------+
| Lead Time  | Forecast Issue     | Valid Window        | Accumulation Window & Meaning                         |
+------------+--------------------+---------------------+-------------------------------------------------------+
| 6 Hours    | T_init (e.g. 00Z)  | T_init + 6h (06Z)   | 6-hour rainfall accumulation from 00Z to 06Z          |
| 12 Hours   | T_init (e.g. 00Z)  | T_init + 12h (12Z)  | 12-hour rainfall accumulation from 00Z to 12Z         |
| 24 Hours   | T_init (e.g. 00Z)  | T_init + 24h (D+1)  | 24-hour daily total for Day 1                         |
| 48 Hours   | T_init (e.g. 00Z)  | T_init + 48h (D+2)  | 24-hour daily total for Day 2 (NOT 48h accumulation)  |
| 72 Hours   | T_init (e.g. 00Z)  | T_init + 72h (D+3)  | 24-hour daily total for Day 3 (NOT 72h accumulation)  |
+------------+--------------------+---------------------+-------------------------------------------------------+
```

The 48h and 72h lead times forecast the daily rainfall depth occurring 2 and 3 days into the future; they do not represent cumulative 48-hour or 72-hour rainfall totals.

