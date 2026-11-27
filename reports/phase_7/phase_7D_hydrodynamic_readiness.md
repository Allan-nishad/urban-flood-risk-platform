# Phase 7D — Hydrodynamic Modeling Readiness Assessment

**Auditor:** Urban Hydrologist & Scientific Research Lead  
**Assessment Target:** Feasibility and Prerequisites for 2D Urban Hydrodynamic Simulation (HEC-RAS / LISFLOOD-FP / SWMM)  
**Decision:** **`DEFERRED_PENDING_SUB_GRID_DATA_ACQUISITION`**  

---

## 1. Readiness Audit

A complete technical evaluation was conducted to determine whether the existing platform data justify the execution of a 2D hydrodynamic flood simulation:

| Hydrodynamic Prerequisite | Platform Current State | Data Sufficiency Status | Gap / Limitation |
| :--- | :--- | :---: | :--- |
| **High-Resolution DTM** | MERIT Hydro / SRTM 1-arcsecond ($30\text{m}$, aggregated to 1-km) | **INSUFFICIENT** | SRTM is a Digital Surface Model (includes tree canopies and building roofs). Hydrodynamics requires bare-earth LiDAR DTM $\le 2\text{m}$ resolution. |
| **Stormwater Drainage Network**| Static built-up fraction from ESA WorldCover ($10\text{m}$) | **INSUFFICIENT** | Surveyed GIS polyline layer of Rajakaluves (primary, secondary, tertiary drains) with bed widths, invert levels, and culvert dimensions is missing. |
| **Sub-Surface Pipe Network** | None available | **MISSING** | Closed municipal drainage pipes, roadside catch-basins, and pumping station specs are unavailable. |
| **Hydraulic Boundary Conditions**| Regional GFS NWP grid averages ($28\text{km}$) | **INSUFFICIENT** | Hydrodynamics requires sub-hourly rainfall hyetographs ($15\text{min}$ timestep) across the catchment. |
| **Infiltration Parameters** | Constant Rational runoff coefficient ($C = 0.15 - 0.85$) | **EXPLORATORY ONLY** | Green-Ampt or Horton infiltration parameters based on surveyed urban soil boring data are unavailable. |
| **Calibration Gauges** | 16 daily total rain gauges; zero streamflow/stage gauges | **MISSING** | Zero water-level sensors in Rajakaluves or lakes to calibrate Manning's $n$ roughness. |

---

## 2. Scientific Decision & Avoidance of Synthetic Fabrication

$$\mathbf{DECISION:\quad FULL\quad 2D\quad HYDRODYNAMIC\quad SIMULATION\quad IS\quad DEFERRED}$$

**Scientific Rationale:**
- Running a 2D hydrodynamic model (e.g. LISFLOOD-FP or HEC-RAS 2D) on a 1-km SRTM grid without surveyed drainage cross-sections would require inventing synthetic drain dimensions, arbitrary roughness coefficients, and assumed pipe capacities.
- Such a simulation would produce visually complex inundation depth maps that give a dangerous illusion of engineering precision while being fundamentally ungrounded in physical reality.
- In accordance with the project's governing principle (*Empirical Authenticity Over Synthetic Optimization*), hydrodynamic modeling is formally deferred until municipal LiDAR and surveyed drainage telemetry are acquired.

