# Final Platform Demonstration Checklist & Live Evaluation Script

**Project:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Repository:** `urban-flood-risk-platform`  
**Phase:** 7.2 Independent Final Audit & Project Closure  
**Target Audience:** Academic Examiners, Research Supervisors, Technical Reviewers  
**Estimated Demonstration Time:** 15–20 minutes  
**Date:** November 2026  

---

## 1. Pre-Demonstration Environment Verification

Ensure the local workstation environment is configured and ready:

```powershell
# 1. Open PowerShell terminal in the repository root
cd c:\Users\allan\Documents\Projects\urban-flood-risk-platform

# 2. Confirm Python version (Python 3.11.x)
.venv\Scripts\python.exe --version
# Expected Output: Python 3.11.15 (or 3.11.x)

# 3. Confirm virtual environment packages
.venv\Scripts\pip.exe list | Select-String -Pattern "rasterio|geopandas|shapely|numpy|scipy|pytest"
```

---

## 2. Step 1: Cryptographic Integrity & Ledger Audit

Demonstrate that all 73 datasets across all project phases match their SHA-256 cryptographic hashes bit-for-bit with zero file tampering:

```powershell
.venv\Scripts\python.exe scratch\phase7_final_verify_all.py
```

**Expected Verifier Output:**
```
======================================================================
PHASE 7 FINAL COMPREHENSIVE BIT-FOR-BIT MANIFEST VERIFICATION
======================================================================
Datasets checked: 73
Passed:           73
Failed:           0
Missing:          0
Success Rate:     100.0%
======================================================================
ALL 73 DATASETS MATCH BIT-FOR-BIT! INTEGRITY AUDIT PASSED!
```
*Examiner Talking Point:* "Every single dataset used in this platform—from historical baselines to raw GRIB2 files and processed SAR rasters—is cryptographically pinned and verified bit-for-bit."

---

## 3. Step 2: Automated Full-Stack Test Suite Execution

Run the complete automated test suite to demonstrate code quality, mathematical correctness, and edge-case handling across all 16 test modules:

```powershell
.venv\Scripts\pytest.exe -v
```

**Expected Test Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\allan\Documents\Projects\urban-flood-risk-platform
collected 109 items

tests\test_cli.py ........                                               [  7%]
tests\test_config.py .......                                             [ 13%]
tests\test_events.py ........                                            [ 21%]
tests\test_grid.py ......                                                [ 26%]
tests\test_integration_real_data.py ......                               [ 32%]
tests\test_phase_2b.py .......                                           [ 38%]
tests\test_phase_3.py ......                                             [ 44%]
tests\test_phase_4.py ......                                             [ 49%]
tests\test_phase_5.py .......                                            [ 55%]
tests\test_phase_6.py .......                                            [ 62%]
tests\test_phase_7.py ........                                           [ 69%]
tests\test_provenance.py ...                                             [ 72%]
tests\test_rainfall.py .......                                           [ 78%]
tests\test_sar.py ......                                                 [ 84%]
tests\test_validation.py ..........                                      [ 93%]
tests\test_zonal.py .......                                              [100%]

================ 109 passed, 2453 warnings in ~63.14s ================
```
*Examiner Talking Point:* "109 out of 109 unit and integration tests pass, proving mathematical correctness of the D8 algorithm, GFS interpolation, SAR calibration, and bootstrap confidence intervals."

---

## 4. Step 3: Launching the Research Dashboard Server

Launch the zero-dependency, high-performance research server:

```powershell
.venv\Scripts\python.exe -m floodrisk.dashboard.server --port 8000
```

**Console Startup Log:**
```
================================================================================
URBAN FLOOD RISK PLATFORM - RESEARCH DASHBOARD SERVER
Port: 8000 | Host: 127.0.0.1
Status: READY (Phase 7.2 Release)
URL: http://127.0.0.1:8000/
================================================================================
```
*Note:* Keep this process running in terminal 1, and open terminal 2 or a browser window.

---

## 5. Step 4: Live REST API Telemetry Queries

Query the live endpoints using PowerShell or curl to demonstrate the backend JSON data service:

### 4.1 System Health & Executive Summary
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/summary" | ConvertTo-Json
```
*Verification Check:* Confirms 1,170 domain cells, bounding box coordinates, and system status `ok`.

### 4.2 Forecast Verification & NWP Skill (Track A)
```powershell
$nwp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/phase6/nwp"
$nwp.verification_metrics | ConvertTo-Json
```
*Verification Check:* Confirms `paired_points: 256`, `mae: 18.64`, `rmse: 33.19`, `mean_bias: -10.88`, `pearson_r: 0.142`.

### 4.3 Ground Rain-Gauge Telemetry & Flood Evidence (Track B)
```powershell
$rain = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/phase6/ground-rainfall"
$rain.summary | ConvertTo-Json

$flood = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/phase6/flood-evidence"
$flood.summary | ConvertTo-Json
```
*Verification Check:* Confirms 21 rain gauges, 357 daily observations, 24 flood incidents across 17 locations in 13 cells, and 7 verified negative cells.

### 4.4 SAR Satellite Backscatter & Water Detection (Track B)
```powershell
$sar = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/phase6/sar"
$sar.summary | ConvertTo-Json
```
*Verification Check:* Confirms 3 Sentinel-1 SAFE scenes, specular decrease ratio, and confusion classification.

### 4.5 Physical Hydrology & Topographic Metrics (Track C)
```powershell
$hydro = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/phase6/hydrology"
$hydro.summary | ConvertTo-Json
```
*Verification Check:* Confirms 19 depression sinks, flow accumulation up to $186.0\text{ km}^2$, TWI range $10.08 - 19.04$, and ROC-AUC $= 0.560$.

### 4.6 Phase 7 Clustered Bootstrap & Uncertainty Bounds
```powershell
$unc = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/phase7/uncertainty"
$unc.bootstrap_correlations | ConvertTo-Json
```
*Verification Check:* Confirms naive CI $[0.02, 0.26]$ vs clustered block bootstrap CI $[-0.07, +0.50]$, proving spatial-autocorrelation variance inflation.

---

## 6. Step 5: Web Console Visual Tour & Demonstration Guide

Open a web browser and navigate to: `http://127.0.0.1:8000/`

### 5.1 Tab 1: Executive Overview & Operational Status
* **Demonstrate:** The high-visibility warning banner stating: *"RESEARCH DECISION-SUPPORT PLATFORM - NOT FOR EMERGENCY DISPATCH - SUPERVISED ML GATE BLOCKED"*.
* **Highlight:** The 1,170 km² domain overview, 21 active rain gauges, and summary KPI cards.

### 5.2 Tab 2: Domain & Grid Explorer
* **Demonstrate:** Interactive 1-km equal-area cells (EPSG:6933) overlaid on Bengaluru.
* **Click:** An individual grid cell to inspect its attributes (Cell ID, elevation, catchment basin).
* **Toggle Layers:** Turn on Ground Rain Gauges ($N=21$) and Flood Incident Pins ($N=17$).
* **Highlight:** The extreme clustering of flood events along the Outer Ring Road and Bellandur basin, contrasting with the vast unobserved grid ($98.29\%$).

### 5.3 Tab 3: Meteorological Skill & Forecast Verification
* **Demonstrate:** Scatter plot comparing NOAA GFS 0.25° forecasted precipitation vs IMD ground-gauge observations.
* **Highlight:** 
  1. The large negative bias ($-10.88\text{ mm}$), showing severe underestimation of convective storms.
  2. The categorical contingency table for the heavy rain threshold ($\ge 64.5\text{ mm/day}$), showing $0\text{ hits}$ and $23\text{ misses}$ ($\text{POD} = 0.00$).

### 5.4 Tab 4: Hydrological Engine & Terrain Analysis
* **Demonstrate:** SRTM 30m Digital Elevation Model with D8 single-flow direction vectors.
* **Toggle SAGA TWI:** Show the spatial transition from steep ridge divides ($\text{TWI} \approx 10.08$) to valley floors ($\text{TWI} \approx 19.04$).
* **Show Depression Sinks:** Point out the 19 identified physical depressions, emphasizing the deepest sink ($4.85\text{ m}$) holding up to $12\text{ km}^2$ upstream flow.
* **Explain AUC:** Show the HIPI susceptibility curve with $\text{ROC-AUC} = 0.560$, pointing out the Hanley-McNeil 95% CI $[0.303, 0.817]$ and explaining why macro-DEMs cannot resolve 2-meter roadside drainage walls.

### 5.5 Tab 5: SAR Satellite Remote Sensing & Physical Scattering
* **Demonstrate:** Pre-flood vs post-flood Sentinel-1 $\gamma^0$ radar backscatter imagery.
* **Highlight:** The physical scattering classification:
  * Open water specular decrease ($<-3\text{ dB}$) in only 5 of 13 cells ($38.5\%$).
  * Permanent lake surfaces accounting for 4 cells ($30.8\%$).
  * Urban double-bounce radar corner reflection ($+2.5\text{ dB}$) in 1 cell ($7.7\%$).
  * Radar shadow canyon obscuration in 3 cells ($23.1\%$).

### 5.6 Tab 6: Scientific Uncertainty & ML Governance
* **Demonstrate:** The Clustered Block Bootstrap chart comparing naive i.i.d. intervals against spatial-block resampled intervals.
* **Explain:** Why the correlation $r=0.142$ is statistically indistinguishable from zero once spatial auto-correlation is respected ($3.1\times$ to $4.2\times$ variance inflation).
* **Present the ML Gate Decision:** Review the formal multi-criteria checklist demonstrating why training a supervised machine learning model on $1.71\%$ observed data is mathematically and scientifically disqualified.

---

## 7. Step 6: Shutdown & Demonstration Wrap-Up

To conclude the demonstration cleanly:
1. In the server terminal, press `Ctrl+C` to terminate the HTTP server gracefully.
2. Direct the reviewer to the comprehensive documentation directory:
   * `reports/phase_7_final/FINAL_PROJECT_SUMMARY.md`
   * `reports/phase_7_final/FINAL_PRESENTATION_OUTLINE.md`
   * `reports/phase_7_final/FINAL_VIVA_MASTER_GUIDE.md`
   * `reports/phase_7_final/FINAL_ACCEPTANCE_DECISION.md`

