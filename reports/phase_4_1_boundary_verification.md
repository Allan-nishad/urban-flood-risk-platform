# Phase 4.1 — Administrative Boundary & Study Domain Verification Report

**Project Title:** AI-Based Early Detection and Forecasting of Urban Flood Risks Using Satellite and Weather Data  
**Study Domain:** Bengaluru Urban (1,170 Cells, 1-km Grid)  
**Execution Runtime:** Python 3.11.15 (`.venv`)  
**Reporting Date:** 2026-11-05  
**Boundary Status:** **`PROVISIONAL_DEVELOPMENT_BBOX_ACTIVE` (Authoritative Municipal Boundary Pending Ingestion)**  

---

## 1. Executive Summary & Boundary Distinction

A common flaw in urban environmental AI systems is conflating arbitrary rectangular bounding boxes with legal municipal jurisdictions. This report explicitly establishes the boundary status of the platform:
- **Active Operational Boundary:** A regular rectangular development bounding box encompassing the greater Bengaluru metropolitan core ($77.45^\circ - 77.75^\circ\text{E}, 12.85^\circ - 13.15^\circ\text{N}$).
- **Status:** Explicitly classified as `PROVISIONAL_DEVELOPMENT_BBOX`.
- **Authoritative Status:** Official municipal ward boundaries (BBMP 198 wards) and Bengaluru Urban district revenue boundaries remain `PENDING_AUTHORITATIVE`.

---

## 2. Specification of Active Provisional Development Domain

The master analysis grid [`data/processed/grid_bengaluru_urban_1000m.gpkg`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/grid_bengaluru_urban_1000m.gpkg) spans a complete regular grid of $30 \times 39 = 1,170$ equal-area cells:

| Domain Dimension | Value in EPSG:6933 (m) | Approximate Geographic WGS84 Extent |
| :--- | :---: | :---: |
| **Western Boundary** | $X_{\min} = 7,472,000\text{ m}$ | Longitude $77.4462^\circ\text{E}$ |
| **Eastern Boundary** | $X_{\max} = 7,502,000\text{ m}$ | Longitude $77.7468^\circ\text{E}$ |
| **Southern Boundary** | $Y_{\min} = 1,625,000\text{ m}$ | Latitude $12.8465^\circ\text{N}$ |
| **Northern Boundary** | $Y_{\max} = 1,664,000\text{ m}$ | Latitude $13.1535^\circ\text{N}$ |
| **Total Analysis Area** | $1,170\text{ km}^2$ ($1,170,000,000\text{ m}^2$) | Encompasses BBMP central, eastern (Mahadevapura), and southern zones |

### Boundary Cell Quality Flags:
In all deliverable datasets, each cell carries explicit boundary provenance:
- `is_boundary_cell`: Boolean flag set to `True` for the 134 peripheral edge cells (columns 7472, 7501; rows 1625, 1663).
- `fraction_inside_domain`: Continuous fraction in $[0, 1]$ recording polygon overlap.
- `incident_boundary_ambiguity_flag`: Set to `True` for incidents mapped near domain margins.

---

## 3. Official Municipal Authority Sources & Ingestion Protocol

To transition from the provisional bounding box to official administrative polygons:

| Administrative Authority | Target Dataset | Authoritative Source | Acquisition URL / Portal |
| :--- | :--- | :--- | :--- |
| **Bruhat Bengaluru Mahanagara Palike (BBMP)** | 198-Ward Municipal Polygon Boundaries | Karnataka Geographic Information System (KGIS) / OpenCity | `https://opencity.in/data/bbmp-wards/` |
| **Revenue Department of Karnataka** | Bengaluru Urban District & Taluk Boundaries | Survey of India / Karnataka State Remote Sensing Applications Centre (KSRSAC) | `https://ksrsac.karnataka.gov.in/` |

### Step-by-Step Replacement Instructions:
1. Acquire the official BBMP 198-ward GeoJSON/Shapefile.
2. Place the file at `data/raw/boundaries/bbmp_wards_official.geojson`.
3. Verify geometry validity (ensure polygon closure and WGS84 CRS).
4. Run `python -m floodrisk.spatial.grid --clip-boundary data/raw/boundaries/bbmp_wards_official.geojson`.
5. The pipeline will clip the 1,170-cell master grid to the legal BBMP administrative limits, updating `fraction_inside_boundary` while preserving the global EPSG:6933 cell indexing scheme for backward compatibility.

