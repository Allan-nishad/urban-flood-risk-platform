# Phase 7D — Terrain Depression Sensitivity & Urban Storage Report

**Auditor:** Urban Hydrologist & Statistical Validation Specialist  
**Dataset Path:** `data/processed/phase7/hydrology/phase7_hydrology_comparison.parquet`  
**Comparisons:** Representation A (Depressions Retained) vs. Representation B (Priority-Flood Conditioned)  
**Status:** **`PASS_WITH_DOCUMENTED_LIMITATIONS`**  

---

## 1. Executive Summary & Problem Formulation

In regional digital elevation models (DEMs), natural closed sinks or pits are typically treated as artifacts and "filled" to enforce continuous downhill flow. However, in an urban environment:
1. Closed depressions frequently represent **interconnected cascade lakes (Kere)**, detention ponds, and quarry pits designed to buffer monsoon runoff.
2. Artificially filling depressions eliminates their storage volume and forces premature downstream spillover.
3. Conversely, retaining raw DEM depressions assumes that pit bottoms have infinite storage and can never fill or overtop.

This audit conducted a comparative sensitivity analysis between:
- **Representation A:** Natural terrain with depressions retained (pits terminate flow paths).
- **Representation B:** Priority-flood conditioned terrain (sinks filled to minimum spill elevation).

---

## 2. Comparative Findings Across 1,170 Cells

| Terrain Property | Representation A (Depressions Retained) | Representation B (Priority-Flood Conditioned) | Observed Impact / Divergence |
| :--- | :---: | :---: | :--- |
| **Identified Sink Cells** | 19 cells | 0 cells (all filled) | 19 natural closed basins ($1.62\%$ of domain). |
| **Filled Depression Depth** | $0.00\text{ m}$ | Mean $0.03\text{m}$, Max $4.85\text{ m}$ | Maximum pit depth observed in quarry basins. |
| **Mean Flow Accumulation** | $5.93\text{ km}^2$ | $5.87\text{ km}^2$ | Macro-average remains stable ($\Delta < 1\%$). |
| **Max Flow Accumulation** | $186.0\text{ km}^2$ | $183.0\text{ km}^2$ | Trunk channel path altered slightly. |
| **Max Downstream Divergence**| — | **$+12.0\text{ km}^2$** | Spillover from filled sinks redirected contributing area by up to $12\text{ km}^2$ downstream. |
| **Mean TWI** | $12.477$ | $12.492$ | Slight increase ($+0.015$) in valley floor cells. |

---

## 3. Hydrological Implications for Bengaluru's Urban Lakes

1. **The Lake Cascade Cascade Effect:**
   - Bengaluru's historical drainage system consists of interconnected tank cascades (e.g. Yelahanka cascade, Bellandur–Varthur cascade).
   - In Representation A, each lake basin acts as an absolute sink, truncating upstream area.
   - In Representation B, priority-flood filling assumes that lakes are full to the brim at the onset of rain, forcing $100\%$ of inflow to spill over into the next downstream tank.
   - During the September 2022 deluge, antecedent rainfall from late August had completely filled the lake storage capacity. Thus, **Representation B (Conditioned)** more closely reflected the co-event hydrodynamic reality, where lake cascades spilled over into surrounding roads and tech parks.

2. **Uncertainty Bounds:**
   - For dry-season antecedent conditions, Representation B overestimates downstream discharge by up to $12\text{ km}^2$.
   - A truly physical model must replace static depression filling with dynamic stage-storage-discharge rating curves for all major tanks.

