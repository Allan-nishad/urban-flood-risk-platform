# Bengaluru Urban: Development Bounding-Box Coverage & Spatial Foundation Report

**Audit Date:** 2026-11-05  
**Platform Version:** 0.1.0  
**Study Area ID:** `bengaluru_urban`  
**Execution Runtime:** Python 3.11.15  

---

## 1. Boundary Status & Critical Geographic Distinction

> [!IMPORTANT]
> **Boundary Classification: DEVELOPMENT BOUNDING BOX COVERAGE (Status: `pending_authoritative_boundary`).**  
> The 1,170 generated grid cells do **NOT** constitute a final, verified Bengaluru Urban administrative district grid. They represent a rectangular regional development extent spanning the urban core and immediate surroundings.

### Explicit Spatial Coverage Breakdown
- **Development Bounding-Box Coverage Extent:**
  - Coordinates: West: $77.45^\circ\text{E}$, South: $12.85^\circ\text{N}$, East: $77.75^\circ\text{E}$, North: $13.15^\circ\text{N}$
  - **Total Cells Generated:** **1,170 cells** ($1.00 \text{ km}^2$ nominal per cell)
  - **Fully Inside Development Bounding Box:** **1,036 cells** ($\text{fraction\_inside\_boundary} \ge 0.9999$)
  - **Partially Intersecting Bounding-Box Perimeter:** **134 cells** ($0.0 < \text{fraction\_inside\_boundary} < 0.9999$)
  - **Outside Cells:** **0 cells**
  - **Mean Fraction Inside Bounding Box:** **0.9232**
- **Verified Administrative District Coverage:**
  - Status: **Pending authoritative polygon ingestion.**
  - Official Source: Survey of India (SOI) / Karnataka State Remote Sensing Applications Centre (KSRSAC).
  - Target Drop-Zone: `data/external/boundaries/bengaluru_urban.geojson`.
  - Once the official administrative polygon is placed in the drop-zone, the platform will re-evaluate cell coverage fractions against the true municipal/district perimeter, separating fully inside taluk/ward cells from peripheral boundary-straddling cells.

---

## 2. Authoritative CRS Definition & Equal-Area Properties

- **Authoritative CRS Name:** `WGS 84 / NSIDC EASE-Grid 2.0 Global` (EPSG:6933)
- **Projection Method:** `Lambert Cylindrical Equal Area` (EPSG Method 9835)
- **Standard Parallel:** $30.0^\circ\text{N/S}$
- **Natural Origin:** $0.0^\circ$ (Greenwich Meridian & Equator)
- **Ellipsoid:** WGS 84 (semi-major axis $a = 6,378,137.0\text{ m}$, inverse flattening $1/f = 298.257223563$)
- **Grid Scheme:** Globally anchored square equal-area grid at global origin $(0, 0)$.
  $$\text{col} = \left\lfloor \frac{X_{\min}}{1000} \right\rfloor, \quad \text{row} = \left\lfloor \frac{Y_{\min}}{1000} \right\rfloor$$
- **Standardized Cell Identifier Syntax:** `g1000_{col}_{row}` (e.g., `g1000_7472_1625` to `g1000_7501_1663`).

---

## 3. Geodesic Measurement & Independent Distortion Audit

Calculated from actual inverse-projected WGS84 cell corners using `pyproj.Geod(ellps="WGS84")`:

| Metric | Nominal Projected Value | Geodesic Value on WGS84 Ellipsoid | Ratio ($\text{Geodesic} / \text{Nominal}$) |
| :--- | :--- | :--- | :--- |
| **Cell Area** | $1,000,000.0000 \text{ m}^2$ | **$1,000,000.0018 \text{ m}^2$** ($\pm 0.000002\text{ m}^2$) | **$1.0000000018$** |
| **Area Difference** | $0.0000 \text{ m}^2$ | **$+0.0018 \text{ m}^2$** ($1.8 \text{ cm}^2$ per $1 \text{ km}^2$) | — |
| **South Edge (E-W parallel)** | $1,000.0000 \text{ m}$ | **$1,124.3756 \text{ m}$** ($\text{Min}=1123.69\text{ m}, \text{Max}=1125.06\text{ m}$) | **$1.124376$** ($+12.44\%$) |
| **North Edge (E-W parallel)** | $1,000.0000 \text{ m}$ | **$1,124.3394 \text{ m}$** ($\text{Min}=1123.65\text{ m}, \text{Max}=1125.02\text{ m}$) | **$1.124339$** ($+12.43\%$) |
| **West Edge (N-S meridian)** | $1,000.0000 \text{ m}$ | **$889.3970 \text{ m}$** ($\text{Min}=888.86\text{ m}, \text{Max}=889.94\text{ m}$) | **$0.889397$** ($-11.06\%$) |
| **East Edge (N-S meridian)** | $1,000.0000 \text{ m}$ | **$889.3970 \text{ m}$** ($\text{Min}=888.86\text{ m}, \text{Max}=889.94\text{ m}$) | **$0.889397$** ($-11.06\%$) |
| **Scale Factor Product** | $1.0000$ | $1.124376 \times 0.889397 = \mathbf{1.000016} \approx \mathbf{1.000000}$ | Strictly Equal-Area |

---

## 4. Multi-District Overlap Verification (Bengaluru Urban & Rural)

- **Bengaluru Urban Development Bounding Box:** 1,170 cells
- **Bengaluru Rural Development Bounding Box:** 5,313 cells
- **Actual Overlapping Shared Cells:** **960 cells**
- **Match Rate:** **960 / 960 (100.0%)** exact match across:
  - Grid IDs (`g1000_...`)
  - Row & Column indices
  - WGS84 centroid coordinates
  - EPSG:6933 geometries
