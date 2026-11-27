# Phase 4.3 — Dynamic Risk-Intelligence Engine Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban (1,170 Cells, 1-km Grid)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Reporting Date:** 2026-11-05  
**Deliverable Dataset:** [`data/processed/dynamic_risk_intelligence_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/dynamic_risk_intelligence_bengaluru.parquet) (1,170 cells, 33 columns)  

---

## 1. Executive Summary & Architectural Philosophy

A foundational tenet of environmental decision intelligence is that **distinct categories of evidence must never be conflated into a single opaque black-box number**. 
The Phase 4.3 Dynamic Risk-Intelligence Engine explicitly segregates four distinct physical questions and evidence streams:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        FOUR SEPARATE ANALYTICAL INFORMATION LAYERS                     │
├──────────────────────────┬────────────────────────────────────────┬────────────────────┤
│ Information Layer        │ Core Operational Question              │ Primary Evidence   │
├──────────────────────────┼────────────────────────────────────────┼────────────────────┤
│ 1. Static Susceptibility │ Where is the terrain naturally prone?  │ DEM & WorldCover   │
│ 2. Observed Exposure     │ Where has rain already fallen?         │ Observed rain & API│
│ 3. Forecast Exposure     │ Where is rain predicted to fall?       │ NWP 72h Forecast   │
│ 4. Ground Flood Evidence │ Where has flooding actually occurred?  │ Ground Incident Log│
└──────────────────────────┴────────────────────────────────────────┴────────────────────┘
```

The engine guarantees that a rainfall forecast is never confused with an observed flood, and that physical susceptibility is never masked by transient dry weather.

---

## 2. Mathematical Formulation of the Four Distinct Layers

All components are strictly normalized to the unit interval $[0.0, 1.0]$:

### Layer 1: Static Physical Susceptibility ($S_{\text{static}}$)
Combines normalized relative topographic depression and sub-cell surface flatness with impervious built-up runoff generation:
$$S_{\text{terrain}, i} = 0.60 \cdot (1 - \tilde{e}_i) + 0.40 \cdot (1 - \tilde{\sigma}_{e, i})$$
$$S_{\text{landcover}, i} = \text{clip}\left(\frac{0.75 f_{\text{built}, i} + 0.25 f_{\text{water}, i} - 0.20 f_{\text{veg}, i} - \min}{\max - \min}, 0, 1\right)$$
$$S_{\text{static}, i} = 0.50 \cdot S_{\text{terrain}, i} + 0.50 \cdot S_{\text{landcover}, i}$$

### Layer 2: Observed Meteorological Exposure ($E_{\text{observed}}$)
Quantifies recent antecedent saturation based on verified 24-hour rainfall depth and exponential soil moisture memory:
$$E_{\text{observed}, i} = 0.55 \cdot \text{clip}\left(\frac{P_{\text{obs}, i}}{100.0}, 0, 1\right) + 0.45 \cdot \text{clip}\left(\frac{API_i}{150.0}, 0, 1\right)$$

### Layer 3: Forecast Meteorological Exposure ($E_{\text{forecast}}$)
Quantifies forward-looking atmospheric rainfall volume predicted by numerical weather models over the next 24 hours:
$$E_{\text{forecast}, i} = \text{clip}\left(\frac{P_{\text{fcst\_24h}, i}}{65.0}, 0.0, 1.0\right)$$

### Layer 4: Ground Flood Evidence ($G_{\text{evidence}}$)
Maintains discrete point and polygon evidence records with spatial uncertainty radius and qualitative evidence categories (`confirmed_inundation`, `reported_waterlogging`, `flood_disruption`).

---

## 3. Exploratory Composite Prioritization Index

For decision-makers requiring a unified spatial ranking for emergency resource staging, an optional exploratory prioritization index is provided:
$$I_{\text{priority}, i} = 0.35 \cdot S_{\text{static}, i} + 0.30 \cdot E_{\text{observed}, i} + 0.35 \cdot E_{\text{forecast}, i}$$

> [!WARNING]
> **Strict Scientific Qualification:**
> This prioritization index represents an **uncalibrated multi-criteria research score $[0, 1]$**. 
> It reflects relative physical vulnerability and meteorological exposure. 
> It is **NEVER a calibrated probability of inundation** and must never be communicated to the public as an official emergency warning.

---

## 4. Qualitative Research Monitoring Levels ($N = 1,170$)

To establish transparent screening categories, four research monitoring tiers are defined:

| Research Monitoring Tier | Defining Threshold Criteria | Cell Count ($N = 1,170$) | Percentage | Operational Meaning |
| :--- | :--- | :---: | :---: | :--- |
| **Research Priority Very High** | $I_{\text{priority}} \ge 0.70$ | 0 | 0.0% | Severe joint convergence of heavy forecast storm over low-lying impervious sink. |
| **Research Priority High** | $0.50 \le I_{\text{priority}} < 0.70$ | 0 | 0.0% | Moderate-to-heavy forecast exposure over susceptible urban corridor. |
| **Research Priority Moderate** | $0.35 \le I_{\text{priority}} < 0.50$ | 89 | 7.6% | Moderate susceptibility requiring active municipal drainage monitoring. |
| **Research Priority Low** | $I_{\text{priority}} < 0.35$ | 1,081 | 92.4% | Baseline condition; rainfall forecast within normal drainage absorption limits. |

