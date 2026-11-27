# Phase 3 — Retrospective Flood Incident Comparison Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban Provisional Development Domain (1,170 Cells at 1,000 m Resolution)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Historical Evidence Base:** 21 Provenance-Linked Historical Records (18 Geocoded Cell-Dates)  
**Associated Artifacts:**
- Historical Incident Overlay Map: [`reports/figures/phase3/fig08_incident_overlay_spatial_uncertainty.png`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase3/fig08_incident_overlay_spatial_uncertainty.png)
- Incident Rank Distribution Chart: [`reports/figures/phase3/fig09_incident_rank_distribution.png`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase3/fig09_incident_rank_distribution.png)

---

## 1. Executive Summary

This report evaluates the exploratory models retrospectively against the verified historical flood-event inventory compiled in Phase 2A.4. The evaluation strictly treats reported incidents as **incomplete positive evidence probes** rather than complete ground truth labels, in accordance with the Positive-Unlabeled (PU) framework.

### Central Scientific Finding:
> **Generic unsupervised anomaly detectors (Isolation Forest and Mahalanobis Distance) fail to capture urban flood locations, while domain-guided Multi-Criteria Decision Analysis (MCDA) demonstrates strong retrospective alignment.**

- **Isolation Forest:** Incident-associated cells ranked at an average percentile of only **43.9%** (worse than random expectation of 50.0%), achieving a **0.0% capture rate** within the top-decile anomaly zone.
- **Regularized Mahalanobis Distance:** Incident cells ranked at an average percentile of **58.8%**, achieving an **11.1% top-decile capture rate**.
- **Domain-Guided MCDA (Runoff-Dominant):** Incident cells ranked at an average percentile of **80.7%** (median **86.5%**), successfully capturing **44.4% of reported incidents within the top 10% highest-scoring cells** on the date of occurrence, with a mean proximity of **1.28 km** to peak hazard zones.
- **MCDA (Equal-Weight):** Captured **50.0% of incidents in the top 10% cells** on event dates (mean rank percentile **82.0%**, mean distance to top-decile zone **1.13 km**).

![Historical Incident Overlay and Spatial Uncertainty](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase3/fig08_incident_overlay_spatial_uncertainty.png)

---

## 2. Descriptive Retrospective Evaluation Metrics

The table below contrasts the 6 evaluated models across descriptive retrospective metrics evaluated across all 18 geocoded incident cell-dates:

| Model / Baseline Approach | Mean Incident Rank %ile | Median Incident Rank %ile | Top 5% Capture Rate | Top 10% Capture Rate | Top 20% Capture Rate | Mean Distance to Top-10% Zone (km) | Median Distance to Top-10% Zone (km) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Isolation Forest (Unsupervised)** | 43.9% | 46.8% | 0.0% | **0.0%** | 0.0% | 1.98 km | 2.00 km |
| **Mahalanobis Distance (Regularized)** | 58.8% | 64.2% | 0.0% | **11.1%** | 16.7% | 2.80 km | 3.38 km |
| **Baseline: Terrain Susceptibility** | 66.9% | 68.6% | 0.0% | **0.0%** | 16.7% | 3.65 km | 3.61 km |
| **Baseline: Dynamic Rainfall Exposure** | 74.4% | 80.0% | 5.6% | **11.1%** | 61.1% | 5.78 km | 4.00 km |
| **MCDA: Runoff-Dominant Scheme** | **80.7%** | **86.5%** | **33.3%** | **44.4%** | **66.7%** | **1.28 km** | **1.00 km** |
| **MCDA: Equal-Weight Scheme** | **82.0%** | **91.4%** | **33.3%** | **50.0%** | **66.7%** | **1.13 km** | **0.50 km** |

> [!IMPORTANT]
> **Methodological Disclosure:** These metrics represent retrospective descriptive agreement with reported historical events. They must **never be described as precision, recall, or accuracy**, because the absence of reports does not indicate the absence of flooding, and the sampling of reports was non-random.

![Incident Rank Distribution Across Models](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/figures/phase3/fig09_incident_rank_distribution.png)

---

## 3. Stratified Evaluation by Evidence Category

To examine whether model alignment varies by evidence certainty, results were stratified across the 3 usable geocoded evidence categories:

| Evidence Category | Matched Cell-Dates | MCDA Runoff-Dominant Mean Score [0, 1] | Mahalanobis Normalized Score [0, 1] | Isolation Forest Anomaly Score [0, 1] | Physical Nature of Evidence |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Confirmed Inundation (Cat A)** | 9 | **0.630** | 0.459 | 0.422 | Deep standing water in residential basements / underpasses. |
| **Reported Waterlogging (Cat B)** | 6 | **0.682** | 0.544 | 0.420 | Surface street runoff and vehicular stranding. |
| **Flood Disruption (Cat C)** | 3 | **0.684** | 0.505 | 0.432 | Severe Outer Ring Road arterial transport paralysis. |

### Observation:
Reported waterlogging (Category B) and flood disruption (Category C) exhibit even higher mean MCDA scores ($0.682 - 0.684$) than confirmed inundation ($0.630$). This reflects the reality that major arterial road disruptions occur in highly built-up, impervious valleys (Outer Ring Road, Ecospace, Mahadevapura) where runoff concentration is maximized.

---

## 4. Why Generic Anomaly Detectors Failed: The Physical Insight

A central finding of this research is that **unsupervised anomaly detection is fundamentally misaligned with flood hazard identification**:

1. **Anomaly Detection vs. Hazard Physics:**
   - Isolation Forest and Mahalanobis distance identify points that are *statistically atypical* relative to the multivariate feature distribution of the regional sample.
   - The cells identified as highest anomalies by Isolation Forest were peripheral agricultural tracts with unusual combinations of extreme tree cover, rocky terrain roughness, or rare shrubland compositions.
   - In contrast, the areas that flooded (e.g. Bellandur, Outer Ring Road, Mahadevapura) have high built-up density ($> 75\%$), typical plateau elevations ($860 - 890\text{ m}$), and typical rainfall for that day. In multivariate space, **these cells are common, dense, and statistically normal within the urban domain**, not outliers!
2. **Directionality vs. Distance:**
   - Mahalanobis distance treats deviations symmetrically: an extremely high elevation ridge is treated as equally "anomalous" as an extremely low valley bottom.
   - Flooding is directional: high elevation *sheds* water; low elevation *accumulates* water. High imperviousness *generates* runoff; high vegetation *absorbs* runoff.
3. **The Necessity of Domain Logic:**
   - Because MCDA incorporates directional physical domain logic ($1 - \text{norm}(e)$, $+f_{\text{built}}$, $+P_{\text{daily}}$, $+API$), it correctly prioritizes the joint convergence of heavy rainfall over flat, impervious, low-elevation terrain.

---

## 5. Critical Caveats: Reporting Bias & Scale Dilution

1. **Severe Spatial Reporting Bias:**
   Over $70\%$ of the 18 geocoded incidents occurred along major tech corridors and arterial roads (Mahadevapura, Bellandur, Outer Ring Road, Koramangala). Low-income settlements, informal slum communities, and peri-urban rural valleys undoubtedly experienced waterlogging but lacked institutional media coverage.
2. **Scale Dilution ($0.002\text{ km}^2$ vs $1.0\text{ km}^2$):**
   A flooded underpass or basement represents an area of $\sim 2,000\text{ m}^2$, which is only **$0.2\%$ of a 1-km grid cell** ($1,000,000\text{ m}^2$). The 1-km spatial resolution averages out sub-grid drainage bottlenecks, meaning that even a cell ranked at the 85th percentile may contain both a dry hillside and a flooded underpass.
3. **Temporal Uncertainty:**
   News reports frequently aggregate events by calendar day, obscuring sub-daily convective rainfall bursts (e.g. 50 mm in 45 minutes) that trigger flash ponding before the 24-hour total is recorded.

---

## 6. Scientific Audit Qualifications: Forecasting vs. Retrospective Association

1. **Same-Day Observed Rainfall vs. True Forecasting:**
   The exploratory MCDA and dynamic rainfall baselines evaluated in this retrospective analysis were calculated using **observed daily rainfall depth and antecedent precipitation up to and including the same date as the reported incident**:
   - **What this demonstrates:** Strong retrospective spatial consistency between combined physical susceptibility (low depression + high imperviousness) and observed meteorological forcing during extreme monsoonal storms.
   - **What this does NOT demonstrate:** It does **not demonstrate that the platform could have forecast the flood event before it occurred**. A true predictive forecast requires numerical weather prediction precipitation forecasts issued at lead times (e.g. 6h, 12h, 24h, 48h before the event), which is the exact subject of Phase 4.2.

2. **Precise Evidence Categorization of the 18 Incident-Associated Cell-Dates:**
   The 18 records evaluated are formally designated as **incident-associated cell-dates**, not homogeneous confirmed inundations:
   - **Confirmed Inundation (Category A, 9 records / 50.0%):** Independently verified deep standing water in residential basements, lake cascade overflows, and underpasses (e.g. Bellandur Lake overflow, Rainbow Drive layout, Ecospace underpass).
   - **Reported Waterlogging (Category B, 6 records / 33.3%):** Citizen complaints and journalistic reports of street-level runoff and vehicular ponding causing slowdowns.
   - **Flood-Related Disruption (Category C, 3 records / 16.7%):** Arterial transportation corridor paralysis (e.g. Outer Ring Road tech corridor shutdown), where waterlogging on road links created widespread network failure.

3. **Denominator and Percentile Orientation Verification:**
   - **Percentile Orientation:** Defined strictly such that **$100.0\% = \text{highest risk/anomaly}$** and **$0.0\% = \text{lowest risk/anomaly}$**. A cell in the top 10% corresponds to a rank percentile $\ge 90.0\%$.
   - **Denominator:** Exactly **18 incident-associated cell-dates**.
     - Equal-Weight MCDA captures **9 of 18 (50.0%)** within the daily top 10% risk cells.
     - Runoff-Dominant MCDA captures **8 of 18 (44.4%)** within the daily top 10% risk cells.
     - Isolation Forest captures **0 of 18 (0.0%)** within the daily top 10% anomaly cells.

