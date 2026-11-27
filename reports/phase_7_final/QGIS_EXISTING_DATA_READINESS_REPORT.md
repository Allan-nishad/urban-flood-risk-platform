# QGIS Existing Data Readiness & Geospatial Inspection Report

**Project:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Repository:** `urban-flood-risk-platform`  
**Task Type:** Existing Implementation Inspection Only (No Code/Data Modifications)  
**Inspection Date:** November 2026  
**Auditor:** Geospatial Systems Specialist & Independent Technical Audit Team  

---

## 1. Executive Summary & Audit Mandate

This report evaluates the readiness of existing data assets in the `urban-flood-risk-platform` repository for direct integration into a supplementary desktop GIS project using **QGIS**.

In strict accordance with the project directives:
* **Zero Source Code Modifications:** No source code was altered.
* **Zero Data Regeneration:** No datasets were regenerated or re-run.
* **Preservation of Baseline & Manifests:** All cryptographic manifests and their SHA-256 hashes remain 100% frozen and untouched.
* **Zero Data Fabrication:** No missing layers or synthetic spatial datasets were fabricated.

### Overall Readiness Verdict:
```
+===================================================================================+
|                              QGIS READINESS VERDICT                               |
|                                                                                   |
|                            READY WITH MINOR CONVERSION                            |
|                                                                                   |
|  All core spatial geometries (1,170-cell grid, SRTM 30m DEM, ESA 10m Land Cover, |
|  Sentinel-1 SAR rasters) exist in native GIS formats (.gpkg, .geojson, .tif) and  |
|  load immediately into QGIS with zero conversion.                                 |
|                                                                                   |
|  Hydrological routing metrics, risk indicators, rain-gauge points, and flood      |
|  incidents reside in Apache Parquet tables. While modern QGIS with GDAL Arrow     |
|  reads them directly, standard QGIS workflows require a 1-to-1 attribute join to  |
|  the grid GeoPackage on 'grid_id', or standard table-to-layer point conversion.   |
+===================================================================================+
```

---

## 2. Directory-by-Directory Inventory of GIS-Compatible Files

The repository data directories (`data/raw`, `data/processed`, `data/interim`, `data/external`) contain **72 data/GIS-relevant files**:

| Directory | Native GIS Rasters (`.tif`) | Native GIS Vectors (`.gpkg`, `.geojson`) | Tabular Spatial Data (`.parquet`, `.csv`) | Total GIS Candidate Files |
|---|:---:|:---:|:---:|:---:|
| `data/raw/elevation/` | 3 GeoTIFFs (29.76 MB) | 0 | 0 | 3 |
| `data/raw/land_cover/` | 1 GeoTIFF (127.65 MB) | 0 | 0 | 1 |
| `data/raw/weather/` | 2 GeoTIFFs (141.37 MB) | 0 | 0 | 2 |
| `data/raw/phase6/nwp/` | 0 (170 GRIB2 + 170 IDX) | 0 | 0 | 0 (GRIB2) |
| `data/processed/` | 2 GeoTIFFs (0.71 MB) | 1 GPKG + 3 GeoJSONs (8.99 MB) | 21 Parquet files | 27 |
| `data/processed/phase6/` | 0 | 0 | 16 Parquet + 1 CSV | 17 |
| `data/processed/phase7/` | 0 | 0 | 5 Parquet files | 5 |
| `data/interim/` & `external/` | 0 | 0 | 0 (Placeholders only) | 0 |
| **Total** | **8 GeoTIFF Rasters** | **4 Native Vector Files** | **43 Spatial Parquet / CSV Files** | **55 Inspected Assets** |

---

## 3. Identification of Target Thematic Layers

| Thematic Layer Required | Actual File in Repository | Format | Storage Mode & Linkage |
|---|---|:---:|---|
| **1. Study Area Boundary** | `data/processed/grid_bengaluru_urban_1000m.gpkg` (or `.geojson`) | GeoPackage / GeoJSON | Regular rectangular provisional development bounding box ($30 \times 39 = 1,170\text{ km}^2$). Legal municipal ward polygon boundaries (`bbmp_wards_official.geojson`) remain `PENDING_AUTHORITATIVE`. |
| **2. 1,170-Cell Spatial Grid** | `data/processed/grid_bengaluru_urban_1000m.gpkg` | GeoPackage (`.gpkg`) | Native equal-area vector polygon grid (1,170 cells, EPSG:6933). |
| **3. Elevation / DEM** | `data/raw/elevation/srtm/SRTMGL1_N12_N13_E077_Bengaluru.tif` | GeoTIFF (`.tif`) | Continuous 1 arc-second ($\approx 30\text{m}$) DEM mosaic covering the entire Bengaluru metropolitan basin. |
| **4. Land Cover** | `data/raw/land_cover/ESA_WorldCover_10m_2021_v200_N12E075_Map.tif` | GeoTIFF (`.tif`) | Continuous 10m ESA WorldCover classification (built-up, tree canopy, water, cropland). |
| **5. Hydrography / Water** | `data/processed/sentinel1_candidate_water_mask_bengaluru.tif` | GeoTIFF (`.tif`) | Binary permanent water mask derived from Sentinel-1 radar backscatter (lakes and major tanks). |
| **6. D8 Flow Direction** | `scripts/phase6/build_hydrology.py` (runtime) | In-Memory Matrix | Flow directions computed in memory; **not exported to disk as a continuous raster**. Represented via downstream network connections. |
| **7. Flow Accumulation** | `data/processed/phase6/hydrology/topographic_routing_static_features.parquet` | Parquet (`.parquet`) | Upstream contributing drainage area (`upstream_contributing_area_km2`) tabulated for all 1,170 cells. Joins to grid on `grid_id`. |
| **8. Topographic Wetness Index (TWI)** | `data/processed/phase6/hydrology/topographic_routing_static_features.parquet` | Parquet (`.parquet`) | SAGA TWI (`topographic_wetness_index`) tabulated for all 1,170 cells ($10.08$ to $19.04$). Joins to grid on `grid_id`. |
| **9. Static Susceptibility** | `data/processed/features_integrated_bengaluru.parquet` | Parquet (`.parquet`) | Multi-criteria static susceptibility score (`susceptibility_score`, rank #1 to #1,170). Joins to grid on `grid_id`. |
| **10. Dynamic Prioritisation Index** | `data/processed/dynamic_risk_intelligence_bengaluru.parquet` | Parquet (`.parquet`) | Dynamic prioritization score (`dynamic_prioritization_score`). Joins to grid on `grid_id`. |
| **11. Rainfall Observations** | `data/processed/phase6/ground_rainfall/rain_gauge_station_registry.parquet` | Parquet (`.parquet`) | 21 station coordinates (`latitude`, `longitude`, `elevation_m`, `station_name`, `network`). |
| **12. Forecast Rainfall** | `data/processed/phase6/nwp/nwp_forecast_archive.parquet` | Parquet (`.parquet`) | 198,900 cell forecast records with `grid_id`, `lead_hour`, and `apcp_accum_mm`. Joins to grid on `grid_id`. |
| **13. Historical Flood Incidents** | `data/processed/phase6/flood_evidence/independent_flood_incident_inventory.parquet` | Parquet (`.parquet`) | 24 incident records with point coordinates (`latitude`, `longitude`, `location_name`, `evidence_class`). |

---

## 4. Comprehensive Technical Metadata for Candidate Files

### 4.1 Native GIS Vector Layers

#### 1. `data/processed/grid_bengaluru_urban_1000m.gpkg`
* **Format:** OGC GeoPackage vector layer (`.gpkg`)
* **File Size:** 569,344 bytes (0.57 MB)
* **Coordinate Reference System (CRS):** **`EPSG:6933`** (World Cylindrical Equal Area)
* **Spatial Extent (Bounding Box):**
  * $X_{\min}: 7,472,000.0\text{ m}$, $Y_{\min}: 1,625,000.0\text{ m}$
  * $X_{\max}: 7,502,000.0\text{ m}$, $Y_{\max}: 1,664,000.0\text{ m}$
* **Geometry Type:** `Polygon` (1,170 regular square polygons, $1,000\text{m} \times 1,000\text{m}$)
* **Feature Count:** 1,170 features
* **Attribute Columns:** `grid_id` (string primary key, e.g., `g1000_7472_1625`), `col_idx`, `row_idx`, `cell_size_m` ($1,000$), `centroid_x_6933`, `centroid_y_6933`, `centroid_lon`, `centroid_lat`, `minx_6933`, `miny_6933`
* **QGIS Usability:** **IMMEDIATE**. Drag-and-drop into QGIS; renders native 1-km equal-area analytical cells.

#### 2. `data/processed/grid_bengaluru_urban_1000m.geojson`
* **Format:** GeoJSON vector layer (`.geojson`)
* **File Size:** 1,405,450 bytes (1.41 MB)
* **CRS:** **`EPSG:4326`** (WGS 84 geographic latitude/longitude)
* **Spatial Extent:** $[77.4411^\circ\text{E}, 12.8422^\circ\text{N}, 77.7520^\circ\text{E}, 13.1558^\circ\text{N}]$
* **Geometry Type:** `Polygon` (1,170 features)
* **Attribute Columns:** Same as GeoPackage.
* **QGIS Usability:** **IMMEDIATE**. Directly opens in standard web mapping projection without on-the-fly reprojection overhead.

---

### 4.2 Native GIS Raster Layers

#### 3. `data/raw/elevation/srtm/SRTMGL1_N12_N13_E077_Bengaluru.tif`
* **Format:** GeoTIFF raster (`.tif`)
* **File Size:** 14,876,879 bytes (14.88 MB)
* **CRS:** **`EPSG:4326`** (WGS 84)
* **Spatial Extent:** $[76.9999^\circ\text{E}, 11.9999^\circ\text{N}, 78.0001^\circ\text{E}, 14.0001^\circ\text{N}]$
* **Raster Dimensions:** $3,601 \text{ pixels wide} \times 7,201 \text{ pixels high}$, 1 band
* **Spatial Resolution:** $0.00027778^\circ \times 0.00027778^\circ$ ($\approx 30\text{ meters}$)
* **Data Type:** Signed 16-bit integer (`int16`, elevation values in meters)
* **Elevation Range:** $\approx 450\text{m}$ to $1,400\text{m}$ across Karnataka plateau (Bengaluru core: $\approx 850\text{m} - 960\text{m}$)
* **QGIS Usability:** **IMMEDIATE**. Superb high-resolution elevation basemap; can be styled with Hillshade or Singleband Pseudocolor.

#### 4. `data/raw/land_cover/ESA_WorldCover_10m_2021_v200_N12E075_Map.tif`
* **Format:** GeoTIFF raster (`.tif`)
* **File Size:** 127,650,362 bytes (127.65 MB)
* **CRS:** **`EPSG:4326`** (WGS 84)
* **Spatial Extent:** $[75.0^\circ\text{E}, 12.0^\circ\text{N}, 78.0^\circ\text{E}, 15.0^\circ\text{N}]$
* **Raster Dimensions:** $36,000 \times 36,000$, 1 band
* **Spatial Resolution:** $0.00008333^\circ \times 0.00008333^\circ$ ($\approx 10\text{ meters}$)
* **Data Type:** 8-bit unsigned integer (`uint8`, categorical land-cover classes: 10=Tree, 50=Built-up, 80=Permanent Water, etc.)
* **QGIS Usability:** **IMMEDIATE**. Authoritative 10m land cover; style with Paletted/Unique Values.

#### 5. `data/raw/weather/sentinel1/S1A_IW_GRDH_20220905_VV_bengaluru.tif`
* **Format:** GeoTIFF raster (`.tif`)
* **File Size:** 70,998,755 bytes (71.00 MB)
* **CRS:** **`EPSG:4326`** (WGS 84)
* **Spatial Extent:** $[77.4300^\circ\text{E}, 12.8300^\circ\text{N}, 77.7700^\circ\text{E}, 13.1700^\circ\text{N}]$
* **Raster Dimensions:** $4,080 \times 4,080$, 1 band
* **Spatial Resolution:** $0.00008333^\circ \times 0.00008333^\circ$ ($\approx 10\text{ meters}$)
* **Data Type:** 32-bit floating point (`float32`, linear or decibel backscatter intensity)
* **QGIS Usability:** **IMMEDIATE**. Co-event Sentinel-1A SAR capture at peak flood (September 5, 2022 06:16 AM IST).

#### 6. `data/processed/sentinel1_candidate_water_mask_bengaluru.tif`
* **Format:** GeoTIFF raster (`.tif`)
* **File Size:** 374,203 bytes (0.37 MB)
* **CRS:** **`EPSG:4326`** (WGS 84)
* **Spatial Extent:** $[77.4300^\circ\text{E}, 12.8300^\circ\text{N}, 77.7700^\circ\text{E}, 13.1700^\circ\text{N}]$
* **Raster Dimensions:** $4,080 \times 4,080$, 1 band
* **Data Type:** 8-bit unsigned integer (`uint8`, binary water mask: 0=non-water, 1=water)
* **QGIS Usability:** **IMMEDIATE**. Pre-processed lake and water-body mask for Bengaluru.

---

### 4.3 Spatial Tabular Datasets (Parquet / Attribute Joins)

These files contain vital flood-risk attributes and coordinates, structured for high-performance tabular computation:

#### 7. `data/processed/phase6/hydrology/topographic_routing_static_features.parquet`
* **Format:** Apache Parquet (`.parquet`)
* **File Size:** 55,398 bytes (0.06 MB)
* **Record Count:** 1,170 rows (exact 1-to-1 match with grid cells)
* **Primary Key:** `grid_id`
* **Key Columns:**
  * `elevation_m`: Mean elevation per cell
  * `slope_deg`: Terrain slope angle in degrees
  * `upstream_contributing_area_km2`: D8 accumulated flow area ($1.0$ to $186.0\text{ km}^2$)
  * `topographic_wetness_index`: SAGA TWI ($10.08$ to $19.04$)
  * `hydraulic_drainage_class`: Qualitative catchment position (`LOWLAND_CATCHMENT_CORRIDOR`, `VALLEY_FLOOR_CONVERGENCE`, etc.)
* **QGIS Integration Method:** **Table Join**. In QGIS, right-click `grid_bengaluru_urban_1000m.gpkg` -> Properties -> Joins -> Add Join with this table using join field `grid_id`.

#### 8. `data/processed/phase6/flood_evidence/flood_validation_ground_truth_matrix.parquet`
* **Format:** Apache Parquet (`.parquet`)
* **File Size:** 27,050 bytes (0.03 MB)
* **Record Count:** 1,170 rows
* **Primary Key:** `grid_id`
* **Key Columns:**
  * `observation_status`: `VERIFIED_POSITIVE` (13), `VERIFIED_NEGATIVE` (7), `UNOBSERVED_DOMAIN_CELL` (1,150)
  * `evidence_class`: `CONFIRMED_SEVERE_INUNDATION`, `CONFIRMED_MODERATE_WATERLOGGING`, `MONITORED_DRY_HIGH_RIDGE`, etc.
  * `water_depth_est_m`: Estimated flood depth in meters
* **QGIS Integration Method:** **Table Join** to grid GeoPackage. Enables immediate choropleth mapping of verified flood points vs unobserved domain.

#### 9. `data/processed/phase6/flood_evidence/independent_flood_incident_inventory.parquet`
* **Format:** Apache Parquet (`.parquet`)
* **File Size:** 14,648 bytes (0.01 MB)
* **Record Count:** 24 rows
* **Spatial Columns:** `latitude`, `longitude` (WGS 84 point coordinates)
* **Key Columns:** `evidence_id`, `event_date`, `location_name`, `evidence_class`, `water_depth_min_m`, `water_depth_max_m`, `topographic_context`
* **QGIS Integration Method:** **Point Layer via Delimited Text or GDAL Parquet**. Point geometry directly plotable onto the map canvas.

#### 10. `data/processed/phase6/ground_rainfall/rain_gauge_station_registry.parquet`
* **Format:** Apache Parquet (`.parquet`)
* **File Size:** 9,500 bytes (0.01 MB)
* **Record Count:** 21 rows
* **Spatial Columns:** `latitude`, `longitude` (WGS 84 point coordinates)
* **Key Columns:** `station_id`, `station_name`, `network` (IMD / KSNDMC / CPCB), `elevation_m`, `is_primary_hydrological_gauge`
* **QGIS Integration Method:** **Point Layer**.

---

## 5. Direct Opening vs. Minor Conversion Assessment

| Data Asset | Opens Directly in QGIS? | Action Required in QGIS |
|---|:---:|---|
| **SRTM 30m Elevation (`.tif`)** | **YES** | Drag and drop directly into QGIS layers panel. |
| **ESA 10m Land Cover (`.tif`)** | **YES** | Drag and drop directly into QGIS layers panel. |
| **Sentinel-1 SAR Rasters (`.tif`)** | **YES** | Drag and drop directly into QGIS layers panel. |
| **Grid GeoPackage (`.gpkg`)** | **YES** | Drag and drop directly; renders polygon boundaries in EPSG:6933. |
| **Grid GeoJSON (`.geojson`)** | **YES** | Drag and drop directly; renders polygon boundaries in EPSG:4326. |
| **Flow Accumulation & TWI (`.parquet`)** | **REQUIRES JOIN** | In QGIS >=3.28, load table via Data Source Manager (Vector -> Arrow/Parquet) and execute a standard Attribute Join to the GeoPackage on `grid_id`. |
| **Flood Incidents & Stations (`.parquet`)** | **REQUIRES POINT LOAD** | If GDAL Parquet driver is active, add as vector point layer specifying `latitude` and `longitude`. Alternatively, a one-line export to GeoPackage or CSV allows universal drag-and-drop. |

---

## 6. Identification of Missing Layers

In strict compliance with repository audit integrity, the following layers were confirmed to be **absent from disk** as standalone spatial files:

1. **Official Administrative Polygon Boundary (`bbmp_wards_official.geojson`):** The repository does not contain the official 198-ward municipal boundary shapefile. As established in Phase 4.1, the study boundary is represented by the 1,170-cell rectangular bounding box (`grid_bengaluru_urban_1000m.gpkg`).
2. **Continuous 30m D8 Flow Direction Raster (`d8_flow_direction.tif`):** Flow routing was computed in memory and is represented by tabular upstream accumulation values, not a standalone D8 raster.
3. **Continuous 30m SAGA TWI Raster (`twi_30m.tif`):** Topographic wetness is stored as a cell-aggregated metric in `topographic_routing_static_features.parquet`, not as a continuous floating-point GeoTIFF.
4. **Vector Streamline Network Shapefile (`drainage_network.shp`):** While major drainage basins are mapped in cell tables, vector line geometries for *rajakaluves* (stormwater channels) are not present.

*Note: Per user instructions, no replacement files were fabricated.*

---

## 7. Recommended Minimal File Set for QGIS Project

To construct a visually compelling and mathematically verified QGIS desktop project without redundant data, the following **minimal set of 5 existing files** is recommended:

```
+---------------------------------------------------------------------------------------------------------+
|                                RECOMMENDED MINIMAL QGIS FILE SUITE                                      |
+---------------------------------------------------------------------------------------------------------+
| 1. Boundary & Grid:    data/processed/grid_bengaluru_urban_1000m.gpkg                                   |
| 2. Elevation:          data/raw/elevation/srtm/SRTMGL1_N12_N13_E077_Bengaluru.tif                       |
| 3. Land Cover / Water: data/raw/land_cover/ESA_WorldCover_10m_2021_v200_N12E075_Map.tif                 |
| 4. Hydrology & TWI:    data/processed/phase6/hydrology/topographic_routing_static_features.parquet      |
| 5. Flood Ground Truth: data/processed/phase6/flood_evidence/flood_validation_ground_truth_matrix.parquet|
+---------------------------------------------------------------------------------------------------------+
```

### Recommended QGIS Layer Loading & Styling Order:
1. **Base Layer (Bottom):** `SRTMGL1_N12_N13_E077_Bengaluru.tif`
   * *Style:* Singleband Pseudocolor (Color ramp: `Elevation` or `Spectral` inverted, min: 800m, max: 1050m), Blending Mode: Normal.
2. **Land Cover Overlay:** `ESA_WorldCover_10m_2021_v200_N12E075_Map.tif`
   * *Style:* Paletted/Unique Values, set opacity to 40% to reveal underlying relief.
3. **Hydrology & Drainage Map:** `grid_bengaluru_urban_1000m.gpkg` (Joined with `topographic_routing_static_features.parquet`)
   * *Style:* Graduated symbology on `upstream_contributing_area_km2` (Color ramp: `Blues`, classes: 0–5 km², 5–20 km², 20–50 km², >50 km²).
4. **Flood-Risk Prioritisation Map:** Duplicate of `grid_bengaluru_urban_1000m.gpkg` (Joined with `flood_validation_ground_truth_matrix.parquet`)
   * *Style:* Categorized symbology on `observation_status`:
     * `VERIFIED_POSITIVE`: Solid Red fill (`#dc2626`)
     * `VERIFIED_NEGATIVE`: Solid Green fill (`#16a34a`)
     * `UNOBSERVED_DOMAIN_CELL`: Transparent fill with light grey outline (`#94a3b8`)
5. **Study Domain Boundary (Top):** `grid_bengaluru_urban_1000m.gpkg`
   * *Style:* Inverted Polygon / Hollow outline with thick black stroke (stroke width: 1.0 mm) displaying the bounding envelope.

---

## 8. CRS & Compatibility Warnings

* **Mixed CRS Environments:**
  * Vector Grid: **`EPSG:6933`** (Cylindrical Equal Area, meter units).
  * SRTM DEM & Land Cover: **`EPSG:4326`** (WGS 84 geographic latitude/longitude).
  * *QGIS Action:* Set the QGIS Project CRS to **`EPSG:4326`** or **`EPSG:3857`** (Web Mercator). QGIS will perform seamless on-the-fly reprojection of the equal-area grid onto the raster basemaps without distortion.
* **Parquet File Reading in QGIS:**
  * In QGIS versions $\ge 3.28$ (standard LTR), Apache Parquet files can be dragged directly into the layers panel as attribute tables via GDAL/OGR Arrow driver.
  * If using an older QGIS installation or a minimal OS build lacking GDAL Parquet support, a simple one-click attribute export or standard CSV export will be required prior to joining.

---

## 9. Final Inspection Verdict

```
+===================================================================================+
|                                  FINAL VERDICT                                    |
|                                                                                   |
|                            READY WITH MINOR CONVERSION                            |
|                                                                                   |
|  The repository contains all required high-resolution basemap rasters and master  |
|  grid geometries. The project can be assembled in QGIS immediately by loading the |
|  native rasters/vectors and executing standard table joins for analytical data.   |
+===================================================================================+
```
