# Phase 4.7.6 — Scientific Audit: Sentinel-1 SAR Quarantine & UI Segregation

**Platform:** Bengaluru Urban Flood Risk Intelligence Platform  
**Component:** Sentinel-1 SAR Processing Subsystem ([`src/floodrisk/processing/sar.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/sar.py))  
**Audited Datasets & Rasters:**
- [`data/processed/sentinel1_candidate_flood_change_mask_bengaluru.tif`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/sentinel1_candidate_flood_change_mask_bengaluru.tif)
- [`data/processed/sentinel1_grid_features_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/sentinel1_grid_features_bengaluru.parquet)
- [`data/processed/sentinel1_incident_comparison_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/sentinel1_incident_comparison_bengaluru.parquet)  
**Audit Classification:** **VERIFIED (Complete Quarantine Maintained & UI Segregated)**

---

## 1. Audit Context & Scientific Objective

In Phase 2A.5, synthetic Sentinel-1A SAR rasters were generated as engineering fixtures to construct the log-ratio differencing and Otsu thresholding pipeline when Copernicus Data Space Ecosystem (CDSE) downloads were gated by OAuth2 authentication tokens.

The scientific objective of this audit is to confirm:
1. That all simulated SAR rasters and derived tables remain strictly quarantined from operational feature matrices and machine learning inputs.
2. That synthetic SAR footprints do not appear on the operational dashboard as satellite observations.
3. That engineering fixtures cannot be visually or analytically confused with authentic observational evidence.

---

## 2. Code, Model & Pipeline Quarantine Audit

A repository-wide audit was conducted across all feature tables and training pipelines:

| Subsystem / Dataset | Inspection Target | Audit Finding & Verification Evidence | Quarantine Status |
| :--- | :--- | :--- | :---: |
| **Phase 2B Integration** | `features_integrated_bengaluru.parquet` | Audited columns. Zero SAR backscatter or change features present. | **VERIFIED CLEAN** |
| **Phase 3 Modeling** | `phase3_model_features.parquet` | Inspected 8 predictor columns. Features restricted entirely to SRTM terrain, WorldCover land cover, and IMERG rainfall. | **VERIFIED CLEAN** |
| **Phase 4 Dynamic Engine** | `dynamic_risk_intelligence_bengaluru.parquet` | Audited 33 schema columns. Zero SAR candidate flood pixels incorporated into risk formulas. | **VERIFIED CLEAN** |
| **Dataset Manifest** | `reports/dataset_manifest.json` | Re-verified provenance metadata. All 5 SAR deliverables tagged explicitly with `validation_status: "SYNTHETIC_TEST_ONLY_QUARANTINED"`. | **VERIFIED CLEAN** |

```python
# Verification from test_spatial_validation.py (Target Leakage Check)
def test_sar_fixture_leakage_check():
    df_features = pd.read_parquet("data/processed/phase3_model_features.parquet")
    sar_cols = [c for c in df_features.columns if "sar" in c.lower() or "backscatter" in c.lower()]
    assert len(sar_cols) == 0, f"Found quarantined SAR columns in model features: {sar_cols}"
```

---

## 3. Web Dashboard Audit & Operational Map Correction

### 3.1 Finding from Phase 4.5 Console:
In the initial Phase 4.5 web console, the main operational layer switcher included a button:
`<button class="layer-btn" data-layer="quarantine">SAR Extent</button>`.

Although the legend stated "Quarantined SAR Fixture", displaying the purple boundary alongside real operational layers (Dynamic Priority, Static Susceptibility, NWP Forecast) created an unacceptable visual risk that end-users might interpret the boundary as an authentic Copernicus satellite detection footprint.

### 3.2 Corrective Action Implemented:
1. **Removed from Operational Map Controls:**  
   The `SAR Extent` button was completely deleted from the primary map toolbar in [`src/floodrisk/dashboard/static/index.html`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/dashboard/static/index.html). The operational map displays only authentic observational and forecast layers.
2. **Relocated to Dedicated Development Drawer:**  
   A separate tab titled `Testing & Dev Fixtures (Quarantined SAR)` was added to the bottom analytics card.
3. **Mandatory Prominent Warning:**  
   The development view embeds a high-visibility warning banner:
   ```html
   <div style="background:#fef2f2; border-left:4px solid #dc2626; padding:12px 16px;">
     <strong>SYNTHETIC TEST DATA — NOT SATELLITE OBSERVATION</strong>
     <p>The Sentinel-1 SAR change footprints generated in Phase 2A.5 are simulated synthetic engineering fixtures used exclusively for pipeline plumbing and unit testing. They are strictly quarantined and permanently excluded from all observational flood risk matrices.</p>
   </div>
   ```
4. **Explicit Manual Toggle:**  
   The synthetic overlay is hidden by default and can only be activated by explicitly clicking an engineering toggle inside the development drawer.

