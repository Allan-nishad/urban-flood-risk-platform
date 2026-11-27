# Phase 7F — Scientific Methodology & Mathematical Formulations

**Document Identifier:** `reports/phase_7/phase_7F_methodology.md`  
**Authors:** Scientific Research Lead, Urban Hydrologist & Verification Specialist  
**Status:** **`FINAL_METHODOLOGICAL_DOCUMENT`**  

---

## 1. Spatial Grid Discretisation

The study domain is projected into the World Cylindrical Equal Area projection (**EPSG:6933**):
- Centered on Bengaluru Urban ($77.45^\circ - 77.75^\circ\text{E}, 12.85^\circ - 13.15^\circ\text{N}$).
- Grid resolution: Exactly $1,000\text{ m} \times 1,000\text{ m}$ ($1.0\text{ km}^2$ per cell).
- Grid dimensions: 30 columns $\times$ 39 rows = 1,170 contiguous regular equal-area cells.
- Equal-area projection ensures that spatial integrals of precipitation volume and contributing areas are distortion-free.

---

## 2. NWP GRIB2 Decoding & Accumulation Disambiguation

NOAA GFS Total Precipitation (`APCP`) messages are encoded in WMO GRIB2 format:
- For forecast step $t$ in lead hours $\{6, 12, 24, 48, 72\}$:
  - Step range `0-6`: Accumulation over $[0, 6\text{h}]$.
  - Step range `6-12`: 6-hour interval accumulation over $[6, 12\text{h}]$.
  - Step range `0-12`: 12-hour cumulative run accumulation over $[0, 12\text{h}]$.
- To obtain daily 24h forecast rainfall for evaluation against ground gauges:
  $$P_{24h} = \text{APCP}_{0-24h} \quad (\text{Step range } 0-24)$$
- Decoded via ECMWF `ecCodes` extracting keys `paramId=228228`, `shortName=tp`, `stepRange`, `stepType=accum`.

---

## 3. Ground Rain Gauge Attribution & Continuous Verification

Each rain gauge station $s$ at $(\phi_s, \lambda_s)$ is mapped to its nearest native GFS grid node $g$ at $(\phi_g, \lambda_g)$ via ellipsoidal distance:
$$d(s, g) = R \sqrt{(\Delta \phi)^2 + (\cos \bar{\phi} \cdot \Delta \lambda)^2}$$
- **Continuous Metrics:**
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |F_i - O_i|$$
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (F_i - O_i)^2}$$
  $$\text{Mean Bias} = \frac{1}{N} \sum_{i=1}^N (F_i - O_i)$$
  $$\text{Pearson } r = \frac{\sum (F_i - \bar{F})(O_i - \bar{O})}{\sqrt{\sum (F_i - \bar{F})^2 \sum (O_i - \bar{O})^2}}$$

---

## 4. Categorical Contingency Verification Metrics

For any rainfall threshold $\tau$ (e.g. $64.5\text{ mm}$):
$$\text{Hits } (H) = \sum [F_i \ge \tau \land O_i \ge \tau], \quad \text{Misses } (M) = \sum [F_i < \tau \land O_i \ge \tau]$$
$$\text{False Alarms } (FA) = \sum [F_i \ge \tau \land O_i < \tau], \quad \text{Correct Negatives } (CN) = \sum [F_i < \tau \land O_i < \tau]$$
$$\text{POD} = \frac{H}{H + M}, \quad \text{FAR} = \frac{FA}{H + FA}, \quad \text{CSI} = \frac{H}{H + M + FA}$$
$$\text{Equitable Threat Score (ETS)} = \frac{H - H_r}{H + M + FA - H_r}, \quad H_r = \frac{(H + M)(H + FA)}{N}$$

---

## 5. Date-Clustered Block Bootstrap Formulation

To account for temporal and spatial dependence across the 16 stations on date $d$:
1. Let $D = \{d_1, d_2, \dots, d_{16}\}$ be the set of 16 verification dates.
2. For iteration $b = 1, \dots, 2000$:
   - Sample 16 dates with replacement: $D^{*(b)} = \{d_1^*, \dots, d_{16}^*\}$.
   - Construct bootstrap sample $S^{*(b)} = \bigcup_{d \in D^{*(b)}} \{ \text{all 16 station observations on date } d \}$.
   - Compute metric $\theta^{*(b)}$ (e.g. MAE, $r$).
3. Derive empirical $95\%$ confidence interval as the $2.5\text{th}$ and $97.5\text{th}$ percentiles of $\{\theta^{*(1)}, \dots, \theta^{*(2000)}\}$.

---

## 6. Deterministic D8 Flow Routing & Topographic Wetness Index

On a regular elevation raster $Z(r, c)$:
1. **Flow Direction (D8):** The flow receiver $(nr, nc)$ of cell $(r, c)$ is chosen to maximize downward drop:
   $$S(r, c; \Delta r, \Delta c) = \frac{Z(r, c) - Z(r+\Delta r, c+\Delta c)}{d(\Delta r, \Delta c)}$$
   where $d(\Delta r, \Delta c) = 1,000\text{ m}$ for cardinal neighbors and $1,414.21\text{ m}$ for diagonal neighbors.
2. **Flow Accumulation:** Cells are sorted in descending order of elevation and accumulated recursively:
   $$A(nr, nc) = A(nr, nc) + A(r, c)$$
   where initial $A(r, c) = 1.0\text{ km}^2$.
3. **Specific Catchment Area ($a$):**
   $$a = A \times \frac{10^6\text{ m}^2}{1,000\text{ m}} = A \times 1,000\text{ m} \quad [\text{m}^2/\text{m}]$$
4. **Topographic Wetness Index (TWI):**
   $$\text{TWI} = \ln\left(\frac{a}{\tan \beta_{\max}}\right)$$
   where $\tan \beta_{\max} = \max(S_{\max}, 0.001)$ ensures stability in flat basins.

---

## 7. Dynamic Hydrological Inundation Potential Index (HIPI)

Couples static terrain convergence with dynamic forecast runoff generation:
1. **Effective Overland Runoff Depth ($R$):**
   $$R = C \times P_{24h} \quad [\text{mm}]$$
   where Rational runoff coefficient $C = 0.15 \cdot (1 - f_{\text{builtup}}) + 0.85 \cdot f_{\text{builtup}}$.
2. **Normalized Dimensionless Components:**
   $$\tilde{\text{TWI}} = \frac{\text{TWI} - \text{TWI}_{\min}}{\text{TWI}_{\max} - \text{TWI}_{\min}}$$
   $$\tilde{D} = \text{clip}\left(\frac{D_{\text{sink}}}{D_{\max}}, 0, 1\right), \quad \tilde{R} = \text{clip}\left(\frac{R}{R_{\max}}, 0, 1\right)$$
3. **Composite HIPI Formulation:**
   $$\text{HIPI} = 0.35 \cdot \tilde{\text{TWI}} + 0.25 \cdot \tilde{D} + 0.40 \cdot \tilde{R} \quad \in [0.0, 1.0]$$
   Evaluated strictly as an exploratory indicator without supervised parameter tuning.

