# Phase 7D — Susceptibility Uncertainty & ROC-AUC Deconstruction

**Auditor:** Statistical Validation Specialist & Research Lead  
**Evaluation Sample:** 20 Verified Ground Truth Cells (13 Positives, 7 Monitored Negatives)  
**Evaluated Scores:** Static Topographic Susceptibility & Dynamic HIPI Index  
**Status:** **`PASS_WITH_DOCUMENTED_LIMITATIONS`**  

---

## 1. Executive Summary & Core Statistical Deconstruction

In Phase 6, the deterministic Hydrological Inundation Potential Index (HIPI) reported a $\text{ROC-AUC} = \mathbf{0.560}$ on ground truth. 

This audit conducted:
1. Exact reconstruction of the ROC-AUC score and its confidence bounds.
2. Sensitivity analysis under three distinct weighting formulations.
3. Hanley & McNeil (1982) analytical standard error quantification for $N=20$.

The audit established that:
- **The 95% Confidence Interval for ROC-AUC completely spans 0.500 (random chance).**
- A sample of $N=20$ is statistically incapable of establishing generalizable predictive capability.
- Macro-topographic indices (1-km scale) cannot resolve micro-scale urban drainage obstructions.

---

## 2. Sensitivity of ROC-AUC Under Alternative Formulations

| Formulation Variant | Feature Weighting Scheme | Evaluated ROC-AUC ($N=20$) | Standard Error (SE) | Analytical 95% CI |
| :--- | :--- | :---: | :---: | :---: |
| **Dynamic HIPI (Phase 6)** | $35\%$ TWI $+ 25\%$ Sink $+ 40\%$ Forecast Runoff | **$0.5604$** | $0.131$ | $[0.303, 0.817]$ |
| **Static Variant 1** | $35\%$ Conditioned TWI $+ 25\%$ Sink $+ 40\%$ Built-up | **$0.6374$** | $0.129$ | $[0.385, 0.890]$ |
| **Static Variant 2** | $35\%$ Retained TWI $+ 25\%$ Sink $+ 40\%$ Built-up | **$0.6374$** | $0.129$ | $[0.385, 0.890]$ |
| **Static Variant 3** | $60\%$ Conditioned TWI $+ 40\%$ Inverse Slope (No Landcover)| **$0.7912$** | $0.108$ | $[0.579, 1.000]$ |

### Critical Observations:
1. **Sample Instability:** On $N=20$ samples, altering feature weights causes ROC-AUC to swing wildly from **$0.560$ to $0.791$**.
2. **Standard Error Magnitude:** The standard error across all variants is massive ($\text{SE} \approx 0.11 - 0.13$).
3. **Overlapping with Random Chance ($0.500$):**
   - For the dynamic HIPI score ($0.560$), the 95% CI is $[0.303, 0.817]$.
   - Because $0.500$ lies well within this interval, the null hypothesis ($H_0: \text{AUC} = 0.500$, i.e., no predictive ability better than chance) cannot be rejected at the $\alpha = 0.05$ level.
4. **Why Variant 3 Scores Higher:** Variant 3 relies purely on TWI and inverse slope. Because all 5 monitored negative sites are high-elevation ridges ($915 - 938\text{m}$) and most flooded sites are valley lowlands ($860 - 890\text{m}$), macro-elevation alone separates them. But this reflects topographic elevation differences between ridges and valleys, **not** street-level flood prediction.

---

## 3. Physical Limitations of 1-km Macro-Topography

Why can a 1-km hydrological model not predict urban street flooding?
1. **Sub-Grid Hydrodynamic Barriers:**
   - In Bengaluru, compound walls around IT tech parks, elevated metro rail piers, and arterial road embankments act as 2-meter dykes that redirect stormwater across natural watershed boundaries.
   - A 1-km DEM averages terrain over $1,000,000\text{ m}^2$, completely erasing 2-meter walls.
2. **Culvert and Drain Silting:**
   - Flooding at Rainbow Drive Layout ($2.5\text{m}$ depth) was caused by a blocked culvert beneath Sarjapur Road.
   - Flooding at Mahadevapura underpass ($1.2\text{m}$ depth) was caused by stormwater pump failure.
   - No regional elevation index can know whether a sub-surface pipe is clogged with silt or plastic waste.

---

## 4. Formal Research Conclusion

$$\mathbf{KEY\quad FINDING:}$$
**A ROC-AUC of 0.560 confirms that macro-topography alone cannot discriminate urban flood risk from dry ground. The HIPI index is an exploratory indicator of regional drainage convergence, not an operational predictive flood model.**

