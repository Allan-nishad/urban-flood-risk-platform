# Phase 7F — Operational User Guide: Urban Flood Risk Intelligence Platform

**Document Identifier:** `reports/phase_7/phase_7F_user_guide.md`  
**System URL:** `http://127.0.0.1:8501/` (Local Operational Web Dashboard)  
**Target Audience:** Researchers, Municipal Engineers, Disaster Analysts, and Examiners  
**Status:** **`USER_DOCUMENTATION`**  

---

## 1. Launching the Surveillance Console

### Prerequisites
- Python 3.11 with activated virtual environment (`.venv`).
- Required dependencies installed: `pip install -r requirements.txt`.

### Execution Command
Launch the operational dashboard server from repository root:
```powershell
.venv\Scripts\python -m floodrisk.dashboard.server
```
Terminal output confirms:
```
[Dashboard Server] Operational console running at http://127.0.0.1:8501/
[Dashboard Server] Serving endpoints: /api/summary, /api/cells, /api/incidents, /api/episodes, /api/manifest
```
Open a browser and navigate to: `http://127.0.0.1:8501/` (or `http://localhost:8501/`).

---

## 2. Navigating the Interactive Interface

The console is structured into four main operational tabs:
1. **Surveillance Console (Default View):**
   - Interactive Leaflet map displaying the 1,170 equal-area 1-km cells.
   - Dynamic layer toggle: Switch between Static Flood Susceptibility, 24h GFS Forecast Rainfall, and HIPI Inundation Potential.
   - Cell inspection: Click on any 1-km cell to view its centroid coordinates, elevation, slope, built-up fraction, TWI, and nearest GFS node.
2. **Phase 6 Authentic Intelligence Tab:**
   - Workstream summary cards (6A through 6F).
   - Ground rain-gauge registry: View 21 stations with real-time paired validation metrics.
   - Ground truth matrix: Interactive table of the 13 verified positive cells, 7 monitored negative cells, and 1,150 unobserved cells.
   - Sentinel-1 SAR cross-validation table.
   - Master Manifest Inspector: Live search and SHA-256 inspection of registered datasets.
3. **Phase 7 Research & Uncertainty Tab:**
   - Clustered bootstrap uncertainty results comparing naive i.i.d. vs date-clustered 95% confidence intervals.
   - Heavy rainfall scale mismatch contingency curves.
   - Terrain depression sensitivity comparisons (Representation A vs B).
4. **Data Manifest & Integrity Tab:**
   - Live view of all 68 cryptographic manifest entries.
   - Status indicators verifying that 0 files have been modified or corrupted.

---

## 3. Querying the REST API Directly

You can query the underlying REST API using `curl` or any HTTP client:
```powershell
# Check health
curl http://127.0.0.1:8501/api/health

# Get platform summary
curl http://127.0.0.1:8501/api/summary

# Get Phase 7 research summary
curl http://127.0.0.1:8501/api/phase7/summary

# Get Phase 7 grouped uncertainty statistics
curl http://127.0.0.1:8501/api/phase7/uncertainty
```
All API responses return strict, clean JSON with zero `NaN` values.

