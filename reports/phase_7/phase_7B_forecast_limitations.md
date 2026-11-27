# Phase 7B — Formal Register of Weather Forecast Limitations

**Auditor:** Multi-Disciplinary Final Research Team  
**Document Identifier:** `reports/phase_7/phase_7B_forecast_limitations.md`  
**Status:** **`MANDATORY_SCIENTIFIC_REGISTER`**  

---

## 1. Register of Weather Forecasting Boundaries

The following limitations are binding upon all research presentations, papers, and platform demonstrations:

| Ref ID | Category | Documented Scientific Boundary | Academic Impact / Presentation Rule |
| :---: | :--- | :--- | :--- |
| **FL-01** | **Grid Resolution** | GFS has a native spatial resolution of $0.25^\circ \approx 27.75\text{ km}$. The study area is covered by only 6 nodes. | Never state that the platform generates "1,170 high-resolution weather forecasts". The 1,170 rows are nearest-neighbor spatial attributions. |
| **FL-02** | **Sample Independence** | The 256 paired records represent 16 primary stations mapped to only 3 GFS nodes across 16 dates. | The effective degrees of freedom is $K \le 48$, not 256. Clustered confidence intervals must be reported alongside point estimates. |
| **FL-03** | **Heavy Rain Detection** | GFS achieved $\text{POD} = 0.00$ on rainfall $\ge 64.5\text{ mm}$ (0 hits, 23 misses). | Coarse global NWP cannot be used as an automated flash flood trigger. It provides general synoptic wetness, not convective storm cores. |
| **FL-04** | **Forecast vs Flood** | Forecast rainfall is an atmospheric prediction, not an observation of surface water. | A rainfall forecast must never be displayed as an active flood warning or confirmed inundation. |
| **FL-05** | **Accumulation Windows** | GFS accumulates over 24h ending 00:00 UTC; ground gauges record ending 03:00 UTC (08:30 IST). | A 3-hour temporal offset exists between GFS cycle ends and IMD/KSNDMC daily reporting. |
| **FL-06** | **Deterministic Output** | GFS forecasts acquired are deterministic single-run solutions, not probabilistic ensemble spreads. | The system cannot provide calibrated probabilities of exceedance without ensemble data (GEFS / ECMWF EPS). |

