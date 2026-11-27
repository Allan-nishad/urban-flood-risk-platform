# Phase 6.1 — Independent Scientific Audit: Audit D (Sentinel-1 SAR Validation)

**Auditor:** Independent Scientific Acceptance Inspector  
**Campaign Baseline:** Phase 6 Master Execution Baseline (`reports/phase_6/`)  
**Audit Target:** Sentinel-1 SAFE Scene Cataloguing, Processing Methodology, 76.9% Sensitivity Claim, and Urban Radar Limitations  
**Classification:** `VERIFIED_WITH_LIMITATIONS`  

---

## 1. Executive Summary & Audit Mandate

In the Phase 6 Executive Report, Workstream 6D reported:
- Three Sentinel-1A SAFE scenes catalogued and audited
- Co-flood peak capture on 2022-09-05 at 00:46:16 UTC (06:16 AM IST)
- C-band SAR backscatter evaluation across 1,170 cells
- Reported sensitivity of **$76.9\%$** on open water flood detection
- Reported specificity of **$85.7\%$** on monitored dry sites

The audit investigated:
1. The exact processing provenance: were raw multi-gigabyte SAFE archives unpacked locally or were previously processed grid features evaluated?
2. The exact mathematical derivation of the $76.9\%$ sensitivity figure.
3. The sample size ($N$) and composition of the reference dataset.
4. Whether permanent perennial water bodies were excluded or conflated with flood expansion.
5. The performance of SAR detection in dense urban street canyons vs. open water/lakes.

---

## 2. Copernicus Sentinel-1A Scene Catalogue & Processing Audit

Inspection of `sar_scene_audit_registry.parquet` confirmed that three Copernicus Data Space Ecosystem (CDSE) Level-1 GRDH products were catalogued:

| Scene Identifier | Role | Acquisition Timestamp | Relative Orbit | Mode / Pol | Mean Inc. Angle |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `S1A_IW_GRDH_..._044512_0550B5_F972` | Pre-Event Dry Baseline | 2022-08-12 00:46:15Z | 165 (Desc) | IW (VV+VH) | 39.2° |
| `S1A_IW_GRDH_..._044862_055C46_89BA` | Co-Event Peak Inundation | 2022-09-05 00:46:16Z | 165 (Desc) | IW (VV+VH) | 39.2° |
| `S1A_IW_GRDH_..._045037_0561F9_E2B1` | Post-Flood Recession | 2022-09-17 00:46:16Z | 165 (Desc) | IW (VV+VH) | 39.2° |

### Processing Methodology Audit:
Inspection of `scripts/phase6/process_sar.py` revealed:
- Stage 6D **did not download, unpack, or execute ESA SNAP / SAR-simulation tools on raw multi-gigabyte `.SAFE` zip archives locally** during Phase 6.
- Instead, Stage 6D utilized the previously calibrated, terrain-corrected $\sigma^0$ features already available in `data/processed/sentinel1_grid_features_bengaluru.parquet` (established during Phase 2a/2b and preserved bit-for-bit).
- Stage 6D classified these features into physical SAR regimes (`CONFIRMED_SPECULAR_WATER_EXPANSION`, `PERENNIAL_WATER_BODY`, `URBAN_DOUBLE_BOUNCE_SUSPECT`, `DRY_UNINUNDATED_TERRAIN`) and cross-validated them against the 20 Stage 6C ground truth cells.
- **Scientific Audit Finding:** The scene metadata and CDSE URN identifiers are authentic, but claims of local raw SAFE pipeline execution must be clarified as *feature re-processing and physical regime classification based on pre-existing calibrated backscatter grids*.

---

## 3. Deconstruction of the 76.9% Sensitivity Claim

Inspection of `sar_ground_truth_cross_validation.parquet` revealed how the $76.9\%$ sensitivity was calculated:
- **Reference Dataset:** The 13 verified positive cells from Stage 6C ($N_{pos} = 13$).
- **Matching Criteria in `process_sar.py`:**
  A positive cell was deemed an agreement ("hit") if its classified SAR regime was:
  - `CONFIRMED_SPECULAR_WATER_EXPANSION` (specular drop), OR
  - `PERENNIAL_WATER_BODY` (low baseline backscatter due to pre-existing lake), OR
  - `URBAN_DOUBLE_BOUNCE_SUSPECT` (backscatter increase due to corner reflection with buildings).

### Detailed Breakdown of the 13 Positive Ground Truth Cells:

| Cell Grid ID | Location Name | Co-Event VV (dB) | Delta VV (dB) | SAR Physical Class | Validation Agreement | Audit Physical Reality |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| `g1000_7487_1631` | Vijaya Bank Layout, Bilekahalli | -10.38 | -0.18 | `CONFIRMED_SPECULAR_WATER_EXPANSION` | `MATCH_SPECULAR_WATER` | Genuine water expansion |
| `g1000_7489_1636` | Koramangala 4th Block (ST Bed) | -9.92 | -0.70 | `CONFIRMED_SPECULAR_WATER_EXPANSION` | `MATCH_SPECULAR_WATER` | Genuine water expansion |
| `g1000_7489_1650` | Manyata Embassy Business Park | -10.54 | -0.74 | `CONFIRMED_SPECULAR_WATER_EXPANSION` | `MATCH_SPECULAR_WATER` | Genuine water expansion |
| `g1000_7495_1633` | Rainbow Drive Layout | -8.55 | -0.05 | `CONFIRMED_SPECULAR_WATER_EXPANSION` | `MATCH_SPECULAR_WATER` | Genuine water expansion |
| `g1000_7495_1635` | RMZ Ecoworld Ingress Road | -8.71 | -0.21 | `CONFIRMED_SPECULAR_WATER_EXPANSION` | `MATCH_SPECULAR_WATER` | Genuine water expansion |
| `g1000_7494_1632` | Kasavanahalli Main Road / Lake | -9.40 | 0.00 | `PERENNIAL_WATER_BODY` | `MATCH_SPECULAR_WATER` | **Conflated with permanent lake** |
| `g1000_7496_1632` | Greenwood Regency / Hadosiddapura | -9.20 | -0.00 | `PERENNIAL_WATER_BODY` | `MATCH_SPECULAR_WATER` | **Conflated with permanent lake** |
| `g1000_7496_1643` | Mahadevapura Lowlands / Flyover | -8.40 | -0.00 | `PERENNIAL_WATER_BODY` | `MATCH_SPECULAR_WATER` | **Conflated with permanent lake** |
| `g1000_7500_1636` | Balagere Road / Varthur Outlet | -9.30 | -0.00 | `PERENNIAL_WATER_BODY` | `MATCH_SPECULAR_WATER` | **Conflated with permanent lake** |
| `g1000_7495_1637` | Divyasree 77 East Villas, Yamalur | -9.28 | +0.02 | `URBAN_DOUBLE_BOUNCE_SUSPECT` | `MATCH_DOUBLE_BOUNCE_INTERFERENCE` | **Dielectric/Double-bounce (not specular)** |
| `g1000_7490_1648` | HBR Layout & Nagavara Lake Edge | -8.70 | 0.00 | `DRY_UNINUNDATED_TERRAIN` | `MISSED_BY_SAR` | Missed (Urban canopy attenuation) |
| `g1000_7497_1641` | Doddanekkundi Industrial Area Ph 2 | -8.50 | 0.00 | `DRY_UNINUNDATED_TERRAIN` | `MISSED_BY_SAR` | Missed (Urban canopy attenuation) |
| `g1000_7498_1639` | Munnekolala & Spice Garden Layout | -9.50 | 0.00 | `DRY_UNINUNDATED_TERRAIN` | `MISSED_BY_SAR` | Missed (Urban canopy attenuation) |

### Mathematical Reconstruction:
- Cells counted as agreement:
  $$\text{Agreement Count} = 5 \text{ (Specular)} + 4 \text{ (Perennial Lake)} + 1 \text{ (Double-bounce)} = 10 \text{ cells}$$
- Reported Sensitivity:
  $$\text{Sensitivity} = \frac{10}{13} = \mathbf{0.7692} \quad (\mathbf{76.9\%})$$

---

## 4. Critical Scientific Findings & Biases

1. **Severe Conflation with Permanent Water Bodies:**
   - In 4 of the 10 "hits" (Kasavanahalli, Greenwood Regency, Mahadevapura, Balagere Road), the low backscatter was present identically in the pre-event baseline ($\Delta\sigma^0 = 0.00\text{ dB}$).
   - These 1-km cells contain permanent water bodies (Kasavanahalli Lake, Kaikondrahalli Lake, Saul Kere, Varthur Lake).
   - SAR detected open water because of the permanent lake, **not** because it detected flood water on the road or buildings.
   - Permanent water bodies were **not** masked out before computing cell-level sensitivity.

2. **Specular Water Expansion Sensitivity Outside Lakes:**
   - If only cells with genuine negative delta backscatter ($\Delta\sigma^0 \le -0.05\text{ dB}$) are counted as flood detections:
     $$\text{True Specular Flood Sensitivity} = \frac{5}{13} = \mathbf{38.5\%}$$

3. **Complete Failure in Dense Urban Canyons:**
   - In 3 out of 13 positive cells (HBR Layout, Doddanekkundi, Munnekolala), SAR backscatter was completely unaffected by flood water ($\Delta\sigma^0 = 0.00\text{ dB}$, classified as dry terrain).
   - Street canyons ($<15\text{m}$ width) flanked by multi-story buildings and shaded by mature tree canopies completely attenuate or scatter the $5.6\text{ cm}$ C-band radar pulses.

4. **False Alarm on Monitored Negative Sluice:**
   - On the 7 monitored negative cells, 6 were classified as dry ($85.7\%$ specificity).
   - However, the 1 failure was `g1000_7489_1642` (Ulsoor Lake Engineered Sluice Outlet), where the monitored dry sluice was flagged as `PERENNIAL_WATER_BODY` because the 1-km cell encompasses Ulsoor Lake!

---

## 5. Audit Classification & Directive

| Audit Dimension | Status | Finding |
| :--- | :--- | :--- |
| **Scene Catalogue** | `VERIFIED` | Authentic Sentinel-1A Level-1 GRDH scenes catalogued from CDSE. |
| **Sensitivity Metric (76.9%)** | `VERIFIED_WITH_LIMITATIONS` | Mathematically reproduced as $10/13$, but depends on including 4 permanent lake cells and 1 double-bounce cell. |
| **True Specular Sensitivity** | `VERIFIED` | Exactly $5/13 = 38.5\%$ on flood water expansion outside permanent lakes. |
| **Urban Radar Limitations** | `VERIFIED` | Documented complete radar blindness in dense urban street canyons. |

**Scientific Acceptance Directive for Phase 7:**  
The platform **must not claim a 76.9% urban flood detection rate**. The report must state that C-band SAR achieves $76.9\%$ sensitivity on open water and lake-margin swales ($N=13$), but drops to $38.5\%$ when excluding permanent water bodies, and suffers from total signal obstruction in dense urban street canyons.

