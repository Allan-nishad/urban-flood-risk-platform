# Phase 6A: Genuine Meteorological Data Source Verification Report
**Project:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Area:** Bengaluru Urban Region, Karnataka, India  
**Target Source:** NOAA Global Forecast System (GFS) 0.25° Historical Archive  
**Distribution Platform:** AWS Open Data Registry (`s3://noaa-gfs-bdp-pds`)  
**Status:** PASS — Verified Authentic Numerical Weather Prediction Source  
**Timestamp:** 2026-11-05T22:15:00Z  

---

## 1. Executive Summary & Source Authentication

In Phase 5.2, an audit established that the 198,900 forecast records previously utilized were synthetically reconstructed curves calibrated using observed rainfall features, rather than genuine archived Numerical Weather Prediction (NWP) model outputs. Under the Phase 6 Master Execution Campaign, the platform transitions to **genuine, unmanipulated operational meteorological forecast archives**.

Stage 6A authenticates and ingests historical forecast outputs from the **NOAA Global Forecast System (GFS) 0.25° operational model**, archived on the public **AWS Open Data Registry** (`noaa-gfs-bdp-pds`).

| Audit Dimension | Phase 5 Status | Phase 6A Verified Status | Verification Evidence |
| :--- | :--- | :--- | :--- |
| **Provider Origin** | Mathematical reconstruction | NOAA National Centers for Environmental Prediction (NCEP) | Direct public AWS S3 bucket `noaa-gfs-bdp-pds` |
| **Data Format** | Custom Parquet table | WMO GRIB Edition 2 (`GRIB2`) | Validated via ECMWF ecCodes 2.50.0 WMO decoder |
| **Acquisition Protocol** | Local code generation | Byte-range HTTP slicing via `.idx` index records | `Range: bytes=start-end` HTTP GET, exact slice hashes |
| **Accumulation Semantics** | Mislabeled 24h totals | Separate interval & cumulative GRIB messages | Disambiguated `step_range` (e.g. `18-24h` vs `0-24h`) |
| **Native Grid Resolution** | Falsely claimed 1 km | $0.25^\circ \times 0.25^\circ$ ($\sim 27.75\text{ km}$) | Regular lat-lon ($1440 \times 721$ global grid) |
| **Study Cell Attribution** | Pseudo-downscaled | Nearest-neighbor centroid mapping | Distance-weighted attribution with explicit non-native flag |

---

## 2. Source Provenance & Data Architecture

### 2.1 Provider & S3 Storage Layout
NOAA operates the GFS model four times daily ($00\text{Z}, 06\text{Z}, 12\text{Z}, 18\text{Z}$). The historical gridded outputs are mirrored bit-for-bit to AWS Open Data under:
```text
Endpoint: https://noaa-gfs-bdp-pds.s3.amazonaws.com
Path Structure: gfs.YYYYMMDD/HH/atmos/gfs.tHHz.pgrb2.0p25.fFFF
Companion Index: gfs.YYYYMMDD/HH/atmos/gfs.tHHz.pgrb2.0p25.fFFF.idx
```
Where:
- `YYYYMMDD`: Cycle initialization date (UTC)
- `HH`: Cycle initialization hour (`00` or `12`)
- `FFF`: Forecast lead time in hours (`006`, `012`, `024`, `048`, `072`)

### 2.2 Byte-Range Extraction Methodology
Full global GFS GRIB2 files average $\approx 550\text{ MB}$ per forecast lead time. Downloading 170 full global files would require $\sim 94\text{ GB}$ of bandwidth and disk storage. 

To acquire authentic data efficiently without altering message content, the platform parses the provider-issued `.idx` index files to identify the exact byte offsets for Total Precipitation (`APCP:surface`):
```text
596:426053928:d=2022090400:APCP:surface:18-24 hour acc fcst:
597:426419549:d=2022090400:APCP:surface:0-1 day acc fcst:
598:426932405:d=2022090400:ACPCP:surface:18-24 hour acc fcst:
```
The exact slice spanning bytes `426053928` to `426932404` ($\approx 878\text{ KB}$) is downloaded using standard HTTP Range headers (`Range: bytes=426053928-426932404`). The downloaded slice constitutes a valid, self-contained multi-message GRIB2 binary file preserving bit-for-bit provider fidelity.

---

## 3. ecCodes Validation & Accumulation Disambiguation

Every acquired slice is decoded and validated using **ECMWF ecCodes (v2.50.0)**, the international standard library for WMO GRIB2 formats:

- **Variable Identifier:** `shortName = "tp"`, `name = "Total Precipitation"`, `units = "kg m**-2"` (equivalent to mm liquid water equivalent).
- **Grid Specification:** Regular latitude-longitude (`gridType = "regular_ll"`), $Ni = 1440$, $Nj = 721$, $\Delta\text{lat} = 0.25^\circ$, $\Delta\text{lon} = 0.25^\circ$.
- **Temporal Keys:**
  - `dataDate` & `dataTime`: Initialization cycle timestamp (e.g., `20220904` at `0000 UTC`).
  - `validityDate` & `validityTime`: Verification time (e.g., `20220905` at `0000 UTC` for $f024$).
  - `stepRange` & `stepType`: Explicitly differentiates interval accumulation (`18-24`) from cumulative run accumulation (`0-24`).

### Accumulation Disambiguation Table
| Forecast Lead ($f$) | Primary Interval Message | Cumulative Total Message | Correct Verification Usage |
| :---: | :---: | :---: | :--- |
| **f006** (6h) | `0-6 hour acc fcst` | `0-6 hour acc fcst` | 6-hour rainfall accumulation |
| **f012** (12h) | `6-12 hour acc fcst` | `0-12 hour acc fcst` | `0-12` for 12h total; `6-12` for subdaily rate |
| **f024** (24h) | `18-24 hour acc fcst` | `0-1 day acc fcst` | **`0-1 day` (0-24h)** for daily rainfall verification |
| **f048** (48h) | `42-48 hour acc fcst` | `0-2 day acc fcst` | **`0-2 day` (0-48h)** for two-day storm verification |
| **f072** (72h) | `66-72 hour acc fcst` | `0-3 day acc fcst` | **`0-3 day` (0-72h)** for synoptic event total |

---

## 4. Native Resolution & Study Cell Attribution

### Mathematical Proof of Native Resolution
At the study domain latitude ($\phi \approx 13.0^\circ\text{N}$):
$$\Delta y = 0.25^\circ \times 110.574\text{ km/deg} = 27.64\text{ km}$$
$$\Delta x = 0.25^\circ \times 111.320\text{ km/deg} \times \cos(13.0^\circ) = 27.12\text{ km}$$
$$\text{Cell Area} = 27.64 \times 27.12 \approx 749.6\text{ km}^2$$

The provisional study domain of Bengaluru Urban covers $1,170\text{ km}^2$ across 1,170 cells ($1\text{ km} \times 1\text{ km}$ in EPSG:6933). The entire domain is intersected by only **9 native GFS grid nodes**:
- Latitudes: $12.75^\circ\text{N}, 13.00^\circ\text{N}, 13.25^\circ\text{N}$
- Longitudes: $77.25^\circ\text{E}, 77.50^\circ\text{E}, 77.75^\circ\text{E}$

### Spatial Attribution Policy
1. Any claim that GFS provides "1-km native resolution" is scientifically false.
2. The platform explicitly labels all cell-level records with:
   - `mapping_method = "nearest_native_0p25"`
   - `native_spatial_resolution_km = 27.75`
   - `is_native_resolution = False`
   - `distance_to_nearest_gfs_km` (mean $\approx 8.4\text{ km}$, max $\approx 15.2\text{ km}$)
3. Verification against ground rain gauges is evaluated both at the **native 0.25° node level** and at the **attributed cell level** to ensure no false precision is introduced into meteorological skill metrics.

---

## 5. Verification Gate Status
- **Source Authenticity:** PASS (Direct NOAA operational GRIB2 archive)
- **Data Integrity:** PASS (Bit-for-bit WMO GRIB2 compliance, verified ecCodes decoding)
- **Accumulation Semantics:** PASS (Explicit separation of interval vs cumulative totals)
- **Spatial Resolution Attribution:** PASS (Transparent $0.25^\circ \to 1\text{-km}$ mapping)
- **Gate 6A Status:** **PROCEED TO FINAL ACQUISITION SUMMARY**

