# Data Preprocessing Pipeline

## Stage-by-Stage Processing Sequence

| Stage | Input Data | Processing Operation | Reason | Output Data | Source File & Function |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Grid Generation** | Study area YAML (`configs/areas/bengaluru.yaml`) | Project bbox to `EPSG:6933`, generate 1,000 m equal-area squares, compute geodesic area | Ensure equal-area cells and permanent IDs | `grid_bengaluru_urban_1000m.{geojson,gpkg}` | `src/floodrisk/spatial/grid.py` (`generate_grid_for_study_area`) |
| **2. Validation & Quarantine** | Raw CSV, GeoTIFF, Vector files | Schema checks, CRS checks, physical range checks, quarantine bad rows | Prevent corrupt/out-of-bounds/leaked data | Validated data + quarantine CSV | `src/floodrisk/validate.py` (`validate_csv`, `validate_raster`, `validate_vector`) |
| **3. Static Zonal Extraction** | SRTM 30m DEM, WorldCover 10m | Reproject/aggregate pixel stats per 1 km cell | Summarise terrain & land cover per cell | `features_static_bengaluru.parquet` | `src/floodrisk/processing/zonal.py` |
| **4. D8 Hydrology** | SRTM DEM | D8 flow direction, accumulation, `TWI = ln(a/tan b)`, sink detection | Capture drainage convergence & depressions | `topographic_routing_static_features.parquet` | `src/floodrisk/processing/hydrology.py` |
| **5. Rainfall & API** | Rainfall time series | Unit conversion, rolling 3d/7d/14d sums, 7d exponential API decay | Represent antecedent soil moisture | `features_rainfall_bengaluru.parquet` | `src/floodrisk/processing/rainfall.py` |
| **6. Dynamic Risk Matrix** | Static + Forecast + Incidents | Min-max normalization, weighted MCDA, incident join (non-circular) | Rank cells without circularity | `dynamic_risk_intelligence_bengaluru.parquet` | `src/floodrisk/processing/dynamic_risk.py` (`compute_dynamic_risk_intelligence`) |
| **7. Live Weather Ingestion** | Open-Meteo JSON (5 anchors) | Coordinate/unit/ISO-UTC validation, `1h–72h` window sums, SQLite WAL upsert | Persistent live 72h forecasts & refresh log | `weather_records`, `forecast_refresh_history` | `src/floodrisk/live/open_meteo.py`, `scheduler.py`, `storage.py`, `forecast_metrics.py` |
| **8. ML Feature Prep** | `flood_event_grid_dataset.parquet` | Filter labeled rows (`{0,1}`), map `EVENT_GROUP_MAP`, add `era5_pre_missing_flag`, block leakage cols | Prevent spatial/temporal leakage | `X`, `y`, `meta` | `src/floodrisk/ml/features.py` (`prepare_ml_dataset`) |

## Key Engineering Controls
- **Missing Values:** Live forecasts flag `quality_status = "UNAVAILABLE"` and track `missing_hours`; ML uses `SimpleImputer(strategy="median")` + `era5_pre_missing_flag`.
- **Duplicate Prevention:** `drop_duplicates()` in static/ML prep; SQLite `UNIQUE INDEX idx_weather_unique` with `ON CONFLICT DO UPDATE`.
- **Integrity:** SHA-256 verification via `DatasetManifest` (`src/floodrisk/provenance.py`).

## Real Before-and-After Example (`g1000_7489_1650`)
- **Before (Raw/Static Input):** `elevation_mean_m = 881.94 m`, `elevation_std_m = 1.9 m`, `built_up_fraction = 0.8582`, `tree_cover_fraction = 0.0476`, `cropland_fraction = 0.0454`, `water_fraction = 0.0`.
- **After (Processed Feature & Risk Output):** `baseline_terrain_susceptibility = 0.5894`, `baseline_landcover_runoff = 0.8747`, `static_susceptibility_score = 0.7321` (Rank `#12`), `dynamic_risk_prioritization_score = 0.3342` (`RESEARCH_PRIORITY_LOW`), `has_ground_flood_evidence = True`.
