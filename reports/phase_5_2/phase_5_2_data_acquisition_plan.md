# Phase 5.2 — Track F: Genuine Data Acquisition & Evidence Closure Plan

## 1. Executive Summary

This report establishes the concrete data acquisition protocol required to close the five primary scientific evidence gaps identified during the Phase 5.2 reconciliation.

The platform will not manufacture, calibrate, or extrapolate synthetic fixtures to simulate real-world phenomena. Every dataset targeted below must be obtained in its native provider format with authentic metadata and verified cryptographic checksums before entering the platform's analytical pipeline.

---

## 2. Priority Acquisition Registry & Technical Specifications

### Dataset 1: Genuine Archived NWP Forecast Cycles
* **Provider:** European Centre for Medium-Range Weather Forecasts (ECMWF) / NOAA National Centers for Environmental Prediction (NCEP).
* **Target Products:**
  1. ECMWF IFS HRES Cycle Archive (0.1° / ~9 km resolution).
  2. NOAA GFS 0.25° Global Forecast System Archive (available via NOAA NOMADS and AWS Open Data Registry).
* **Geographic Coverage:** Bounding box $[77.0^\circ - 78.0^\circ\text{E}, 12.5^\circ - 13.5^\circ\text{N}]$ (covers Bengaluru Urban and surrounding catchment).
* **Temporal Coverage:** 2022 Monsoon Season (August 15 – October 15, 2022) and 2024 Monsoon Season.
* **Temporal Resolution:** 3-hourly forecast steps out to 72 hours (cycles: 00Z and 12Z).
* **Native Data Format:** WMO GRIB2 format.
* **License:** Creative Commons CC-BY-4.0 (ECMWF Open Data) / Open Public Domain (NOAA GFS).
* **Access Method & Tools:** `ecmwf-opendata` Python API client / NOAA AWS S3 public bucket direct download.
* **Authentication Requirements:** ECMWF API key / Anonymous AWS S3 access.
* **Required Processing:**
  * Byte-level GRIB2 message decoding using `cfgrib` / `eccodes`.
  * Spatial cropping and bilinear remapping to EPSG:6933 1-km grid.
  * Temporal differencing to calculate 6h, 12h, and 24h accumulated rainfall depth ($\text{mm}$).

### Dataset 2: Telemetric Ground Rainfall Observations
* **Provider:** Karnataka State Natural Disaster Monitoring Centre (KSNDMC) / India Meteorological Department (IMD).
* **Target Product:** KSNDMC Varuna Telemetric Rain Gauge (TRG) network (over 100 automated stations across BBMP zones) and IMD AWS stations.
* **Geographic Coverage:** Bruhat Bengaluru Mahanagara Palike (BBMP) municipal boundary.
* **Temporal Coverage:** August 15 – October 15, 2022 (covering August 29–30 and September 4–5 extreme events).
* **Temporal Resolution:** 15-minute / Hourly / 24-hour daily depths (08:30 IST standard cutoff).
* **Native Data Format:** CSV / Tabular XLSX / Portal API payload.
* **License:** Government of Karnataka Open Data Initiative / Academic Research License.
* **Access Method:** Official data requisition letter to KSNDMC Director / RTI request / Web portal archival download.
* **Authentication Requirements:** Government institutional login or formal data agreement.
* **Known Limitations:** In high-intensity storms, tipping bucket gauges may underestimate intense downpours ($>100\text{ mm/hr}$) by $5–10\%$ due to mechanical tipping time.

### Dataset 3: Official Civic Flood-Inundation Records
* **Provider:** BBMP Disaster Management Cell / Karnataka State Disaster Management Authority (KSDMA) / Bengaluru Traffic Police (BTP).
* **Target Product:** Emergency Control Room Inundation Logbooks, Ward Engineer Field Assessment Registers, and Geo-tagged Citizen SOS records.
* **Geographic Coverage:** All 198 BBMP wards.
* **Temporal Coverage:** August 29 – September 8, 2022.
* **Temporal Resolution:** Incident event timestamp (nearest hour).
* **Native Data Format:** PDF dispatch reports, municipal GIS shapefiles, dispatch logbooks.
* **Required Processing:**
  * Spatial geocoding of street intersections to point coordinates with explicit spatial uncertainty radii ($\pm 50–200\text{ m}$).
  * Standardization into the platform's 7-class flood evidence taxonomy.
  * Extraction of flood depth measurements ($\text{cm}$) and duration (hours until drainage).

### Dataset 4: Instrumented Valley Negative Ground Truth
* **Provider:** BBMP Stormwater Drain (SWD) Department / Bangalore Water Supply and Sewerage Board (BWSSB).
* **Target Product:** Water-level telemetry in primary/secondary storm drains (raja kaluves) and monitored lake sluice gates.
* **Objective:** Establish verified absence of inundation in low-lying valley corridors during heavy rain events.
* **Required Processing:**
  * Temporal alignment with peak rainfall episodes.
  * Identification of low-lying cells ($<860\text{ m}$) where water levels remained strictly within channel banks ($0\text{ cm}$ surface flooding).

### Dataset 5: Authentic Sentinel-1 C-Band SAR SAFE Packages
* **Provider:** European Space Agency (ESA) via Copernicus Data Space Ecosystem (CDSE).
* **Target Scenes:**
  1. `S1A_IW_GRDH_1SDV_20220812T004616_20220812T004641_044512_0550B6_F821.SAFE` (Pre-event)
  2. `S1A_IW_GRDH_1SDV_20220905T004616_20220905T004641_044862_055BE4_D16F.SAFE` (Co-event peak)
  3. `S1A_IW_GRDH_1SDV_20220917T004616_20220917T004641_045037_0561C8_9A7B.SAFE` (Post-event)
* **Access Method:** CDSE OData REST API using `sentinelsat` or `requests`.
* **Authentication Requirements:** CDSE User Account credentials.
* **Storage Footprint:** ~4.8 GB total download storage.
* **Required Processing:** ESA SNAP Graph Processing Tool (`gpt`) calibration and Doppler terrain correction.

---

## 3. Ethical and Security Compliance Rules

* **Access Restrictions:** The platform will never attempt to bypass web scrapers, login walls, CAPTCHAs, or token expirations.
* **Manual Acquisition Path:** When programmatic APIs are gated behind organizational credentials, the platform will generate explicit, reproducible curl/Python scripts for the authorized user to run locally.
* **Prohibition of Workarounds:** Open-Meteo retrospective reanalysis or synthetic rainfall curves must never be substituted for authentic operational forecasts.

