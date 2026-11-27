# Phase 5.2 — Track E: SAR Authenticity & Processing Readiness Audit

## 1. Executive Summary

This report audits the status of Synthetic Aperture Radar (SAR) observations within the platform, evaluating the Copernicus Sentinel-1A scene records and the physical feasibility of radar-based urban flood detection in Bengaluru.

* **Repository Data Audit:** The repository contains **only catalogue search metadata queried from the Copernicus Data Space Ecosystem (CDSE)**. It contains **no raw Sentinel-1 Level-1 SAFE archives, no measurement GeoTIFFs, no orbit state vectors (.EOF), and no local SNAP/GDAL processing execution logs**.
* **Processing Classification:** Formally classified as **`SCENE_AUDIT_ONLY`**.
* **Validated Inundation Mask Status:** **`NOT_ESTABLISHED`**. No authentic satellite radar flood mask has been generated on-premises.
* **Engineering Fixture Quarantine:** The simulated synthetic Sentinel-1 raster fixture created in Phase 2A.5 remains **strictly quarantined** in `tests/fixtures/` and is barred from entering the real-world feature matrix or dashboard.

---

## 2. On-Disk File Audit for Sentinel-1 Products

An exhaustive file-system inspection of the workspace was conducted:

| Expected SAR Artifact | File Extension | Found in Repository? | Actual Location / Status |
| :--- | :---: | :---: | :--- |
| Raw SAFE Zip Archive | `.zip` | **NO** | Not downloaded (multi-gigabyte storage constraints). |
| Measurement Raster Files | `.tiff` / `.tif` | **NO** | Zero raw SAR measurement rasters present. |
| Product Annotation XML | `.xml` | **NO** | No ESA calibration/noise vectors on disk. |
| Precise Orbit Ephemerides | `.EOF` | **NO** | No orbit state vectors downloaded. |
| SNAP Processing Graph Log | `.xml` / `.log` | **NO** | SNAP graph execution was not run locally. |
| Calibrated $\sigma^0$ Backscatter | `.tif` | **NO** | Zero calibrated backscatter rasters present. |
| Terrain-Corrected Orthorectified Mask | `.tif` | **NO** | Zero orthorectified radar flood masks present. |
| CDSE Scene Inventory Metadata | `.parquet` | **YES** | `authentic_sar_scene_manifest.parquet` (3 rows). |

---

## 3. Audited Scene Inventory (Copernicus Data Space Ecosystem)

The 3 authentic scenes catalogued in `authentic_sar_scene_manifest.parquet` possess verified Copernicus metadata:

```
+------------------------------------+------------+--------------+--------------+-----------------------+----------------------+
| Scene Identifier                   | Orbit Path | Direction    | Polarization | Acquisition Time UTC  | Role in Flood Event  |
+------------------------------------+------------+--------------+--------------+-----------------------+----------------------+
| S1A_IW_GRDH_1SDV_20220812T004616...| Path 165   | DESCENDING   | VV + VH      | 2022-08-12 00:46:16   | PRE_EVENT_BASELINE   |
| S1A_IW_GRDH_1SDV_20220905T004616...| Path 165   | DESCENDING   | VV + VH      | 2022-09-05 00:46:16   | CO_FLOOD_PEAK        |
| S1A_IW_GRDH_1SDV_20220917T004616...| Path 165   | DESCENDING   | VV + VH      | 2022-09-17 00:46:16   | POST_RECESSION       |
+------------------------------------+------------+--------------+--------------+-----------------------+----------------------+
```

*Geometric Compatibility:* All three scenes share identical flight direction (Descending) and identical relative orbit path (Track 165), providing consistent incidence angle geometry ($30.4^\circ - 46.2^\circ$).

---

## 4. Fundamental Physical Barriers to Urban C-Band Flood Mapping

Even upon future download and SNAP execution, two major physical limitations govern C-band SAR in Bengaluru Urban:

### A. The 24-Day Baseline Temporal Gap
Sentinel-1B suffered an instrument failure in December 2021, reducing the constellation revisit frequency from 6 days to 12 days. Over Bengaluru on Track 165, the pre-event acquisition was August 12 and the peak co-flood acquisition was September 5, 2022—a gap of **24 days**.
Over a 24-day tropical monsoon interval:
* Natural vegetation grows rapidly, dramatically altering radar volume scattering.
* Ambient soil moisture across the non-flooded urban landscape increases by $15–30\%$, raising dielectric constants and causing widespread background backscatter increases ($+2\text{ to }+4\text{ dB}$).
* Backscatter change detection ($\Delta \sigma^0 = \sigma_{\text{post}}^0 - \sigma_{\text{pre}}^0$) is confounded by environmental moisture changes unrelated to standing water.

### B. Urban Corner Reflectors & Double-Bounce Scattering
Specular reflection of radar waves off smooth open water sends energy away from the sensor, producing dark pixels ($\sigma^0 < -18\text{ dB}$).
However, in high-density urban environments:
* The right-angle junction between a vertical building facade and a horizontal flooded street acts as a **radar dihedral corner reflector**.
* Energy reflects off the water to the wall, and bounces directly back to the satellite antenna.
* Consequently, flooded urban street canyons often appear **anomalously bright ($\sigma^0 > -6\text{ dB}$)**, rather than dark!
* Standard thresholding algorithms (e.g., Otsu, Bunting, Kittler-Illingworth) fail in urban canyons, detecting open lakes while missing flooded residential layouts.

---

## 5. Requirements for Genuine SAR Validation in Phase 6

To elevate SAR processing from `SCENE_AUDIT_ONLY` to a validated scientific product:
1. **Acquire Raw Level-1 GRD SAFE Packages:** Ingest the actual 1.6 GB ZIP archives from CDSE using dedicated credentials.
2. **Execute SNAP Preprocessing Pipeline:**
   * Apply Precise Orbit Files (`.EOF`).
   * Remove thermal noise and GRD border noise.
   * Radiometric calibration to $\sigma^0$ (sigma nought in decibels).
   * Refined Lee speckle filtering ($7\times 7$ window).
   * Range Doppler Terrain Correction using Copernicus 30m DEM.
3. **Deploy Interferometric Coherence (InSAR) or High-Resolution Radar:**
   * High-resolution X-band (TerraSAR-X, 1–3m) to resolve street widths.
   * Multi-temporal coherence loss ($\gamma_{\text{coherence}}$) to detect flooded streets independent of corner reflection backscatter.

