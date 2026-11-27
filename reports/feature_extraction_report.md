# Real Data Feature Extraction Report
**Project:** AI-Based Early Detection and Forecasting of Urban Flood Risks  
**Phase:** 2A.2 — Multimodal Terrain & Land-Cover Feature Baseline  
**Dataset Stored:** `data/processed/grid_features_bengaluru_urban_1000m.parquet`  
**Dataset SHA-256:** `d5404934065182e050369d0f1352b931e06b010283f56231dfe698c97976b6ee`  
**File Size:** 50,412 bytes (1,170 rows, 26 columns)  
**Generated:** 2026-11-05  

---

## 1. Zonal Extraction Architecture

Feature extraction was executed using the audited [`RasterZonalExtractor`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/zonal.py#L66-L235) engine:
1. **Windowed Memory Reading:** For each 1-km cell, the EPSG:6933 cell polygon is transformed into the raster native CRS (EPSG:4326) and enclosed in an integer pixel window (`math.floor(col_off)`, `math.ceil(col_off + width)`).
2. **Exact Vector Geometry Masking:** `rasterio.features.geometry_mask(all_touched=False)` evaluates strict pixel-center inclusion, completely eliminating rectangular window leakage and sub-pixel edge truncation.
3. **Continuous Zonal Analysis (SRTM 30m):** Computes `mean`, `min`, `max`, and `std` elevation, filtering out NoData (`-32768`).
4. **Categorical Histogram Analysis (WorldCover 10m):** Computes pixel-centre categorical fractions for Class 50 (Built-up) and Class 80 (Permanent water bodies), filtering out NoData (`0`).
5. **Execution Latency:**
   - WorldCover extraction: $13.24\text{ seconds}$ across 1,170 cells ($\sim 11.3\text{ ms/cell}$).
   - SRTM DEM extraction: $9.53\text{ seconds}$ across 1,170 cells ($\sim 8.1\text{ ms/cell}$).
   - Total batch processing time: $< 25\text{ seconds}$.

---

## 2. Derived Feature Schema (Parquet Table)

The generated Parquet file contains 1,170 records with the following 26-column schema:

| Column Name | Layer / Source | Data Type | Units / Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `grid_id` | Grid Engine | `string` | `g1000_{col}_{row}` | Standardized global equal-area grid identifier |
| `col_idx` | Grid Engine | `int64` | $[7472, 7501]$ | Global EPSG:6933 column index |
| `row_idx` | Grid Engine | `int64` | $[1625, 1663]$ | Global EPSG:6933 row index |
| `centroid_lon` | Grid Engine | `float64` | $[77.4462, 77.7468]^\circ\text{E}$ | WGS84 centroid longitude |
| `centroid_lat` | Grid Engine | `float64` | $[12.8462, 13.1517]^\circ\text{N}$ | WGS84 centroid latitude |
| `fraction_inside_domain` | Domain Engine | `float64` | $[0.0, 1.0]$ | Fraction of cell inside development bounding box domain |
| `fraction_inside_boundary` | Domain Engine | `float64` | $[0.0, 1.0]$ | Backward-compatible alias to `fraction_inside_domain` |
| `coverage_class` | Domain Engine | `string` | `fully_inside` / `partially_intersecting` | Spatial domain coverage status |
| `geodesic_area_sqm` | Grid Engine | `float64` | $\approx 1,000,000.0018\text{ m}^2$ | Geodesic area calculated on WGS84 ellipsoid |
| `valid_pixel_count` | ESA WorldCover | `int64` | $[11904, 12125]$ | Count of valid 10m pixels inside cell polygon |
| `nodata_pixel_count` | ESA WorldCover | `int64` | $0$ | Count of NoData pixels inside cell polygon |
| `valid_pixel_fraction` | ESA WorldCover | `float64` | $1.0000$ ($100.0\%$) | Ratio of valid pixels to total cell pixels |
| `fraction_built_up` | ESA WorldCover | `float64` | $[0.0, 1.0]$ | Pixel-centre fraction classified as built-up |
| `fraction_water_bodies` | ESA WorldCover | `float64` | $[0.0, 1.0]$ | Pixel-centre fraction classified as water bodies |
| `elevation_mean_m` | SRTM GL1 30m | `float64` | $[755.54, 944.55]\text{ m}$ | Zonal mean elevation above sea level |
| `elevation_min_m` | SRTM GL1 30m | `float64` | $[738.00, 931.00]\text{ m}$ | Local lowest elevation (drainage depression) |
| `elevation_max_m` | SRTM GL1 30m | `float64` | $[774.00, 961.00]\text{ m}$ | Local highest elevation (topographic ridge) |
| `elevation_std_m` | SRTM GL1 30m | `float64` | $[1.50, 18.62]\text{ m}$ | Topographic relief / vertical standard deviation |
| `elevation_valid_pixel_count` | SRTM GL1 30m | `int64` | $[1036, 1102]$ | Count of valid 30m pixels inside cell polygon |
| `elevation_nodata_pixel_count`| SRTM GL1 30m | `int64` | $0$ | Count of filtered NoData pixels inside cell |
| `elevation_valid_pixel_fraction`| SRTM GL1 30m| `float64` | $1.0000$ ($100.0\%$) | Ratio of valid pixels to total cell pixels |
| `upa_mean_sqkm` | MERIT Hydro 90m| `float64` | $\text{km}^2$ / `NaN` | Mean upstream contributing area (pending download) |
| `upa_max_sqkm` | MERIT Hydro 90m| `float64` | $\text{km}^2$ / `NaN` | Peak upstream contributing area (pending download) |
| `upa_valid_pixel_count` | MERIT Hydro 90m| `float64` | Count / `NaN` | Valid pixels count (pending download) |
| `upa_nodata_pixel_count` | MERIT Hydro 90m| `float64` | Count / `NaN` | NoData pixels count (pending download) |
| `upa_valid_pixel_fraction` | MERIT Hydro 90m| `float64` | $[0.0, 1.0]$ / `NaN` | Valid pixel fraction (pending download) |

---

## 3. Spatial Distribution & Topographic Characteristics

- **Plateau Ridge Spine:**
  - High ground runs along the north-central spine of Bengaluru (Malleswaram, Hebbal, Yelahanka, MG Road) at **$900 - 945\text{ m}$**.
  - Local depressions drop to **$860 - 885\text{ m}$** in major lake basins (Bellandur Lake, Varthur Lake, Agara Lake).
  - Outlying southern cells drop to **$738 - 770\text{ m}$** toward the Kanakapura / Arkavathi river valley.
- **Topographic Roughness:**
  - Standard deviation (`elevation_std_m`) is lowest in the flat lake basins ($1.5 - 4.5\text{ m}$), reflecting high inundation susceptibility under heavy rainfall.
  - Relief increases to $12 - 18.6\text{ m}$ on peripheral ridge escarpments.
