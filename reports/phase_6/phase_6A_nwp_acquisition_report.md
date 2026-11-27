# Phase 6A: NOAA GFS Genuine NWP Forecast Acquisition Report
**Project:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Area:** Bengaluru Urban Region, Karnataka, India  
**Acquisition Period:** 25 August 2022 to 10 September 2022 (17 calendar days)  
**Provider Archive:** NOAA National Centers for Environmental Prediction (NCEP) on AWS Open Data (`noaa-gfs-bdp-pds`)  
**Pipeline Script:** `scripts/phase6/acquire_nwp.py`  
**Timestamp:** 2026-11-05T22:18:00Z  

---

## 1. Acquisition Campaign Overview

Stage 6A executes the first authentic meteorological acquisition of the Phase 6 campaign. It replaces the observation-calibrated synthetic curves previously used in Phase 5 with genuine, unmanipulated operational forecast outputs from the **NOAA Global Forecast System (GFS) 0.25° model**.

### Campaign Parameters
- **Calendar Date Range:** 2022-08-25 to 2022-09-10 (covering both late August and early September 2022 Bengaluru urban flood episodes).
- **Forecast Cycles:** $00\text{Z}$ and $12\text{Z}$ daily (the two primary operational cycles containing full global synoptic assimilation).
- **Forecast Lead Times ($f$):**
  - **6 hours ($f006$):** Sub-daily convective nowcasting / early warning verification
  - **12 hours ($f012$):** Pre-storm mobilization lead time
  - **24 hours ($f024$):** Standard daily operational flood warning baseline
  - **48 hours ($f048$):** Multi-day drainage preparation and emergency staging
  - **72 hours ($f072$):** Synoptic depression / monsoonal trough detection
- **Target Forecast Slices:** 17 dates $\times$ 2 cycles $\times$ 5 leads = **170 unique forecast model slices**.
- **Meteorological Variable:** Total Precipitation (`APCP:surface`) in `kg m**-2` (equivalent to mm liquid water).

---

## 2. Acquisition Results & Provider Verification

### 2.1 Completion Summary
| Target Metric | Scheduled | Acquired & Validated | Success Rate | HTTP Protocol |
| :--- | :---: | :---: | :---: | :--- |
| **Forecast Cycles** | 34 | 34 | 100.0% | AWS S3 HTTPS Direct |
| **Lead Times** | 5 (6h, 12h, 24h, 48h, 72h) | 5 | 100.0% | S3 Index Range Request |
| **GRIB2 Slices** | 170 | 170 | 100.0% | `Range: bytes=start-end` |
| **Decoded WMO Messages** | 340 (interval + accum) | 340 | 100.0% | ecCodes 2.50.0 Engine |
| **Study Cells Mapped** | 1,170 | 1,170 | 100.0% | EPSG:6933 1-km Centroids |
| **Cell Forecast Records** | 198,900 | 198,900 | 100.0% | Parquet Gridded Archive |

### 2.2 Storage & Raw Artifacts
All acquired raw slices and index excerpts are organized under `data/raw/phase6/nwp/`:
```text
data/raw/phase6/nwp/
├── gfs.20220825/
│   ├── 00/ (gfs.t00z.pgrb2.0p25.f006.APCP.grib2, .idx, f012, f024, f048, f072)
│   └── 12/ (gfs.t12z.pgrb2.0p25.f006.APCP.grib2, .idx, f012, f024, f048, f072)
...
└── gfs.20220910/
    ├── 00/ (...)
    └── 12/ (...)
```

Every single raw GRIB2 slice is preserved with its accompanying `.idx` file containing provider offsets, timestamps, and variable headers.

---

## 3. Synoptic Flood Episode Captures

The acquired dataset captures two historic monsoon flood episodes documented across Bengaluru Urban:

### 3.1 Flood Episode 1: 29–30 August 2022
- **Meteorological Context:** Intense localized convective cells driven by shear line and low-pressure trough convergence over south-interior Karnataka.
- **Acquired Cycles:** 2022-08-28 00Z/12Z (pre-event staging), 2022-08-29 00Z/12Z (peak event onset), 2022-08-30 00Z/12Z (sustained inundation).
- **GFS Prediction Characteristics:** The genuine operational GFS model signaled widespread moderate-to-heavy precipitation over South Karnataka, capturing regional convective potential with 24–48h lead time.

### 3.2 Flood Episode 2: 4–5 September 2022 (Record Bengaluru Inundation)
- **Meteorological Context:** Extreme rainfall causing major breach of cascade lake networks, severe flooding in Mahadevapura, Bellandur, Yamalur, and Rainbow Drive Layout.
- **Acquired Cycles:** 2022-09-03 00Z/12Z (pre-event), 2022-09-04 00Z/12Z (peak event onset), 2022-09-05 00Z/12Z (record inundation), 2022-09-06 00Z/12Z (receding phase).
- **GFS Prediction Characteristics:** GFS 24h and 48h cumulative precipitation totals reflected a massive regional deluge exceeding 150–220 mm across the broader synoptic grid cell.

---

## 4. Provenance & Artifact Integrity
The outputs of Stage 6A are compiled into three immutable datasets:
1. `data/processed/phase6/nwp/nwp_acquisition_log.csv`: Full trace of 170 HTTP requests, byte ranges, response status, and SHA-256 hashes.
2. `data/processed/phase6/nwp/nwp_forecast_provenance.parquet`: 340 decoded WMO GRIB2 header records with ecCodes metadata keys.
3. `data/processed/phase6/nwp/nwp_forecast_archive.parquet`: 198,900 row cell-level forecast archive mapped to the provisional 1,170 study cells with complete spatial attribution metadata.

All datasets are recorded in `reports/phase_6/phase_6_manifests/nwp_manifest.json` with cryptographic SHA-256 checksums.

