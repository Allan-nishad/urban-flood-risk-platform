# Data Sources, Specifications, and Methodological Limitations

**Project:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Phase:** 1 — Data Foundation & Spatial Architecture  
**Geographic Scope:** Bengaluru Urban (Initial) | Karnataka & Pan-India (Architecture-Ready)

---

## 1. Core Principles of the Data Architecture

1. **Susceptibility vs. Risk vs. Forecasting Distinction:**
   - **Flood Susceptibility:** Static geographical, topographical, and hydrological characteristics (e.g., elevation depressions, slope, upstream contributing area, soil permeability, impervious surface fraction) that make an area predisposed to water accumulation.
   - **Short-Term Flood Risk:** Dynamic hazard level influenced by real-time antecedent rainfall accumulation, soil saturation, and immediate storm events interacting with terrain susceptibility.
   - **Flood Forecasting:** A time-specific, probabilistic or deterministic prediction conditioned on numerical weather forecasts, antecedent state, and calibrated with historically verified inundation labels.
   - *Rule:* Terrain-based screening scores must never be labeled or presented as validated flood forecasts.

2. **No Data Fabrication:**
   - No synthetic observations or unverified labels are ever treated as real ground truth.
   - Missing data is reported explicitly; invalid or physically implausible records are quarantined with reasons, never silently omitted or interpolated without documentation.

3. **India-Wide Spatial Stability (EPSG:6933):**
   - The platform uses a globally anchored equal-area projection (**EPSG:6933**, WGS 84 / NSIDC EASE-Grid 2.0 Global; Lambert Cylindrical Equal Area).
   - Cell coordinates are computed using global origin `(0.0, 0.0)` in meters:
     $$\text{col} = \lfloor x / 1000 \rfloor, \quad \text{row} = \lfloor y / 1000 \rfloor$$
   - Standardized Cell ID: `g{cell_size_m}_{col}_{row}` (e.g. `g1000_7472_1625`).
   - This guarantees that cell IDs are invariant whether processing Bengaluru Urban, Bengaluru Rural, Mysuru, the Cauvery basin, Karnataka, or all of India.

---

## 2. Ingested & Planned Data Sources

### A. Rainfall: NASA GPM IMERG V07 & IMD Gridded

- **NASA GPM IMERG V07 (Final & Early Runs):**
  - *Provider:* NASA Goddard Earth Sciences Data and Information Services Center (GES DISC).
  - *Product Version:* GPM_3IMERGHH V07B (Half-Hourly) / GPM_3IMERGDF (Daily).
  - *Spatial Resolution:* $0.1^\circ \times 0.1^\circ$ (~10 km at the equator; ~9.7 km over Bengaluru).
  - *Temporal Resolution:* 30-minute half-hourly / Daily.
  - *Native Units & Dynamic Verification:*
    - Half-hourly Level 3 (`precipitationCal`): units are `mm/hr` (instantaneous/calibrated precipitation rate).
      $$\text{Accumulated Depth (mm)} = \text{precipitationCal [mm/hr]} \times 0.5 \text{ hours}$$
    - Daily Level 3 (`precipitation`): units are `mm` or `mm/day` (accumulated depth over 24-hr period).
      $$\text{Accumulated Depth (mm)} = \text{precipitation [mm]} \times 1.0$$
    - *Critical Rule:* The engine inspects variable metadata dynamically via `parse_and_validate_rainfall_units()`. It never multiplies by 0.5 automatically without metadata verification.
  - *Latency:* ~3.5 months for calibrated Final Run (research/historical validation); 4 hours for Early Run (operational alert pipeline).

- **IMD Gridded Daily Rainfall (Reference Validation):**
  - *Provider:* India Meteorological Department (IMD Pune).
  - *Spatial Resolution:* $0.25^\circ \times 0.25^\circ$ (~27 km).
  - *Temporal Resolution:* Daily (08:30 IST to 08:30 IST).
  - *Native Units:* $\text{mm/day}$ accumulated depth.
  - *Role:* Cross-validation baseline for satellite-derived precipitation. Identity factor (1.0).

### B. Terrain: SRTM GL1 30m DEM

- *Provider:* NASA / USGS / JPL.
- *Native Spatial Resolution:* 1 arc-second (~30 meters).
- *Native CRS:* EPSG:4326 (WGS84 horizontal, EGM96 geoid vertical).
- *Vertical Units:* Meters above sea level (Int16).
- *Nodata Value:* -32768.
- *Aggregation to 1-km Grid:*
  - Sub-pixel statistics per 1-km equal-area cell: mean elevation, min elevation, max elevation, standard deviation of elevation, and slope.
  - *Scientific Note:* A 1-km modeling grid cell aggregating 30-meter elevation pixels captures *macro-topographic depressions and regional drainage sinks*. It does *not* claim 30-meter localized curb-scale hydraulic precision.

### C. Hydrology: MERIT Hydro

- *Provider:* Yamazaki Lab, Institute of Industrial Science, University of Tokyo.
- *Native Resolution:* 3 arc-seconds (~90 meters).
- *Key Layers:*
  - `upa`: Upstream Contributing Area in $\text{km}^2$ (Float32). Nodata: -9999.0.
  - `elv`: Hydrologically conditioned elevation (Float32).
  - `dir`: D8 Flow Direction (UInt8).
- *Aggregation:* Maximum and mean upstream contributing area per 1-km grid cell to quantify regional surface runoff influx.

### D. Land Cover: ESA WorldCover 10m

- *Provider:* European Space Agency (ESA) / VITO Remote Sensing.
- *Product Version:* v200 (Reference Year 2021) / v100 (2020).
- *Resolution:* 10 meters.
- *Classes of Interest:* Class 50 (Built-up / Impervious), Class 80 (Permanent water bodies), Class 90 (Herbaceous wetland), Classes 10–40 (Vegetation / Open ground).
- *Aggregation:* Fractional land cover percentages per 1-km equal-area grid cell.

### E. Weather Forecasts (NWP) & Leakage Prevention

- *Providers:* IMD NCUM (4 km / 12 km), ECMWF HRES (9 km), NOAA GFS ($0.25^\circ$).
- *Temporal Separation Requirement:*
  - Forecasts must record both `forecast_issue_time` (UTC cycle timestamp) and `valid_time` (target precipitation period).
  - *Information Leakage Rule:* In retrospective backtesting, any forecast with `forecast_issue_time > decision_timestamp` is strictly quarantined. Only forecasts that would have been physically accessible prior to the event are admissible.

### F. Historical Flood Events & Inundation Inventory

- *Investigated Sources:* BBMP Disaster Management Cell, KSNDMC, KSRSAC, CWC/NDMA, Dartmouth Flood Observatory.
- *Feasibility Finding:* **For continuous, machine-readable, daily historical flood inundation labels across 1-km grid cells in Bengaluru Urban: "No usable data found."**
- *Operational Hotspot Registers:* BBMP maintains static point inventories (~210 hotspots), while KSNDMC issues qualitative ward alerts. No open automated daily time series exists.
- *Fidelity Safeguards:*
  - Coarse district- or taluk-level flood records are never assigned to individual 1-km cells.
  - Flood-event labels are never inferred from rainfall.
  - Supervised training is prohibited until empirical ground-truth masks are acquired via formal institutional agreements or derived via satellite SAR change detection (e.g. Sentinel-1 for verified extreme storms).

---

## 3. Equal-Area Grid Distortion Characteristics (EPSG:6933)

The platform adopts **EPSG:6933** (`WGS 84 / NSIDC EASE-Grid 2.0 Global`; projection method: `Lambert Cylindrical Equal Area`, EPSG:9835, standard parallel $30^\circ\text{N/S}$) to ensure that every 1-km cell has an exact, globally comparable surface area footprint:

1. **Area Preservation ($1.000000 \text{ km}^2$):**
   - By definition, equal-area projections preserve the surface area ratio globally:
     $$\text{Geodesic Area on WGS84 Ellipsoid} \approx 1,000,000.0 \text{ m}^2 \quad (\text{Ratio} = 1.000000)$$
2. **Linear Scale and Angular Distortion:**
   - Because Earth is an oblate spheroid, preserving area on a plane requires reciprocal scale distortion: $h \times k = 1$.
   - At Bengaluru's latitude ($\approx 13^\circ\text{N}$):
     - **East-West edges (parallels):** stretched by $+12.4\%$ ($\text{length} \approx 1,124.38\text{ m}$; ratio $\approx 1.124376$).
     - **North-South edges (meridians):** compressed by $-11.1\%$ ($\text{length} \approx 889.40\text{ m}$; ratio $\approx 0.889397$).
     - **Product of scale factors:** $1.124376 \times 0.889397 = 1.000016 \approx 1.000000$.
   - *Limitation:* Grid cells on the map appear slightly wider east-to-west than tall north-to-south. This is normal and expected for cylindrical equal-area projections, ensuring that hydrological flux and zonal satellite accumulations are mathematically unbiased by latitude.

---

## 4. Boundary Lineage, Coverage Fractions & Licensing

### Bengaluru Urban District Boundary
- **Current Status:** `pending_authoritative_boundary`.
- **Development Extent:** Bounding box $[77.45^\circ\text{E}, 12.85^\circ\text{N}]$ to $[77.75^\circ\text{E}, 13.15^\circ\text{N}]$.
- **Cell Classification:**
  - `fraction_inside_boundary`: calculated as $\text{Area}(\text{cell} \cap \text{boundary}) / \text{Area}(\text{cell})$.
  - Fully inside: 1,036 cells ($\ge 99.99\%$).
  - Partially intersecting: 134 cells ($0 < \text{fraction} < 99.99\%$).
- **Authoritative Ingestion & Alternative Boundary Datasets:**
  - *Survey of India (SOI) / KSRSAC:* The primary official standard. Pending direct upload into `data/external/boundaries/bengaluru_urban.geojson`.
  - *DataMeet / OpenStreetMap (OSM) Alternative Boundaries:*
    - DataMeet Community Spatial Repository (ODbL / Creative Commons) and OSM provide community-digitized district boundaries.
    - *Caveat:* Non-governmental status; boundaries may exhibit slight topological shifts along municipal borders compared to SOI Survey Sheets. If utilized, their non-official lineage must be explicitly recorded.

---

## 5. Current Platform Limitations (Phase 1)

1. **Grid Resolution vs. Micro-Hydraulics:**
   - 1,000-meter ($1\text{ km}^2$) grid cells are designed for district, state, and national regional flood risk screening and daily forecast modeling.
   - Stormwater drain (rajakaluve) blockages, localized culvert overflows, and building-level basement flooding require hydraulic hydrodynamic models (e.g., SWMM, LISFLOOD-FP) and sub-10m digital surface models (DSM). Phase 1 establishes the regional data backbone.

2. **Temporal Granularity:**
   - Initial canonical rainfall schema supports hourly and daily accumulations. Sub-hourly flash flood modeling requires telemetry from high-frequency automatic weather stations (AWS/ARG).

3. **External Dataset Access:**
   - Satellite datasets (SRTM, GPM IMERG, ESA WorldCover) and official SOI administrative boundaries require user credentials or local network access. The ingestion and validation interfaces are fully implemented, tested, and ready to receive production feeds.

