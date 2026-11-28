# Prototype Page & Navigation Guide

The prototype serves **two HTML pages** from `src/floodrisk/dashboard/server.py`:
1. **Authority Dashboard:** `/` (or `/index.html`)
2. **Civilian Safety Page:** `/civilian-alert.html`

---

## 1. Authority Dashboard (`/`)

| UI Component / Tab | Exact Selector / Navigation | Purpose & Data Displayed | Backend APIs Used |
| :--- | :--- | :--- | :--- |
| **Top Header & Live Status** | `#headerStatusText`, `#autoAlertBtn` | Live connection pulse + **AUTOMATIC ALERT** trigger button | `/api/summary`, `/api/health` |
| **Live Weather Status Bar** | `#liveFcstProvider`, `#liveFcstModel`, `#liveObsStatus` | Open-Meteo `ecmwf_ifs025` freshness, 24h rain, gauge status (`UNAVAILABLE`), source health | `/api/weather/forecast`, `/api/weather/current`, `/api/sources` |
| **KPI Row** | `#kpiTotalCells` .. `#kpiEpisodes` | `1,170 km²` scope, heavy rain cells, peak 24h rain, high-priority cells, `21` incidents, `6` episodes | `/api/summary`, `/api/cells` |
| **Flood Alert Center** | `#floodAlertCenter`, `#zoneCardsGrid`, `#unifiedAlertHistoryTbody` | 4 Bengaluru zone cards (North/South/East/West), unified `REAL DATA` + `DEMO` history, `VIEW CIVILIAN ALERT`, `Reset Demo` | `/api/weather/forecast`, `/api/risk/forecast`, `/api/alerts` |
| **Interactive Grid Map** | `#map`, `button[data-layer]` | 1,170-cell Leaflet + OSM map; switch layers: `Dynamic Priority`, `Static Susceptibility`, `Forecast 24h`, `Observed Monsoonal`, `Historical Incidents` | `/api/cells`, `/api/incidents` |
| **Cell Inspector (Right Panel)** | `button[data-tab="inspectorTab"]`, `forecastTab`, `incidentsTab` | Click any cell to inspect elevation, built-up, static score, TWI, UPA, 1h–72h live risk timeline, and past incidents | `/api/cells`, `/api/risk/forecast?grid_id=...`, `/api/incidents` |
| **Rainfall Episodes Tab** | `button[data-bottom-tab="episodesTableTab"]` | 6 historical & monitored Bengaluru rainfall episodes | `/api/episodes` |
| **Data Manifest Tab** | `button[data-bottom-tab="manifestTableTab"]` | SHA-256 dataset integrity verification | `/api/manifest` |
| **Development Fixtures Tab** | `button[data-bottom-tab="devSarTab"]` | Quarantined Phase 2A.5 synthetic SAR fixtures | Static quarantined table |
| **Scientific Validation Tab** | `button[data-bottom-tab="phase5Tab"]` | Forecast benchmark, 7-class flood taxonomy (1,170 cells), indicator ROC/PR-AUC, Sentinel-1A manifest | `/api/phase5/*` |
| **Multi-Source Intelligence Tab** | `button[data-bottom-tab="phase6Tab"]` | Phase 6 NWP, 21 rain gauges, 24 flood records, SAR 5/13 (`38.5%`) x-val, D8 hydrology, Experimental RF ML status | `/api/phase6/*`, `/api/phase7/*`, `/api/ml/experimental` |
| **Alert Candidates Tab** | `button[data-bottom-tab="alertsTab"]` | Spatial alert clusters (5.5 km tiles), active/ack/history alerts, `Re-evaluate Now`, Forecast Refresh History | `/api/alerts`, `/api/alerts/clusters`, `/api/alerts/summary`, `/api/spatial/coverage`, `/api/weather/history` |

---

## 2. Civilian Safety Page (`/civilian-alert.html`)
- **Navigation:** Open directly at `http://127.0.0.1:8501/civilian-alert.html` (or click **VIEW CIVILIAN ALERT** from the Authority Dashboard).
- **Features:** Predefined **East Bengaluru** demonstration scenario (works independently in a fresh browser), **Copy Alert Link**, **Share Alert**, **SOS — Call 112** (`tel:112` with confirmation modal), **4 Bengaluru zones** (red affected, orange caution), **4 green suggested demonstration destinations**, and **indicative OSRM routing** (with offline fallback warning).
