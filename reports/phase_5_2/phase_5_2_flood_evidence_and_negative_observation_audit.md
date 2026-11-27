# Phase 5.2 — Track D: Flood Evidence & Negative Observation Audit

## 1. Executive Summary

This report conducts an exhaustive evidence audit of the reference flood observations, spatial censorship, and negative control sites across the 1,170-cell Bengaluru Urban study domain.

* **Outcome Separation Maintained:**
  * **Outcome A (Confirmed Inundation Only):** $N_{\text{pos}} = 7, N_{\text{neg}} = 5$ (Total $N = 12$).
  * **Outcome B (Combined Impact: Inundation + Waterlogging):** $N_{\text{pos}} = 13, N_{\text{neg}} = 5$ (Total $N = 18$).
* **Domain-Wide Censorship:** **98.13% of the study area (1,148 of 1,170 cells) is unobserved**. Unobserved cells are formally marked as `UNOBSERVED_STATUS_UNKNOWN` and strictly excluded from negative labeling.
* **Negative Site Nature:** All 5 negative reference cells are **high-ground ridge weather stations ($>888\text{ m}$ elevation)** without flood depth sensors. They are formally classified as **`CONDITIONALLY_MONITORED_HIGH_GROUND_PROXIES`**. A dry ridge does not establish that adjacent unmonitored valley bottoms remained dry.
* **Gate B Determination:** **`BLOCKED_BY_DATA_ACCESS` / `INSUFFICIENT_INDEPENDENT_EVIDENCE`**. Supervised machine learning or deep learning flood prediction is strictly blocked.

---

## 2. 7-Class Flood Evidence Taxonomy

Inspection of `flood_validation_reference_matrix.parquet` across all 1,170 cells:

```
+------------------------------------------------+-------------+----------+---------------------------------------------------------+
| Formal Evidence Class                          | Cell Count  | Domain % | Scientific Interpretation & Operational Handling       |
+------------------------------------------------+-------------+----------+---------------------------------------------------------+
| UNOBSERVED_STATUS_UNKNOWN                      |       1,148 |   98.13% | Censored. Never imputed as dry/negative.                |
| CONFIRMED_INUNDATION                           |           7 |    0.60% | Verified deep standing water (>0.5m) entering premises.  |
| REPORTED_WATERLOGGING                          |           6 |    0.51% | Street waterlogging / vehicular disruption (<0.3m).     |
| CONDITIONALLY_MONITORED_HIGH_GROUND_PROXY      |           5 |    0.43% | Elevated AWS/CPCB weather station ridge proxy.           |
| DISRUPTION_WITHOUT_INUNDATION                  |           2 |    0.17% | Traffic congestion / tree fall; no standing water.       |
| RAINFALL_ONLY_NO_FLOOD                         |           1 |    0.09% | Gauge exceeded 64.5mm without surface flooding reports. |
| UNVERIFIED_REPORT                              |           1 |    0.09% | Social media post lacking spatial/temporal coordinates.  |
+------------------------------------------------+-------------+----------+---------------------------------------------------------+
| TOTAL STUDY DOMAIN                             |       1,170 |  100.00% | Full 1-km provisional study grid.                       |
+------------------------------------------------+-------------+----------+---------------------------------------------------------+
```

---

## 3. Station-by-Station Provenance of the Five Negative Reference Sites

| Site ID | Station Name | Operating Agency | Coordinates (Lat, Lon) | Grid ID | Elevation | Sensor Types | Hydrological Context | Verified Dry Valley Truth? |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| **NEG_1** | GKVK University AWS | IMD / UAS Bangalore | $13.076^\circ\text{N}, 77.581^\circ\text{E}$ | `cell_0248` | $928\text{ m}$ | Tipping bucket rain gauge, thermometer, anemometer | High-elevation northern ridge; campus open canopy; rapid natural runoff. | **NO (Ridge Proxy)** |
| **NEG_2** | Bengaluru City Observatory | IMD | $12.969^\circ\text{N}, 77.584^\circ\text{E}$ | `cell_0594` | $921\text{ m}$ | Standard manual rain gauge, barograph, psychrometer | Central ridge crest; well-drained historical observatory grounds. | **NO (Ridge Proxy)** |
| **NEG_3** | HAL Airport AWS | IMD / AAI | $12.950^\circ\text{N}, 77.668^\circ\text{E}$ | `cell_0672` | $888\text{ m}$ | Automated weather station, optical rain sensor | Engineered airport runway plateau; dedicated high-capacity perimeter drainage. | **NO (Ridge Proxy)** |
| **NEG_4** | BTM Layout Station | CPCB / KSPCB | $12.914^\circ\text{N}, 77.610^\circ\text{E}$ | `cell_0812` | $910\text{ m}$ | Continuous ambient air quality monitors (PM2.5, NOx), rain sensor | Rooftop air quality station on local institutional ridge. | **NO (Ridge Proxy)** |
| **NEG_5** | Peenya Industrial Area | CPCB / KSPCB | $13.028^\circ\text{N}, 77.518^\circ\text{E}$ | `cell_0411` | $932\text{ m}$ | Continuous ambient air quality monitor, rain sensor | High plateau northwest industrial zone; bedrock shallow. | **NO (Ridge Proxy)** |

### Scientific Limitations of the Negative Controls
1. **No Inundation Telemetry:** None of the 5 stations possess ultrasonic water-level sensors, pressure transducers, or surface-water contact switches. They record atmospheric precipitation depth, not street flood depth.
2. **Topographical Ridge Bias:** All 5 stations sit atop topographical ridges ($888–932\text{ m}$). Urban flood inundation occurs in valleys, topographic depressions, and valley lake bed corridors ($800–860\text{ m}$, e.g., Bellandur, Varthur, Rainbow Drive).
3. **Absence of Negative Valley Ground Truth:** The repository contains **zero instrumented dry observations in low-lying valley bottoms**. A dry ridge does not prove that an adjacent unmonitored valley was dry.

---

## 4. Evaluation Metrics & Small-Sample Statistical Analysis

The discrimination of the platform's risk indicators was evaluated across the verified cells:

```
Target Outcome   Indicator Name                 Scope             N_total  N_pos  N_neg   ROC-AUC   95% Bootstrap CI   p-value   Classification
-------------------------------------------------------------------------------------------------------------------------------------------------------
Outcome B        dynamic_risk_score             Verified Domain      18      13     5      0.7231    [0.294, 1.000]    0.0867    EXPLORATORY_SMALL_SAMPLE
Outcome B        static_susceptibility_score    Verified Domain      18      13     5      0.7231    [0.294, 1.000]    0.0867    EXPLORATORY_SMALL_SAMPLE
Outcome B        forecast_exposure_score        Verified Domain      18      13     5      0.1769    [0.033, 0.382]    0.9872    EXPLORATORY_SMALL_SAMPLE
Outcome A        dynamic_risk_score             Verified Domain      12       7     5      0.7714    [0.407, 1.000]    0.0745    EXPLORATORY_SMALL_SAMPLE
Outcome A        static_susceptibility_score    Verified Domain      12       7     5      0.7714    [0.407, 1.000]    0.0745    EXPLORATORY_SMALL_SAMPLE
Outcome B        dynamic_risk_buffer_5km        Buffer <= 5km        14      13     1      1.0000    [1.000, 1.000]       NaN    DEGENERATE_SAMPLE_ARTIFACT
Outcome B        dynamic_risk_buffer_10km       Buffer <= 10km       17      13     4      0.8269    [0.375, 1.000]       NaN    EXPLORATORY_SMALL_SAMPLE
```

### Critical Statistical Audit Findings
1. **The 5-km Buffer Degeneracy ($N_{\text{neg}} = 1$):** Within $5\text{ km}$ of positive flood incidents, exactly **one negative station** (`cell_0672`, HAL Airport) was located. In any binary ranking where $N_{\text{neg}} = 1$, if the single negative receives a score lower than the positives, ROC-AUC evaluates mathematically to $1.0000$. This is a **degenerate sample artifact**, not evidence of flawless predictive discrimination.
2. **Mathematical Proof of Static vs Dynamic AUC Identity:** Both static susceptibility and dynamic risk score produced an identical $\text{ROC-AUC} = 0.7231$ (Outcome B) and $0.7714$ (Outcome A).
   - Spearman rank correlation between static and dynamic scores across the 18 cells is $r_s = 0.9979$.
   - The Mann-Whitney $U$ statistic depends exclusively on pairwise rank ordering:
     $$U = \sum_{i=1}^{N_{\text{pos}}} \sum_{j=1}^{N_{\text{neg}}} I(S_{\text{pos}, i} > S_{\text{neg}, j})$$
   - While two positive cells swapped adjacent ranks with each other, every positive score remained strictly higher or lower than the negative scores in the exact same configuration ($U = 47.0$).
   - Rank preservation is a mathematical consequence of small sample size; it does not constitute independent validation of dynamic exposure weighting.
3. **Bootstrap Confidence Interval Width:** The 95% bootstrap CI for Outcome B spans from **$0.294$ to $1.000$** ($p = 0.0867$). Because the confidence interval encompasses $0.50$ (random coin flip) and $p > 0.05$, the null hypothesis of no discriminative ability cannot be rejected at the standard $\alpha = 0.05$ significance level.

