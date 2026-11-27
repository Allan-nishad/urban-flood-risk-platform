# Historical Flood-Event Data Feasibility & Source Assessment Report

**Audit Date:** 2026-11-05  
**Geographic Scope:** Bengaluru Urban & Greater Metropolitan Region  
**Assessment Standard:** Scientific feasibility for direct 1 km supervised machine learning training  

---

## 1. Executive Summary & Defensible Conclusion

> [!IMPORTANT]
> **Core Finding:**  
> **"No publicly accessible, verified, continuous historical flood-inundation dataset suitable for direct 1 km supervised training was established during this assessment."**

This finding does **not** mean that no historical flood information exists for Bengaluru. Significant flood information exists across government agencies, municipal control rooms, and academic publications. However, this information is partitioned into **static engineering inventories, qualitative ward-level SMS alerts, coarse district disaster statistics, or episodic satellite maps**, none of which provide a continuous, verified, cell-by-cell ground truth time series for supervised model training.

---

## 2. Categorical Source-by-Source Investigation Matrix

The evaluated sources are categorized into four distinct data regimes:

### Category A: Static Municipal Hotspot Inventories

#### 1. BBMP Stormwater Drain (SWD) Department Vulnerable Points Inventory
- **Document Reference:** Bruhat Bengaluru Mahanagara Palike (BBMP) SWD Department Annual Monsoon Action Plan (Master List of Vulnerable Inundation Points).
- **Direct Reference:** Municipal circulars and SWD zone-wise action plans published via BBMP portal ([https://bbmp.gov.in](https://bbmp.gov.in)).
- **Inspection Status:** **Actually inspected** (published summary inventories of ~209 to 226 chronic waterlogging hotspots).
- **Retrieval / Assessment Date:** 2026-11-05.
- **Access Status:** Public summary tables available; underlying raw municipal CAD/GIS geodatabase is internal government property.
- **Spatial Precision:** `point_exact` (identified by specific road underpasses, rajaluve junctions, and low-lying layouts, e.g., Okalipuram underpass, Le Méridien underpass, Silk Board junction, Kodichikkanahalli, Rainbow Drive Layout).
- **Temporal Coverage:** Static compilations updated annually (2018–2023).
- **Data Format:** Non-machine-readable PDF tables and executive text reports.
- **Licence / Access Restrictions:** Government internal; no open machine-readable CSV/API.
- **Scientific Usability:** Valid as static spatial risk verification points for susceptibility screening, but **unsuitable as temporal training labels** (lacks date-by-date inundation depth and duration).

---

### Category B: Ward-Level & Station-Level Operational Alerts

#### 2. KSNDMC Urban Flood Early Warning System (Varuna Mitra / UFEWS)
- **Direct Reference:** Karnataka State Natural Disaster Monitoring Centre (KSNDMC) Bengaluru Urban Flood Warning Dashboard ([https://bengaluru.ksndmc.org](https://bengaluru.ksndmc.org) and [https://ksndmc.org](https://ksndmc.org)).
- **Inspection Status:** **Actually inspected** (public telemetry web interface).
- **Retrieval / Assessment Date:** 2026-11-05.
- **Access Status:** Real-time gauge telemetry is public; historical incident dispatch registers and sensor water-level archives require inter-departmental authorization.
- **Spatial Precision:** `point_exact` for automated telemetric rain gauges (TRG) and telemetric weather stations (TWS); `ward` to `subward` for broadcast flood warning alerts.
- **Temporal Coverage:** Operational telemetry from ~2015 to present.
- **Data Format:** Web interface dashboard (HTML/JSON streams) and daily weather bulletins (PDF).
- **Licence / Access Restrictions:** Government of Karnataka proprietary; redistribution restricted without formal MoU.
- **Scientific Usability:** Gauge rainfall provides valuable in-situ precipitation validation, but alert text records represent *forecast warnings or citizen distress dispatches*, not verified inundation polygon footprints.

---

### Category C: District-Level & Basin-Level Historical Compendiums

#### 3. Central Water Commission (CWC) & NDMA Disaster Statistics
- **Direct Reference:** Central Water Commission Flood Management Reports; National Disaster Management Authority (NDMA) Disaster Statistics ([https://cwc.gov.in](https://cwc.gov.in) and [https://data.gov.in](https://data.gov.in)).
- **Inspection Status:** **Actually inspected** (annual public disaster statistical bulletins).
- **Retrieval / Assessment Date:** 2026-11-05.
- **Access Status:** Open public access under National Data Sharing and Accessibility Policy (NDSAP).
- **Spatial Precision:** `district_level` to state/basin level aggregates (e.g., total flood damage for Karnataka or Bengaluru Urban district aggregate).
- **Temporal Coverage:** 1953 to 2023 (annual compendiums).
- **Data Format:** PDF and tabular CSV summaries.
- **Licence / Access Restrictions:** Open Government Data (OGD) Licence India.
- **Scientific Usability:** **Unsuitable for 1 km grid modeling.** Assigning a district-level flood occurrence to individual 1-km cells introduces extreme spatial false-precision and misclassification error.

---

### Category D: Satellite-Derived Inundation Products

#### 4. KSRSAC Karnataka GIS (K-GIS) Flood Mapping Services
- **Direct Reference:** Karnataka State Remote Sensing Applications Centre (KSRSAC), Department of Electronics, IT, BT and S&T, Government of Karnataka ([https://kgis.ksrsac.in](https://kgis.ksrsac.in)).
- **Inspection Status:** **Identified as potential source (access gated)** (portal accessible; direct download of GIS raster/vector layers requires departmental credentials).
- **Retrieval / Assessment Date:** 2026-11-05.
- **Access Status:** Restricted to authorized Karnataka government departments.
- **Spatial Precision:** High resolution (10–30 meter satellite derived flood extents).
- **Temporal Coverage:** Episodic satellite acquisitions during major cyclone and flood emergencies.
- **Data Format:** WMS/WFS map services and internal GeoTIFF/Shapefiles.
- **Licence / Access Restrictions:** State government internal; formal inter-institutional MoU required.
- **Scientific Usability:** Highly valuable for discrete event calibration once institutional access is approved, but not currently available for automated ingestion.

#### 5. Dartmouth Flood Observatory (DFO) Global Active Archive
- **Direct Reference:** University of Colorado Boulder, Dartmouth Flood Observatory Global Active Archive of Large Flood Events ([https://floodobservatory.colorado.edu](https://floodobservatory.colorado.edu)).
- **Inspection Status:** **Actually inspected** (public spatial archive).
- **Retrieval / Assessment Date:** 2026-11-05.
- **Access Status:** Fully open public access.
- **Spatial Precision:** `regional_envelope` ($\pm 10\text{ to }50\text{ km}$ positional envelope).
- **Temporal Coverage:** 1985 to present (includes major historical South India flood episodes such as October 2005 and September 2022).
- **Data Format:** GeoJSON, Shapefile, CSV.
- **Licence / Access Restrictions:** Open Access (CC BY 4.0).
- **Scientific Usability:** Too coarse for 1 km urban grid cell supervision. DFO envelopes delineate broad multi-taluk regions rather than localized street or lake breach ponding.

---

## 3. Methodological Safeguards for Phase 2

1. **No Inference of Flood Events from Rainfall:**
   - Under no circumstances will high precipitation readings (e.g., $> 100\text{ mm/day}$) be mathematically converted into positive flood training labels. Flooding is governed by the non-linear interaction of rainfall, infiltration capacity, drainage infrastructure, and terrain depressions.
2. **Phase 2 Prioritization of Unsupervised Terrain Susceptibility:**
   - Because no continuous historical inundation ground truth is openly accessible, Phase 2 will focus on **unsupervised physical topographic indices** (Height Above Nearest Drainage, Topographic Position Index, MERIT Hydro catchment area, and built-up fraction) rather than unvalidated supervised classifiers.
