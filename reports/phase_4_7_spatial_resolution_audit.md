# Phase 4.7.2 — Scientific Audit: Forecast Spatial Resolution & Coarse Grid Mapping

**Platform:** Bengaluru Urban Flood Risk Intelligence Platform  
**Component:** Spatial NWP Mapping Engine ([`src/floodrisk/ingestion/forecast.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/ingestion/forecast.py))  
**Audited Datasets:**
- [`data/processed/forecast_rainfall_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/forecast_rainfall_bengaluru.parquet)
- [`data/processed/forecast_exposure_indicators_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/forecast_exposure_indicators_bengaluru.parquet)  
**Audit Classification:** **REQUIRES_CORRECTION (Corrected & Documented with Limitations)**

---

## 1. Audit Context & Scientific Objective

In Phase 4.2, the forecast ingestion pipeline was described as providing $72,540$ time-series forecast records across the $1,170$ project grid cells covering the Bengaluru Urban domain.

The scientific objective of this audit is to determine:
1. The native spatial resolution of the underlying numerical weather models.
2. The exact number of independent forecast time series acquired across the domain.
3. How coarse forecast data is mapped to the 1-km master grid.
4. Whether the presentation of $1,170$ cell-level forecast records implies false spatial precision.

---

## 2. Ingestion Architecture & Sampling Inspection

Inspection of [`src/floodrisk/ingestion/forecast.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/ingestion/forecast.py) (lines 42–104) reveals:

```python
sample_grid_density: int = 3 # 3x3 = 9 spatial anchor points across domain
lats = np.linspace(df_grid_cells["centroid_lat"].min(), df_grid_cells["centroid_lat"].max(), sample_grid_density)
lons = np.linspace(df_grid_cells["centroid_lon"].min(), df_grid_cells["centroid_lon"].max(), sample_grid_density)
```

And in the cell-mapping loop:

```python
# Assign each grid cell to its nearest NWP spatial anchor point
for _, cell in cell_coords.iterrows():
    # Find closest anchor by Euclidean distance
    best_anchor = min(anchor_forecasts, key=lambda a: (c_lat - a['lat'])**2 + (c_lon - a['lon'])**2)
```

### Critical Findings:

1. **Native NWP Resolution:**
   - **ECMWF IFS (HRES):** Native resolution is approximately $0.1^\circ \times 0.1^\circ$ (roughly $9\text{ km} \times 9\text{ km}$ at $13^\circ\text{N}$).
   - **NOAA GFS:** Native resolution is approximately $0.125^\circ \times 0.125^\circ$ (roughly $13\text{ km} \times 13\text{ km}$).
   - The Open-Meteo seamless model blends these coarse atmospheric products.
2. **Exactly 9 Independent Forecast Time Series:**
   - The domain covers $30\text{ km}$ (longitude) by $39\text{ km}$ (latitude).
   - Ingestion samples a $3 \times 3$ grid of 9 spatial anchors (`NWP_ANCHOR_0_0` to `NWP_ANCHOR_2_2`).
   - Consequently, across the entire domain, there are only **9 independent forecast time series**.
3. **The 67,860 Row Count Represents Coarse Re-Sampling:**
   - Each of the 1,170 equal-area 1-km cells inherits values from its nearest regional anchor.
   - On average, each coarse anchor is copied to $1,170 / 9 = 130$ master grid cells.
   - The ~67,860 rows in `forecast_rainfall_bengaluru.parquet` represent $9\text{ anchors} \times 58\text{ lead hours} = 522$ distinct hourly forecast values replicated across 1,170 cells.
   - **Scientific Verdict:** These records do **NOT** represent 67,860 independent atmospheric observations or genuine 1-km localized weather forecasts.

---

## 3. Spatial Resolution Audit Table

| Metric | Project Master Grid | Forecast Model (ECMWF IFS) | Forecast Model (NOAA GFS) | Operational Ingestion Anchor Grid |
| :--- | :---: | :---: | :---: | :---: |
| **Grid Cell Spacing** | $1.0\text{ km}$ ($1,000\text{ m}$) | $\sim 9.0\text{ km}$ ($0.1^\circ$) | $\sim 13.0\text{ km}$ ($0.125^\circ$) | $\sim 13.0\text{ km} \times 15.0\text{ km}$ |
| **Domain Coverage Units** | 1,170 cells | $\sim 12\text{ pixels}$ | $\sim 7\text{ pixels}$ | 9 spatial anchor points |
| **Projection / CRS** | EPSG:6933 (Equal Area) | EPSG:4326 (WGS84 Lat/Lon) | EPSG:4326 (WGS84 Lat/Lon) | Centroid Euclidean Nearest |
| **Independent Observations** | 1,170 physical cells | $\le 12$ regional states | $\le 7$ regional states | **9 distinct time series** |
| **Replication Factor** | $1.0\times$ (Unique) | $\sim 97.5\times$ | $\sim 167\times$ | **$130\times$ average per anchor** |

---

## 4. Risks of Misrepresentation & Corrective Measures

### Identified Scientific Risks:
1. **Ecological Fallacy:** Assuming that a 1-km grid cell displaying $68.2\text{ mm}$ of forecast rain has localized, sub-kilometer meteorological intelligence. Atmospheric convective cells in Bengaluru can be $2\text{ to }5\text{ km}$ in scale; a $9\text{ to }13\text{ km}$ NWP product smooths extreme localized downpours.
2. **Artificial Precision through Interpolation:** Bilinear or spline interpolation across coarse anchors would produce visually smooth gradients across the 1,170 cells, but would **not** add genuine micro-meteorological information. Nearest-centroid mapping is scientifically honest because it clearly shows the stepped nature of the regional anchors.

### Corrective Implementations:
1. **Schema Enrichment:**
   - Added `source_pixel_id` (`NWP_ANCHOR_i_j`) to track exactly which coarse anchor feeds each cell.
   - Added `mapping_method: "nearest_centroid_anchor"`.
   - Added `coarse_grid_note: "Inherited from nearest 9-13km regional anchor; not an independent 1-km weather observation."`
2. **Dashboard Disclaimers:**
   - Updated top header badge to: `NWP Grid: 9 Regional Anchors (~9-13km)`.
   - Updated map controls and cell inspector to state: `Layer 3: NWP Forecast Exposure (9-13km Regional Anchor Mapping)`.
   - Updated legend note: `* Mapped from 9 coarse anchors. Not independent 1-km weather observations.`

