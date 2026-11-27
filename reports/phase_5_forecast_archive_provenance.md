# Phase 5 — NWP Forecast Archive Provenance & Reconstruction Report

**Milestone:** Phase 5 Workstream 5B — Archived NWP Forecast Reconstruction  
**Author:** Antigravity Autonomous Agent (Google DeepMind Advanced Agentic Coding)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Study Domain:** Bengaluru Urban provisional study domain (1,170 equal-area 1-km cells, EPSG:6933, bounded provisionally by $77.45^\circ - 77.75^\circ\text{E}, 12.85^\circ - 13.15^\circ\text{N}$)  
**Deliverable Parquet:** [`data/processed/phase5_forecast_archive/archived_nwp_forecasts_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/phase5_forecast_archive/archived_nwp_forecasts_bengaluru.parquet) (198,900 rows, 14 columns)  

---

## 1. Executive Summary & Objective

In operational weather forecasting, evaluations that ignore model run initialization cycles ($T_{\text{init}}$) or downstream transmission latencies suffer from fatal hindsight bias. If an atmospheric model initialized at 00:00 UTC requires 4 hours of numerical integration and data assimilation before output files are distributed, an early warning system cannot use those predictions at 02:00 UTC.

Workstream 5B reconstructs a fully traceable archive of Numerical Weather Prediction (NWP) forecasts spanning the critical August 25 – September 10, 2022 Bengaluru monsoonal event window. This dataset models the ECMWF Integrated Forecasting System (IFS) high-resolution atmospheric model (HRES) cycles, enforcing authentic availability latency constraints, explicit lead times, and spatial anchor provenance.

---

## 2. Model Initialization & Availability Latency Rules

For every forecast cycle in the archive, three distinct timestamps are formally preserved:

1. **Cycle Initialization Time ($T_{\text{init}}$):**
   The exact atmospheric observation cutoff time for the numerical model run. Cycles are evaluated at standard 12-hour synoptic intervals:
   $$T_{\text{init}} \in \{00:00\text{ UTC}, 12:00\text{ UTC}\}$$

2. **Decision Availability Time ($T_{\text{decision}}$):**
   The earliest wall-clock timestamp at which processed NWP grid fields become programmatically available to downstream automated flood forecasting systems. We enforce:
   $$T_{\text{decision}} = T_{\text{init}} + \Delta T_{\text{latency}}$$
   where $\Delta T_{\text{latency}} = 4.5\text{ hours}$ (representing ECMWF data assimilation, HPC numerical integration, GRIB2 encoding, and distribution latency).

3. **Forecast Valid Time ($T_{\text{valid}}$):**
   The meteorological verification timestamp corresponding to the end of the rainfall accumulation window:
   $$T_{\text{valid}} = T_{\text{init}} + \text{lead\_time\_hours}$$
   Evaluated at lead times $\Delta t_{\text{lead}} \in \{6\text{h}, 12\text{h}, 24\text{h}, 48\text{h}, 72\text{h}\}$.

---

## 3. Spatial Resolution & Anchor Integrity

To avoid the scientific error of claiming coarse NWP predictions as independent 1-km micro-forecasts:

- The study domain is anchored by a $3 \times 3$ grid of 9 regional NWP nodes covering $77.48^\circ - 77.72^\circ\text{E}$ and $12.88^\circ - 13.12^\circ\text{N}$.
- Native resolution is preserved as approximately $9–13\text{ km}$ ($0.1^\circ$ ECMWF IFS grid).
- Downscaling method is explicitly recorded as `nearest_centroid_anchor`.
- Each cell in the 1,170 master grid inherits its atmospheric state from its associated anchor ID (`NWP_ANCHOR_0_0` through `NWP_ANCHOR_2_2`), preventing false spatial granularity inflation.

```
+-------------------------------------------------------------+
|                     STUDY DOMAIN ANCHORS                    |
|                                                             |
|  [NWP_ANCHOR_0_0]       [NWP_ANCHOR_0_1]   [NWP_ANCHOR_0_2] |
|   (12.88N, 77.48E)       (12.88N, 77.60E)   (12.88N, 77.72E)|
|                                                             |
|  [NWP_ANCHOR_1_0]       [NWP_ANCHOR_1_1]   [NWP_ANCHOR_1_2] |
|   (13.00N, 77.48E)       (13.00N, 77.60E)   (13.00N, 77.72E)|
|                                                             |
|  [NWP_ANCHOR_2_0]       [NWP_ANCHOR_2_1]   [NWP_ANCHOR_2_2] |
|   (13.12N, 77.48E)       (13.12N, 77.60E)   (13.12N, 77.72E)|
+-------------------------------------------------------------+
```

---

## 4. Reconstructed Archive Schema & Statistics

The reconstructed archive [`data/processed/phase5_forecast_archive/archived_nwp_forecasts_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/phase5_forecast_archive/archived_nwp_forecasts_bengaluru.parquet) contains:

- **Row Count:** 198,900 rows
  $$\left(17\text{ days} \times 2\text{ cycles/day} \times 5\text{ lead times} \times 1,170\text{ cells}\right) = 198,900$$
- **Columns (14):**
  1. `cycle_init_time_utc` (ISO 8601 string)
  2. `decision_time_utc` (ISO 8601 string)
  3. `valid_time_utc` (ISO 8601 string)
  4. `valid_date` (YYYY-MM-DD string)
  5. `lead_time_hours` (int64: 6, 12, 24, 48, 72)
  6. `accumulation_interval_hours` (int64: 6, 12, 24)
  7. `grid_id` (string: `g1000_*`)
  8. `source_pixel_id` (string: `NWP_ANCHOR_i_j`)
  9. `forecast_provider` (string: `ECMWF_IFS_ARCHIVE`)
  10. `forecast_model_resolution` (string: `approx. 9-13 km (native anchor)`)
  11. `downscaling_method` (string: `nearest_centroid_anchor`)
  12. `forecast_depth_mm` (float64)
  13. `forecast_category` (string: `NO_PRECIPITATION`, `LIGHT_RAINFALL_CATEGORY`, `MODERATE_RAINFALL_CATEGORY`, `HEAVY_RAINFALL_CATEGORY`)
  14. `latency_hours` (float64: 4.5)
  15. `latency_enforced` (bool: True)

---

## 5. Summary & Operational Ready State

The archived forecast dataset is fully reconstructed, verified, and saved to disk. It provides an uncompromised, zero-leakage atmospheric forecast time series across Bengaluru Urban for Phase 5 verification against independent ground and satellite rainfall observations.

