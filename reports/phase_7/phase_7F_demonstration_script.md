# Phase 7F — Live Demonstration Script & Presentation Walkthrough

**Document Identifier:** `reports/phase_7/phase_7F_demonstration_script.md`  
**Target Duration:** 15 Minutes Presentation + 5 Minutes Live Console Demonstration  
**Audience:** Academic Committee, Project Reviewers, and Examination Board  
**Status:** **`PRESENTATION_GUIDE`**  

---

## Part 1: Slide Presentation (15 Minutes)

### Slide 1: Title & Motivation (2 min)
- **Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data.
- **Core Research Question:** Can freely available satellite remote sensing (Sentinel-1) and global numerical weather prediction (NOAA GFS) provide reliable early detection of urban flood risks in tropical cities like Bengaluru?
- **Key Message:** Moving from black-box synthetic claims to empirical authenticity, rigorous physical validation, and transparent uncertainty quantification.

### Slide 2: Urban Flood Context — Bengaluru 2022 Deluge (2 min)
- Geographical setting: Granitic ridge watershed divide between Cauvery and Ponnaiyar basins ($900\text{m}$ elevation).
- Rapid urban growth: $1,000\%$ built-up expansion encroached on natural lake cascades (*Kere*) and stormwater channels (*Rajakaluves*).
- Deluge: Extreme convective downpours on August 30 and September 4–5, 2022 dumped up to $162\text{ mm}$ in 24 hours, submerging tech corridors and residential layouts up to $2.5\text{m}$ depth.

### Slide 3: Genuine NWP Acquisition & The 6-Node Grid Reality (3 min)
- Show provenance: 170 authentic GFS GRIB2 slices acquired directly from AWS Open Data (`s3://noaa-gfs-bdp-pds`) and decoded with ECMWF `ecCodes`.
- Explain resolution reality: GFS native resolution is $0.25^\circ \approx 27.75\text{ km}$. The entire $1,170\text{ km}^2$ study domain is covered by **exactly 6 native GFS grid nodes**.
- Demystify the 198,900 archive rows: $170 \text{ slices} \times 1,170 \text{ cells} = 198,900$, but each slice contains at most 6 distinct numerical values mapped via nearest-neighbor attribution.

### Slide 4: Forecast Skill & The Convective Scale Mismatch (3 min)
- Ground truth: 16 primary rain gauges (3 IMD, 13 KSNDMC BBMP TRGs), 256 matched pairs.
- Continuous skill: $\text{MAE} = 18.64\text{ mm}$, $\text{Bias} = -10.88\text{ mm}$, Pearson $r = 0.142$, Spearman $\rho = 0.364$.
- The $\text{POD} = 0.00$ Paradox: At heavy rainfall ($\ge 64.5\text{ mm}$), POD was $0.00$ ($0$ hits, $23$ misses).
- Physical Explanation: GFS averages over $750\text{ km}^2$, smoothing localized convective cloudbursts ($>130\text{ mm}$) down to $\le 38.7\text{ mm}$ grid means. Global NWP cannot trigger flash flood warnings without downscaling.

### Slide 5: Sentinel-1 SAR Remote Sensing & Urban Radar Blindness (3 min)
- Sentinel-1A C-band capture at peak flood: September 5, 2022 at 06:16 AM IST.
- Apparent agreement: $76.9\%$ ($10/13$).
- Deconstruction: 4 cells were pre-existing permanent lakes ($\Delta\sigma^0 = 0.0\text{ dB}$), 1 cell had double-bounce backscatter increase ($+0.02\text{ dB}$).
- True specular flood expansion: $38.5\%$ ($5/13$).
- Street canyon blindness: In 3 urban cells, dense multi-story buildings and tree canopies completely attenuated radar pulses ($\Delta\sigma^0 = 0.0\text{ dB}$).

### Slide 6: Terrain Hydrology & AI Ethics (2 min)
- Deterministic D8 routing and TWI ($10.08 - 19.04$) on 1-km grid.
- $\text{ROC-AUC} = 0.560$ on ground truth ($N=20$), 95% CI $[0.303, 0.817]$ spans $0.500$ (random chance). Explains why 1-km macro-topography cannot resolve 2-meter culverts.
- Supervised ML Gate: $98.29\%$ of the city is unobserved. Supervised ML is strictly **`BLOCKED_BY_INSUFFICIENT_EVIDENCE`** to prevent catastrophic spatial bias.

---

## Part 2: Live Platform Demonstration (5 Minutes)

### Step 1: Launch Server and Access Web Console
1. Run `.venv\Scripts\python -m floodrisk.dashboard.server`.
2. Open browser at `http://127.0.0.1:8501/`.

### Step 2: Show Interactive Leaflet Surveillance Console
1. Display the 1,170 equal-area 1-km cells.
2. Toggle between **Static Flood Susceptibility**, **24h GFS Forecast Rainfall**, and **HIPI Inundation Potential**.
3. Point out the coarse GFS grid node outlines and the prominent resolution disclaimer banner.
4. Click on a cell in Mahadevapura / Bellandur to show its elevation, slope, TWI, and nearest GFS node.

### Step 3: Demonstrate Phase 6 Authentic Datasets Tab
1. Show the **Ground Rain-Gauge Registry**: Point out the 16 primary meteorological stations and the quarantined CPCB air quality stations.
2. Show the **Ground Truth Flood Evidence Matrix**: Show the 13 positive cells, 7 monitored negative control cells, and highlight the 1,150 unobserved cells.
3. Show the **Supervised ML Gate Status Badge**: Display the formal `BLOCKED_BY_INSUFFICIENT_EVIDENCE` status.

### Step 4: Demonstrate Phase 7 Research & Uncertainty Tab
1. Display the **Grouped Bootstrap Uncertainty Table**: Show how date-clustering widens confidence intervals by $3.1\times$ to $4.2\times$, revealing that Pearson $r$ confidence interval spans zero.
2. Show the **Depression Sensitivity Table**: Compare Representation A (depressions kept) vs Representation B (priority-flood filled).
3. Query live API in terminal: `curl http://127.0.0.1:8501/api/phase7/uncertainty`.

