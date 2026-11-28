# Live Prototype Demonstration Script (5–7 Minutes)

## Step 1: Overview & Live Weather (1 min)
- **Open:** `http://127.0.0.1:8501/`
- **Highlight:** Header (`Live Data Connected`), Live Weather Status Bar (`open_meteo`, `ecmwf_ifs025`, `LIVE/RECENT`), and KPI cards (`1,170 km²`, `21 Events`, `6 Episodes`).
- **Say:** *"Our platform divides Bengaluru into 1,170 equal-area 1 km² cells and continuously ingests live 72-hour ECMWF IFS forecasts via Open-Meteo into a SQLite WAL database."*

## Step 2: Trace Real Cell `g1000_7489_1650` (1.5 min)
- **Action:** Click cell `g1000_7489_1650` (or top-ranked cell) on the map; switch layer buttons (`Static Susceptibility` → `Dynamic Priority` → `Historical Incidents`); click `72h Timeline` tab in the right panel.
- **Highlight:** `Static Score = 0.7321` (Rank `#12`, `elevation = 881.9 m`, `built-up = 85.8%`, `TWI`), `Dynamic Score = 0.3342`, `has_ground_flood_evidence = True`, and the `1h–72h` live risk timeline.
- **Say:** *"This cell has high static susceptibility (0.73) due to 85.8% built-up area and recorded past waterlogging. Because today's live forecast rain is light, its dynamic priority stays low (0.33). Historical flood labels are excluded from the risk formula to prevent circularity."*

## Step 3: Validation, Gauges, SAR & Experimental ML (1.5 min)
- **Action:** Click bottom tabs **Multi-Source Intelligence** (`phase6Tab`) and **Scientific Validation** (`phase5Tab`).
- **Highlight:** `21` rain-gauge stations (`16` primary gauges, `256` pairs, `MAE = 18.64 mm`), Sentinel-1 SAR `5/13 True Specular (38.5%)`, D8 Hydrology sinks, and `Random Forest (Research Mode)` (`48` records, Spatial CV `ROC-AUC = 0.8382`, `PR-AUC = 0.9232`).
- **Say:** *"We benchmarked coarse 0.25° NWP against 16 real rain gauges, audited Sentinel-1 SAR against urban-canyon limitations, and trained an experimental Random Forest strictly as supporting research context."*

## Step 4: Automatic Alert & Civilian Safety Page (2 min)
- **Action:** Click **AUTOMATIC ALERT** (red button in header) → keep **East Bengaluru** and **50 mm/hour — Severe** → click **Trigger Demo Alert**.
- **Highlight:** Floating **Danger Popup** (`DEMONSTRATION ALERT — SIMULATED DATA`), red East Bengaluru zone highlight + green destinations on the map, `Active Alerts: 1`, and `DEMO` row in Unified Alert History.
- **Action:** Click **VIEW CIVILIAN ALERT** → opens `/civilian-alert.html` in a new tab. Show OSRM indicative route to `Cubbon Park High Ground`, **Copy Alert Link**, and **SOS — Call 112** confirmation modal. Return and click **Reset Demo**.
- **Say:** *"Even when Bengaluru is dry, our clearly labelled Demo Mode lets authorities test end-to-end alerting and citizen-facing indicative routing without faking real weather data."*

## Expected Evaluator Q&A
- **Q:** *Why not use ML to trigger public emergency sirens?*  
  **A:** *Because only 48 labeled records exist (1.71% of cells observed); `98.29%` of the domain is unobserved, so ML remains `EXPERIMENTAL_UNVALIDATED` and `public_dispatch_enabled = false`.*
