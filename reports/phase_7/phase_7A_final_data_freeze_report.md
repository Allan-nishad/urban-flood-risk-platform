# Phase 7A — Final Data Freeze, Provenance, and Reproducibility Report

**Date of Execution:** 2026-11-05 18:17:14 UTC  
**Auditor:** Multi-Disciplinary Final Research & Engineering Team  
**Campaign Baseline:** `PHASE_6_ACCEPTED_WITH_DOCUMENTED_LIMITATIONS`  
**Study Domain:** Bengaluru Urban Region ($1,170\text{ km}^2$, 1,170 equal-area 1-km cells in EPSG:6933)  
**Status:** **`PASS_WITH_DOCUMENTED_LIMITATIONS`**  

---

## 1. Executive Summary & Audit Mandate

Workstream 7A establishes the final immutable research data baseline for Phase 7. Before conducting final uncertainty quantification, platform finalisation, and project closure, all underlying datasets from Phases 1 through 6 were audited to confirm:
1. Complete cryptographic preservation without silent alteration.
2. Complete schema, dimension, unit, and coordinate reference system (CRS) documentation.
3. Clean separation between raw archives, processed artifacts, and temporary scratch files.
4. Independent sandbox reproducibility of core physical processing pipelines.

---

## 2. Dataset Inventory & Integrity Audit (68 Manifest Entries / 68 Distinct Paths)

Across the five frozen platform manifests, **68 total dataset entries** were inspected and verified against disk:
- **Phase 1–4 Core Manifest:** 33 entries verified bit-for-bit (100% PASS)
- **Phase 5 Manifest:** 8 entries verified bit-for-bit (100% PASS)
- **Phase 5 Final Manifest:** 8 entries verified bit-for-bit (100% PASS)
- **Phase 5.2 Manifest:** 3 entries verified bit-for-bit (100% PASS)
- **Phase 6 Master Manifest:** 16 entries verified bit-for-bit (100% PASS)
- **Total Manifest Entries Audited:** **68 / 68 Verified Bit-for-Bit ($100.0\%$)**
- **Distinct File Paths on Disk:** **68 Unique Paths**

### Summary by Processing Tier:
| Category | File Count | Primary Storage Formats | Coordinate Systems / Grids | Checksum Integrity |
| :--- | :---: | :--- | :--- | :---: |
| **Grid & Spatial Boundaries** | 4 | `.gpkg`, `.parquet`, `.geojson` | EPSG:6933 (Equal Area 1-km), EPSG:4326 | 100% MATCH |
| **Terrain & Hydrography** | 8 | `.parquet`, `.tif` | SRTM / MERIT Hydro 1-km grid | 100% MATCH |
| **Precipitation & Remote Sensing**| 12 | `.parquet`, `.grib2` | IMERG $0.1^\circ$, GFS $0.25^\circ$ kwbc | 100% MATCH |
| **Ground Stations & Observations** | 5 | `.parquet` | Point lat/lons (IMD, KSNDMC, CPCB) | 100% MATCH |
| **SAR Feature Grids** | 6 | `.parquet`, `.tif` | Sentinel-1 IW GRDH Desc Orbit 165 | 100% MATCH |
| **Flood Incidents & Ground Truth** | 7 | `.parquet` | High-confidence geotagged records | 100% MATCH |
| **Exploratory Indicators** | 10 | `.parquet` | 1-km grid features, TWI, HIPI | 100% MATCH |
| **Validation & Audit Registries** | 16 | `.parquet`, `.csv`, `.json` | Matrix records, contingency logs | 100% MATCH |
| **Total** | **68** | — | — | **100% MATCH** |

---

## 3. End-to-End Data Dependency Graph

The platform maintains a strict one-way lineage from authoritative raw sources to exploratory indicators and verification matrices:

```mermaid
graph TD
    subgraph Raw Source Data
        A1["Copernicus CDSE Sentinel-1A SAFE Archive (Orbit 165)"]
        A2["AWS Open Data NOAA GFS 0.25° GRIB2 (s3://noaa-gfs-bdp-pds)"]
        A3["NASA GES DISC GPM IMERG Final Run v06B"]
        A4["MERIT Hydro / SRTM 1-arcsecond DEM"]
        A5["ESA WorldCover 2021 v200 (10m Land Cover)"]
        A6["IMD + KSNDMC Rain Gauge Daily Bulletins"]
        A7["Multi-Source Civic & Official Flood Incidents"]
    end

    subgraph Phase 1-4 Core Ingestion & Preprocessing
        B1["Equal-Area Study Grid 1,170 Cells (EPSG:6933)"]
        B2["Static Terrain Features (Elevation, Slope, WorldCover built-up)"]
        B3["Calibrated Sentinel-1 Backscatter (VV/VH, RTC, Speckle Filter)"]
        B4["IMERG Historical Precipitation Daily Raster & Zonal Totals"]
        B5["Exploratory Risk Indicators (Hazard, Exposure, Vulnerability)"]
    end

    subgraph Phase 6 Authentic Empirical Datasets
        C1["Authentic NOAA GFS Forecast Archive (170 slices, 6 native nodes)"]
        C2["Ground Rain Gauge Station Registry & 272 Primary Observations"]
        C3["Independent Flood Incident Inventory (24 records, 17 locations)"]
        C4["Flood Validation Ground Truth Matrix (13 Pos, 7 Neg, 1,150 Unobserved)"]
        C5["SAR Physical Regime Features & Open-Water Cross-Validation"]
        C6["Deterministic D8 Flow Routing, TWI & Dynamic HIPI Index"]
    end

    subgraph Phase 7 Verification & Academic Delivery
        D1["Dependence-Aware NWP Verification & Grouped Uncertainty"]
        D2["SAR Water Ambiguity Deconstruction & Street Canyon Blindness"]
        D3["Depression Sensitivity (Retention Basin vs Priority-Flood)"]
        D4["Operational Dashboard Console & Full 101+ Automated Test Suite"]
        D5["Final Academic Research Package & Closure Decision"]
    end

    A1 --> B3 --> C5 --> D2
    A2 --> C1 --> C6 --> D3
    A3 --> B4
    A4 --> B1 --> B2 --> C6 --> D3
    A5 --> B2 --> C6
    A6 --> C2 --> D1
    C1 --> D1
    A7 --> C3 --> C4 --> D2
    C4 --> D3
    D1 & D2 & D3 --> D4 --> D5
```

---

## 4. Sandbox Reproducibility Verification

To verify that the processed datasets are not orphaned static files, an independent reproducibility test was executed in sandbox directory `scratch/phase7/reproducibility`:
- **Pipeline Tested:** Canonical O'Callaghan & Mark (1984) D8 flow direction, recursive area accumulation, and Topographic Wetness Index (TWI) calculation.
- **Input:** `data/processed/features_static_bengaluru.parquet` (frozen elevation mean per cell).
- **Output Compared:** `data/processed/phase6/hydrology/topographic_routing_static_features.parquet`.
- **Results:**
  - Max absolute difference in TWI across 1,170 cells: **`0.000000`**
  - Max absolute difference in Flow Accumulation across 1,170 cells: **`0.000000`**
  - Reproducibility determination: **`REPRODUCIBLE_BIT_FOR_BIT`**

---

## 5. Storage Cleanliness & Path Verification

- **Duplicate Dataset IDs:** 0
- **Path Collisions:** 0
- **Unregistered Processed Files in Historical/Phase 6 Storage:** Only 1 non-gitkeep file (`data/processed/grid_bengaluru_urban_1000m.geojson`, which is the geojson representation of the registered `.gpkg`).
- **Active Git Status:** Clean, untracked repository state; no unauthorized git commits or destructive modifications.

---

## 6. Formal Gate Determination for Workstream 7A

$$\mathbf{GATE\_STATUS:\quad PASS\_WITH\_DOCUMENTED\_LIMITATIONS}$$

**Documented Baseline Limitations:**
1. All 68 baseline datasets are frozen and immutable.
2. The 198,900 NWP rows represent 6 native nodes; this attribution structure must be preserved.
3. The 1,150 unobserved cells remain strictly unobserved; no dry-label imputation is permitted.
4. Core physical algorithms are verified to be 100% reproducible bit-for-bit from frozen inputs.
