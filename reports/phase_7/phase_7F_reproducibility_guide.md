# Phase 7F — End-to-End Reproducibility Guide

**Document Identifier:** `reports/phase_7/phase_7F_reproducibility_guide.md`  
**Target Audience:** Independent Evaluators, Reviewers, and Auditors  
**Status:** **`AUDIT_VERIFIED`**  

---

## 1. System Setup & Environment Recreation

To reproduce all results from scratch in a clean environment:

```powershell
# 1. Clone repository and navigate to workspace
git clone <repo_url> urban-flood-risk-platform
cd urban-flood-risk-platform

# 2. Create Python 3.11 virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install pinned dependencies
pip install -r requirements.txt
```

---

## 2. Step-by-Step Pipeline Execution Sequence

Execute the Phase 6 and Phase 7 processing pipelines in exact chronological order:

### Step 1: Pre-Flight Baseline Manifest Audit
```powershell
.venv\Scripts\python scratch/audit_g_manifests.py
```
*Expected Result:* All 52 historical baseline datasets and 16 Phase 6 datasets verified bit-for-bit (0 mismatches).

### Step 2: NWP Ingestion & GRIB2 Decoding (Stage 6A)
```powershell
.venv\Scripts\python scripts/phase6/acquire_nwp.py
```
*Expected Result:* Downloads 170 GFS slices from AWS Open Data, decodes 340 WMO messages, generates `nwp_forecast_archive.parquet` (198,900 rows).

### Step 3: Ground Rain Gauge Ingestion & Paired Verification (Stage 6B)
```powershell
.venv\Scripts\python scripts/phase6/build_ground_rainfall.py
```
*Expected Result:* Ingests 21 stations, evaluates 256 paired samples, generates $\text{MAE} = 18.64\text{ mm}$, $\text{POD} = 0.00$ at $\ge 64.5\text{ mm}$.

### Step 4: Independent Flood Evidence & Ground Truth Matrix (Stage 6C)
```powershell
.venv\Scripts\python scripts/phase6/build_flood_evidence.py
```
*Expected Result:* Compiles 24 incidents, generates 1,170-cell matrix (13 pos, 7 neg, 1,150 unobserved), enforces Supervised ML Gate `BLOCKED_BY_INSUFFICIENT_EVIDENCE`.

### Step 5: Sentinel-1 SAR Backscatter & Regime Classification (Stage 6D)
```powershell
.venv\Scripts\python scripts/phase6/process_sar.py
```
*Expected Result:* Catalogs 3 CDSE scenes, classifies physical regimes, evaluates cross-validation table.

### Step 6: Deterministic Terrain Hydrology & Depression Routing (Stage 6E)
```powershell
.venv\Scripts\python scripts/phase6/build_hydrology.py
```
*Expected Result:* Implements D8 routing, fills 19 sinks, calculates TWI ($10.08 - 19.04$), generates HIPI index ($\text{ROC-AUC} = 0.560$).

### Step 7: Phase 7 Final Data Freeze & Sandbox Audit (Stage 7A)
```powershell
.venv\Scripts\python scripts/phase7/audit_7a_freeze.py
```
*Expected Result:* Validates all 68 datasets, reproduces D8 routing in sandbox bit-for-bit ($0.000000$ difference).

### Step 8: Final Forecast Verification & Grouped Uncertainty (Stage 7B)
```powershell
.venv\Scripts\python scripts/phase7/verify_forecasts.py
.venv\Scripts\python scripts/phase7/grouped_uncertainty.py
```
*Expected Result:* Runs 2,000 bootstrap iterations, computes date-clustered CIs, demonstrates $3.1\times$ to $4.2\times$ uncertainty inflation.

### Step 9: Flood Evidence Audit & SAR Ambiguity Deconstruction (Stage 7C)
```powershell
.venv\Scripts\python scripts/phase7/audit_flood_evidence.py
.venv\Scripts\python scripts/phase7/compare_sar_evidence.py
```
*Expected Result:* Deconstructs sensitivity into 5 true specular flood ($38.5\%$), 4 permanent lakes ($30.8\%$), 1 double-bounce ($7.7\%$), 3 missed ($23.1\%$).

### Step 10: Terrain Depression Sensitivity & Hanley-McNeil AUC Analysis (Stage 7D)
```powershell
.venv\Scripts\python scripts/phase7/depression_sensitivity.py
```
*Expected Result:* Compares unconditioned vs conditioned terrain, proves AUC 95% CI $[0.385, 0.890]$ spans $0.500$.

---

## 3. Running Automated Verification Test Suite

Run the full pytest suite:
```powershell
.venv\Scripts\python -m pytest
```
*Expected Result:* **109 passed / 109 total tests across 16 test files (100% pass rate)**.

