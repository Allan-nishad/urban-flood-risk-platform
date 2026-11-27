# Phase 6.1 — Independent Scientific Audit: Audit A (NWP Independence & Grid Resolution)

**Auditor:** Independent Scientific Acceptance Inspector  
**Campaign Baseline:** Phase 6 Master Execution Baseline (`reports/phase_6/`)  
**Audit Target:** NOAA GFS 0.25° NWP Ingestion, Grid Resolution, and Statistical Independence  
**Classification:** `VERIFIED_WITH_LIMITATIONS`  

---

## 1. Executive Summary & Core Audit Question

In the Phase 6 Executive Report, Workstream 6A reported:
- **198,900** cell-forecast records in `nwp_forecast_archive.parquet`
- **170** forecast slices (34 cycles $\times$ 5 lead hours)
- **1,170** equal-area (1-km) study domain grid cells
- Relationship: $198,900 = 170 \times 1,170$

The audit investigated whether the 198,900 archive rows represent 198,900 independent atmospheric forecasts, or whether coarse GFS numerical weather prediction values were replicated across the 1-km grid cells.

---

## 2. Source Provenance & GRIB2 Integrity Verification

The source files in `data/raw/phase6/nwp/` and metadata in `nwp_forecast_provenance.parquet` and `nwp_acquisition_log.csv` were inspected:
- **Source Bucket:** AWS Open Data (`s3://noaa-gfs-bdp-pds`, `https://noaa-gfs-bdp-pds.s3.amazonaws.com/`)
- **Acquisition Protocol:** HTTP Range-GET using `.idx` byte offsets to retrieve only the `APCP` (Total Precipitation) messages.
- **Slices Downloaded:** 170 individual `.grib2` slices covering 2022-08-25 to 2022-09-10 (34 cycles: 00Z and 12Z; lead times: 6h, 12h, 24h, 48h, 72h).
- **Checksum Verification:** 170/170 files matched their recorded SHA-256 hashes bit-for-bit.
- **ecCodes Message Inspection:**
  - WMO Centre: `kwbc` (NOAA NCEP, Washington)
  - Grid Type: `regular_ll`
  - Dimensions: $N_i = 1440$, $N_j = 721$ (global grid: $360^\circ \times 180^\circ$ at $0.25^\circ \approx 27.75\text{ km}$ spacing)
  - Parameter: `paramId = 228228`, `shortName = tp`, `name = Total Precipitation`, `units = kg m**-2` (equivalent to mm)
  - Step Type: `accum` (interval and cumulative accumulations disambiguated using step ranges `0-6`, `6-12`, `18-24`, `42-48`, `66-72`).

The meteorological source files are authentic, uncorrupted WMO GRIB2 files from NOAA NCEP.

---

## 3. Native Grid Resolution vs. 1,170 Study Domain Cells

The Bengaluru Urban study domain is bounded by $77.45^\circ - 77.75^\circ\text{E}$ and $12.85^\circ - 13.15^\circ\text{N}$ ($30\text{ km} \times 39\text{ km}$, $1,170\text{ km}^2$).

At $0.25^\circ$ spacing ($\approx 27.75\text{ km}$ in latitude and $\approx 27.05\text{ km}$ in longitude at $13^\circ\text{N}$), the entire $1,170\text{ km}^2$ study domain is covered by **exactly six native GFS grid nodes**:

| GFS Latitude (°N) | GFS Longitude (°E) | Mapped 1-km Cells | Domain Percentage | Topographic / Spatial Sector |
| :---: | :---: | :---: | :---: | :---: |
| **12.75** | **77.50** | 72 | 6.15% | Southwest Peripheral (Anekal / Bannerghatta border) |
| **12.75** | **77.75** | 48 | 4.10% | Southeast Peripheral (Sarjapur border) |
| **13.00** | **77.50** | 558 | 47.69% | West / Central Bengaluru (City Core, Vrishabhavathi, Peenya) |
| **13.00** | **77.75** | 372 | 31.79% | East Bengaluru (Bellandur, Varthur, Mahadevapura, Whitefield) |
| **13.25** | **77.50** | 72 | 6.15% | Northwest Peripheral (Hesaraghatta border) |
| **13.25** | **77.75** | 48 | 4.10% | Northeast Peripheral (Devanahalli / KIA border) |
| **Total** | — | **1,170** | **100.0%** | **Entire Provisional Study Domain** |

### Key Observations:
1. Two central GFS nodes ($(13.00^\circ\text{N}, 77.50^\circ\text{E})$ and $(13.00^\circ\text{N}, 77.75^\circ\text{E})$) cover **930 out of 1,170 cells (79.49% of the platform's study area)**.
2. In `nwp_forecast_archive.parquet`, each 1-km cell was attributed the rainfall of its nearest native GFS grid node via nearest-neighbor assignment (`mapping_method: nearest_native_0p25`).
3. In every single forecast slice of 1,170 rows, there are **at most 6 unique numerical precipitation values**:
   - 134 slices contain exactly 6 unique precipitation values.
   - 23 slices contain 5 unique values.
   - 7 slices contain 4 unique values.
   - 4 slices contain 3 unique values.
   - 2 slices contain 2 unique values.
4. The dataset schema honestly and explicitly flags this:
   - `is_native_resolution: False` (100% of rows)
   - `native_spatial_resolution_km: 27.75` (100% of rows)
   - `distance_to_nearest_gfs_km`: Mean $10.82\text{ km}$, Min $0.24\text{ km}$, Max $19.00\text{ km}$.

---

## 4. Scientific Implication: Degrees of Freedom & Statistical Independence

1. **Effective Sample Size:**
   - The 198,900 rows are **not 198,900 independent atmospheric forecasts**.
   - The number of independent numerical atmospheric simulations in the archive is:
     $$\text{Effective Forecast Sample Size} = 170 \text{ slices} \times 6 \text{ nodes} = 1,020 \text{ native forecast values}$$
   - Treating 1,170 cells as 1,170 independent evaluations in any spatial statistical calculation would inflate degrees of freedom by a factor of $1,170 / 6 = 195\times$.

2. **Absence of Sub-Grid Atmospheric Physics:**
   - Attributing a single GFS grid value ($27.75\text{ km}$ spacing, representing an area of $\sim 750\text{ km}^2$) to 558 contiguous 1-km cells is a spatial attribution convenience, not micro-scale atmospheric physics.
   - It cannot resolve localized urban heat island effects, street canyon turbulence, or convective storm cells of $2 - 5\text{ km}$ diameter.

---

## 5. Audit Finding & Recommendation

| Audit Dimension | Status | Finding |
| :--- | :--- | :--- |
| **GRIB2 Source Integrity** | `VERIFIED` | 170 authentic GFS GRIB2 files acquired from AWS Open Data, verified bit-for-bit. |
| **WMO Message Decoding** | `VERIFIED` | Decoded via ecCodes 2.50.0; correct parameter, units, and accumulation step ranges. |
| **Spatial Attribution** | `VERIFIED_WITH_LIMITATIONS` | 198,900 rows represent 170 slices mapped across exactly 6 GFS nodes. Not 198,900 independent forecasts. |
| **Metadata Transparency** | `VERIFIED` | Schema correctly sets `is_native_resolution: False` and `native_spatial_resolution_km: 27.75`. |

**Scientific Acceptance Directive for Phase 7:**  
Any forecast validation, error computation, or spatial verification must be evaluated at the **native 6-node GFS resolution** (or aggregated across the 6 spatial clusters), and never reported as 198,900 independent degrees of freedom.

