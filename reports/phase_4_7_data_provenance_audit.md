# Phase 4.7.8 — Scientific Audit: Primary Data Acquisition & Provenance Gates

**Platform:** Bengaluru Urban Flood Risk Intelligence Platform  
**Component:** Data Ingestion, Provenance Tracking & Manifest Engine ([`src/floodrisk/provenance.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/provenance.py))  
**Audited Manifest:** [`reports/dataset_manifest.json`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/reports/dataset_manifest.json) (33 registered datasets)  
**Audit Classification:** **VERIFIED_WITH_LIMITATIONS (Strict Provenance Distinctions Documented)**

---

## 1. Audit Context & Epistemological Principles

In data-driven environmental platforms, three distinct levels of verification must be rigorously distinguished:
1. **Software Verification:** Code executes without syntax errors, tests pass, and files can be serialized and deserialized.
2. **Cryptographic Integrity:** A file on disk matches its recorded SHA-256 hash byte-for-byte, proving it has not been modified or corrupted since registration.
3. **Scientific Data Authenticity & Validity:** The source data represents authentic physical measurements, correctly acquired from authoritative providers, uncompromised by synthetic placeholders, with known spatial/temporal accuracy.

A 100% SHA-256 manifest match proves **Level 2 (Cryptographic Integrity)**; it does **not** automatically establish **Level 3 (Scientific Ground Truth)**.

---

## 2. Comprehensive Provenance Audit Matrix

Every primary data source across Phases 1 through 4.6 was audited against its physical availability on disk, credential requirements, and scientific validity:

| Data Foundation | Source Provider | Physical File on Disk | SHA-256 Checksum Verified? | Authentic or Synthetic? | Licensing / Credential Gate Status | Audit Classification |
| :--- | :--- | :--- | :---: | :---: | :--- | :---: |
| **ESA WorldCover 10m** | European Space Agency | `ESA_WorldCover_10m_2021_v200_N12E075_Map.tif` (1.06 GB) | **YES** (`VALID`) | **AUTHENTIC** | Open Access (Creative Commons). Acquired & Extracted. | **VERIFIED** |
| **SRTM GL1 30m DEM** | NASA / ESA STEP Archive | `SRTMGL1_N12_N13_E077_Bengaluru.tif` (15.6 MB) | **YES** (`VALID`) | **AUTHENTIC** | Public Domain. Two $1^\circ$ tiles mosaicked & validated. | **VERIFIED** |
| **Historical Flood Inventory** | BBMP / KSNDMC / Press Archives | `flood_event_inventory_bengaluru.parquet` (27.8 KB) | **YES** (`VALID`) | **AUTHENTIC** | Curated crowd/media records with spatial uncertainty ($250-1000\text{ m}$). | **VERIFIED_WITH_LIMITATIONS** |
| **NWP Weather Forecast** | Open-Meteo (ECMWF IFS & NOAA GFS) | `forecast_rainfall_bengaluru.parquet` (452.6 KB) | **YES** (`VALID`) | **AUTHENTIC** | Open API. 9 regional anchors (~9-13 km coarse model resolution). | **VERIFIED_WITH_LIMITATIONS** |
| **Sentinel-1A SAR Rasters** | Simulated Engineering Fixtures | `sentinel1_candidate_flood_change_mask_bengaluru.tif` | **YES** (`VALID`) | **SYNTHETIC** | Copernicus CDSE OAuth2 token gated. Quarantined from models. | **BLOCKED_BY_DATA_ACCESS** |
| **NASA GPM IMERG Granules** | NASA GES DISC Archive | `features_rainfall_bengaluru.parquet` (72.6 KB) | **YES** (`VALID`) | **SYNTHETIC PROXY** | NASA Earthdata login gated. Pipeline plumbing verified. | **BLOCKED_BY_DATA_ACCESS** |
| **MERIT Hydro UPA Raster** | Yamazaki Hydrology Lab | *Pipeline Proxy* | *N/A* | *PROXY* | Academic registration required (`n10e075_upa.tif`). | **BLOCKED_BY_DATA_ACCESS** |
| **Official Admin Boundary** | Survey of India / KGIS | *Provisional Bounding Box* | **YES** (`VALID`) | *PROVISIONAL* | Official municipal shapefile pending formal release. | **BLOCKED_BY_DATA_ACCESS** |

---

## 3. Epistemological Findings & Honest Status Declarations

1. **Authentic Foundations:**  
   The terrain elevation features (SRTM 30m) and land-cover imperviousness features (ESA WorldCover 10m) are authentic, physical satellite measurements with complete coverage of the 1,170 master grid cells.
2. **Authentic Forecast Stream with Resolution Limitations:**  
   The Open-Meteo NWP continuous forecast stream is an authentic operational service, but it operates at a coarse regional resolution (9 anchors covering the domain, $\sim 9 - 13\text{ km}$ native grid). It provides macro-scale atmospheric hazard surveillance, not localized 1-km weather observations.
3. **Quarantined Synthetic Fixtures:**  
   Sentinel-1 SAR simulated change masks and IMERG rainfall proxies are validated software fixtures. They are explicitly tagged with `SYNTHETIC_TEST_ONLY_QUARANTINED` in `dataset_manifest.json` and are forbidden from entering scientific or statistical risk evaluations.
4. **No Promotion Without Evidence:**  
   In compliance with scientific integrity rules, no pending or credential-gated dataset has been falsely promoted to "verified". All blocked datasets remain transparently identified.

