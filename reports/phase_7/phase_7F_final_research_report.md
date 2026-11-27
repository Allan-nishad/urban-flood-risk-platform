# Final Academic Research Report: AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Repository:** `urban-flood-risk-platform`  
**Study Domain:** Bengaluru Urban Region, Karnataka, India ($1,170\text{ km}^2$, 1,170 equal-area 1-km cells, EPSG:6933)  
**Target Episode:** 2022 Monsoon Extreme Deluges (August 30 & September 4–5, 2022)  
**Authors:** Multi-Disciplinary Research & Engineering Team  
**Date of Completion:** 2026-11-05  

---

## Abstract

Urban flooding in rapidly densifying tropical plateaus is driven by complex interactions between convective atmospheric forcing, fragmented micro-drainage networks, and land-use alteration. This research investigates the feasibility, empirical limits, and physical boundaries of integrating global numerical weather prediction (NOAA GFS 0.25°), spaceborne Synthetic Aperture Radar (Copernicus Sentinel-1A C-band), and deterministic topographic hydrological routing (D8 and Topographic Wetness Index) for urban flood risk intelligence across the $1,170\text{ km}^2$ Bengaluru Urban domain. 

Through an end-to-end empirical campaign evaluating 256 matched forecast-gauge pairs across 16 primary meteorological stations, 24 multi-source verified flood incidents, and multi-temporal SAR backscatter, this project demonstrates that:
1. Global NWP provides reliable synoptic rain occurrence ($\text{POD} = 0.884$ at $\ge 2.5\text{ mm}$), but completely misses localized convective cloudbursts ($\text{POD} = 0.00$ at $\ge 64.5\text{ mm}$) due to severe areal smoothing across its $\sim 750\text{ km}^2$ grid box.
2. Spaceborne C-band SAR achieves $76.9\%$ sensitivity on open water and lake-margin overflows, but true specular flood expansion outside permanent water bodies is only $38.5\%$, with total signal obstruction in narrow urban street canyons ($23.1\%$ false negatives).
3. Deterministic macro-topography (1-km D8 routing) successfully delineates regional drainage corridors ($A = 1.0 - 186.0\text{ km}^2$), but achieves an exploratory $\text{ROC-AUC} = 0.560$ against ground truth because street-level flooding is governed by sub-grid barriers (2-meter compound walls, road culvert silting) that are invisible at 1-km scale.
4. Because $98.29\%$ of the urban domain lacks verified flood observations, training supervised machine learning classifiers introduces severe spatial bias; supervised ML flood prediction is therefore strictly blocked.

The platform provides a transparent, scientifically defensible foundation that replaces unvalidated black-box AI claims with rigorous physical uncertainty quantification.

---

## Table of Contents
1. Introduction & Urban Flood Risk Context
2. Research Objectives & Scope
3. Data Acquisition & Multi-Source Provenance
4. Meteorological Forecast Verification & Grouped Uncertainty
5. Spaceborne Remote Sensing (Sentinel-1 SAR) Analysis
6. Deterministic Terrain Hydrology & Depression Routing
7. Ground Truth Flood Evidence & Observational Censorship
8. Platform Architecture & Dashboard Engineering
9. Synthesis of Scientific Findings & Limitations
10. Future Research Directions & Conclusion

---

## 1. Introduction & Urban Flood Context

Bengaluru ($12.97^\circ\text{N}, 77.59^\circ\text{E}$, elevation $880 - 960\text{m}$ above MSL) is situated on a granitic ridge in the semi-arid Deccan Plateau, functioning as a watershed divide between the Arkavathi (Cauvery basin) to the west and the Dakshina Pinakini (Ponnaiyar basin) to the east. Historically, surface runoff was managed via a sophisticated cascade of man-made irrigation tanks (*Kere*). Over four decades of explosive technological urbanisation, the city's built-up footprint expanded by over $1,000\%$, encroaching upon natural interconnecting valley drainage channels (*Rajakaluves*) and fragmenting lake cascades.

During late August and early September 2022, consecutive mesoscale convective cloudbursts dumped up to $162\text{ mm}$ of rain within 24 hours over eastern Bengaluru. The resulting inundation overwhelmed major arterial corridors (Outer Ring Road, Sarjapur Road), submerged multinational IT tech parks (RMZ Ecoworld, Manyata), and inundated gated residential layouts (Rainbow Drive, Divyasree 77 East) up to $2.5\text{m}$ depth. This research addresses the urgent scientific question: *Can freely available satellite remote sensing and global numerical weather prediction provide reliable early detection of urban flood risks, and what are the strict physical limits of such data?*

---

## 2. Research Objectives & Scope

The investigation was guided by four core objectives:
1. **NWP Forecast Skill Assessment:** Quantify the accuracy, bias, and detection capability of operational NOAA GFS 0.25° rainfall forecasts against authoritative ground rain gauges across multiple IMD rainfall intensity thresholds.
2. **SAR Remote Sensing Verification:** Evaluate Copernicus Sentinel-1 C-band SAR backscatter before, during, and after peak inundation, disambiguating true flood water expansion from permanent water bodies and urban corner-reflection anomalies.
3. **Physical Hydrological Routing:** Implement deterministic D8 flow routing, depression filling, and Topographic Wetness Index (TWI) on an equal-area study grid to establish the baseline discriminative capability of macro-topography.
4. **Statistical Rigour & AI Ethics:** Enforce strict data provenance, preserve historical baselines bit-for-bit, conduct dependence-aware uncertainty analysis, and establish the evidentiary prerequisites required before supervised machine learning flood prediction can be deployed.

---

## 3. Data Acquisition & Multi-Source Provenance

The research platform integrates seven authoritative data sources:
- **Atmospheric NWP:** 170 WMO GRIB2 forecast slices downloaded directly from AWS Open Data (`s3://noaa-gfs-bdp-pds`), decoded with ECMWF `ecCodes 2.50.0`.
- **Rainfall Gauges:** 16 primary meteorological stations (3 IMD surface observatories and 13 KSNDMC BBMP telemetric rain gauges) providing 272 authentic daily observations.
- **Satellite Radar:** Three Copernicus Sentinel-1A Level-1 GRDH scenes (Relative Orbit 165 Descending; 2022-08-12 pre-event, 2022-09-05 co-event peak at 00:46 UTC / 06:16 IST, 2022-09-17 recession).
- **Digital Elevation:** MERIT Hydro / SRTM 1-arcsecond global DEM aggregated to the 1-km equal-area grid (EPSG:6933).
- **Land Cover:** ESA WorldCover 2021 v200 ($10\text{m}$ resolution) providing built-up imperviousness fractions.
- **Satellite Precipitation:** NASA GPM IMERG Final Run v06B daily calibrated rasters.
- **Ground Truth Incidents:** 24 multi-source verified incident records across 17 distinct locations, cross-referenced from official disaster management logs, traffic police advisories, and geotagged resident footage.

---

## 4. Meteorological Forecast Verification & Grouped Uncertainty

Evaluation of 256 paired forecast-observation records revealed:
- **Continuous Metrics:** $\text{MAE} = 18.64\text{ mm}$, $\text{RMSE} = 33.19\text{ mm}$, $\text{Mean Bias} = -10.88\text{ mm}$, $\text{Pearson } r = 0.1421$, $\text{Spearman } \rho = 0.3635$ ($p = 2.04 \times 10^{-9}$).
- **Categorical Skill:** High skill on rain occurrence ($\text{POD} = 0.884, \text{CSI} = 0.788$ at $\ge 2.5\text{ mm}$), moderate skill on routine monsoon rain ($\text{POD} = 0.480, \text{CSI} = 0.395$ at $\ge 15.6\text{ mm}$), and zero skill on convective extremes ($\text{POD} = 0.00$ at $\ge 35.5\text{ mm}$, $\ge 64.5\text{ mm}$, and $\ge 115.6\text{ mm}$).
- **The Convective Scale Mismatch:** GFS simulates an areal average across $\sim 750\text{ km}^2$. It smoothed localized $130 - 162\text{ mm}$ convective cores down to grid averages of $\le 38.7\text{ mm}$.
- **Dependence-Aware Uncertainty:** Date-clustered block bootstrapping across 16 daily cycles revealed that naive i.i.d. statistics underestimate uncertainty by **$3.1\times$ to $4.2\times$**. The true 95% CI for Pearson $r$ is **$[-0.07, +0.50]$**, proving that linear correlation is not statistically significant at $\alpha = 0.05$.

---

## 5. Spaceborne Remote Sensing (Sentinel-1 SAR) Analysis

Cross-validation of Sentinel-1A C-band backscatter against the 13 verified inundation cells demonstrated:
- **Apparent vs. True Sensitivity:** The apparent agreement was $76.9\%$ ($10/13$). However, deconstruction revealed that 4 cells were pre-existing permanent lakes ($\Delta\sigma^0 = 0.0\text{ dB}$) and 1 cell exhibited double-bounce backscatter increase ($+0.02\text{ dB}$).
- **True Specular Flood Sensitivity:** Only **$38.5\%$** ($5/13$) exhibited true negative backscatter drops from flood water expansion.
- **Urban Street Canyon Blindness:** In $23.1\%$ of cases ($3/13$), dense multi-story buildings and mature roadside tree canopies completely attenuated the $5.6\text{ cm}$ radar pulse, rendering street inundation invisible to satellite radar.

---

## 6. Deterministic Terrain Hydrology & Depression Routing

- **Routing Implementation:** Implemented D8 flow direction and recursive area accumulation, yielding contributing areas from $1.0\text{ km}^2$ to $186.0\text{ km}^2$, and TWI from $10.08$ to $19.04$.
- **Depression Sensitivity:** Priority-flood filling eliminated 19 natural closed basins (max depth $4.85\text{m}$), altering downstream flow accumulation by up to $12.0\text{ km}^2$. While necessary for continuous macro-routing, pit filling removes urban lake retention capacity.
- **ROC-AUC Deconstruction:** The dynamic HIPI index achieved $\text{ROC-AUC} = 0.560$ on ground truth ($N=20$). Hanley & McNeil analytical standard error ($\text{SE} = 0.129$) established a 95% confidence interval of **$[0.303, 0.817]$**, completely encompassing random chance ($0.500$). 
- **Physical Reason:** Urban flooding is triggered by sub-grid bottlenecks ($1\text{m} - 2\text{m}$ drain culvert silting, compound walls) that are invisible in 1-km DEMs.

---

## 7. Ground Truth Evidence & Observational Censorship

- **Domain Accounting:** 13 positive cells ($1.11\%$), 7 monitored negative cells ($0.60\%$), and **1,150 unobserved cells ($98.29\%$)**.
- **Negative Control Protocol:** Negatives were restricted to 5 high-elevation ridges ($915 - 938\text{m}$) and 2 engineered lowlands (Cubbon Park bioswale, Ulsoor Lake sluice). No unobserved cell was assumed dry.
- **Supervised ML Gate:** With $98.29\%$ domain censorship, training supervised classifiers introduces fatal spatial selection bias. The Supervised ML Gate was formally marked **`BLOCKED_BY_INSUFFICIENT_EVIDENCE`**.

---

## 8. Platform Architecture & Dashboard Engineering

- **Architecture:** Lightweight, zero-external-server architecture using standard library `http.server.HTTPServer` with `ThreadingMixIn` and client-side Leaflet.js.
- **Endpoints:** 15 live REST API endpoints (`/api/summary`, `/api/phase6/*`, `/api/phase7/*`) returning HTTP 200 OK.
- **Software Verification:** 101 unit/integration tests pass with 100% pass rate. 68 datasets verified bit-for-bit across 5 manifests.

---

## 9. Synthesis of Scientific Findings & Limitations

1. Global NWP provides regional monsoon volume, but cannot serve as a direct flash flood warning trigger without convective downscaling.
2. Spaceborne SAR is highly effective for rural/lake flood mapping, but unreliable for dense urban street canyons.
3. 1-km topographic indices describe macro-catchment drainage, but cannot predict localized urban inundation depths.
4. AI/ML flood prediction models cannot be scientifically justified without high-density municipal telemetry.

---

## 10. Future Research Directions & Conclusion

To advance from exploratory risk indicators to operational flood forecasting, future research must:
1. Integrate convective-permitting mesoscale models (e.g. WRF $\le 3\text{ km}$) and X-band radar nowcasting.
2. Acquire bare-earth LiDAR DTMs ($\le 2\text{m}$) and surveyed GIS layers of urban stormwater drains.
3. Deploy IoT ultrasonic water-level sensors in major Rajakaluves and lake sluice gates.
4. Develop coupled 1D/2D urban hydrodynamic models (e.g. SWMM / LISFLOOD-FP).

In conclusion, this project provides a reproducible, scientifically defensible platform that establishes the true boundaries of satellite and meteorological flood intelligence, ensuring academic integrity and operational safety.

