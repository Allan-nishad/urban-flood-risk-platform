# Real Data Acquisition Readiness & Source Verification Report
**Project:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Phase:** 2A — Real Data Acquisition & Feature Engineering Baseline  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Audit Date:** 2026-11-05  

---

## 1. Resolution of Critical Scientific Inconsistencies

### A. MERIT Hydro Tile Verification & Geographic Bounds
- **The Initial Proposal Discrepancy:** The initial Phase 1 listing proposed tile `n10e070_upa.tif`.
- **Geographic Investigation:**
  - MERIT Hydro tiles follow a **$5^\circ \times 5^\circ$ grid tiling system** where the tile name represents the lower-left (Southwest) corner in integer degrees.
  - `n10e070` covers latitude $10.0^\circ\text{N} \le \phi < 15.0^\circ\text{N}$ and longitude $70.0^\circ\text{E} \le \lambda < 75.0^\circ\text{E}$. This covers the Arabian Sea, Goa, and coastal Karnataka, terminating at $75.0^\circ\text{E}$—approximately $250\text{ km}$ west of Bengaluru.
  - Bengaluru Urban development extent spans **$12.85^\circ\text{N} \le \phi \le 13.15^\circ\text{N}$** and **$77.45^\circ\text{E} \le \lambda \le 77.75^\circ\text{E}$**.
- **Corrected Tile Designation:**
  - The correct tile enclosing Bengaluru is **`n10e075`** (specifically file **`n10e075_upa.tif`**), which covers $10.0^\circ\text{N} \text{ to } 15.0^\circ\text{N}$ and $75.0^\circ\text{E} \text{ to } 80.0^\circ\text{E}$.
  - The regional tarball package is `upa_n00e070.tar` (covering the $30^\circ \times 30^\circ$ quadrant $0^\circ-30^\circ\text{N}, 70^\circ-100^\circ\text{E}$).
- **Tile Properties:**
  - Layer: `upa` (Upstream Contributing Drainage Area)
  - Native Resolution: 3 arc-seconds ($\sim 90\text{ m}$)
  - Native CRS: EPSG:4326 (WGS84)
  - Data Type: Float32
  - Units: $\text{km}^2$
  - NoData Value: $-9999.0$
- **Access Protocol:** Yamazaki Lab download requires registration via Google Form on the project portal ([http://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_Hydro/](http://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_Hydro/)) to receive an automated HTTP basic-authentication password.

---

### B. Correct Semantic Classification of ESA WorldCover
- **Terminology Correction:** The built-up layer from ESA WorldCover is classified strictly as **`fraction_built_up`** (fraction of valid pixels classified as built-up land cover, Class 50).
- **Scientific Limitation Enforced:**
  - WorldCover built-up class detects structural presence (roofs, concrete, paved surfaces, transport corridors).
  - It is **NOT** a direct physical measurement of soil imperviousness or infiltration capacity. A high built-up fraction indicates dense urban structural presence, but does not distinguish permeable interlocking pavers, roadside unpaved shoulders, or green roofs from impermeable concrete.
  - Dedicated imperviousness surface models (e.g., Copernicus High Resolution Layers or localized municipal drainage coefficients) will be investigated if micro-hydraulic runoff modeling is initiated in later phases.

---

### C. SRTM GL1 30m Surface vs. Ground-Level Elevation Constraints
- **Physical Sensor Constraints:**
  - SRTM (Shuttle Radar Topography Mission) utilized C-band radar interferometry ($5.3\text{ GHz}$). At C-band, radar pulses reflect off tree canopies and building rooftops with only partial penetration.
  - In Bengaluru's dense multi-story urban core, SRTM behaves as a **Digital Surface Model (DSM)** or composite surface model rather than a bare-earth Digital Terrain Model (DTM).
  - A 30-meter SRTM pixel cannot resolve street curb hydraulics, roadside drains (rajakaluves), or underpass depressions.
- **Implications for HAND (Height Above Nearest Drainage):**
  - HAND calculation requires a hydrologically conditioned, pit-filled bare-earth DTM and a topologically consistent drainage network.
  - Running HAND directly on raw urban SRTM introduces severe flow blockage artifacts across elevated road flyovers and building clusters. HAND will be evaluated strictly as a regional macro-topographic susceptibility metric once hydro-conditioned DEMs (e.g., MERIT Hydro `elv`) are integrated.

---

### D. Verification of IMERG V07B Native Resolution & Unit Semantics
- **Native Spatial Resolution:** $0.1^\circ \times 0.1^\circ$ ($\sim 10\text{ km} \times 10\text{ km}$ at low latitudes; $\sim 9.7\text{ km}$ over Bengaluru).
- **Spatial Precision Disclaimer Enforced:**
  - Mapping IMERG precipitation to 1-km grid cells provides spatial indexing alignment with terrain features.
  - **It does NOT create 1-km precipitation detail.** Multiple contiguous cells within a $10\text{ km} \times 10\text{ km}$ footprint legitimately receive the identical rainfall estimate.
- **Unit Verification Rule (in `src/floodrisk/processing/rainfall.py`):**
  - `GPM_3IMERGHH` (30-min half-hourly): Variable `precipitationCal` has units `mm/hr`. Converted to depth via:
    $$\text{Depth (mm)} = \text{precipitationCal} \times 0.5\text{ hr}$$
  - `GPM_3IMERGDF` (24-hr daily): Variable `precipitation` has units `mm`. Converted to depth via factor **$1.0$ (no multiplication by 0.5)**.

---

## 2. Successfully Acquired Real Satellite Dataset

### ESA WorldCover 10m 2021 v200
- **Physical File on Disk:** `data/raw/land_cover/ESA_WorldCover_10m_2021_v200_N12E075_Map.tif`
- **Source:** European Space Agency / VITO Remote Sensing via AWS S3 Open Data Public Bucket
- **Direct HTTPS URL:** `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N12E075_Map.tif`
- **File Size:** $127,650,362\text{ bytes}$ ($121.74\text{ MB}$)
- **SHA-256 Checksum:** `f9269901e07d86c2e180d661d0e8924e3ee57dd589f7433b9874861b3c65a978`
- **Raster Dimensions:** $36,000 \times 36,000\text{ pixels}$ ($1.296\text{ billion pixels}$)
- **Native Resolution:** $0.0000833333^\circ \approx 10\text{ m}$
- **Native Coordinate System:** EPSG:4326 (WGS 84)
- **Bounding Box:** $[75.0^\circ\text{E}, 12.0^\circ\text{N}]$ to $[78.0^\circ\text{E}, 15.0^\circ\text{N}]$ (Encloses Bengaluru Urban $77.45^\circ-77.75^\circ\text{E}, 12.85^\circ-13.15^\circ\text{N}$)
- **NoData Value:** `0`
- **Verified Classes Present:** 10 (Trees), 20 (Shrub), 30 (Grass), 40 (Cropland), 50 (Built-up), 60 (Bare), 80 (Water), 90 (Wetland), 95 (Mangroves)
- **Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0)

---

## 3. Pending Datasets & Exact Acquisition Instructions

| Dataset | Required Filename(s) | Destination Path | Access Protocol & Instructions |
| :--- | :--- | :--- | :--- |
| **Authoritative Boundary** | `bengaluru_urban.geojson` | `data/external/boundaries/` | **Survey of India Portal:** Requires mobile OTP login on [onlinemaps.surveyofindia.gov.in](https://onlinemaps.surveyofindia.gov.in/). Download State/District Boundary Database (`OVSF/1M/7`), extract Bengaluru Urban polygon to destination. |
| **SRTM GL1 30m DEM** | `N12E077.SRTMGL1.tif`<br>`N13E077.SRTMGL1.tif` | `data/raw/terrain/` | **NASA Earthdata Login:** Free account required at [urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov/). Download from USGS LP DAAC inventory: `https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/`. |
| **MERIT Hydro 90m** | `n10e075_upa.tif` | `data/raw/hydrology/` | **Yamazaki Lab Portal:** Submit Google registration form at [http://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_Hydro/](http://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_Hydro/). Use received HTTP basic-auth credentials to download `n10e075_upa.tif`. |
| **NASA GPM IMERG V07B** | `GPM_3IMERGHH_07B` / `GPM_3IMERGDF` | `data/raw/rainfall/` | **NASA GES DISC:** Earthdata login required at [disc.gsfc.nasa.gov](https://disc.gsfc.nasa.gov/). Download half-hourly or daily NetCDF4/GeoTIFF files for target historical dates. |
| **Sentinel-1A SAR Scenes** | `S1A_IW_GRDH_1SDV_20220824T...`<br>`S1A_IW_GRDH_1SDV_20220905T...` | `data/raw/weather/sar/` | **Copernicus Data Space (CDSE):** Register at [dataspace.copernicus.eu](https://dataspace.copernicus.eu/). Download Relative Orbit Track 91 Level-1 GRDH scenes for August 24, 2022 and September 5, 2022. |

