# Phase 3 — Final Technical Report: Exploratory Modeling, Spatial Validation & Retrospective Evaluation

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban Provisional Development Domain (EPSG:6933, 1,170 Cells at 1,000 m Resolution)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Reporting Date:** 2026-11-05  
**Automated Test Suite:** **81 / 81 tests passing (100% pass rate in 17.37 seconds)**  
**Cryptographic Manifest Verification:** **29 / 29 datasets verified valid (100% SHA-256 match)**  
**Formal Phase 3 Entry & Exit Decision:** **DECISION B: Exploratory Modeling Completed; Supervised Flood Prediction BLOCKED.**

---

## 1. Project Objective

The overarching mission of this project is to develop an artificial intelligence and satellite-driven platform for the early detection and forecasting of urban flood risks. Focusing on the rapidly urbanizing megacity of Bengaluru, India, the project aims to integrate multi-sensor satellite observations (digital elevation models, high-resolution land cover, and precipitation) with historical incident telemetry on a standardized, equal-area spatial grid.

Phase 3 marks the culmination of the exploratory data science and validation phase, delivering:
1. Systematic comparison of unsupervised anomaly detection, multivariate statistical distances, and physical multi-criteria models.
2. Empirical spatial dependence estimation and buffered spatial block cross-validation.
3. Retrospective evaluation against verified historical flood incidents.
4. Definitive scientific determination regarding readiness for supervised machine learning.

---

## 2. Data Provenance, Rigor & Limitations

Every dataset in the platform operates under a strict, immutable provenance taxonomy:

| Source Dataset | Canonical Product & Provider | Native Resolution | Spatial Coverage | Cryptographic SHA-256 Hash | Provenance Classification | Scientific Modeling Role |
| :--- | :--- | :---: | :---: | :--- | :---: | :--- |
| **Land Cover** | ESA WorldCover 2021 v200 (VITO / ESA) | 10 m | Tile `N12E075` | `fa1f49618b7636e093c4c9faad37f9e8020a103c800c14c5b364cc9f7c0d2e8e` | `VERIFIED_REAL` | Primary surface imperviousness and canopy fractions. |
| **Terrain (DEM)** | SRTM GL1 30m (NASA / ESA STEP Auxiliary) | 30 m | Mosaicked `N12_N13_E077` | `8f57fe315359218684fc0bf5670fc6dd6311dd65427b3e404b9679f222ee40b3` | `VERIFIED_REAL` | Primary topographic depression and roughness baseline. |
| **Spatial Grid** | Master Equal-Area Grid (EPSG:6933) | 1,000 m | 1,170 cells ($30 \times 39$) | `07c1b48b7fcae8c2ba033783935db0fffa2723bb1d556ad5c3785be8bf2c2fe4` | `VERIFIED_REAL` | Master spatial integration framework. |
| **Precipitation** | NASA GPM IMERG V07B (`precipitationCal`) | ~10 km ($0.1^\circ$) | 17 dates (Aug 25 – Sep 10, 2022) | Staged processing engine | `PARTIALLY_VERIFIED` | Dynamic exposure forcing (qualified; raw NetCDF pending). |
| **Flood Incidents** | Historical Event Register (21 records) | Point coords | 18 geocoded cell-dates | `cb7a16dbb945d8f6385cf55d57b2cb612dbf57e62a5b28fb35905106b8642398` | `VERIFIED_REAL` (Inventory) | Retrospective descriptive probe; NOT training labels. |
| **Hydrology** | MERIT Hydro 90m (`n10e075_upa.tif`) | 90 m | $10^\circ - 15^\circ\text{N}, 75^\circ - 80^\circ\text{E}$ | Pending download | `PENDING_ACQUISITION` | Preserved as `NaN`. Hydrological routing marked unavailable. |
| **Satellite SAR** | Sentinel-1A IW GRDH Simulation | ~10 m | Descending Orbit 165 | Isolated fixtures | `SYNTHETIC_TEST_ONLY` | Strictly excluded from all observational models. |
| **Administrative Boundary** | Official BBMP Ward Polygons | Vector | 198 BBMP Wards | Pending KGIS ingestion | `PENDING_AUTHORITATIVE` | Provisional rectangular development bounding box active. |

---

## 3. Geospatial Data Engineering Methodology

1. **Standardized Global Equal-Area Grid:**
   The domain is anchored to **EPSG:6933 (Equal Earth Cylindrical)** with grid cell coordinates aligned to integer multiples of $1,000\text{ m}$. Geodesic distortion was verified via `pyproj.Geod(ellps="WGS84")`, demonstrating area distortion $< 0.05\%$.
2. **Exact Geometry Masking:**
   Raster zonal statistics were extracted using exact polygon intersection (`all_touched=False`), sampling 14.04 million pixels for WorldCover and 1.26 million pixels for SRTM across the 1,170 cells with zero NoData dropouts.
3. **Spatiotemporal Panel Architecture:**
   The dynamic panel integrates the 1,170 cells across 17 consecutive dates ($1,170 \times 17 = 19,890$ records) with rolling antecedent rainfall lookbacks (3d, 7d, 14d) and an exponential decay Antecedent Precipitation Index ($API_t = P_t + 0.85 API_{t-1}$).

---

## 4. Exploratory Modeling Approaches

Five complementary modeling approaches were developed in [`src/floodrisk/processing/modeling.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/modeling.py):

1. **Isolation Forest ($n=100$ trees, $c=0.05$):** Unsupervised tree ensemble isolating statistical anomalies in 8-dimensional standardized predictor space.
2. **Regularized Mahalanobis Distance:** Numerically stable multivariate distance metric using Ledoit-Wolf shrinkage covariance estimation ($\text{cond}(\Sigma) = 30,627.9$) to handle land cover collinearity:
   $$D_M(x) = \sqrt{(x - \mu)^T \Sigma_{\text{reg}}^{-1} (x - \mu)}$$
3. **Topographic Susceptibility Baseline:** Transparent physical combination of normalized relative depression ($1 - \tilde{e}$) and flat relief ($1 - \tilde{\sigma}_e$).
4. **Dynamic Meteorological Exposure Baseline:** Joint combination of daily rainfall intensity ($P_{\text{daily}} / 150$) and antecedent catchment saturation ($API / 250$).
5. **Multi-Criteria Decision Analysis (MCDA):** Directional multi-criteria model combining terrain susceptibility, landcover runoff potential ($0.75 f_{\text{built}} + 0.25 f_{\text{water}} - 0.20 f_{\text{veg}}$), and dynamic rainfall exposure across Equal, Terrain-Dominant, and Runoff-Dominant configurations.

---

## 5. Spatial Validation & Dependence Analysis

1. **Empirical Variograms:**
   Semi-variogram analysis established that spatial dependence ranges reach **16 km for elevation** and **12 km for built-up density**, proving that spatial autocorrelation operates far beyond immediate cell neighbors.
2. **Buffered Spatial Block Cross-Validation:**
   Partitioned the domain into $5\text{ km} \times 5\text{ km}$ blocks with an enforced **5-km spatial quarantine buffer** (purging an average of $10.9\%$ of domain cells per fold).
3. **Spatial Generalization Stability:**
   The buffered spatial holdout models achieved a **mean Spearman rank stability of $\rho = 0.9351 \pm 0.0498$** (median $\rho = 0.9463$), confirming that model feature representations capture generalized regional relationships rather than memorizing localized spatial neighborhoods.

---

## 6. Retrospective Flood Incident Comparison

The models were retrospectively benchmarked against the 18 verified geocoded flood incident cell-dates across the Late August – Early September 2022 monsoon period:

| Evaluated Model | Mean Incident Rank %ile | Median Incident Rank %ile | Top 10% Incident Capture Rate | Mean Distance to Top 10% Zone (km) |
| :--- | :---: | :---: | :---: | :---: |
| **Isolation Forest** | 43.9% | 46.8% | **0.0%** | 1.98 km |
| **Mahalanobis Distance** | 58.8% | 64.2% | **11.1%** | 2.80 km |
| **Baseline: Terrain Susceptibility** | 66.9% | 68.6% | **0.0%** | 3.65 km |
| **Baseline: Rainfall Exposure** | 74.4% | 80.0% | **11.1%** | 5.78 km |
| **MCDA: Runoff-Dominant** | **80.7%** | **86.5%** | **44.4%** | **1.28 km** |
| **MCDA: Equal-Weight** | **82.0%** | **91.4%** | **50.0%** | **1.13 km** |

---

## 7. Model Stability & Sensitivity Findings

1. **Random Seed Invariance:** Isolation Forest evaluated across random seeds 42, 100, and 2022 demonstrated near-perfect rank stability ($\rho \ge 0.9982$, Top-10% agreement $> 98.5\%$).
2. **Feature Ablation Impact:**
   - Removing land cover caused the greatest disruption ($\rho = 0.7076$, Top-10% Jaccard overlap $0.3708$).
   - Removing terrain caused high disruption ($\rho = 0.7575$, Top-10% Jaccard overlap $0.3933$).
   - Dropping built-up fraction had minimal impact ($\rho = 0.9401$, Jaccard $0.6679$) because cropland fraction ($r = -0.786$) acted as an effective collinear surrogate.
3. **MCDA Weight Sensitivity:** Rank correlations between Equal, Terrain-Dominant, and Runoff-Dominant MCDA schemes exceeded $\rho \ge 0.884$, with a modest mean sensitivity spread of $0.056 \pm 0.041$.

---

## 8. Synthesis & Interpretation: Why Generic Anomaly Detection Fails

The stark contrast between Isolation Forest (0.0% capture rate, mean rank 43.9%) and MCDA (50.0% capture rate, mean rank 82.0%) delivers an invaluable scientific finding:
- **Anomaly Detectors Seek Rareness, Not Hazard:** In an urban megacity, flooded cells (e.g. Mahadevapura, Bellandur, Outer Ring Road) consist of dense commercial built-up cover situated on typical plateau valley elevations. In multivariate feature space, **these cells are frequent, dense, and statistically normal**.
- Isolation Forest flagged peripheral rocky hills with rare shrub combinations as top anomalies.
- **Directional Domain Physics is Mandatory:** Because MCDA explicitly encodes directional physical relationships (low elevation accumulates water, high imperviousness accelerates runoff, high rainfall triggers flooding), it reliably prioritized the historic disaster epicenters.

---

## 9. Limitations & Methodological Constraints

1. **Positive-Unlabeled (PU) Data Ambiguity:** Unreported cells cannot be assumed dry without injecting severe label noise.
2. **Spatial Media Reporting Bias:** $> 70\%$ of historical reports occurred in affluent IT corridors where commuters reported stranded vehicles; peri-urban agricultural ponding was under-reported.
3. **Spatial Scale Dilution ($0.002\text{ km}^2$ vs $1.0\text{ km}^2$):** A 1-km cell dilutes localized underpass bottlenecks.
4. **IMERG Microwave Resolution:** Satellite microwave precipitation ($\sim 10\text{ km}$) cannot resolve micro-scale convective cloudburst cells (1–2 km).

---

## 10. Future Data Requirements & Supervised ML Blueprint

To transition to supervised machine learning in a subsequent phase:
1. **Hydrodynamic Benchmark Footprints:** Construct 1D/2D hydraulic simulation baselines (EPA-SWMM or HEC-RAS) for Bengaluru's Hebbal, KC, and Vrishabhavathi valleys to generate continuous ground-truth flood footprints.
2. **Formal PU Learning Algorithms:** Implement Elkan-Noto or Bagging Positive-Unlabeled classifiers with explicit prior estimation $c = P(s=1|y=1)$.
3. **Spatial Resolution Downscaling:** Transition analysis units from $1\text{ km}^2$ to **$100\text{ m} \times 100\text{ m}$ ($0.01\text{ km}^2$)** grids or sub-catchment Hydrological Response Units (HRUs).
4. **Telemetry Ingestion:** Ingest real-time telemetric rainfall and water-level gauges from the KSNDMC municipal network.

---

## 11. Final Scientific Conclusion & Formal Decision Gate

### Formal Decision:
> **DECISION B: Exploratory Modeling Completed; Supervised Flood Prediction BLOCKED.**

The exploratory modeling pipeline, spatial validation protocols, and multi-criteria risk formulations are scientifically verified, fully reproducible, and rigorously tested (81/81 tests passing). However, because ground-truth labels remain incomplete, unrepresentative, and subject to Positive-Unlabeled ambiguity, supervised machine learning model training is **strictly deferred until systematic hydrodynamic or telemetric ground truth is acquired**.

