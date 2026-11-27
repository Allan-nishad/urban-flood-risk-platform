# QGIS Desktop GIS Implementation Methodology & Cartographic Standard

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Repository:** `urban-flood-risk-platform`  
**Deliverable Scope:** Phase QGIS-2 Desktop GIS Supplementary Implementation  
**Target Project File:** `reports/qgis_final/Bengaluru_Urban_Flood_Risk.qgz`  
**Author:** Geospatial Systems Specialist & Independent Technical Audit Team  
**Date:** November 2026  

---

## 1. Executive Summary & Objective

The objective of **Phase QGIS-2** is to create a professional, reproducible, and fully organized desktop GIS project in **QGIS** (`.qgz`) using the existing verified spatial datasets and analytical outputs produced across Phases 1 through 7.2 of the Urban Flood Risk Platform.

The QGIS desktop project is engineered as a **supplementary desktop GIS implementation** that allows researchers, municipal planners, and academic examiners to independently visualize, query, and inspect every layer of the flood-risk platform within an industry-standard GIS environment.

### Strict Governance & Non-Modification Constraints:
1. **Source Data Immutability:** No existing raw, interim, or processed datasets were modified, overwritten, or deleted.
2. **Algorithm Preservation:** No hydrologic or meteorological algorithms were altered or rerun.
3. **Baseline & Manifest Integrity:** All historical manifests and their cryptographic SHA-256 ledgers remain 100% frozen.
4. **Zero Geometry Fabrication:** No missing official municipal ward boundaries or drainage line shapefiles were fabricated.
5. **Observational Truth:** Unobserved grid cells ($98.29\%$) remain explicitly labeled as unobserved; they are never converted into negative flood training labels.
6. **Probabilistic Discipline:** Risk scores are explicitly labeled as **uncalibrated prioritization indices**, never as calibrated flood probabilities.
7. **Isolated Output Directory:** All derived GeoPackages, map prints, and project archives reside exclusively in `reports/qgis_final/`.

---

## 2. Spatial Data Integration & Layer Preparation Methodology

### 2.1 The Master 1,170-Cell Equal-Area Grid
* **Geometry Source:** `data/processed/grid_bengaluru_urban_1000m.gpkg` (EPSG:6933, World Cylindrical Equal Area).
* **Grid Properties:** $30 \text{ columns} \times 39 \text{ rows} = 1,170 \text{ regular cells}$, each spanning exactly $1,000\text{m} \times 1,000\text{m} = 1.0\text{ km}^2$.
* **Boundary Definition:** The grid represents the rectangular provisional development study domain encompassing the greater Bengaluru metropolitan core ($77.44^\circ - 77.75^\circ\text{E}, 12.84^\circ - 13.16^\circ\text{N}$). As documented in Phase 4.1, official BBMP 198-ward administrative boundaries remain `PENDING_AUTHORITATIVE`.
* **Study Extent Outline:** Derived via geometric union (dissolve) of all 1,170 cells, creating `reports/qgis_final/study_extent_outline.gpkg` to represent the outer bounding envelope.

### 2.2 Relational Attribute Joins via Primary Key `grid_id`
In desktop GIS, analytical Parquet tables cannot always be opened directly by older GDAL builds. To ensure universal compatibility, all verified analytical attributes were joined 1-to-1 to the master grid using the string primary key `grid_id`:

```
+-------------------------------------------------------------------------------+
|                      RELATIONAL ATTRIBUTE JOIN SCHEMA                         |
+-------------------------------------------------------------------------------+
| PRIMARY VECTOR:                                                               |
|   grid_bengaluru_urban_1000m.gpkg [1,170 Polygons | EPSG:6933]                |
|                                                                               |
| JOINED ATTRIBUTE TABLES (1-to-1 match on 'grid_id'):                          |
|   1. topographic_routing_static_features.parquet                             |
|      -> upstream_contributing_area_km2, topographic_wetness_index, slope_deg   |
|   2. dynamic_risk_intelligence_bengaluru.parquet                              |
|      -> dynamic_risk_prioritization_score, static_susceptibility_score, rank  |
|   3. flood_validation_ground_truth_matrix.parquet                             |
|      -> observation_status, evidence_class, water_depth_est_m                 |
|   4. phase7_hydrology_comparison.parquet                                      |
|      -> depression_depth_m, is_closed_sink, flow_acc_conditioned_km2          |
|                                                                               |
| OUTPUT:                                                                       |
|   reports/qgis_final/bengaluru_study_grid.gpkg      [Native EPSG:6933]        |
|   reports/qgis_final/bengaluru_study_grid_wgs84.gpkg[Exported EPSG:4326]      |
+-------------------------------------------------------------------------------+
```

* **Join Verification:** Exactly 1,170 input rows merged with 1,170 grid features ($0\text{ unmatched}$, $0\text{ duplicate keys}$, $0\text{ null keys}$).
* **Integrity of Nulls:** Unobserved cells retain explicit `UNOBSERVED_DOMAIN_CELL` status; no nulls are filled with zero or negative assumptions.

### 2.3 Point Vector Generation
Two verified spatial point layers were extracted from tabular sources:
1. **Rain Gauge Stations (`rain_gauge_stations.gpkg`):** 21 point records extracted from `rain_gauge_station_registry.parquet`, containing station name, network (IMD / KSNDMC / CPCB), elevation, and primary hydrological gauge flag.
2. **Historical Flood Incidents (`flood_incident_points.gpkg`):** 24 deluge incident point records extracted from `independent_flood_incident_inventory.parquet`, containing location name, date, reported minimum/maximum flood depth, and hydraulic mechanism.

---

## 3. QGIS Layer Group Organization & Cartographic Styling

The QGIS project (`Bengaluru_Urban_Flood_Risk.qgz`) is structured into six hierarchical layer groups:

### Group A: Study Area & Grid
* **Study Extent Boundary Outline (1,170 km²):** Inverted hollow polygon with a solid `#0f172a` slate outline (width: 0.8 mm), defining the study domain.
* **Bengaluru 1-km Grid Mesh (WGS 84):** Hollow polygon grid with thin `#64748b` borders (width: 0.2 mm), enabling interactive cell inspection.
* **Bengaluru 1-km Equal-Area Grid (Native EPSG:6933):** Preserved for geodesic area calculations and projection verification.

### Group B: Terrain & Land Cover
* **NASA SRTM 30m Digital Elevation Model:** GeoTIFF raster displayed with a Singleband Pseudocolor terrain ramp (780m to 1,020m ASL), showing high ridges and drainage valleys.
* **ESA WorldCover 10m Land Cover (2021):** GeoTIFF raster displayed with official ESA categorical colors (Red = Built-up, Green = Tree cover, Blue = Water, Pink = Cropland, Yellow = Grassland).
* **Sentinel-1A SAR Co-Flood Backscatter (2022-09-05):** Singleband gray image displaying radar return intensity at 06:16 AM during peak flooding.

### Group C: Hydrology & Catchment Drainage
* **19 DEM-Derived Depression Sinks (Depth up to 4.85m):** Highlighted using rule-based filtering (`"is_closed_sink" = 1`), rendered with a red outline (`#dc2626`) and diagonal hatching.
* **D8 Catchment Flow Accumulation (km²):** Graduated blue color ramp classified into four catchment scales:
  * $< 5\text{ km}^2$: Headwater drainage swales
  * $5 - 20\text{ km}^2$: Mid-slope drainage swales
  * $20 - 50\text{ km}^2$: Major valley floor convergence
  * $> 50\text{ km}^2$: Regional trunk drainage
* **Topographic Wetness Index (SAGA TWI):** Graduated green-blue ramp ($10.08$ on ridges to $19.04$ on valley floors).
* **Permanent Lake & Water Mask (Sentinel-1):** Binary water mask displaying permanent water bodies in `#0064c8`.

### Group D: Flood Evidence & Ground Truth
* **Ground Truth Classification (13 Pos / 7 Proxy / 1,150 Unobserved):**
  * `VERIFIED_POSITIVE` (13 cells, $1.11\%$): Solid dark red fill (`#dc2626`) with cross-hatch.
  * `VERIFIED_NEGATIVE` (7 cells, $0.60\%$): Solid green outline (`#16a34a`). Explicitly labeled as **Monitored Negative Proxy Cells**, never "confirmed dry ground".
  * `UNOBSERVED_DOMAIN_CELL` (1,150 cells, $98.29\%$): Pale slate-grey fill (`#f1f5f9`) with thin gray border, maintaining full transparency regarding unobserved territory.

### Group E: Risk Assessment
* **Uncalibrated Flood-Risk Prioritisation Index — Not Flood Probability:**
  * Symbology: Graduated Yellow-Orange-Red (`YlOrRd`) color ramp classified into quartiles ($<0.30, 0.30-0.55, 0.55-0.75, >0.75$).
  * Mandatory Label: Clearly informs users that the score is an exploratory multi-criteria ranking index, not an actuarial flood probability.
* **Static Multi-Criteria Susceptibility (MCDA):** Baseline terrain and impervious surface susceptibility score.

### Group F: Weather and Rainfall
* **Rain Gauge Stations (21 Stations):** Rendered as blue triangles (`#2563eb`, 4.5 mm) with black outlines.
* **Historical Deluge Incidents (24 Records / 17 Locations):** Rendered as red circles (`#dc2626`, 4.0 mm) with white outlines.

---

## 4. Professional Cartographic Print Layout Specifications

Five publication-grade print layouts were designed and exported as both **300 DPI high-resolution PNG** and **vector/raster PDF** in `reports/qgis_final/`:

| Layout File (PNG & PDF) | Layout Title & Focus | Cartographic Elements Included |
|---|---|---|
| **`layout1_study_area_and_grid`** | Bengaluru Urban Study Area and 1-km Analytical Grid | Map canvas, boundary outline, grid mesh, rain gauges, flood incidents, north arrow, 10-km scale bar, source credits, provisional bbox disclaimer. |
| **`layout2_elevation_and_terrain`** | Bengaluru Urban Topography & Digital Elevation Model | SRTM 30m continuous elevation basemap, terrain color ramp, elevation color bar (meters ASL), grid mesh, north arrow, scale bar, DEM resolution disclaimer. |
| **`layout3_land_cover`** | Bengaluru Urban Land Cover & Impervious Surface Distribution | ESA WorldCover 10m raster, official class legend (Built-up, Tree cover, Water, Crop), boundary outline, north arrow, scale bar, infiltration disclaimer. |
| **`layout4_hydrological_indicators`** | Bengaluru Urban Catchment Hydrology & Flow Accumulation | 4-tier flow accumulation graduated polygons, 19 DEM depression sinks with red hatch, north arrow, scale bar, macro-hydrology disclaimer. |
| **`layout5_flood_evidence_and_risk`** | Bengaluru Flood Evidence & Dynamic Risk Prioritisation | Dynamic prioritization index, 13 positive cells, 7 negative proxies, 1,150 unobserved cells, incident points, stations, north arrow, scale bar, **Uncalibrated Index Disclaimer**. |

---

## 5. QGIS Project Technical Structure (`.qgz`)

The primary deliverable `reports/qgis_final/Bengaluru_Urban_Flood_Risk.qgz` is an OGC-compliant QGIS project archive containing:
* `Bengaluru_Urban_Flood_Risk.qgs`: The XML project definition file (23,801 bytes).
* **Relative Data Paths:**
  * Derived GeoPackages: `./bengaluru_study_grid_wgs84.gpkg`, `./study_extent_outline.gpkg`, etc.
  * Raw and processed rasters: `../../data/raw/...` and `../../data/processed/...`.
  * Allows the entire repository to be moved or shared without breaking layer file paths.
* **Coordinate Handling:** Project CRS is configured to **`EPSG:4326` (WGS 84)** with On-The-Fly (OTF) reprojection active, seamlessly overlaying native equal-area layers (`EPSG:6933`) and raster basemaps (`EPSG:4326`).

---

## 6. Scientific Limitations & Governance Declarations

1. **Provisional Development Extent:** The outer polygon outline reflects the 1,170 km² analysis grid bounding box ($30 \times 39\text{ km}$), not the legal municipal administrative boundary of BBMP or Bengaluru Urban district.
2. **Observational Domain Censorship ($98.29\%$):** The vast majority of Bengaluru ($1,150 / 1,170\text{ cells}$) is unobserved by ground sensors. Absence of flood symbols in unobserved cells must never be interpreted as verified safety.
3. **Uncalibrated Index:** The Dynamic Prioritisation score is a multi-criteria screening indicator. It does not represent physical inundation depth or statistical flood return periods.

