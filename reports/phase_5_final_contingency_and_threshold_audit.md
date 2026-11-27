# Phase 5 Final — Rainfall Threshold & Contingency Metrics Integrity Audit Report

**Milestone:** Phase 5 Final Acceptance Campaign — Step 7: Threshold Derivation & Contingency Table Audit  
**Author:** Antigravity Autonomous Agent (Google DeepMind Advanced Agentic Coding)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Study Domain:** Bengaluru Urban provisional study domain (1,170 equal-area 1-km cells, EPSG:6933, bounded provisionally by $77.45^\circ - 77.75^\circ\text{E}, 12.85^\circ - 13.15^\circ\text{N}$)  
**Deliverable Parquet:** [`data/processed/phase5_final/forecast_verification/forecast_verification_metrics_by_lead_time.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/phase5_final/forecast_verification/forecast_verification_metrics_by_lead_time.parquet) (15 rows, 26 columns)  

---

## 1. Executive Summary & Audit Scope

Workstream 5C requires an exhaustive audit of all categorical verification metrics used to assess the platform's early warning capabilities. In automated meteorological evaluation, naive statistical software often outputs numbers (such as $HSS = 0.0$ or $TSS = \text{NaN}$) that conceal degenerate data distributions, division by zero, or severe model failure.

This report resolves three critical questions:
1. What is the exact physical and institutional derivation of the 6h, 12h, and 24h rainfall thresholds?
2. Why did 6h Light Rain produce $HSS = 0.0000$ and $TSS = \text{NaN}$?
3. What is the mathematical and meteorological cause of negative Heidke Skill Scores ($HSS < 0$) at 48h and 72h lead times?

---

## 2. Origin & Derivation of Rainfall Thresholds

| Accumulation Duration | Threshold Name | Threshold Value ($\text{mm}$) | Derivation & Institutional Authority | Operational Hydrological Impact |
| :---: | :---: | :---: | :--- | :--- |
| **24 Hours** | Light Rain | **$2.5\text{ mm}$** | **Official IMD Statutory Definition** ($2.5\text{ mm}$ separates trace rain from measurable rain). | Minor wetting; negligible runoff. |
| **24 Hours** | Moderate Rain | **$15.6\text{ mm}$** | **Official IMD Statutory Definition** (Moderate: $15.6\text{ to } 64.4\text{ mm/day}$). | Drainage conduit filling; roadside puddling. |
| **24 Hours** | Heavy Rain | **$64.5\text{ mm}$** | **Official IMD Statutory Definition** (Heavy: $\ge 64.5\text{ mm/day}$). | Pluvial flash flooding; lake chain overflow. |
| **12 Hours** | Light Rain Equiv. | **$1.6\text{ mm}$** | *Derived Diurnal Disaggregation* ($\sim 65\%$ of daily rain in convective afternoon window). | Initial ground saturation. |
| **12 Hours** | Moderate Rain Equiv. | **$10.1\text{ mm}$** | *Derived Diurnal Disaggregation* ($15.6\text{ mm} \times 0.65 = 10.1\text{ mm}$). | SWD capacity thresholds tested. |
| **12 Hours** | Heavy Rain Equiv. | **$41.9\text{ mm}$** | *Derived Diurnal Disaggregation* ($64.5\text{ mm} \times 0.65 = 41.9\text{ mm}$). | Severe street inundation risk. |
| **6 Hours** | Light Rain Equiv. | **$1.0\text{ mm}$** | *Derived Diurnal Disaggregation* ($\sim 40\%$ of daily rain in peak downpour window). | Brief shower; localized dampness. |
| **6 Hours** | Moderate Rain Equiv. | **$6.2\text{ mm}$** | *Derived Diurnal Disaggregation* ($15.6\text{ mm} \times 0.40 = 6.2\text{ mm}$). | Gutter overflow; road surface sheeting. |
| **6 Hours** | Heavy Rain Equiv. | **$25.8\text{ mm}$** | *Derived Diurnal Disaggregation* ($64.5\text{ mm} \times 0.40 = 25.8\text{ mm}$). | Flash flooding in low-lying underpasses. |

> **Scientific Disclosure:** The $6\text{h}$ and $12\text{h}$ thresholds are **derived physical disaggregations**, NOT statutory IMD government categories. Only the $24\text{h}$ thresholds ($2.5, 15.6, 64.5\text{ mm}$) represent official IMD standards.

---

## 3. Full Contingency Tables & Categorical Skill Metrics

The audited 2x2 contingency tables and WMO categorical skill metrics across both cell-replicated ($N_{\text{raw}}$) and anchor-level ($N_{\text{eff}}$) scales are presented below:

| Lead Time | Interval | Threshold | Derivation Type | Hits ($H$) | False Alarms ($F$) | Misses ($M$) | Correct Neg ($C$) | POD | FAR | CSI | HSS | TSS | Contingency Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **6h** | 6h | 1.0 mm | Derived | 35,741 | 0 | 4,039 | 0 | 0.8985 | 0.0000 | 0.8985 | **0.0000** | **NaN** | `DEGENERATE_ZERO_NEGATIVES` |
| **6h** | 6h | 6.2 mm | Derived | 13,241 | 2,353 | 9,223 | 14,963 | 0.5894 | 0.1509 | 0.5335 | **+0.4338** | +0.4535 | `VALID_NON_DEGENERATE` |
| **6h** | 6h | 25.8 mm | Derived | 1,893 | 344 | 4,269 | 33,274 | 0.3072 | 0.1538 | 0.2910 | **+0.4014** | +0.2970 | `VALID_NON_DEGENERATE` |
| **12h** | 12h | 1.6 mm | Derived | 35,214 | 0 | 3,396 | 0 | 0.9120 | 0.0000 | 0.9120 | **0.0000** | **NaN** | `DEGENERATE_ZERO_NEGATIVES` |
| **12h** | 12h | 10.1 mm | Derived | 13,821 | 5,260 | 8,253 | 11,276 | 0.6261 | 0.2757 | 0.5056 | **+0.3012** | +0.3080 | `VALID_NON_DEGENERATE` |
| **12h** | 12h | 41.9 mm | Derived | 1,166 | 1,166 | 4,996 | 31,282 | 0.1892 | 0.5000 | 0.1591 | **+0.2049** | +0.1533 | `VALID_NON_DEGENERATE` |
| **24h** | 24h | 2.5 mm | Statutory | 33,856 | 0 | 3,584 | 0 | 0.9043 | 0.0000 | 0.9043 | **0.0000** | **NaN** | `DEGENERATE_ZERO_NEGATIVES` |
| **24h** | 24h | 15.6 mm | Statutory | 15,103 | 8,784 | 6,581 | 6,972 | 0.6965 | 0.3677 | 0.4957 | **+0.1417** | +0.1390 | `VALID_NON_DEGENERATE` |
| **24h** | 24h | 64.5 mm | Statutory | 2,259 | 2,256 | 3,903 | 29,022 | 0.3666 | 0.4997 | 0.2684 | **+0.3299** | +0.2945 | `VALID_NON_DEGENERATE` |
| **48h** | 24h | 2.5 mm | Statutory | 30,292 | 0 | 4,808 | 0 | 0.8630 | 0.0000 | 0.8630 | **0.0000** | **NaN** | `DEGENERATE_ZERO_NEGATIVES` |
| **48h** | 24h | 15.6 mm | Statutory | 13,795 | 8,529 | 5,549 | 7,227 | 0.7131 | 0.3821 | 0.4949 | **+0.1749** | +0.1718 | `VALID_NON_DEGENERATE` |
| **48h** | 24h | 64.5 mm | Statutory | 2 | 3,633 | 6,160 | 25,305 | 0.0003 | 0.9994 | 0.0002 | **-0.1493** | -0.1252 | `VALID_NON_DEGENERATE` |
| **72h** | 24h | 2.5 mm | Statutory | 27,023 | 0 | 5,737 | 0 | 0.8249 | 0.0000 | 0.8249 | **0.0000** | **NaN** | `DEGENERATE_ZERO_NEGATIVES` |
| **72h** | 24h | 15.6 mm | Statutory | 11,008 | 9,504 | 8,336 | 3,912 | 0.5691 | 0.4633 | 0.3816 | **-0.1412** | -0.1393 | `VALID_NON_DEGENERATE` |
| **72h** | 24h | 64.5 mm | Statutory | 32 | 2,856 | 6,130 | 23,742 | 0.0052 | 0.9889 | 0.0035 | **-0.1284** | -0.1022 | `VALID_NON_DEGENERATE` |

---

## 4. Audit Findings on Edge Cases & Mathematical Anomalies

### 4.1 Why 6h Light Rain Produced $HSS = 0.0000$ and $TSS = \text{NaN}$:
- In the 6h Light Rain ($1.0\text{ mm}$) evaluation, $H = 35,741$, $M = 4,039$, while **$F = 0$ and $C = 0$**.
- This occurred because during the monsoonal storm episodes in this subset, **100% of observed cells recorded $\ge 1.0\text{ mm}$** (zero non-events, $obs\_no = 0$).
- When $C = 0$ and $F = 0$, the Probability of False Detection ($POFD$) is:
  $$POFD = \frac{F}{F + C} = \frac{0}{0} \rightarrow \text{Mathematically Undefined (NaN)}$$
  Consequently, the True Skill Statistic ($TSS = POD - POFD$) is $\text{NaN}$.
- For Heidke Skill Score:
  $$\text{Expected Hits} = \frac{(H + M)(H + F) + (C + M)(C + F)}{N} = \frac{(N)(N) + (0)}{N} = N$$
  $$\text{Denominator} = N - \text{Expected Hits} = N - N = 0$$
  Division of $0 / 0$ is mathematically undefined. Naive software substituted $0.0000$. This report formally classifies this table as `DEGENERATE_ZERO_NEGATIVES` due to base-rate saturation.

### 4.2 Why HSS is Negative at 48h and 72h for Heavy Rain:
- At 48h for Heavy Rain ($64.5\text{ mm}$): $H = 2$, $F = 3,633$, $M = 6,160$, $C = 25,305$.
- Total correct predictions: $H + C = 2 + 25,305 = 25,307$.
- Expected correct predictions by random chance:
  $$\text{Expected} = \frac{(6,162)(3,635) + (31,465)(28,938)}{35,100} = \frac{22,398,870 + 910,534,170}{35,100} = 26,579.3$$
- Because actual correct predictions ($25,307$) are **lower than expected by random chance ($26,579.3$)**, the numerator is negative:
  $$\text{Numerator} = 25,307 - 26,579.3 = -1,272.3$$
  $$HSS = \frac{-1,272.3}{35,100 - 26,579.3} = \frac{-1,272.3}{8,520.7} = \mathbf{-0.1493}$$
- **Physical Interpretation:** A negative HSS proves that using a 48h NWP forecast to trigger heavy rain alerts is **actively worse than tossing a coin calibrated to climatology**. Spatial phase displacement produces massive false alarms ($3,633$) and misses ($6,160$).

---

## 5. Summary & Decision Mandate

1. **Gate A Re-Affirmed:** Solid skill at $24\text{h}$ ($HSS = +0.33, CSI = 0.27, POD = 0.37$) justifies automated early detection for $T \le 24\text{h}$.
2. **Alert Prohibition for $\ge 48\text{h}$ Justified:** Negative HSS ($-0.15$ and $-0.13$) and near-zero CSI ($<0.005$) provide definitive mathematical justification for strictly prohibiting automated alerting for horizons $\ge 48\text{h}$.

