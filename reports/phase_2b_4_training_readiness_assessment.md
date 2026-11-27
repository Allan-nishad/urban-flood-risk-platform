# Phase 2B.4 — Training Dataset Readiness & Label Audit Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban Provisional Development Domain (1,170 Cells at 1-km Resolution)  
**Execution Environment:** Python 3.11.15 (`.venv`)  
**Target Assessment:** Scientific and Statistical Viability of Supervised Machine Learning Model Training  

---

## 1. Executive Summary & Formal Readiness Verdict

This report delivers the comprehensive label audit, leakage pathway evaluation, and training readiness assessment required before entering Phase 3. 

### Formal Entry Decision:
> **DECISION B: Limited Exploratory Modeling Permitted; Supervised Binary Classification / Supervised Flood Prediction BLOCKED.**

### Justification:
While the data engineering pipeline successfully harmonizes multi-source geospatial data onto a regular 1-km equal-area grid (EPSG:6933), the current historical flood label inventory ($N = 21$ records, 18 geocoded incident cell-dates out of 19,890 cell-days) is **statistically insufficient and methodologically unsuited for supervised machine learning training**. Treating unobserved cells as "negative" (dry) instances would introduce catastrophic label noise, and random validation splits would suffer from severe spatial and temporal data leakage.

Supervised binary prediction is strictly blocked until:
1. Systematic, authoritative flood hazard labels (e.g. BBMP GIS ground surveys or hydrodynamic modeling benchmarks) are integrated.
2. Official administrative boundaries replace the provisional rectangular domain.
3. Upstream hydrological contributing area (MERIT Hydro UPA) is acquired.

---

## 2. Historical Incident Inventory & Label Audit

The historical flood inventory compiled in Phase 2A.4 and integrated in Phase 2B.1 comprises 21 records across the Late August – Early September 2022 monsoon period:

### Breakdown by Evidence Category ($N = 21$)

| Evidence Category | Record Count | Spatial Status | Grid Assignment | Valid for Supervised ML Training? | Methodological Rationale |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Confirmed Inundation** | 9 | Exact coordinates | 9 distinct cell-dates | ❌ No (extreme positive sparsity) | Ground-verified deep standing water, but localized to sub-hectare underpasses / basements. |
| **Reported Waterlogging** | 6 | Approximate street | 6 distinct cell-dates | ❌ No (high spatial uncertainty) | Citizen/news reports of road runoff; transient ponding rather than structural inundation. |
| **Flood Disruption** | 3 | Arterial road corridor | 3 distinct cell-dates | ❌ No (spatial corridor ambiguity) | Outer Ring Road traffic collapse; reported as road segment rather than spatial polygon. |
| **Rainfall-Only** | 2 | Rain gauge station | N/A (unmapped) | ❌ No (meteorological only) | High precipitation reported without explicit inundation evidence. |
| **Unverified Report** | 1 | City-wide text | N/A (unmapped) | ❌ No (unverified) | Narrative mention lacking geographic coordinates or photographic evidence. |
| **Total Geocoded Incidents** | **18** | Mapped to grid | **18 cell-dates** | ❌ **UNSUITABLE FOR SUPERVISED ML** | **18 positive instances out of 19,890 panel rows (0.0905%)** |

---

## 3. Methodological Obstacles to Supervised ML

### 1. The Positive-Unlabeled (PU) Problem & Absence of Verified Negatives
In the $1,170 \times 17 = 19,890$ spatiotemporal panel, exactly 18 cell-dates contain reported flood incidents. The remaining **19,872 cell-dates have NO reported incidents**.
- **The Fatal Assumption:** In standard supervised classification (e.g. Random Forest, XGBoost, Logistic Regression), unlabelled cells are routinely assigned $y = 0$ ("No Flood").
- **Scientific Reality:** A cell without a news or Twitter report is **not proven dry**. It may have experienced 0.5 m of waterlogging that went unreported due to low population density, lack of media presence, nighttime occurrence, or absence of critical arterial infrastructure.
- **Consequence:** Imposing $y = 0$ on unobserved cells injects massive false-negative label noise, penalizing models that correctly identify high-risk physical conditions in unmonitored peri-urban zones.

### 2. Severe Spatial Reporting Bias
Historical reports are heavily biased toward:
- **Affluent Tech Corridors:** Mahadevapura, Bellandur, Outer Ring Road, and Whitefield represent $> 70\%$ of all geocoded reports.
- **Major Arterial Roads & Underpasses:** Locations where traffic delays immediately prompt social media complaints and municipal complaints.
- **Reporting Blindspots:** Low-income settlements, open agricultural peri-urban valleys, and slum clusters in northern and western Bengaluru had equal or greater surface ponding but negligible formal media coverage. A model trained on these labels will learn to predict *media attention and affluent commuter density*, not *physical flood physics*.

### 3. Severe Spatial Scale Mismatch
- **Observation Scale:** A flooded underpass (e.g. Ecospace ORR) occupies an area of approximately $20\text{ m} \times 100\text{ m} = 0.002\text{ km}^2$.
- **Grid Cell Scale:** The master equal-area grid operates at $1,000\text{ m} \times 1,000\text{ m} = 1.0\text{ km}^2$ ($1,000,000\text{ m}^2$).
- **Scale Ratio:** The reported incident occupies **0.2%** of the grid cell area. Labeling the entire $1\text{ km}^2$ cell as $y = 1$ asserts that the entire square kilometre was flooded, introducing severe spatial over-generalization.

---

## 4. Leakage Pathway Audit

Three distinct data leakage pathways exist that would artificially inflate validation performance if naive machine learning pipelines were applied:

### Pathway 1: Spatial Autocorrelation Leakage (Moran's $I > 0.76$)
- **Mechanism:** As established in Phase 2B.2, elevation ($I = 0.942, z = 62.79$) and built-up fraction ($I = 0.765, z = 53.59$) are strongly autocorrelated across adjacent cells.
- **The Risk:** If a standard random k-fold train/test split is used, cell $i$ will be in the training set while its immediate neighbor $i+1$ (less than 1 km away, sharing 98% identical elevation and land cover) will be in the test set. The model will memorize local geography rather than generalizing flood susceptibility.
- **Mandatory Prevention:** Spatial block cross-validation with spatial exclusion buffers $\ge 5\text{ km}$.

### Pathway 2: Temporal Lookahead & Overlapping Memory Leakage
- **Mechanism:** Antecedent rainfall features (`precip_antecedent_3d_mm`, `precip_antecedent_7d_mm`, `precip_api_decay_mm`) integrate rainfall from preceding days.
- **The Risk:** If cell-date $(i, t)$ is in the training set and $(i, t-1)$ or $(i, t+1)$ is in the test set, the rolling accumulation windows share common precipitation observations.
- **Mandatory Prevention:** Temporal block cross-validation (e.g. train on August 2022, test on September 2022) with lookback buffer purging.

### Pathway 3: Threshold Circularity & Tuning Leakage
- **Mechanism:** Using the 18 historical incident locations to optimize risk score weights or classification thresholds, and subsequently evaluating model accuracy on those exact same 18 points.
- **Mandatory Prevention:** Explicitly designating the 18 points as an exploratory validation probe, never as training targets.

---

## 5. Comprehensive 11-Dimension Training Readiness Matrix

| # | Readiness Dimension | Evaluated Status | Grade | Detailed Justification & Blocking Rationale |
| :-: | :--- | :--- | :---: | :--- |
| **1** | Spatial Coverage & Domain Definition | Provisional $30 \times 39$ Grid (1,170 cells) | **AMBER** | Master equal-area grid EPSG:6933 is functional, but official BBMP administrative boundary remains `pending_authoritative_boundary`. |
| **2** | Spatial Resolution & Grid Standard | 1,000 m Equal-Area ($1\text{ km}^2$) | **GREEN** | Fully compliant with EPSG:6933 standard; area distortion $< 0.05\%$. |
| **3** | Real Observational Data Integration | SRTM DEM (100%), ESA WorldCover (100%) | **GREEN** | Authentic raster tiles acquired, mosaicked, clipped, and zonally extracted with exact geometry masking. |
| **4** | Upstream Hydrology Availability | MERIT Hydro UPA 90m (0.0%) | **RED** | Pending user authentication at Yamazaki Lab; preserved cleanly as `NaN`. Without upstream accumulation, valley drainage networks cannot be modeled. |
| **5** | SAR Observational Validation | Sentinel-1A Synthetic Test Only | **RED** | Phase 2A.5.1 Audit Decision C: SAR rasters are simulation fixtures. Real satellite flood extents are NOT established. |
| **6** | Target Label Completeness | 18 Geocoded Cell-Dates (0.0905%) | **RED** | Extreme positive sparsity; completely insufficient for supervised parameter estimation. |
| **7** | Target Label Representativeness | High Media / Tech Corridor Bias | **RED** | Severe spatial sampling bias toward affluent urban corridors; rural and slum inundations unrecorded. |
| **8** | Negative Label Reliability | 19,872 Unlabelled Cell-Dates | **RED** | Positive-Unlabeled (PU) ambiguity. Unreported cells cannot be assumed dry without introducing catastrophic false-negative noise. |
| **9** | Spatial / Temporal Leakage Protection | Protocols Defined, Not Yet Enforced | **AMBER** | Moran's $I = 0.942$; spatial block cross-validation must be architected before any model fitting. |
| **10** | Multicollinearity & Predictor Stability | VIF Analyzed (Built-up VIF = 7.22) | **GREEN** | VIF and correlation matrices documented; landcover collinearity diagnosed and mitigation strategy established. |
| **11** | Pipeline Reproducibility & Testing | 68 Automated Tests Passing (100%) | **GREEN** | Verified Python 3.11 environment, strict typing, schema enforcement, and zero-fabrication logging. |

---

## 6. Phase 3 Permitted vs. Prohibited Scope Boundaries

To prevent scientific invalidity and maintain strict research integrity, the following boundaries govern Phase 3 activities:

### ⛔ PROHIBITED IN PHASE 3 (Until Labels & Hydrology are Acquired):
1. **NO Supervised Binary Classification:** Training supervised classifiers (Logistic Regression, Random Forest, XGBoost, LightGBM, Multi-Layer Perceptrons) that treat unreported cells as $y = 0$.
2. **NO Synthetic Label Generation:** Creating artificial pseudo-flood labels from precipitation thresholds or SAR simulation rasters to simulate supervised training.
3. **NO Random Cross-Validation:** Performing un-buffered random k-fold cross-validation on spatial grid cells.

### ✅ PERMITTED & RECOMMENDED IN PHASE 3:
1. **Unsupervised Anomaly Detection:** Spatial isolation forests, one-class SVMs, or Mahalanobis distance scoring to detect extreme multivariate physical anomalies without binary labels.
2. **Multi-Criteria Decision Analysis (MCDA):** Refining un-trained physics-based susceptibility indices (Analytical Hierarchy Process / fuzzy logic) benchmarked against hydrological principles.
3. **PU Learning / Positive-Unlabeled Formulations:** Advanced semi-supervised algorithms (e.g. Elkan-Noto, bagging PU) that formally treat unlabelled cells as containing unknown mixtures of wet and dry conditions.
4. **Hydrological Acquisition & Upstream Routing:** Integrating official MERIT Hydro UPA rasters to unlock hydrological stream power index (SPI) and topographic wetness index (TWI).
5. **Authoritative Administrative Boundary Ingestion:** Replacing provisional bounding boxes with official BBMP ward boundaries.

