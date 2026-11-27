# Phase 4.1 — NASA GPM IMERG Precipitation Data Verification Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban (1,170 Cells at 1,000 m Resolution, EPSG:6933)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Reporting Date:** 2026-11-05  
**Data Evaluation Status:** **`PARTIALLY_VERIFIED` (Staged Engineering Pipeline Verified; Raw NetCDF Granules Pending Authentication)**  

---

## 1. Executive Summary & Critical Provenance Audit

This report addresses the critical IMERG precipitation provenance gate. 
The earlier Phase 2A.3 and Phase 3 implementations developed the spatial mapping, unit validation, and antecedent accumulation logic, but did not conclusively establish raw NetCDF granule downloads on disk.

### Forensic Disk Inspection:
- **Directory Inspected:** `data/raw/rainfall/`
- **Physical Granules Present:** 0 raw `.nc4` files (directory contains only `.gitkeep`).
- **Download Automation:** Shell script [`scripts/download_imerg_gesdisc.sh`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/scripts/download_imerg_gesdisc.sh) defines automated retrieval commands for 17 daily granules from NASA GES DISC (`https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/`).
- **Authentication Blocker:** GES DISC HTTPS endpoints enforce HTTP Basic Authentication via NASA Earthdata Login (`urs.earthdata.nasa.gov`). Host configuration file `~/.netrc` does not exist on this development workstation.
- **Strict Compliance:** In accordance with Non-Negotiable Rule 9 (Zero Fabrication) and access boundary guidelines, no credentials were manufactured and no proxy bypasses were attempted.

---

## 2. IMERG Granule Specifications & Processing Lineage

The platform targets the definitive research-grade Level-3 calibrated product:

| Attribute | Specification | Verification Audit Notes |
| :--- | :--- | :--- |
| **Product Short Name** | `GPM_3IMERGDF` (Daily) / `GPM_3IMERGHH` (Half-Hourly) | Version 07B (released 2024, superseding V06). |
| **Provider** | NASA Goddard Earth Sciences Data and Information Services Center (GES DISC) | Official DAAC for GPM mission data. |
| **Target Time Range** | 2022-08-25 to 2022-09-10 (17 consecutive daily intervals) | Monsoonal storm events and inter-storm antecedent period. |
| **Variable Name** | `precipitationCal` | Multi-satellite precipitation estimate with gauge calibration. |
| **Native Spatial Resolution** | $0.1^\circ \times 0.1^\circ$ (approx. $10\text{ km} \times 10\text{ km}$ at equator) | Microwave + infrared constellation with GPCC gauge calibration. |
| **Native Units** | $\text{mm/day}$ for daily product; $\text{mm/hr}$ for half-hourly product | Verified in [`src/floodrisk/processing/rainfall.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/rainfall.py). |
| **Fill / NoData Value** | `-9999.9` (masked as `NaN`) | Documented in official IMERG technical specification. |

---

## 3. Unit Conversion & Antecedent Logic Validation

The rainfall processing engine in [`src/floodrisk/processing/rainfall.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/rainfall.py) was audited for physical and temporal correctness:

1. **Daily Depth Integration:**
   - Daily granules express rainfall depth directly in $\text{mm/day}$. The code preserves this directly without erroneous multiplication by 24.
   - Half-hourly granules express precipitation rate in $\text{mm/hr}$. The pipeline correctly applies:
     $$\text{Depth}_{30\text{min}} = \text{Rate} (\text{mm/hr}) \times 0.5 \text{ hr}$$
2. **Strict Antecedent Lookbacks:**
   - Rolling antecedent windows strictly exclude the target date:
     - 3-day antecedent: $\sum_{k=1}^3 P_{t-k}$
     - 7-day antecedent: $\sum_{k=1}^7 P_{t-k}$
     - 14-day antecedent: $\sum_{k=1}^{14} P_{t-k}$
   - Exponential decaying Antecedent Precipitation Index:
     $$API_t = P_t + \alpha API_{t-1}, \quad \alpha = 0.85$$
   - This prevents forward temporal leakage while capturing persistent catchment wetness.

---

## 4. Fundamental Spatial Support Constraint: Coarse vs. Fine Resolution

> [!WARNING]
> **Spatial Support Limitation:**
> IMERG provides satellite microwave precipitation at approximately **$10\text{ km} \times 10\text{ km}$ ($0.1^\circ$) resolution**.
> Remapping this raster onto the $1,000\text{ m}$ master grid ($1\text{ km}^2$ cells in EPSG:6933) represents **spatial re-binning/downsampling of the observation canvas**, NOT fine-scale local measurement.
> The platform strictly disclaims that 1-km grid cells contain 1-km-resolution precipitation measurements. Convective micro-scale cloudburst cells ($1 - 2\text{ km}$) cannot be resolved by IMERG.

---

## 5. Unblocking Action Plan for Authentic Granule Download

To transition IMERG from `PARTIALLY_VERIFIED` to `VERIFIED_REAL`:
1. Register a free NASA Earthdata account at `https://urs.earthdata.nasa.gov/`.
2. Approve the NASA GES DISC application in user profile permissions.
3. Configure `~/.netrc` (or `%USERPROFILE%\_netrc` on Windows) with:
   ```
   machine urs.earthdata.nasa.gov login <YOUR_USERNAME> password <YOUR_PASSWORD>
   ```
4. Execute [`scripts/download_imerg_gesdisc.sh`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/scripts/download_imerg_gesdisc.sh) in a bash terminal to stream granules into `data/raw/rainfall/gpm_imerg_v07/`.
5. Run `python -m floodrisk.processing.rainfall` to parse NetCDF files directly and update checksums in `reports/dataset_manifest.json`.

