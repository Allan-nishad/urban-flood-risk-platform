# Phase 2A.3 Integration Report: NASA GPM IMERG Precipitation Integration & Temporal Feature Engineering

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Sub-Phase:** Phase 2A.3 — NASA GPM IMERG Precipitation Integration  
**Date:** 2026-11-05  
**Target Study Domain:** Bengaluru Urban (1,170 cells, provisional development bounding box)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Automated Tests:** 54 passed (100% pass rate in 6.01 seconds)

---

## 1. Executive Summary & Integration Status

In Phase 2A.3, the platform foundation was expanded from static environmental susceptibility (land-cover and terrain) to **dynamic precipitation forcing and temporal hydrological feature engineering** by integrating NASA's Global Precipitation Measurement (GPM) Integrated Multi-satellitE Retrievals for GPM (IMERG):

1. **NASA GES DISC Product Specification & Access Investigation:**
   - Authoritative product: **GPM IMERG Final Precipitation L3 Daily 0.1° × 0.1° (V07B)** (`GPM_3IMERGDF.07`), complemented by half-hourly calibrated rates (`GPM_3IMERGHH.07`).
   - Catalog inspection confirmed that NASA GES DISC HTTPS and OPeNDAP metadata servers (`https://gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3/GPM_3IMERGDF.07/`) are active and provide authoritative data attribute schemas (`.das` / `.dds`).
   - Direct download of `.nc4` / `.HDF5` data arrays is protected by NASA Earthdata Login authentication (`HTTP 401: Unauthorized` without credentials).
2. **Automated Downloader & Staging Architecture:**
   - Implemented [`IMERGDownloader`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/rainfall.py#L173-L236) to generate canonical GES DISC URLs across user-specified date windows.
   - Generates production-ready download scripts ([`scripts/download_imerg_gesdisc.sh`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/scripts/download_imerg_gesdisc.sh)) supporting `curl -b ~/.urs_cookies -c ~/.urs_cookies -L --netrc`.
   - Exposed operational CLI commands: [`download-imerg`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/cli.py#L311-L352) and [`process-rainfall`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/cli.py#L355-L446).
3. **Dynamic Unit Verification & Standardization:**
   - Audited and verified [`parse_and_validate_rainfall_units`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/rainfall.py#L46-L135) and [`convert_precipitation_to_depth_mm`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/rainfall.py#L138-L154):
     - For half-hourly rate (`precipitationCal` in `mm/hr` over 30 min): multiplies by duration ($0.5\text{ hr}$) to produce accumulated depth in mm.
     - For daily depth (`precipitation` in `mm` or `mm/day` over 24 hr): applies identity factor $1.0$, preventing improper multiplication by 0.5.
     - Dynamically rejects unverified units or missing metadata.
4. **Spatial Remapping Engine (0.1° to 1-km EPSG:6933):**
   - Implemented [`IMERGGridMapper`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/rainfall.py#L329-L432) to remap native 0.1° (~10 km) IMERG cells onto the 1,170 equal-area 1-km grid cells in EPSG:6933.
   - Supports both `centroid_lookup` (discrete satellite pixel values preserved) and `bilinear` (smooth gradient across cell centroids).
   - Strictly enforces the scientific disclaimer:
     > *"1-km grid remapping provides spatial indexing alignment only for multimodal tabular joining; native 0.1 deg (~10 km) satellite precipitation does NOT resolve localized convective micro-cells, storm sewer backups, or street-level runoff dynamics."*
5. **Temporal Antecedent Precipitation Index (API) Engine:**
   - Implemented [`AntecedentPrecipitationEngine`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/rainfall.py#L435-L536):
     - Computes 3-day ($API_{3d}$), 7-day ($API_{7d}$), and 14-day ($API_{14d}$) antecedent cumulative rainfall prior to day $t$.
     - Computes exponential decaying Antecedent Precipitation Index:
       $$API_t = \sum_{k=1}^{n} P_{t-k} \cdot \alpha^k \quad (\alpha = 0.85, n = 14\text{ days})$$
     - Calculates cell-level event summary statistics (peak daily rainfall, total event rainfall, max API decay, rainy days, heavy rain days).
6. **Automated Testing Suite:**
   - 7 unit tests in [`tests/test_rainfall.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/tests/test_rainfall.py).
   - 2 CLI tests in [`tests/test_cli.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/tests/test_cli.py).
   - 1 full integration test in [`tests/test_integration_real_data.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/tests/test_integration_real_data.py).
   - Total test suite: **54 passed, 0 failed, 0 skipped** under Python 3.11.15 in 6.01s.

---

## 2. NASA GES DISC Product & Archive Investigation

### 2.1 Product Metadata (OPeNDAP DAS Inspection)
Inspection of the official NASA GES DISC OPeNDAP metadata server for `3B-DAY.MS.MRG.3IMERG.20220901-S000000-E235959.V07B.nc4.das` revealed the exact variable definition and attribute structure:

```
Attributes {
    precipitation {
        String units "mm/day";
        String long_name "Daily mean precipitation rate (combined microwave-IR) estimate. Formerly precipitationCal.";
        String coordinates "time lon lat";
        Float32 _FillValue -9999.90039;
    }
    precipitation_cnt {
        String units "count";
        String long_name "Count of all valid half-hourly precipitation retrievals for the day";
        String coordinates "time lon lat";
    }
}
```

### 2.2 Key Operational Insights
1. **Official Variable Name:** The primary daily calibrated rainfall variable is named `precipitation` (not `precipitationCal`, which is retained in the half-hourly product).
2. **Official Units:** The unit string is `"mm/day"`. Since the aggregation window is 1 day (24 hours), the accumulated depth in millimetres is:
   $$\text{Daily Depth (mm)} = \text{precipitation} [\text{mm/day}] \times 1.0 = \text{mm}$$
   Our [`parse_and_validate_rainfall_units`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/rainfall.py#L97-L111) correctly maps `"mm/day"` to a conversion factor of $1.0$.
3. **Fill Value:** NoData is represented by `_FillValue = -9999.90039`. Values $< -9000.0$ are strictly masked to `np.nan`.
4. **Dimension Ordering:** In native NASA HDF5/NetCDF files, the spatial grid is indexed as `[lon = 3600][lat = 1800]`. Our reader ([`IMERGRasterReader`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/rainfall.py#L237-L327)) transposes this array to standard geospatial `(lat, lon)` with descending latitudes ($+90^\circ \to -90^\circ$).

---

## 3. Canonical Historical Flood Event Window: Bengaluru Late-Monsoon 2022

To anchor all temporal feature engineering in authentic meteorological history, we selected the **Bengaluru Urban Flood Disaster of Late August – Early September 2022**:

* **Analysis Period:** **2022-08-25 to 2022-09-10** (17 consecutive daily observation steps).
* **Pre-Storm Antecedent Soaking (Aug 25 – Aug 29):** Continuous rain saturated Bengaluru's catchment soils, elevating the antecedent precipitation index ($API$) across all basins.
* **First Waterlogging Wave (Aug 30 – Sep 1):** Substantial localized inundation along peripheral valleys.
* **Catastrophic Torrential Peak (Sep 4 – Sep 5):** Extreme localized convective downpours overwhelmed the Bellandur, Varthur, and Outer Ring Road cascading lake systems, inundating Bellandur, Mahadevapura, EcoSpace, Rainbow Drive, and Sarjapur Road.
* **Drainage Recession (Sep 6 – Sep 10):** Water levels receded slowly due to obstructed natural drainage and encroached lake buffers.

### Granule Retrieval URLs (17 Daily Granules)
The following canonical URLs are managed by `IMERGDownloader`:
```
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/08/3B-DAY.MS.MRG.3IMERG.20220825-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/08/3B-DAY.MS.MRG.3IMERG.20220826-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/08/3B-DAY.MS.MRG.3IMERG.20220827-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/08/3B-DAY.MS.MRG.3IMERG.20220828-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/08/3B-DAY.MS.MRG.3IMERG.20220829-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/08/3B-DAY.MS.MRG.3IMERG.20220830-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/08/3B-DAY.MS.MRG.3IMERG.20220831-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220901-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220902-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220903-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220904-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220905-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220906-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220907-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220908-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220909-S000000-E235959.V07B.nc4
https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220910-S000000-E235959.V07B.nc4
```

---

## 4. Mathematical Formulations

### 4.1 Unit Verification and Depth Conversion
Given variable $V$ with attribute unit $u$ and observation timestep $\Delta t = 1440\text{ min}$ ($24\text{ hr}$):
$$D_{\text{daily}} = \begin{cases} 
V \times 1.0 & \text{if } u \in \{\text{'mm'}, \text{'mm/day'}\} \\
V \times \frac{\Delta t}{60} & \text{if } u \in \{\text{'mm/hr'}\} \\
V \times (\Delta t \times 60) \times 1.0 & \text{if } u \in \{\text{'kg m}^{-2}\text{ s}^{-1}\text{'}\}
\end{cases}$$

### 4.2 Spatial Remapping (Centroid Lookup)
For 1-km grid cell $i$ with projected polygon $G_i \in \text{EPSG:6933}$:
1. Cell centroid is inverse-projected to ellipsoidal WGS84 coordinates:
   $$(\lambda_i, \phi_i) = \mathcal{T}_{\text{EPSG:6933}\to\text{EPSG:4326}}(\bar{x}_i, \bar{y}_i)$$
2. Column and row indices in the native 0.1° IMERG raster ($R_{\text{native}}$ with origin $(\lambda_0, \phi_0)$ and resolution $\Delta \theta = 0.1^\circ$):
   $$c_i = \left\lfloor \frac{\lambda_i - \lambda_0}{\Delta \theta} \right\rfloor, \quad r_i = \left\lfloor \frac{\phi_0 - \phi_i}{\Delta \theta} \right\rfloor$$
3. Assigned precipitation:
   $$P_{i, t} = R_{\text{native}}[r_i, c_i, t]$$

### 4.3 Multi-Day Cumulative Antecedent Rainfall
For cell $i$ on day $t$:
$$A_{3d, i, t} = \sum_{k=1}^{3} P_{i, t-k}, \quad A_{7d, i, t} = \sum_{k=1}^{7} P_{i, t-k}, \quad A_{14d, i, t} = \sum_{k=1}^{14} P_{i, t-k}$$
where summation strictly begins at $t-1$ to reflect antecedent soil conditions before day $t$.

### 4.4 Hydrological Antecedent Precipitation Index ($API_{\text{decay}}$)
Modeling daily soil moisture depletion via an exponential recession curve:
$$API_{i, t} = \sum_{k=1}^{n} P_{i, t-k} \cdot \alpha^k$$
where:
* $\alpha = 0.85$ is the empirical recession coefficient for tropical monsoon soils in Peninsular India.
* $n = 14\text{ days}$ is the maximum hydrologically active antecedent lookback window.

---

## 5. Derived Spatiotemporal Schema & Data Products

### 5.1 Spatiotemporal Panel (`rainfall_bengaluru_urban_20220825_20220910.parquet`)
Records: $1,170\text{ cells} \times 17\text{ days} = 19,890\text{ observations}$.

| Column Name | Data Type | Units | Description |
| :--- | :--- | :--- | :--- |
| `grid_id` | `string` | — | Canonical grid identifier (`g1000_{col}_{row}`) |
| `date` | `date` | `YYYY-MM-DD` | Observation calendar date |
| `rainfall_daily_depth_mm` | `float32` | `mm` | 24-hour accumulated rainfall depth |
| `precip_antecedent_3d_mm` | `float32` | `mm` | 3-day antecedent accumulated rainfall ($t-1$ to $t-3$) |
| `precip_antecedent_7d_mm` | `float32` | `mm` | 7-day antecedent accumulated rainfall ($t-1$ to $t-7$) |
| `precip_antecedent_14d_mm` | `float32` | `mm` | 14-day antecedent accumulated rainfall ($t-1$ to $t-14$) |
| `precip_api_decay_mm` | `float32` | `mm` | Exponential decay Antecedent Precipitation Index ($\alpha = 0.85$) |
| `precip_cumulative_event_mm` | `float32` | `mm` | Cumulative rainfall from start of event window up to day $t$ |

### 5.2 Event Summary Table (`rainfall_bengaluru_urban_event_summary.parquet`)
Records: $1,170\text{ cells}$ (1 row per cell).

| Column Name | Data Type | Units | Description |
| :--- | :--- | :--- | :--- |
| `grid_id` | `string` | — | Canonical grid identifier |
| `event_total_rainfall_mm` | `float32` | `mm` | Total accumulated rainfall across the 17-day flood event window |
| `event_peak_daily_rainfall_mm` | `float32` | `mm` | Maximum single-day rainfall depth during the event |
| `event_mean_daily_rainfall_mm` | `float32` | `mm` | Average daily rainfall across the event |
| `event_max_antecedent_3d_mm` | `float32` | `mm` | Peak 3-day antecedent rainfall experienced during the event |
| `event_max_antecedent_7d_mm` | `float32` | `mm` | Peak 7-day antecedent rainfall experienced during the event |
| `event_max_api_decay_mm` | `float32` | `mm` | Maximum soil saturation index ($API$) reached during the event |
| `event_rainy_days_count` | `int64` | `count` | Days with daily precipitation $\ge 2.5\text{ mm}$ (IMD definition) |
| `event_heavy_rain_days_count` | `int64` | `count` | Days with daily precipitation $\ge 64.5\text{ mm}$ (IMD definition) |

---

## 6. Scientific Qualifications & Safeguards

1. **Resolution Mismatch & Micro-Convection:**
   - IMERG native pixels are $0.1^\circ \times 0.1^\circ$ (~$10\text{ km} \times 10\text{ km} \approx 100\text{ km}^2$).
   - Across the $30\text{ km} \times 39\text{ km}$ Bengaluru study area, there are approximately $3 \times 4 = 12$ native satellite pixels.
   - Resampling to 1-km grid cells provides **spatial alignment** for tabular feature joining; it does **not** create localized micro-convective storm resolution. Local street flooding is governed by localized drainage blockages, culvert capacities, and lake weir overflows.
2. **Satellite Microwave-IR Limitations:**
   - IMERG integrates passive microwave sensors and geostationary infrared observations. Heavy precipitation attenuation and urban surface thermal inertia can introduce retrieval noise, especially in complex cloud tops.
3. **Soil Moisture Parameterization:**
   - The decay coefficient $\alpha = 0.85$ is a standard hydrological approximation. In highly paved urban cells (e.g., MG Road with built-up fraction $> 0.70$), infiltration is minimal and surface runoff occurs almost instantaneously ($t \approx 0$). In contrast, in suburban vegetated cells, soil moisture memory is prolonged.

---

## 7. Deliverable Verification & Next Steps

* **All Automated Tests:** 54/54 passing under Python 3.11.15 (`.venv`).
* **Cryptographic Ledger:** 13 registered assets in `reports/dataset_manifest.json`.
* **Recommended Next Step:** Proceed to **Phase 2A.4: Historical Flood-Event Inventory**, establishing traceable geo-referenced ground-truth flood incident evidence across Bengaluru (BBMP control room logs, KSNDMC reports, news archives) for the August–September 2022 disaster.

