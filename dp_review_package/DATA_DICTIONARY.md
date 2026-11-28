# Data Dictionary — 100-Row Review Sample Datasets

The 5 CSV files in `dp_review_package/` contain **100% real records** extracted directly from the processed datasets without synthetic modification:
- **`01_raw_sample_100.csv` through `04_risk_output_sample_100.csv`** share the **exact same 100 `grid_id` values** (including all 20 verified Phase 6 ground-truth cells plus 80 stratified cells across risk tiers).
- **`05_ml_evaluation_sample_100.csv`** has **event × grid** granularity (`data/phase8/flood_event_grid_dataset.parquet`), containing all **48 labeled event-grid records** (34 positive, 14 proxy-negative) plus **52 `UNOBSERVED` records** from the same sample grid cells.

## Key Columns Across Sample Files

| Column | Unit | Source | Purpose |
| :--- | :--- | :--- | :--- |
| `grid_id` | text (`g1000_col_row`) | EPSG:6933 Grid | Persistent 1 km² cell identifier |
| `col_idx`, `row_idx` | integer | EPSG:6933 Grid | Global equal-area grid indices |
| `centroid_lon`, `centroid_lat` | degrees (WGS84) | EPSG:6933 → 4326 | Cell center coordinates |
| `centroid_x_6933`, `centroid_y_6933` | metres | EPSG:6933 | Equal-area projected center coordinates |
| `geodesic_area_sqm` | m² | WGS84 Ellipsoid | True geodesic cell area (~1,000,000 m²) |
| `elevation_mean_m`, `elevation_std_m` | metres | SRTM GL1 30m DEM | Mean elevation and terrain roughness |
| `slope_deg`, `topographic_wetness_index`, `upstream_contributing_area_km2` | deg / dimless / km² | D8 Hydrology (Phase 6E) | Slope, wetness index `ln(a/tan b)`, drainage area |
| `built_up_fraction`, `tree_cover_fraction`, `cropland_fraction`, `water_fraction` | fraction `[0, 1]` | ESA WorldCover 10m | Land-cover proportions per cell |
| `baseline_terrain_susceptibility`, `baseline_landcover_runoff`, `static_susceptibility_score` | index `[0, 1]` | `dynamic_risk.py` | Normalized static physical susceptibility & domain rank |
| `observed_rainfall_24h_mm`, `observed_api_decay_mm`, `observed_rainfall_exposure_score` | mm / index `[0, 1]` | Phase 4.3 Baseline (`STALE`) | Historical antecedent rainfall baseline |
| `forecast_issue_time`, `forecast_rainfall_{3h,6h,24h,72h}_mm`, `forecast_peak_hourly_intensity_mm` | UTC / mm / mm/h | Forecast Exposure Parquet | Forecast rainfall accumulations & peak rate |
| `forecast_exposure_score_24h`, `forecast_intensity_category` | `[0, 1]` / category | Forecast Exposure | Normalized 24h forecast score & rain category |
| `has_ground_flood_evidence`, `historical_incident_count`, `historical_incident_categories` | bool / count / text | Flood Inventory | Historical incident presence (excluded from risk math) |
| `dynamic_risk_prioritization_score`, `dynamic_risk_rank`, `research_monitoring_level` | `[0, 1]` / rank / tier | `dynamic_risk.py` | Exploratory screening index (not a probability) |
| `observation_status` | category | Phase 6C Matrix | `VERIFIED_POSITIVE`, `VERIFIED_NEGATIVE`, or `UNOBSERVED_DOMAIN_CELL` |
| `event_id`, `event_timestamp_utc` | text / UTC | Phase 8 Event-Grid | Flood episode ID & timestamp (File 05) |
| `era5_rain_24h_pre_mm`, `era5_rain_72h_pre_mm`, `era5_api_7d_pre_mm`, `era5_pre_missing_flag` | mm / binary | Open-Meteo ERA5-Land | Pre-event rainfall predictors (`< event_start_utc`) |
| `flood_label`, `evidence_status`, `label_source`, `label_confidence` | `0/1/NaN` / text | Phase 8 Event-Grid | ML target label & provenance |
| `experimental_ml_score`, `ml_qualification_status`, `evaluation_partition` | `[0, 1]` / status / text | `ExperimentalFloodInference` | Random Forest score (`EXPERIMENTAL_UNVALIDATED`) & CV/holdout partition |
