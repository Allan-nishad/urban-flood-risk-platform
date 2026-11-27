# Phase 4.1 — Sentinel-1A Synthetic Fixture Audit & Authentic SAR Protocol

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban (1,170 Cells, 1-km Grid)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Reporting Date:** 2026-11-05  
**SAR Status:** **`SYNTHETIC_TEST_ONLY` (Simulation Fixtures Quarantined; Observational SAR Pending Authentic Processing)**  

---

## 1. Executive Summary & Audit Re-Affirmation

In strict adherence to Non-Negotiable Rule 8 (Never treat synthetic Sentinel-1 rasters as actual satellite observations), this report re-affirms the findings of the **Phase 2A.5.1 Independent Scientific SAR Validation Audit**:
- **Existing SAR Rasters:** Files located in `data/raw/weather/sentinel1/` (`S1A_IW_GRDH_20220812_VV_bengaluru.tif` and `S1A_IW_GRDH_20220905_VV_bengaluru.tif`) were generated as synthetic spatial fixtures to verify software pipeline syntax, raster slicing, and GeoTIFF export logic.
- **Audit Verdict:** Classified as **Decision C (Simulation Fixture Only)**. The rasters do **not represent calibrated backscatter observations from the European Space Agency Sentinel-1 constellation**.
- **Quarantine Enforcement:** These files are strictly quarantined within test fixtures. They are **100% excluded from model predictor matrices, exploratory risk scores, and dashboard observational layers**.

---

## 2. Requirements of an Authentic Sentinel-1 Level-1 Processing Chain

To produce genuine satellite radar observations of urban flooding, raw Sentinel-1 Level-1 Ground Range Detected (GRD) SAFE packages must be processed through an authentic SAR chain (e.g. via ESA SNAP, pyroSAR, or GAMMA):

```
┌────────────────────────────────────────────────────────────────────────┐
│             MANDATORY SENTINEL-1 LEVEL-1 SAR PROCESSING CHAIN          │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Orbit State Vectors: Apply Precise Orbit Ephemerides (.EOF)         │
│ 2. Thermal Noise Removal: Subtract instrument thermal noise vector     │
│ 3. Border Noise Removal: Mask false low-intensity antenna edge values │
│ 4. Radiometric Calibration: Convert digital numbers to sigma-nought σ⁰ │
│ 5. Range-Doppler Terrain Correction: Orthorectify with SRTM 30m DEM    │
│ 6. Speckle Filtering: Refined Lee filter (7x7 window)                  │
│ 7. Decibel Conversion: γ_dB = 10 * log10(σ⁰)                          │
│ 8. Urban Double-Bounce & Water Masking: Thresholding & change detection│
└────────────────────────────────────────────────────────────────────────┘
```

### Urban SAR Complications:
In dense urban terrain (such as Bengaluru's IT corridors), radar backscatter behaves in complex ways:
- **Specular Reflection:** Open surface water reflects radar pulses away from the sensor, producing very low backscatter ($< -18\text{ dB}$).
- **Double-Bounce Scattering:** When standing water accumulates at the base of vertical buildings, radar pulses bounce from the water to the wall and back to the satellite, creating an **increase in backscatter (+3 to +6 dB)** rather than a decrease.
- **Layover & Shadow:** Tall high-rise structures obscure ground streets, creating false radar shadows that mimic open water.

---

## 3. Manual Unblocking Instructions for Authentic SAR SAFE Ingestion

To acquire authentic Copernicus Sentinel-1A Level-1 SAFE products:
1. Register a free account at the **Copernicus Data Space Ecosystem (CDSE)**:
   `https://dataspace.copernicus.eu/`
2. Search for Interferometric Wide (IW) Ground Range Detected High-Resolution (GRDH) products covering Bengaluru:
   - **Pre-Event Scene:** `S1A_IW_GRDH_1SDV_20220812T...` (Relative Orbit 165, Descending Pass)
   - **Post-Event Scene:** `S1A_IW_GRDH_1SDV_20220905T...` (Relative Orbit 165, Descending Pass)
3. Download the uncompressed `.SAFE` archives into `data/raw/weather/sentinel1/safe/`.
4. Run the automated SNAP/pyroSAR batch pipeline via `bash scripts/process_sentinel1_snap.sh` to generate calibrated GeoTIFFs with precise orbit vectors and Range-Doppler terrain correction.
5. Ingest calibrated backscatter rasters into `reports/dataset_manifest.json`.

