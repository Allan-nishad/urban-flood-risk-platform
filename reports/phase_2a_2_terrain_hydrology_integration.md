# Phase 2A.2 Integration Report: SRTM Terrain & MERIT Hydro Baseline

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Sub-Phase:** Phase 2A.2 — SRTM Terrain and MERIT Hydro Integration  
**Date:** 2026-11-05  
**Target Study Domain:** Bengaluru Urban (1,170 cells, provisional development bounding box)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Automated Tests:** 47 passed (100% pass rate in 4.77 seconds)

---

## 1. Executive Summary & Integration Status

In Phase 2A.2, the data engineering foundation established in Phase 2A.1 was expanded from land-cover analysis to multimodal static environmental feature extraction by incorporating authentic digital elevation data and establishing the ingestion pipeline for hydrological drainage accumulation:

1. **SRTM GL1 30m DEM (Acquired, Validated & Extracted):**
   - Two contiguous 1° × 1° tiles (`N12E077` and `N13E077`) were acquired from the official European Space Agency (ESA) Science Toolbox Exploitation Platform (STEP) auxiliary archive.
   - Both tiles were validated for coordinate system (`EPSG:4326`), 1 arc-second resolution (~30 m), `int16` depth, and `-32768.0` NoData flag.
   - Converted to standardized Cloud-Optimized GeoTIFFs and merged into a seamless 3,601 × 7,201 mosaic (`SRTMGL1_N12_N13_E077_Bengaluru.tif`, 14.88 MB).
   - Continuous zonal extraction was executed across all 1,170 cells using the audited pixel-center inclusion engine, extracting 7 terrain features (`elevation_mean_m`, `elevation_min_m`, `elevation_max_m`, `elevation_std_m`, `elevation_valid_pixel_count`, `elevation_nodata_pixel_count`, `elevation_valid_pixel_fraction`).
   - Valid data coverage is **100.0%** ($1,263,354$ valid 30m pixels; $0$ NoData pixels).
2. **MERIT Hydro v1.0.1 Upstream Contributing Area (Gated Behind Research Registration):**
   - Detailed investigation confirmed that the official MERIT Hydro repository (`https://global-hydrodynamics.github.io/MERIT_Hydro/`) restricts automated downloads via a Google Form license registration and a password-protected Dropbox store.
   - In accordance with project restrictions, **no synthetic data was fabricated**, nor were unauthorized credential bypasses attempted.
   - The extraction pipeline was implemented and tested to support `upa_mean_sqkm`, `upa_max_sqkm`, `upa_valid_pixel_count`, `upa_nodata_pixel_count`, and `upa_valid_pixel_fraction`. In the merged Parquet dataset, these columns are explicitly preserved as **missing values (`NaN`)**, cleanly distinguishing acquired observations from pending layers.
   - Precise manual acquisition instructions and staging paths are provided below.
3. **Multimodal Parquet Feature Matrix Merged:**
   - Saved to `data/processed/grid_features_bengaluru_urban_1000m.parquet` (50,412 bytes, SHA-256: `d5404934065182e050369d0f1352b931e06b010283f56231dfe698c97976b6ee`).
   - Contains 1,170 unique records, 0 duplicate grid IDs, 0 unexpected row multiplications, across 26 verified columns.

---

## 2. Dataset Acquisition & Provenance Ledger

### 2.1 Shuttle Radar Topography Mission (SRTM GL1 30m)
* **Provider:** NASA / USGS / NGA, mirrored by European Space Agency (ESA) STEP.
* **Product:** SRTM Global 1 Arc-Second (SRTMGL1 V003, void-filled).
* **Retrieval Date:** 2026-11-05.
* **Licence & Terms:** Open Data / Public Domain (NASA/USGS Open Data Policy).
* **Native CRS:** `EPSG:4326` (WGS 84 ellipsoidal coordinates).
* **Spatial Resolution:** $1\text{ arc-second} \approx 0.0002777778^\circ \approx 30.87\text{ m}$ at the equator.
* **Vertical Units:** Metres above the EGM96 geoid.
* **NoData Value:** `-32768.0`.
* **Download URLs & Raw Assets:**
  - `https://step.esa.int/auxdata/dem/SRTMGL1/N12E077.SRTMGL1.hgt.zip` (10,071,528 B, SHA-256: `37c8aafaa1acae395053cab5bd1d3766676897a7c08724590a1999d4caa28d76`)
  - `https://step.esa.int/auxdata/dem/SRTMGL1/N13E077.SRTMGL1.hgt.zip` (7,813,126 B, SHA-256: `17d69dfe6a9c484a23844d81b682adb27fcf384f4f4cc27b06935079ef659790`)
* **Extracted GeoTIFF Assets:**
  - `data/raw/elevation/srtm/N12E077.SRTMGL1.tif` (8,095,151 B, SHA-256: `697aa24791cd02b43a5002fc5b7f6137434d74c420d5a7a0d6f58743b1595b15`)
  - `data/raw/elevation/srtm/N13E077.SRTMGL1.tif` (6,783,967 B, SHA-256: `d9a8821fd3017803f3ab7086afd7ba60679aa2e7b4c1dde09395f649073d2fd6`)
* **Combined Analysis Mosaic:**
  - `data/raw/elevation/srtm/SRTMGL1_N12_N13_E077_Bengaluru.tif` (14,876,879 B, SHA-256: `ba45614211dbcbf686a47b36e19a32a9cfd82ce7c82a80bcc9e269a95d93946f`)
  - Dimensions: $3,601 \times 7,201\text{ pixels}$.
  - Extent: $[77.0^\circ\text{E}, 12.0^\circ\text{N}] \times [78.0^\circ\text{E}, 14.0^\circ\text{N}]$ (completely encloses the $77.45^\circ - 77.75^\circ\text{E}, 12.85^\circ - 13.15^\circ\text{N}$ study area).

### 2.2 MERIT Hydro (Upstream Contributing Area)
* **Provider:** Dai Yamazaki Lab, Institute of Industrial Science, The University of Tokyo.
* **Product:** MERIT Hydro: A Global High-Resolution Hydrography Datasets (v1.0.1).
* **Target Tile:** `n10e075_upa.tif` (covering $10^\circ - 15^\circ\text{N}, 75^\circ - 80^\circ\text{E}$).
* **Variable:** `upa` (upstream drainage area).
* **Expected CRS:** `EPSG:4326`.
* **Expected Resolution:** $3\text{ arc-seconds} \approx 90\text{ m}$.
* **Expected Units:** $\text{km}^2$.
* **Status:** **BLOCKED / PENDING USER REGISTRATION PASSWORD**.
* **Access Reason:** The official Yamazaki Lab portal requires users to submit an agreement form before accessing the password-protected repository.

---

## 3. Step-by-Step Manual Instructions for MERIT Hydro Staging

To stage `n10e075_upa.tif` for downstream feature extraction:

1. **Submit Registration Form:**
   - Navigate to the official Yamazaki Lab registration form:  
     `https://goo.gl/forms/6VwfnasNjkYm0Wqu2`
   - Complete the standard research usage agreement and submit your email.
2. **Retrieve Access Password:**
   - An automated email will be sent containing the repository access password (check spam folder if delayed).
3. **Open the Download Repository:**
   - Access the MERIT Hydro Dropbox repository linked on the project page:  
     `https://www.dropbox.com/scl/fo/fw8qrf73zhzmo6p92gbxv/AIlVRfnQVEWOyXEimsK2qKk?rlkey=a0be5opyb2kpkf0ssbvau8y9q&st=t8rtowe9&dl=0`
   - When prompted, enter **only the password** received via email (leave username blank).
4. **Download the South Asia Regional Tar Archive:**
   - Locate the regional archive covering South Asia / Peninsular India:  
     `upa_s00_n30_e060_e090.tar` (or the direct `n10e075_upa.tif` tile).
5. **Stage the File:**
   - Extract and place `n10e075_upa.tif` directly into the designated project directory:  
     `data/raw/hydrology/merit_hydro/n10e075_upa.tif`
6. **Execution Trigger:**
   - Once staged, run the automated extraction command:
     ```powershell
     .venv\Scripts\python.exe -c "
     import geopandas as gpd, pandas as pd
     from floodrisk.processing.zonal import extract_multimodal_grid_features
     gdf = gpd.read_file('data/processed/grid_bengaluru_urban_1000m.gpkg')
     df_cur = pd.read_parquet('data/processed/grid_features_bengaluru_urban_1000m.parquet')
     extract_multimodal_grid_features(
         grid_gdf=gdf,
         srtm_raster_path='data/raw/elevation/srtm/SRTMGL1_N12_N13_E077_Bengaluru.tif',
         merit_hydro_raster_path='data/raw/hydrology/merit_hydro/n10e075_upa.tif',
         existing_features_df=df_cur,
         output_parquet_path='data/processed/grid_features_bengaluru_urban_1000m.parquet'
     )
     "
     ```

---

## 4. Independent 5-Cell Reference Validation (SRTM Elevation)

To confirm that SRTM continuous feature extraction is free from edge effects, five representative cells were audited against independent GIS vector clipping (`rasterio.mask.mask`):

| Grid ID | Regime Description | Production Pixels | Reference Pixels | Discrepancy ($\Delta$ Pixels) | Prod Mean (m) | Ref Mean (m) | Discrepancy ($\Delta$ Mean) | Prod Min (m) | Ref Min (m) | Prod Max (m) | Ref Max (m) | Prod Std (m) | Ref Std (m) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `g1000_7472_1625` | Rural Peripheral (SW) | 1,064 | 1,064 | **0** | 762.60 | 762.60 | $0.0013\text{ m}$ | 747.0 | 747.0 | 774.0 | 774.0 | 6.20 | 6.20 |
| `g1000_7487_1641` | Dense Urban Core (MG Rd) | 1,073 | 1,073 | **0** | 919.92 | 919.92 | $0.0048\text{ m}$ | 906.0 | 906.0 | 946.0 | 946.0 | 5.46 | 5.46 |
| `g1000_7494_1635` | Bellandur Lake Region | 1,073 | 1,073 | **0** | 885.76 | 885.76 | $0.0014\text{ m}$ | 875.0 | 875.0 | 897.0 | 897.0 | 4.67 | 4.67 |
| `g1000_7497_1635` | Varthur Lake Region | 1,073 | 1,073 | **0** | 884.51 | 884.51 | $0.0035\text{ m}$ | 869.0 | 869.0 | 903.0 | 903.0 | 5.36 | 5.36 |
| `g1000_7501_1640` | Partial Domain (East) | 1,102 | 1,102 | **0** | 878.37 | 878.37 | $0.0025\text{ m}$ | 865.0 | 865.0 | 891.0 | 891.0 | 6.64 | 6.64 |

### Numerical Tolerance Assessment:
- **Pixel Count:** Exactly **$0\text{ pixels}$** discrepancy.
- **Min / Max Elevation:** Exactly **$0.0\text{ m}$** discrepancy (integer precision).
- **Mean / Std Elevation:** Discrepancy $\le 0.0048\text{ m}$ (purely due to 2-decimal rounding in output storage).

---

## 5. Statistical Distribution Across All 1,170 Cells

| Feature Name | Layer | Count | Nulls (%) | Min | 25th % | Median | Mean | 75th % | Max | Std Dev | Physical Meaning |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `elevation_mean_m` | SRTM 30m | 1,170 | 0.0% | 755.54 | 873.93 | 893.07 | 885.54 | 907.61 | 944.55 | 34.29 | Macro-topographic elevation |
| `elevation_min_m` | SRTM 30m | 1,170 | 0.0% | 738.00 | 860.00 | 879.00 | 870.33 | 893.00 | 931.00 | 35.33 | Cell drainage depression base |
| `elevation_max_m` | SRTM 30m | 1,170 | 0.0% | 774.00 | 889.00 | 909.00 | 902.18 | 924.00 | 961.00 | 32.94 | Local topographic ridge |
| `elevation_std_m` | SRTM 30m | 1,170 | 0.0% | 1.50 | 5.19 | 6.08 | 6.60 | 7.32 | 18.62 | 2.33 | Surface relief / roughness |
| `elevation_valid_pixel_count` | SRTM 30m | 1,170 | 0.0% | 1,036 | 1,073 | 1,073 | 1,079.8 | 1,102 | 1,102 | 16.89 | Valid native 30m pixels |
| `elevation_nodata_pixel_count` | SRTM 30m | 1,170 | 0.0% | 0 | 0 | 0 | 0.00 | 0 | 0 | 0.00 | Filtered NoData pixels |
| `elevation_valid_pixel_fraction`| SRTM 30m | 1,170 | 0.0% | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | Ratio of valid to total pixels |
| `fraction_built_up` | WorldCover | 1,170 | 0.0% | 0.0000 | 0.1507 | 0.4356 | 0.4429 | 0.7205 | 0.9904 | 0.3013 | Pixel-centre built-up fraction |
| `fraction_water_bodies` | WorldCover | 1,170 | 0.0% | 0.0000 | 0.0000 | 0.0000 | 0.0091 | 0.0027 | 0.4833 | 0.0354 | Pixel-centre open water fraction |
| `valid_pixel_count` | WorldCover | 1,170 | 0.0% | 11,904 | 11,904 | 12,000 | 11,996.6| 12,028 | 12,125 | 77.52 | Valid native 10m pixels |
| `valid_pixel_fraction` | WorldCover | 1,170 | 0.0% | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | Ratio of valid to total pixels |
| `upa_mean_sqkm` | MERIT Hydro| 1,170 | **100.0%**| — | — | — | **NaN** | — | — | — | **Pending download** |
| `upa_max_sqkm` | MERIT Hydro| 1,170 | **100.0%**| — | — | — | **NaN** | — | — | — | **Pending download** |
| `fraction_inside_domain` | Domain | 1,170 | 0.0% | 0.0045 | 1.0000 | 1.0000 | 0.9232 | 1.0000 | 1.0000 | 0.2376 | Coverage in development bbox |

---

## 6. Critical Scientific Qualifications & Methodological Distinctions

In adherence to scientific integrity:

1. **SRTM is a Surface Model (DSM), Not a Bare-Earth DTM:**
   - C-band radar signals reflect off building rooftops, industrial warehouses, tree canopies, and infrastructure. In dense urban sectors of Bengaluru (e.g. Mahadevapura, Peenya, Whitefield), elevation values include building heights ($5 - 25\text{ m}$ above ground).
   - SRTM elevation must **not** be interpreted as street-grade curb elevation or invert levels of stormwater culverts.
2. **Pixel-Centre Sampling vs. Area-Weighted Land-Cover:**
   - WorldCover fractions reflect **pixel-centre inclusion** (`all_touched=False`), which provides a disjoint, conservative spatial partition across the 1-km grid.
   - It is not described as an area-weighted continuous integration.
3. **Upstream Contributing Area (UPA) is Not Observed Flood Discharge:**
   - When MERIT Hydro is integrated, `upa_max_sqkm` represents the theoretical cumulative upstream topographic catchment area draining across a cell under natural topography.
   - It does **not** measure instantaneous storm discharge ($Q\text{ in m}^3/\text{s}$), stormwater pipe conveying capacity, siltation state, or flood depth.
4. **No HAND Calculation on Raw SRTM:**
   - Height Above Nearest Drainage (HAND) requires hydrologically conditioned bare-earth DTMs, verified stream burning, and pit removal. Calculating HAND from raw unconditioned SRTM in an urban environment creates false topographic dams and spurious drainage disconnects.

