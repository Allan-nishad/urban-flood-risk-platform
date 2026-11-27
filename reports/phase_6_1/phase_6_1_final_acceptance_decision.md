# Phase 6.1 — Final Scientific Acceptance Decision

**Document Identifier:** `reports/phase_6_1/phase_6_1_final_acceptance_decision.md`  
**Campaign:** Phase 6.1 Independent Acceptance Audit  
**Target Repository:** `urban-flood-risk-platform`  
**Study Domain:** Bengaluru Urban Provisional Study Area ($1,170\text{ km}^2$, 1,170 equal-area 1-km cells in EPSG:6933)  
**Date of Decision:** 2026-11-05  

---

## 1. Final Acceptance Determination

Following the independent, evidence-based scientific and technical audit of all Phase 6 deliverables (Workstreams 6A through 6F), the final acceptance determination is:

$$\mathbf{DECISION:\quad PHASE\_6\_ACCEPTED\_WITH\_DOCUMENTED\_LIMITATIONS}$$

---

## 2. Summary of Acceptance Basis

Phase 6 represents a major scientific and technical milestone in the evolution of the `urban-flood-risk-platform`. It has replaced synthetic or observation-calibrated curves with **authentic numerical weather prediction**, integrated **real telemetric rain-gauge measurements**, compiled **multi-source verified ground truth inundation evidence**, conducted **rigorous physical SAR evaluation**, and established **deterministic topographic routing**:

1. **Software & Infrastructure Verification (100% PASS):**
   - All 101 unit, integration, and platform tests pass with zero errors.
   - All 13 live REST API endpoints return HTTP 200 OK with valid payloads.
   - The interactive surveillance console correctly displays workstream cards, ground truth matrices, and provenance metadata.

2. **Cryptographic Integrity & Baseline Preservation (100% PASS):**
   - All 52 historical baseline datasets across four manifests match their recorded SHA-256 hashes bit-for-bit.
   - All 16 Phase 6 datasets match their recorded SHA-256 hashes in `phase_6_master_manifest.json` bit-for-bit.
   - Zero unregistered or orphaned files exist in processed storage (68 total platform datasets).

3. **Scientific Honesty & Gate Enforcement (100% ENFORCED):**
   - The Supervised ML Flood Prediction Gate remains strictly **`BLOCKED_BY_INSUFFICIENT_EVIDENCE`**.
   - No unobserved cell has been assumed, classified, or imputed as dry.
   - Macro-spatial resolution disclaimers are prominently displayed across API and dashboard layers.

---

## 3. Formally Documented Scientific Boundaries & Limitations

The acceptance of Phase 6 for Phase 7 research validation is conditioned upon strict adherence to the following **five documented scientific boundaries**:

### Limitation 1: Atmospheric Forecast Independence (Native 6-Node Grid)
- **Documented Boundary:** The 198,900 archive rows represent 170 forecast slices across **exactly six native GFS grid nodes** ($27.75\text{ km}$ spacing), not 198,900 independent atmospheric forecasts.
- **Mandate for Phase 7:** Any forecast evaluation, error distribution, or spatial correlation must be evaluated at the **native 6-node resolution** ($1,020$ native forecasts) or grouped by spatial cluster, and never reported as 198,900 independent degrees of freedom.

### Limitation 2: Ground Rainfall Sample Independence & POD = 0.00
- **Documented Boundary:** The 256 paired forecast-observation samples are clustered within only **three GFS grid nodes** across 16 dates. The effective degrees of freedom is at most 48 forecast realizations.
- **Heavy Rainfall POD:** The Probability of Detection at heavy rainfall ($\ge 64.5\text{ mm}$) is **$0.00$** due to spatial scale mismatch: GFS $0.25^\circ \approx 750\text{ km}^2$ grid averaging smooths localized convective storm cells down to $\le 38.7\text{ mm}$ grid means.
- **Mandate for Phase 7:** Continuous skill metrics ($\text{MAE} = 18.64\text{ mm}$, $\text{RMSE} = 33.19\text{ mm}$) must always be reported alongside cluster-level confidence intervals and the physical explanation of the convective scale mismatch.

### Limitation 3: Observational Domain Censorship & Supervised ML Block
- **Documented Boundary:** The study domain is **$98.29\%$ unobserved** ($1,150$ out of $1,170$ cells). Only 20 cells have verified ground truth evidence (13 positive, 7 monitored negative).
- **Mandate for Phase 7:** **Supervised machine learning flood prediction remains strictly prohibited.** Training supervised models on $N=20$ samples or assuming unobserved cells are dry produces severe spatial bias and invalid predictions.

### Limitation 4: C-Band Radar Physical Sensitivity & Urban Blindness
- **Documented Boundary:** The reported sensitivity of $76.9\%$ ($10/13$) is an open-water / lake-margin metric that includes 4 cells with pre-existing permanent lakes ($\Delta\sigma^0 = 0.0\text{ dB}$) and 1 cell with double-bounce increase. True specular flood expansion outside permanent lakes was observed in only **$5$ of $13$ cells ($38.5\%$)**. In dense urban street canyons, SAR suffers from complete signal attenuation and missed detections.
- **Mandate for Phase 7:** C-band SAR backscatter must not be claimed as an operational urban street flood detector; its role is strictly as an open-water retention basin and lake overflow monitor.

### Limitation 5: Hydrological Discrimination at 1-km Scale ($\text{ROC-AUC} = 0.560$)
- **Documented Boundary:** The deterministic Hydrological Inundation Potential Index (HIPI) achieved $\text{ROC-AUC} = 0.560$ on ground truth ($N=20$), which is **statistically indistinguishable from random chance ($0.500$)**.
- **Physical Reason:** Urban flooding on September 4–5, 2022 was driven by sub-grid hydrodynamic features ($1\text{m} - 2\text{m}$ drain culvert silting, compound walls, underpass dips) that are smoothed away on a 1-km elevation grid.
- **Mandate for Phase 7:** HIPI must be presented strictly as an exploratory macro-topographic routing index, not as an operational predictive flood model. Operational urban prediction requires high-resolution ($\le 10\text{m}$) urban hydrodynamic modeling.

---

## 4. Phase 7 Authorization & Recommendations

With the formal recording of these documented limitations, Phase 6 is accepted. The project is scientifically authorized to proceed into:

### **Phase 7 — Final Research Synthesis, Hydrodynamic Modeling & Operational Validation**

**Recommended Priority Initiatives for Phase 7:**
1. **High-Resolution Sub-Grid Hydrodynamic Modeling:** Transition from coarse 1-km macro-topography to fine-scale ($\le 10\text{m}$) DEM routing with explicit representation of Rajakaluves (stormwater canals), road embankments, and culvert capacities.
2. **Convective Precipitation Downscaling:** Couple regional NWP forecasts (NOAA GFS / ECMWF) with statistical or dynamical downscaling to capture localized convective rainfall extremes ($>100\text{ mm}$) that coarse grids miss.
3. **Multi-Sensor Water Body Disambiguation:** Implement automated masking of permanent water bodies to separate pre-existing lakes from genuine flood inundation in satellite remote sensing.
4. **Independent Flood Label Expansion:** Systematically integrate crowdsourced civic tickets (BBMP Sahaya) and drone surveys with rigorous spatial verification to expand domain observational coverage beyond $1.71\%$.

---

**Signed and Formally Accepted:**  
*Independent Scientific Acceptance Inspector*  
*Urban Flood Risk Intelligence Platform Project*

