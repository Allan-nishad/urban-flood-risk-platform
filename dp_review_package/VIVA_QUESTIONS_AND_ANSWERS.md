# Technical Viva Questions & Accurate Answers (32 Q&As)

1. **What problem does this project solve?**  
   Conventional city-wide weather warnings lack neighbourhood terrain context. We combine 1 km² equal-area terrain/drainage indicators with live 72h weather forecasts to prioritise flood-prone zones in Bengaluru.
2. **Why did you choose Bengaluru Urban District?**  
   Bengaluru experiences frequent urban flash flooding (e.g., Aug–Sep 2022) driven by rapid urbanisation, lake-bed encroachment, and flat valley depressions, and has documented BBMP/KSNDMC records.
3. **Why a 1 km × 1 km grid instead of 100 m or 10 km?**  
   1 km balances computational speed (`1,170` cells) and data availability against 30m DEM / 10m land cover while avoiding false precision from 27.8 km weather models.
4. **Why use `EPSG:6933` instead of lat/lon degrees?**  
   Lat/lon degrees vary in area with latitude; `EPSG:6933` is an equal-area projection so every cell is ~`1 km²` (`geodesic_area_sqm`), enabling fair spatial comparisons and stable global IDs (`g1000_col_row`).
5. **Where does live weather data come from?**  
   Open-Meteo's `ecmwf_ifs025` model (`0.25°` ~27.8 km), queried across 5 Bengaluru sector anchors in one batched HTTPS request every 30 minutes (`LiveWeatherRefresher`).
6. **How is coarse 0.25° weather mapped to 1 km cells?**  
   Nearest-anchor assignment (`assign_cell_to_forecast_zone` within 25 km, `NEAREST_SECTOR_ANCHOR_NO_INTERPOLATION`). We deliberately do not fabricate sub-grid downscaling.
7. **Are live ground rain gauges connected?**  
   No. KSNDMC and IMD live portals lack open unauthenticated REST APIs; `/api/weather/current` honestly reports `UNAVAILABLE`.
8. **How is Static Susceptibility calculated?**  
   Equal blend (`0.50` terrain + `0.50` land cover) using normalized elevation (`60%`), elevation std (`40%`), built-up (`+0.75`), water (`+0.25`), and vegetation (`-0.20`).
9. **Were the MCDA weights learned by AI?**  
   No. They are manually selected domain weights (`dynamic_risk.py`).
10. **What is Dynamic Risk Prioritisation?**  
    `0.35 * Static + 0.30 * Observed_Baseline + 0.35 * Forecast_24h` (and `0.35 * terrain + 0.20 * drainage(TWI, UPA) + 0.15 * landcover + 0.30 * forecast_rain` in `risk_engine.py`).
11. **Does the risk score use historical flood labels?**  
    No. Flood labels are deliberately excluded from the risk formula to prevent circularity when evaluating against past floods.
12. **Is the risk score a probability of flooding?**  
    No. It is an uncalibrated relative screening/prioritisation index in `[0, 1]`.
13. **What is Topographic Wetness Index (TWI)?**  
    `TWI = ln(a / tan(beta))` from D8 flow routing; higher TWI means larger upstream drainage area `a` and flatter slope `beta`, indicating water accumulation potential.
14. **Which ML algorithms did you implement?**  
    Logistic Regression, Random Forest (selected), HistGradientBoosting, and XGBoost (`src/floodrisk/ml/train.py`).
15. **How does Random Forest work here?**  
    100 shallow decision trees (`max_depth=4`, `class_weight='balanced'`) trained on bootstrap samples of 48 labeled records; predictions are averaged across trees.
16. **Why only 48 training records?**  
    Only 34 verified flood records and 14 high-ground proxy-negative records exist across 2020–2025; `98.29%` of the domain is `UNOBSERVED`.
17. **What happens to `UNOBSERVED` cells in ML?**  
    They are excluded from training/testing (`prepare_ml_dataset`), never falsely labeled as `0` (dry).
18. **How did you prevent data leakage in ML?**  
    `FORBIDDEN_LEAKAGE_COLS` assertion blocks target/post-event columns (`sar_delta_vv_db`, `era5_rain_during_event_mm`), and ERA5-Land rainfall strictly precedes `event_start_utc`.
19. **Did you use GridSearchCV or RandomizedSearchCV?**  
    No. Hyperparameters were manually regularized (`max_depth=3..4`) due to the small sample size (`n=48`).
20. **What were the Random Forest evaluation results?**  
    5-fold spatial `GroupKFold`: `ROC-AUC = 0.8382`, `PR-AUC = 0.9232`, `F1 = 0.8696`, `Brier = 0.1425`, confusion matrix `TN=9, FP=5, FN=4, TP=30`. Temporal holdout (2023–2025): `0.3333` recall (`1/3`).
21. **Why is Temporal Recall (0.3333) much lower than Spatial ROC-AUC (0.8382)?**  
    Spatial CV evaluates on 2020–2022 where all 14 negative controls sit on high-ground stations in one episode, whereas 2023–2025 has only 3 positives and 0 negatives.
22. **Why is the ML model blocked from operational alerts?**  
    Because `n=48` with single-episode negative controls is insufficient for calibrated public warnings (`EXPERIMENTAL_UNVALIDATED`, `BLOCKED_EXPERIMENTAL_MODEL`).
23. **How reliable were historical NOAA GFS forecasts vs. rain gauges?**  
    Across `256` pairs (`16` gauges, Aug–Sep 2022): `Mean Bias = -10.88 mm`, `MAE = 18.64 mm`, `r = 0.142`, and `POD = 0.000` at `>= 64.5 mm`.
24. **Why do coarse NWP models underestimate peak urban rain?**  
    A `0.25°` cell averages rainfall over ~770 km², smoothing out intense localized convective cloudbursts.
25. **Why did Sentinel-1 SAR miss some urban floods?**  
    C-band radar had `5/13` (`38.5%`) true specular detection; dense high-rise street canyons, tree canopy, and permanent lake conflation obscure standing street water.
26. **How does the Alert Engine prevent alert fatigue and duplicates?**  
    One open alert per `grid_id` (updates in place on severity change), `120-minute` post-resolution cooldown, `12-hour` TTL expiration, and `5.5 km` spatial clustering (`clustering.py`).
27. **What happens if Open-Meteo goes down?**  
    `LiveWeatherRefresher` retries 3 times with exponential backoff, records the error in `provider_health` and `forecast_refresh_history`, marks freshness `STALE`/`UNAVAILABLE`, and `OperationalAlertEngine` skips generating new alerts.
28. **How is the SQLite database protected against concurrency and data loss?**  
    WAL mode (`PRAGMA journal_mode=WAL`), `busy_timeout=5000`, `threading.Lock()`, schema versioning (`user_version=2`), and online `sqlite3.Connection.backup()` with 10-snapshot retention.
29. **Why add a Demo Mode (`AUTOMATIC ALERT`)?**  
    To demonstrate the complete alert lifecycle, map highlighting, and civilian safety workflow reliably during viva/review even on dry days, strictly separated (`DEMO` badge) from real data.
30. **Does the Civilian Safety Page use Google Maps or SMS?**  
    No. It uses free **Leaflet + OpenStreetMap**, public **OSRM** for indicative routes (with offline fallback), and `tel:112` for SOS without tracking GPS or claiming rescue dispatch.
31. **What security controls exist for deployment?**  
    `FLOODRISK_ADMIN_TOKEN` with `hmac.compare_digest()`, fail-closed non-loopback check, restricted CORS, `X-Content-Type-Options`/`X-Frame-Options`, `SIGTERM` shutdown, and `AlertStore` column allowlist.
32. **What are the top future improvements?**  
    Integrating live KSNDMC/IMD rain-gauge APIs, expanding multi-year verified dry-control & flood-depth labels, sub-10m hydrodynamic drainage modeling, and reliability-weighted risk fusion.
