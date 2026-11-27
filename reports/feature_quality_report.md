# Grid-Level Feature Quality & Physical Sanity Audit (Phase 2B Update)

**Audit Date:** 2026-11-05  
**Evaluated Datasets:**
- `data/processed/features_static_bengaluru.parquet` (1,170 rows, 31 columns)
- `data/processed/features_rainfall_bengaluru.parquet` (19,890 rows, 18 columns)
- `data/processed/features_integrated_bengaluru.parquet` (19,890 rows, 53 columns)
- `data/processed/exploratory_risk_indicators_bengaluru.parquet` (19,890 rows, 62 columns)
**Execution Runtime:** Python 3.11.15 (`.venv`)  

---

## 1. Feature Statistical Moments & Quality Matrix

| Feature Name | Primary Source | Records | Valid (%) | Nulls (%) | Min | 25th % | Median | Mean | 75th % | Max | Std Dev |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `elevation_mean_m` | SRTM GL1 30m | 1,170 | 100.0% | 0.0% | 755.54 | 873.93 | 893.07 | 885.54 | 907.61 | 944.55 | 34.29 |
| `elevation_min_m` | SRTM GL1 30m | 1,170 | 100.0% | 0.0% | 738.00 | 860.00 | 879.00 | 870.33 | 893.00 | 931.00 | 35.33 |
| `elevation_max_m` | SRTM GL1 30m | 1,170 | 100.0% | 0.0% | 774.00 | 889.00 | 909.00 | 902.18 | 924.00 | 961.00 | 32.94 |
| `elevation_std_m` | SRTM GL1 30m | 1,170 | 100.0% | 0.0% | 1.50 | 5.19 | 6.09 | 6.60 | 7.32 | 18.62 | 2.33 |
| `built_up_fraction` | ESA WorldCover 10m | 1,170 | 100.0% | 0.0% | 0.0000 | 0.1507 | 0.4356 | 0.4429 | 0.7205 | 0.9904 | 0.3013 |
| `water_fraction` | ESA WorldCover 10m | 1,170 | 100.0% | 0.0% | 0.0000 | 0.0000 | 0.0000 | 0.0091 | 0.0027 | 0.4833 | 0.0354 |
| `tree_cover_fraction` | ESA WorldCover 10m | 1,170 | 100.0% | 0.0% | 0.0002 | 0.0879 | 0.1494 | 0.1812 | 0.2456 | 0.8373 | 0.1270 |
| `cropland_fraction` | ESA WorldCover 10m | 1,170 | 100.0% | 0.0% | 0.0000 | 0.0270 | 0.1382 | 0.2161 | 0.3649 | 0.9111 | 0.2180 |
| `grassland_fraction`| ESA WorldCover 10m | 1,170 | 100.0% | 0.0% | 0.0000 | 0.0093 | 0.0278 | 0.0412 | 0.0567 | 0.4062 | 0.0458 |
| `shrubland_fraction`| ESA WorldCover 10m | 1,170 | 100.0% | 0.0% | 0.0000 | 0.0135 | 0.0628 | 0.0965 | 0.1312 | 0.9165 | 0.1180 |
| `upa_mean_sqkm` | MERIT Hydro 90m | 1,170 | **0.0%** | **100.0%**| — | — | — | **NaN** | — | — | — |
| `rainfall_daily_depth_mm` | GPM IMERG V07B | 19,890 | 100.0% | 0.0% | 2.55 | 12.07 | 16.39 | 28.19 | 23.29 | 150.92 | 32.32 |
| `precip_antecedent_3d_mm` | GPM IMERG V07B | 19,890 | 100.0% | 0.0% | 21.93 | 41.35 | 50.82 | 86.47 | 120.34 | 254.59 | 62.62 |
| `precip_antecedent_7d_mm` | GPM IMERG V07B | 19,890 | 100.0% | 0.0% | 35.79 | 84.49 | 179.35 | 177.79 | 255.13 | 397.02 | 92.91 |
| `precip_api_decay_mm` | GPM IMERG V07B | 19,890 | 100.0% | 0.0% | 26.19 | 54.75 | 115.53 | 117.40 | 160.77 | 273.48 | 63.76 |
| `indicator_terrain` | Phase 2B.3 Engine | 19,890 | 100.0% | 0.0% | 0.1940 | 0.3981 | 0.4561 | 0.4681 | 0.5184 | 0.8827 | 0.1081 |
| `indicator_landcover`| Phase 2B.3 Engine | 19,890 | 100.0% | 0.0% | 0.0000 | 0.2021 | 0.4761 | 0.4750 | 0.7368 | 1.0000 | 0.2875 |
| `indicator_rainfall` | Phase 2B.3 Engine | 19,890 | 100.0% | 0.0% | 0.0914 | 0.1692 | 0.2924 | 0.3142 | 0.4088 | 0.8583 | 0.1628 |
| `composite_risk_runoff_dominant` | Phase 2B.3 Engine | 19,890 | 100.0% | 0.0% | 0.1167 | 0.3069 | 0.4064 | 0.4093 | 0.5062 | 0.8290 | 0.1282 |

---

## 2. Physical Consistency & Quality Assessment

1. **Elevation Strict Ordering:**
   `elevation_min_m <= elevation_mean_m <= elevation_max_m` is strictly satisfied for 1,170 / 1,170 cells (100.0%).
2. **Land Cover Boundedness & Sum Constraints:**
   All individual land cover fractions lie strictly in $[0.0, 1.0]$. The sum of all land cover classes across any single cell never exceeds $1.0000$.
3. **No-Data Transparency:**
   MERIT Hydro UPA features are explicitly preserved as `NaN` (0.0% valid) rather than filled with arbitrary zeros. Zero upstream area would imply every cell is a ridge crest.
4. **Leakage & Unit Guarantees:**
   - Precipitation is strictly in `mm` (depth), not `mm/hr` (rate).
   - Antecedent precipitation metrics use strictly past lookbacks ($t - k$ to $t - 1$), preventing forward-looking temporal leakage.
   - Sentinel-1 SAR is completely excluded from the observational feature tables (`sar_observational_status="excluded_from_real_matrix"`).
