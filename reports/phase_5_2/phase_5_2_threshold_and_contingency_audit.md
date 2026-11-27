# Phase 5.2 — Track C: Threshold Provenance & Contingency Table Audit

## 1. Executive Summary

This report conducts a strict audit of the categorical threshold definitions and contingency tables utilized across Phase 5 verification.

* **Correction of Threshold Terminology:** The term `OFFICIAL_IMD_STATUTORY` is **formally retracted**. The India Meteorological Department (IMD) issues published meteorological classification guidelines and public advisory definitions, not legally enacted statutory legislation. The correct scientific terminology is **`IMD_PUBLISHED_24H_RAINFALL_CLASSIFICATION_THRESHOLD`**.
* **Sub-Daily Thresholds:** The 6-hour ($1.0, 6.2, 25.8\text{ mm}$) and 12-hour ($1.6, 10.1, 41.9\text{ mm}$) thresholds are mathematical diurnal approximations created by project code (`PROJECT_DERIVED_SUBDAILY_THRESHOLD`), not IMD official standards.
* **Contingency Table Degeneracies:** The appearance of $HSS = 0.0$ and $TSS = \text{NaN}$ in the 6h, 12h, and 24h Light Rain tables is mathematically audited: during the 17-day monsoon event window, precipitation occurred across all grid cells ($100\%$ base rate), resulting in zero observed non-events ($C = 0, F = 0$). This induces division by zero in $POFD = F/(F+C)$ and forces $HSS = 0.0$. These rows are formally flagged as **`DEGENERATE_ZERO_NEGATIVES`**.

---

## 2. Threshold Provenance & Semantic Corrections

| Previous Identifier | Reconciled Phase 5.2 Identifier | Threshold Value | Physical & Legal Provenance |
| :--- | :--- | :---: | :--- |
| `OFFICIAL_IMD_STATUTORY` | **`IMD_PUBLISHED_24H_RAINFALL_CLASSIFICATION_THRESHOLD`** | $2.5\text{ mm}$ / 24h | IMD published lower bound for "Rainy Day" / Light Rain ($2.5–15.5\text{ mm}$). Published scientific standard; not a statutory legal decree. |
| `OFFICIAL_IMD_STATUTORY` | **`IMD_PUBLISHED_24H_RAINFALL_CLASSIFICATION_THRESHOLD`** | $15.6\text{ mm}$ / 24h | IMD published lower bound for "Moderate Rain" ($15.6–64.4\text{ mm}$). Published scientific standard. |
| `OFFICIAL_IMD_STATUTORY` | **`IMD_PUBLISHED_24H_RAINFALL_CLASSIFICATION_THRESHOLD`** | $64.5\text{ mm}$ / 24h | IMD published lower bound for "Heavy Rain" ($64.5–115.5\text{ mm}$). Triggers Yellow/Orange weather warning advisories. |
| `DERIVED_DIURNAL_DISAGGREGATION` | **`PROJECT_DERIVED_SUBDAILY_THRESHOLD`** | $1.0, 6.2, 25.8\text{ mm}$ | Derived by multiplying 24h thresholds by $0.40$ (approximating 40% diurnal convective peak in 6 hours). Internal project derivation. |
| `DERIVED_DIURNAL_DISAGGREGATION` | **`PROJECT_DERIVED_SUBDAILY_THRESHOLD`** | $1.6, 10.1, 41.9\text{ mm}$ | Derived by multiplying 24h thresholds by $0.65$ (approximating 65% convective volume in 12 hours). Internal project derivation. |

> [!IMPORTANT]
> The derived 6-hour and 12-hour thresholds must never be presented as official IMD operational warning thresholds. They are heuristic disaggregations for exploratory research.

---

## 3. Contingency Table Audit & Degeneracy Analysis

The $2\times 2$ contingency table is defined as:
* **Hits ($H$):** Forecast Yes, Observed Yes
* **False Alarms ($F$):** Forecast Yes, Observed No
* **Misses ($M$):** Forecast No, Observed Yes
* **Correct Negatives ($C$):** Forecast No, Observed No
* **Total ($N$):** $H + F + M + C$

### Complete Recalculated Contingency Table
```
Lead  Accum  Threshold (mm)  Hits (H)   FA (F)  Miss (M)   Corr Neg (C)    POD     FAR     CSI    HSS      TSS      Status
--------------------------------------------------------------------------------------------------------------------------------------
6h     6h    1.0 (Light)       35,741        0     4,039              0  0.8985  0.0000  0.8985  0.0000     NaN    DEGENERATE_ZERO_NEG
6h     6h    6.2 (Moderate)    13,241    2,353     9,223         14,963  0.5894  0.1509  0.5335  0.4338   0.4535   VALID_NON_DEGENERATE
6h     6h   25.8 (Heavy)        1,893      344     4,269         33,274  0.3072  0.1538  0.2910  0.4014   0.2970   VALID_NON_DEGENERATE
12h   12h    1.6 (Light)       35,214        0     3,396              0  0.9120  0.0000  0.9120  0.0000     NaN    DEGENERATE_ZERO_NEG
12h   12h   10.1 (Moderate)    13,821    5,260     8,253         11,276  0.6261  0.2757  0.5056  0.3012   0.3080   VALID_NON_DEGENERATE
12h   12h   41.9 (Heavy)        1,166    1,166     4,996         31,282  0.1892  0.5000  0.1591  0.2049   0.1533   VALID_NON_DEGENERATE
24h   24h    2.5 (Light)       33,856        0     3,584              0  0.9043  0.0000  0.9043  0.0000     NaN    DEGENERATE_ZERO_NEG
24h   24h   15.6 (Moderate)    15,103    8,784     6,581          6,972  0.6965  0.3677  0.4957  0.1417   0.1390   VALID_NON_DEGENERATE
24h   24h   64.5 (Heavy)        2,259    2,256     3,903         29,022  0.3666  0.4997  0.2684  0.3299   0.2945   VALID_NON_DEGENERATE
48h   24h    2.5 (Light)       30,292        0     4,808              0  0.8630  0.0000  0.8630  0.0000     NaN    DEGENERATE_ZERO_NEG
48h   24h   15.6 (Moderate)    13,795    8,529     5,549          7,227  0.7131  0.3821  0.4949  0.1749   0.1718   VALID_NON_DEGENERATE
48h   24h   64.5 (Heavy)            2    3,633     6,160         25,305  0.0003  0.9994  0.0002 -0.1493  -0.1252   VALID_NON_DEGENERATE
72h   24h    2.5 (Light)       27,023        0     5,737              0  0.8249  0.0000  0.8249  0.0000     NaN    DEGENERATE_ZERO_NEG
72h   24h   15.6 (Moderate)    11,008    9,504     8,336          3,912  0.5691  0.4633  0.3816 -0.1412  -0.1393   VALID_NON_DEGENERATE
72h   24h   64.5 (Heavy)           32    2,856     6,130         23,742  0.0052  0.9889  0.0035 -0.1284  -0.1022   VALID_NON_DEGENERATE
```

---

## 4. Mathematical Origin of Undefined and Negative Metrics

### A. The Zero-Negative Degeneracy (Light Rain)
For the lowest threshold ($2.5\text{ mm}$ / 24h, $1.0\text{ mm}$ / 6h), $C = 0$ and $F = 0$.
1. **Probability of False Detection ($POFD$):**
   $$POFD = \frac{F}{F + C} = \frac{0}{0 + 0} \implies \text{UNDEFINED (NaN)}$$
2. **True Skill Statistic ($TSS$):**
   $$TSS = POD - POFD = 0.8985 - \text{NaN} \implies \text{UNDEFINED (NaN)}$$
3. **Heidke Skill Score ($HSS$):**
   When $F=0$ and $C=0$, the number of expected hits by chance evaluates exactly to the observed hits ($E = H$), making $(H - E) = 0$, so $HSS = 0.0$.
This does not mean the forecast had zero skill; it means a binary contingency metric cannot evaluate discrimination when the reference dataset has a $100\%$ positive base rate (no negative control cases).

### B. Negative HSS at 48h and 72h (Heavy Rain)
At 48h lead time for Heavy Rain ($\ge 64.5\text{ mm}$):
* $H = 2$ hits, while $F = 3,633$ false alarms and $M = 6,160$ misses.
* Expected random hits:
  $$E = \frac{(H + M)(H + F)}{N} = \frac{(6,162)(3,635)}{35,100} = 638.16\text{ hits}$$
* Heidke Skill Score:
  $$HSS = \frac{2(H \cdot C - F \cdot M)}{(H+M)(M+C) + (H+F)(F+C)} = \frac{2(50,610 - 22,379,280)}{\dots} = -0.1493$$
Negative spatial or temporal association is observed; physical displacement mechanism is not independently established. At 48h and 72h lead times, the forecast predicted heavy rain in locations where moderate rain was recorded and missed heavy rain where observed, yielding contingency performance worse than random chance ($HSS < 0$). This confirms why medium-range guidance cannot support automated alerting.

