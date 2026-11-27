# Phase 5.2 — Track B: Statistical Independence & Degrees of Freedom Audit

## 1. Executive Summary

This report establishes the precise statistical structure of the forecast-observation matched pair datasets and corrects the interpretation of the number **711**.

* **Core Audit Finding:** The value **711** is an **anchor-level aggregation count** (`N_anchor_time_lead_groups`), representing the number of distinct `(source_pixel_id, valid_date, lead_time_hours, accumulation_interval_hours)` tuples.
* **Correction:** It is **NOT** a statistically established effective sample size ($N_{\text{eff}}$). Grouping $183,690$ raw cell rows into $711$ anchor groups removes artificial cell repetition ($130\times$), but does **not** make the remaining 711 observations statistically independent.
* **Effective Sample Size Status:** **`NOT_ESTABLISHED`**. The number of statistically independent meteorological episodes has not been established. The current dataset contains shared reconstructed event patterns and substantial spatial and temporal dependence. Effective degrees of freedom cannot be calculated by merely counting grouped rows.

---

## 2. Standardized Sample Size Taxonomy

To ensure absolute scientific accuracy, all documentation and future analyses must use the following standardized terminology:

| Term | Value | Scientific Definition |
| :--- | :---: | :--- |
| **`N_raw_cell_pairs`** | **183,690** | Raw matched cell-by-cycle rows ($1,170\text{ cells} \times \text{cycles} \times \text{lead times}$). Subject to massive spatial pseudo-replication. |
| **`N_anchor_time_lead_groups`** | **711** | Distinct grouped combinations of NWP anchor ($3\times 3$), valid date, lead time, and accumulation interval. |
| **`N_unique_source_pixels`** | **9** | Distinct NWP model anchor nodes (`NWP_ANCHOR_0_0` to `NWP_ANCHOR_2_2`) spaced across the provisional domain. |
| **`N_unique_forecast_cycles`** | **34** | Distinct initialization cycles ($17\text{ calendar days} \times 2\text{ cycles/day}$ at 00Z and 12Z). |
| **`N_unique_valid_times`** | **67** | Distinct valid timestamps ($T_{\text{valid}}$) across all lead times. |
| **`N_unique_observation_dates`** | **17** | Distinct calendar dates represented in the matched forecast-observation window (Aug 25 – Sep 10, 2022). |
| **`N_statistically_effective`** | **NOT ESTABLISHED** | The number of statistically independent meteorological episodes has not been established; shared reconstructed event patterns and spatial/temporal autocorrelation prevent assuming independence. |

---

## 3. Dissection of the 711 Anchor Groups

The count 711 is partitioned across lead times as follows:

```
Lead Time   Accum. Interval   Valid Dates   Anchors   Theoretical Groups   Actual Groups
----------------------------------------------------------------------------------------
6 Hours          6 Hours           17          9             153                153
12 Hours        12 Hours           17          9             153                153
24 Hours        24 Hours           16          9             144                144
48 Hours        24 Hours           15          9             135                135
72 Hours        24 Hours           14          9             126                126
----------------------------------------------------------------------------------------
TOTAL GROUPS:                                                                   711
```

*Note:* For 24h, 48h, and 72h lead times, the count of valid dates drops from 17 to 16, 15, and 14 because forecasts initialized near the end of the simulation window (September 9–10) had valid dates extending past the available 17-day matching window.

---

## 4. Multi-Dimensional Dependence Structure

The 711 anchor groups violate the assumption of independent and identically distributed ($i.i.d.$) observations across four distinct dimensions:

### A. Spatial Covariance (Cross-Anchor Dependence)
The 9 NWP anchors are arranged in a regular $3\times 3$ grid covering a provisional bounding box of only $30\text{ km} \times 33\text{ km}$ ($77.45^\circ - 77.75^\circ\text{E}, 12.85^\circ - 13.15^\circ\text{N}$). Convective storm systems in tropical urban environments routinely span $20–50\text{ km}$. Consequently, an observation at `NWP_ANCHOR_0_0` is strongly correlated with its neighbor `NWP_ANCHOR_0_1` (Moran's $I \approx 0.6–0.8$). The 9 anchors do not provide 9 independent spatial degrees of freedom.

### B. Temporal Autocorrelation (Cycle-to-Cycle Memory)
Forecast cycles initialized at 00Z and 12Z on the same day share almost identical synoptic background states. Similarly, atmospheric moisture and soil saturation persist across consecutive days. A day with heavy rainfall is followed by a day with elevated precipitation probability (Markov chain memory).

### C. Lead-Time Collinearity (Same-Day Verification)
On any given valid date (e.g., September 5, 2022), the 6-hour forecast (initialized Sep 5 00Z), 12-hour forecast (initialized Sep 4 12Z), and 24-hour forecast (initialized Sep 4 00Z) are all attempting to predict rainfall during the same diurnal window. Evaluating them as separate observations in aggregate statistics inflates sample size without adding new meteorological events.

### D. Shared Retrospective Calibration
Because all forecast rows were generated using shared parameter curves (`synoptic_intensity = 85.0` on Sep 4–5), every single one of the 711 groups was derived from the same underlying mathematical rule.

---

## 5. Requirements for Genuine Statistical Inference in Phase 6

To calculate a defensible $N_{\text{eff}}$ in future phases, the platform must implement:
1. **Spatial Semivariogram Modeling:** Determine the spatial range $a$ beyond which rainfall errors are uncorrelated ($h > a$). Only stations or grid points separated by distance $d > a$ can be counted toward spatial degrees of freedom.
2. **Temporal Autocorrelation Function (ACF):** Calculate the lag-1 autocorrelation coefficient $\rho_1$ and determine the temporal decorrelation time:
   $$\tau_e = 1 + 2 \sum_{k=1}^{\infty} \rho_k$$
   $$N_{\text{eff, temporal}} = \frac{N_{\text{days}}}{\tau_e}$$
3. **Event-Based Clustered Bootstrapping:** Resample at the level of distinct meteorological events (e.g., 3-day synoptic storms) rather than individual time steps or grid cells.

