# Phase 6.1 — Independent Scientific Audit: Audit E (Hydrology & ROC-AUC Reproducibility)

**Auditor:** Independent Scientific Acceptance Inspector  
**Campaign Baseline:** Phase 6 Master Execution Baseline (`reports/phase_6/`)  
**Audit Target:** Deterministic D8 Flow Routing, TWI, Priority-Flood Depression Filling, HIPI, and ROC-AUC of 0.560  
**Classification:** `VERIFIED_WITH_LIMITATIONS`  

---

## 1. Executive Summary & Audit Mandate

In the Phase 6 Executive Report, Workstream 6E reported:
- Deterministic D8 flow direction and accumulation routing on a $30 \times 39$ grid (1-km cells)
- Topographic Wetness Index ($\text{TWI} = 10.08 - 19.04$)
- 19 topographic closed depressions (sink cells) identified via 2D priority-flood filling
- Hydrological Inundation Potential Index (HIPI) coupled with genuine NOAA GFS forecast rainfall
- Evaluation on Stage 6C ground truth yielding $\text{ROC-AUC} = \mathbf{0.560}$

The audit investigated:
1. The mathematical implementation of D8 routing and TWI.
2. The physical consequence of 2D priority-flood depression filling in an urban environment.
3. The exact derivation, target variable, sample size, and data leakage risks of the $\text{ROC-AUC} = 0.560$ score.
4. Whether a ROC-AUC of 0.560 can be claimed as a predictive flood model.

---

## 2. Terrain Routing Algorithm & Metric Reproducibility

Inspection of `scripts/phase6/build_hydrology.py` and `topographic_routing_static_features.parquet` confirmed:
- **Grid Geometry:** $30 \text{ columns} \times 39 \text{ rows} = 1,170 \text{ cells}$ on a regular 1-km Cartesian grid (EPSG:6933).
- **Elevation Source:** MERIT Hydro / SRTM 1-arcsecond aggregated mean cell elevation.
- **D8 Flow Direction:** Canonical O'Callaghan & Mark (1984) single steepest descent algorithm across 8 neighbors. Diagonal distance correctly scaled to $\sqrt{2} \times 1,000\text{ m} \approx 1,414.21\text{ m}$.
- **Flow Accumulation:** Upstream cells sorted in descending order of elevation and recursively accumulated. Range: **$1.0\text{ km}^2$ (headwater ridge) to $186.0\text{ km}^2$ (Vrishabhavathi / Dakshina Pinakini trunk valley)**.
- **Topographic Wetness Index (TWI):**
  $$\text{TWI} = \ln\left(\frac{a}{\tan \beta}\right)$$
  where specific catchment area $a = A \times 1,000\text{ m}$ (in $\text{m}^2/\text{m}$), and $\tan \beta$ is the maximum downward slope gradient. Range: **$10.08$ to $19.04$**.
- All static hydrological metrics were reproduced bit-for-bit.

---

## 3. Depression Filling Audit & Urban Storage Realities

The script implements a 2D priority-flood iterative depression filling routine:
```python
def fill_depressions_2d(elev_grid):
    filled = np.copy(elev_grid)
    # iterates until filled[r, c] >= min_neighbor
    ...
```
- **Sinks Identified:** Exactly **19 closed depression cells** across the domain, with filled depths ranging from $0.05\text{m}$ to $4.85\text{m}$.
- **Physical Hydrological Consequence:**
  - In standard natural terrain hydrology, pit filling is performed under the assumption that depressions are DEM artifacts or noise that must be eliminated to enforce continuous drainage to the ocean.
  - In Bengaluru's urban plateau, however, closed depressions represent **interconnected cascade lakes (Kere), retention basins, and quarry pits**.
  - Depression filling artificially removes their natural stormwater storage retention capacity, forcing immediate downstream spillover.
  - While necessary for continuous macro-routing, this introduces a systematic bias in urban flood depth modeling unless lake retention volumes are explicitly parameterized.

---

## 4. Deconstruction of the ROC-AUC = 0.560 Evaluation

Inspection of `hydrology_ground_truth_validation.parquet` revealed the exact evaluation design:
- **Evaluation Dataset:** Only cells with verified ground truth status from Stage 6C:
  - 13 verified positive flood cells ($y = 1$)
  - 7 verified monitored negative cells ($y = 0$)
  - Total Sample Size: $\mathbf{N = 20}$ cells.
  - 1,150 unobserved cells were excluded from ROC-AUC calculation (zero label imputation).
- **Evaluated Metric:** The continuous Hydrological Inundation Potential Index (HIPI) for cycle `20220904` (peak flood valid 2022-09-05):
  $$\text{HIPI} = 0.35 \times \text{norm\_TWI} + 0.25 \times \text{norm\_Depression} + 0.40 \times \text{norm\_Runoff}$$

### Score Distribution across Ground Truth Cells:
- **Verified Positive Cells ($N=13$):** Mean HIPI = $0.188$ (Min: $0.078$, Max: $0.578$)
- **Verified Negative Cells ($N=7$):** Mean HIPI = $0.139$ (Min: $0.054$, Max: $0.239$)
- **Unobserved Domain Cells ($N=1,150$):** Mean HIPI = $0.141$

### Mathematical Reproduction:
$$\text{ROC-AUC} = \text{roc\_auc\_score}(y_{\text{true}}, y_{\text{scores}}) = \mathbf{0.5604} \quad (\mathbf{0.560})$$

---

## 5. Critical Scientific Assessment of ROC-AUC = 0.560

1. **Barely Above Random Guessing:**
   - A ROC-AUC of **0.560** is barely distinguished from a coin flip ($0.500$).
   - Given the extremely small sample size ($N=20$: 13 positives, 7 negatives), the standard error of the AUC estimate is:
     $$\text{SE}(\text{AUC}) \approx \sqrt{\frac{\text{AUC}(1-\text{AUC}) + (N_{pos}-1)(Q_1-\text{AUC}^2) + (N_{neg}-1)(Q_2-\text{AUC}^2)}{N_{pos} N_{neg}}} \approx 0.13$$
   - The 95% confidence interval spans roughly $[0.30, 0.82]$, completely encompassing $0.500$.
   - The score is **statistically indistinguishable from random chance**.

2. **No Data Leakage, But Purely Exploratory:**
   - The weights ($0.35, 0.25, 0.40$) were fixed *a priori* based on physical reasoning, not fitted or optimized via machine learning on the 20 ground truth cells.
   - Therefore, there is **no data leakage or artificial parameter tuning**.
   - However, this also means that HIPI is purely an *exploratory physical index*, **not** an operational predictive model.

3. **Physical Reason for Low Discrimination at 1-km Scale:**
   - Urban flooding in Bengaluru on September 4–5, 2022 was triggered by micro-scale failures:
     - Encroached stormwater drains (Rajakaluves)
     - Silted $1\text{m} - 2\text{m}$ culverts under arterial roads
     - Compound walls blocking natural overland spillways
     - Underpasses dipping $3\text{m}$ below street grade
   - A 1-km elevation model smooths these features completely away. At 1-km resolution, a 2-meter culvert blockage in an otherwise flat valley cannot be detected.

---

## 6. Audit Classification & Conclusions

| Audit Item | Status | Finding |
| :--- | :--- | :--- |
| **D8 & TWI Implementation** | `VERIFIED` | Canonical formulas implemented accurately; ranges mathematically reproducible. |
| **Depression Filling** | `VERIFIED_WITH_LIMITATIONS` | 19 sinks identified; filling is standard for routing but eliminates urban retention basins. |
| **ROC-AUC Calculation** | `VERIFIED` | Mathematically exact on $N=20$ samples. |
| **Predictive Capability** | `UNSUPPORTED` | $\text{ROC-AUC} = 0.560$ is statistically equivalent to random chance; cannot be used as an operational predictive flood model. |

