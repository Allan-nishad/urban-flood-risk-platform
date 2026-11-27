# Phase 4.1 — MERIT Hydro Upstream Contributing Area (UPA) Verification Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban (1,170 Cells, 1-km Grid)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Reporting Date:** 2026-11-05  
**Data Evaluation Status:** **`PENDING_ACQUISITION` (Access Restricted by Yamazaki Lab Agreement; Preserved Cleanly as `NaN`)**  

---

## 1. Executive Summary & Acquisition Status

Upstream Contributing Area (UPA, $\text{km}^2$) represents the accumulated upstream catchment area draining into each pixel. It is the primary hydrological predictor required to compute Topographic Wetness Index ($\text{TWI} = \ln(\alpha / \tan \beta)$) and Stream Power Index ($\text{SPI} = \alpha \cdot \tan \beta$).

### Forensic Status Audit:
- **Target File:** `data/raw/hydrology/merit_hydro/n10e075_upa.tif`
- **Current Disk State:** Directory `data/raw/hydrology/merit_hydro/` exists as an empty staging directory (`.gitkeep`).
- **Access Constraint:** MERIT Hydro is developed by Prof. Dai Yamazaki (Institute of Industrial Science, The University of Tokyo). Distribution terms require researchers to register via the official Google Form to receive automated download credentials (HTTP Basic Auth).
- **Compliance Enforcement:** In adherence to access boundary rules, the platform did not fabricate synthetic UPA values. All UPA columns (`upa_mean_sqkm`, `upa_max_sqkm`, `upa_valid_pixel_fraction`) are preserved strictly as `NaN`.

---

## 2. Product Specifications & Target Granule Metadata

| Attribute | Specification | Hydrological Audit Notes |
| :--- | :--- | :--- |
| **Product Name** | MERIT Hydro: Global Hydrography Datasets (v1.0.1) | Hydrography based on MERIT DEM and multi-source hydro datasets. |
| **Target Tile** | `n10e075_upa.tif` | Covers $10^\circ\text{N} - 15^\circ\text{N}, 75^\circ\text{E} - 80^\circ\text{E}$ (encompassing all of southern Karnataka). |
| **Native Resolution** | 3 arc-seconds ($\approx 90\text{ m}$ at equator) | Hydrologically conditioned flow accumulation raster. |
| **Variable Name** | `upa` (Upstream Drainage Area) | Unit: Square kilometres ($\text{km}^2$). |
| **Fill / NoData Value** | `-9999.0` | Ocean and undefined endorheic sinks. |
| **CRS** | EPSG:4326 (WGS84 Geodetic) | Unprojected geographic latitude/longitude. |
| **Licence** | Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) | Free for academic and research evaluation. |

---

## 3. Methodological Risk of Substituting Arbitrary Zeros

> [!CAUTION]
> **Preserving NaN vs. Zero Substitution:**
> In unprincipled machine learning pipelines, missing hydrological data is frequently replaced with $0.0$.
> In hydrology, an upstream contributing area of $0.0\text{ km}^2$ asserts that a cell is a razor-sharp mountain ridge crest with zero catchment inflow.
> Substituting zeros in low-elevation valley bottoms (such as Bellandur or Outer Ring Road) would severely mislead models into classifying natural drainage bottlenecks as hilltops.
> Preserving UPA as `NaN` ensures that downstream algorithms explicitly recognize that catchment drainage area is unobserved.

---

## 4. Manual Unblocking Instructions

1. Visit the Yamazaki Lab registration portal:
   `http://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_Hydro/`
2. Complete the Google Form with academic/research affiliation to obtain download credentials.
3. Access the distribution server:
   `https://web.hydro.iis.u-tokyo.ac.jp/MERIT_Hydro/v1.0.1/upa/`
4. Download tile `n10e075_upa.tif` (approx. 45 MB).
5. Place the file at `data/raw/hydrology/merit_hydro/n10e075_upa.tif`.
6. Run `python -m floodrisk.processing.integration` to extract zonal accumulation statistics across the 1,170 master grid cells.

