# Phase 7F — Comprehensive Limitations Register & Future Scope

**Document Identifier:** `reports/phase_7/phase_7F_limitations_and_future_scope.md`  
**Authors:** Multi-Disciplinary Research Team  
**Status:** **`FORMAL_ACADEMIC_REGISTER`**  

---

## 1. Master Limitations Register

| Boundary ID | Domain | Detailed Limitation Description | Impact on Research Interpretation |
| :---: | :--- | :--- | :--- |
| **LIM-01** | **NWP Resolution** | NOAA GFS has a native grid spacing of $0.25^\circ \approx 27.75\text{ km}$. Only 6 nodes cover the entire study domain. | The 198,900 archive rows are spatial mappings of 1,020 native forecasts. GFS cannot simulate micro-scale urban heat islands or street-level turbulence. |
| **LIM-02** | **Convective Mismatch** | GFS smooths localized rainfall extremes across $\sim 750\text{ km}^2$, yielding $\text{POD} = 0.00$ at $\ge 64.5\text{ mm}$. | Global NWP cannot be used as an automated flash flood trigger without high-resolution convective-permitting downscaling. |
| **LIM-03** | **Rain Gauge Clustering** | The 16 primary rain gauges map to only 3 native GFS nodes across 16 dates. | The effective degrees of freedom is $K \le 48$, not 256. Clustered bootstrap intervals must be used to avoid artificial certainty. |
| **LIM-04** | **Ground Truth Censorship** | $98.29\%$ of the urban domain ($1,150 / 1,170\text{ km}^2$) has zero verified flood observations during the deluge. | Supervised ML flood prediction is strictly prohibited. Imputing unobserved cells as dry injects fatal spatial bias. |
| **LIM-05** | **SAR Urban Attenuation** | C-band ($5.6\text{ cm}$) radar suffers from severe tree canopy attenuation, building layover, and double-bounce reflection in urban street canyons. | Spaceborne SAR cannot reliably map street-level flooding in dense residential neighborhoods; its validity is restricted to open water and lake-margin swales. |
| **LIM-06** | **Permanent Water Conflation** | 4 of the 10 SAR detections were pre-existing permanent lakes with unchanged backscatter ($\Delta\sigma^0 = 0.0\text{ dB}$). | Water body masks must be used to isolate true flood expansion ($38.5\%$) from permanent lakes ($30.8\%$). |
| **LIM-07** | **Terrain Macro-Resolution** | 1-km elevation routing (D8) cannot resolve 2-meter culverts, road embankments, or compound walls. | Topographic indices (TWI, HIPI with $\text{ROC-AUC} = 0.560$) are exploratory indicators of regional drainage convergence, not predictive flood models. |
| **LIM-08** | **Sink Filling Bias** | Priority-flood filling eliminates 19 natural closed basins (lakes/quarries), redirecting up to $12.0\text{ km}^2$ downstream. | Static pit filling overestimates downstream discharge during dry antecedent conditions by ignoring lake storage retention capacity. |
| **LIM-09** | **Lack of Stage Telemetry** | Zero water-level sensors exist in Bengaluru's Rajakaluves (stormwater canals) in the public domain. | Hydrodynamic models cannot be calibrated or validated against observed channel discharge or water depth. |
| **LIM-10** | **Operational Status** | The platform is a research intelligence console, not an official municipal disaster warning system. | All outputs are informational research assessments; public emergency alerts remain the sole authority of IMD and KSNDMC. |

---

## 2. Realistic Future Scope & Roadmap

To transition this research into an operational urban flood early warning system, future work should proceed across five phases:

### A. Atmospheric Downscaling & Nowcasting
- Deploy Weather Research and Forecasting (WRF) model runs at $\le 3\text{ km}$ convective-permitting resolution driven by ECMWF IFS / GFS boundary conditions.
- Integrate IMD Bengaluru Doppler Weather Radar (DWR) reflectivity for $0 - 3\text{ hour}$ quantitative precipitation estimation (QPE) and cell tracking.

### B. High-Resolution Digital Elevation & Drainage Mapping
- Acquire airborne LiDAR bare-earth DTM at $\le 2\text{m}$ spatial resolution and $\le 15\text{cm}$ vertical accuracy to resolve roadside curbs, culverts, and compound walls.
- Map the complete GIS topological network of Bengaluru's $840\text{ km}$ Rajakaluves, including surveyed cross-sections, culvert invert levels, and bridge bottlenecks.

### C. Sensor Telemetry Expansion
- Deploy a network of solar-powered IoT ultrasonic water-level sensors at $500\text{m}$ intervals along major trunk storm drains and at all lake sluice gates.
- Connect telemetry directly to KSNDMC and BBMP disaster management consoles for real-time automated hydrograph tracking.

### D. Coupled 1D/2D Hydrodynamic Modeling
- Implement physical 1D/2D hydrodynamic simulations (e.g. EPA-SWMM coupled with 2D overland flow) using dynamic stage-storage-discharge curves for all 200+ interconnected lakes.
- Calibrate Manning's roughness coefficients ($n$) against observed water levels during monsoon events.

### E. Supervised Machine Learning Authorization
- Once municipal telemetry and systematic civic reporting cover $>20\%$ of the urban domain with verified negative controls in valleys, re-evaluate the Supervised ML Gate for gradient-boosted spatial decision trees.

