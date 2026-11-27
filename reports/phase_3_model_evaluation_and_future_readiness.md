# Phase 3 — Model Evaluation, Limitations & Future Readiness Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban Provisional Development Domain (1,170 Cells at 1,000 m Resolution)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Associated Artifact:** [`reports/figures/phase3/fig10_model_comparison_summary.png`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase3/fig10_model_comparison_summary.png)

---

## 1. Executive Summary & Comparative Synthesis

Phase 3 designed, implemented, and systematically evaluated five distinct exploratory modeling methodologies across the 1,170-cell spatiotemporal panel ($19,890$ cell-dates). The approaches span unsupervised statistical outlier detectors, transparent single-domain physical baselines, and multi-criteria spatial decision models.

### Comparative Synthesis Matrix

| Model / Modeling Paradigm | Primary Inputs | Core Mathematical Formulation | Spatial Rank Stability ($\rho$) | Top-10% Incident Capture Rate | Directional Flood Physics | Interpretability | Operational Recommendation |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Isolation Forest** | 8 features (terrain, landcover, rain) | Ensemble random axis-aligned partition tree path lengths | 0.9351 | **0.0%** | ❌ None (symmetrical outlier detection) | Low | **NOT Recommended for Flood Risk.** Identifies rare rural landcover, misses urban floods. |
| **Mahalanobis Distance** | 8 features (standardized) | $D_M = \sqrt{(x - \mu)^T \Sigma_{\text{reg}}^{-1} (x - \mu)}$ via Ledoit-Wolf shrinkage | 0.9410 | **11.1%** | ❌ None (multivariate distance from centroid) | Moderate | **Spatial Prioritization Only.** Useful for multivariate data QA, but unaligned with flood hazard. |
| **Terrain Susceptibility Baseline** | SRTM 30m DEM (Mean, Std) | $0.60(1 - \tilde{e}) + 0.40(1 - \tilde{\sigma}_e)$ (Relative depression & flatness) | **1.0000** (Static) | 0.0% (alone) | ✅ Yes (topographic accumulation) | High | **Recommended Component.** Static baseline for identifying natural lacustrine depressions. |
| **Rainfall Exposure Baseline** | GPM IMERG (Daily depth, API) | $0.55 \tilde{P} + 0.45 \tilde{API}$ (Storm intensity & soil memory) | N/A (Temporal) | 11.1% (alone) | ✅ Yes (meteorological forcing) | High | **Recommended Component.** Dynamic driver of convective flood event timing. |
| **MCDA (Runoff-Dominant)** | Multimodal (Terrain, LC, Rain) | $0.20 S_{\text{terrain}} + 0.40 S_{\text{landcover}} + 0.40 S_{\text{rainfall}}$ | **0.9520** | **44.4%** | ✅ Yes (joint convergence of rain, imperviousness, depression) | High | **STRONGLY RECOMMENDED.** Best overall balance of stability, physics, and retrospective capture. |

![Multi-Model Scientific Evaluation Matrix](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase3/fig10_model_comparison_summary.png)

---

## 2. Failure-Case Analysis

To understand the boundary conditions of each modeling approach, explicit failure cases were investigated:

### Failure Case 1: The "False Outlier" Trap (Isolation Forest)
- **Observation:** Isolation Forest assigned its highest anomaly scores (98th - 100th percentiles) to peripheral rural cells in northwestern Bengaluru characterized by high rocky elevation variance (`elevation_std_m` $> 15\text{ m}$) and sparse shrubland. None of these cells experienced flooding.
- **Root Cause:** Isolation Forest partitions feature space randomly. Cells with rare combinations of features require very few partitions to isolate, receiving high anomaly scores regardless of whether the physical combination is dangerous or beneficial.
- **Scientific Lesson:** Extreme multivariate statistical atypicality does not equal flood hazard.

### Failure Case 2: The Symmetrical Distance Blindspot (Mahalanobis Distance)
- **Observation:** A high ridge crest at $940\text{ m}$ elevation and a deep valley bottom at $760\text{ m}$ elevation with identical distance from the mean $\mu_e = 885\text{ m}$ receive identical Mahalanobis distance contributions.
- **Root Cause:** Mahalanobis distance is a quadratic norm that measures distance without direction.
- **Scientific Lesson:** Hydrological hazard is fundamentally directional; water accumulates in low depressions, not on high ridges.

### Failure Case 3: The Urban Rain Trap (Rainfall-Only Baseline)
- **Observation:** On 2022-09-05, rainfall was intense across the entire domain ($85 - 151\text{ mm/day}$). Relying on rainfall exposure alone flagged $61.1\%$ of the entire $1,170\text{ km}^2$ study domain as high risk, producing massive spatial over-prediction.
- **Root Cause:** Rainfall is a regional meteorological forcing that covers hundreds of square kilometres.
- **Scientific Lesson:** Rainfall triggers flood events in time, but land cover imperviousness and local topography dictate where floods materialize in space.

---

## 3. Why Supervised Binary Classification Remains Blocked

The formal Phase 3 entry decision remains **Decision B (Supervised Flood Prediction BLOCKED)**. The methodological barriers are insurmountable with the current data foundation:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               THE FATAL OBSTACLES TO SUPERVISED BINARY CLASSIFICATION                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. The Positive-Unlabeled (PU) Problem:                                                │
│    - 18 positive cell-dates out of 19,890 panel rows (0.0905%).                       │
│    - The remaining 19,872 cell-dates are UNREPORTED, not proven dry.                   │
│    - Standard classifiers (Random Forest, XGBoost, MLP) require true negative labels.  │
│    - Forcing y = 0 onto unreported cells introduces massive false-negative noise.      │
│                                                                                        │
│ 2. Severe Spatial Media Reporting Bias:                                                │
│    - > 70% of reports originate from affluent IT corridors (Bellandur, ORR).           │
│    - Peri-urban valleys and low-income slum settlements had unrecorded ponding.        │
│    - A supervised model will optimize for predicting media activity, not flood water. │
│                                                                                        │
│ 3. 500:1 Spatial Scale Dilution:                                                       │
│    - Flooded underpass = 0.002 km² (20 m x 100 m).                                     │
│    - Analysis Grid Cell = 1.000 km² (1,000 m x 1,000 m).                               │
│    - Labeling a 1 km² cell as y = 1 asserts that 1,000,000 m² was inundated.          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Future Supervised-Learning Blueprint & Unblocking Requirements

To transition the platform to supervised machine learning in a future research phase, the following prerequisites must be fulfilled:

### 1. Systematic Flood Ground Truth via Hydrodynamic Modeling
Rather than relying on citizen tweets and news articles, generate authoritative physical inundation footprints using calibrated hydrodynamic simulations:
- Construct 1D/2D coupled hydraulic models (e.g. EPA-SWMM or HEC-RAS 2D) for Bengaluru's three major valley catchments:
  1. **Vrishabhavathi Valley Catchment** (Western drainage)
  2. **Koramangala-Challaghatta (KC) Valley Catchment** (Central/Eastern tech corridor)
  3. **Hebbal Valley Catchment** (Northern drainage)
- Calibrate models against BBMP automated stormwater drain (SWD) water level sensors.
- Rasterize simulated water depth onto the 1-km grid ($> 0.3\text{ m}$ depth over $> 5\%$ cell area = flood instance).

### 2. Formal Positive-Unlabeled (PU) Learning Formulation
If complete negative surveys remain unavailable, deploy formal PU learning algorithms:
- **Elkan-Noto Formulation:** Estimate the label frequency $c = P(s=1 | y=1)$ from a representative validation subset, and re-weight unlabelled instances via $P(y=1 | x) = P(s=1 | x) / c$.
- **Bagging PU:** Train an ensemble of classifiers where each base estimator draws all 18 positive instances and a balanced random subsample of unlabelled instances, aggregating probabilities across the ensemble.

### 3. Spatial Resolution Downscaling
Downscale the analysis framework from $1,000\text{ m}$ ($1\text{ km}^2$) to **$100\text{ m} \times 100\text{ m}$ ($0.01\text{ km}^2$)** or sub-basin hydrological response units (HRUs). This eliminates the 500:1 scale dilution, aligning the unit of analysis with urban road underpasses and lake cascade overflow channels.

### 4. Integration of In-Situ Sensor Telemetry
Ingest real-time telemetric precipitation and water-level gauges from the Karnataka State Natural Disaster Monitoring Centre (KSNDMC) mesh across Bengaluru, resolving the spatial coarse resolution ($\sim 10\text{ km}$) of satellite microwave retrievals.

