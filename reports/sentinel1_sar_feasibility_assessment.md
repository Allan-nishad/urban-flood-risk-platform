# Sentinel-1 Synthetic Aperture Radar (SAR) Feasibility & Limitations Assessment

**Audit Date:** 2026-11-05  
**Study Area:** Bengaluru Urban ($77.45^\circ\text{E}$ to $77.75^\circ\text{E}$, $12.85^\circ\text{N}$ to $13.15^\circ\text{N}$)  
**Sensor:** European Space Agency (ESA) Sentinel-1 C-band SAR  

---

## 1. Candidate Benchmark Event Verification

### Documented Event: Greater Bengaluru Urban Inundation (September 4–6, 2022)
- **Supporting Meteorological Documentation:**
  - Karnataka State Natural Disaster Monitoring Centre (KSNDMC) Daily Weather Bulletins recorded over $130\text{ mm}$ of localized rainfall within 24 hours across multiple telemetric stations in East Bengaluru (Mahadevapura, Bellandur, Marathahalli).
  - Bruhat Bengaluru Mahanagara Palike (BBMP) Stormwater Drain Department operational incident sheets logged severe lake breaches and channel overflows along the Bellandur–Varthur catchment and the Outer Ring Road (ORR) corridor.
  - Documented in Central Water Commission flood advisories and national media records with extensive photographic confirmation of inundated arterial roads and residential layouts.
- **Audit Determination:** **The September 4–6, 2022 event is verified as a documented historical benchmark event.**

---

## 2. Satellite Scene Availability & Acquisition Metadata

During September 2022, only **Sentinel-1A** was operational (Sentinel-1B suffered an anomaly on December 23, 2021 and was formally decommissioned), resulting in a **12-day repeat orbit cycle** over any given track rather than the nominal 6-day constellation revisit.

### Identified Sentinel-1A Scenes
- **Relative Orbit Track 91 (Descending Pass, morning ~00:50 UTC / 06:20 IST):**
  - **Pre-Event Reference Scene:** August 24, 2022 ($\sim 00:50\text{ UTC}$).
  - **Event Scene:** September 05, 2022 ($\sim 00:50\text{ UTC}$).  
    *Significance:* This scene was acquired within hours of the overnight cloudburst of September 4/5, capturing peak inundation in open floodplains and low-lying layouts.
- **Relative Orbit Track 164 (Ascending Pass, evening ~12:45 UTC / 18:15 IST):**
  - **Pre-Event Reference Scene:** August 29, 2022 ($\sim 12:45\text{ UTC}$).
  - **Post-Event Scene:** September 10, 2022 ($\sim 12:45\text{ UTC}$).  
    *Significance:* Acquired ~5 days after the event; useful for flood recession analysis rather than peak inundation.
- **Sensor Parameters:**
  - Instrument: C-band Synthetic Aperture Radar (SAR, $5.405\text{ GHz}$).
  - Acquisition Mode: Interferometric Wide (IW) swath mode.
  - Polarizations: Dual-polarization $\text{VV} + \text{VH}$.
  - Product Level: Level-1 Ground Range Detected (GRD) High Resolution (GRDH).
  - Pixel Spacing: $10\text{ m} \times 10\text{ m}$ (effective spatial resolution $\approx 20\text{ m}$).

---

## 3. Required Radiometric & Geometric Processing Pipeline

To process Sentinel-1 GRD scenes into quantitative radar backscatter without introducing positional or radiometric artifacts, the pipeline requires:

1. **Orbit State Vector Application:** Ingest ESA Precise Orbit Ephemerides (POE) to correct satellite orbital positioning errors.
2. **Thermal Noise Removal:** Eliminate additive thermal noise along azimuth and range sub-swaths, particularly in weak VH cross-polarization channels.
3. **Radiometric Calibration:** Convert digital numbers (DN) to radar backscatter coefficient $\sigma^0$ or terrain-flattened $\gamma^0$ in linear units.
4. **Range-Doppler Terrain Correction:** Orthorectify using a high-resolution DEM (Copernicus 30m GLO-30 or SRTM 30m) into the platform's canonical analysis projection (**EPSG:6933**).
5. **Speckle Filtering:** Apply a spatial adaptive filter (e.g., Refined Lee $5 \times 5$ or Lee Sigma) to reduce coherent speckle noise while preserving linear canal/drain boundaries.
6. **Bi-Temporal Change Detection:** Calculate the logarithmic backscatter ratio:
   $$\Delta \sigma^0_{\text{dB}} = 10 \log_{10}\left( \frac{\sigma^0_{\text{event}}}{\sigma^0_{\text{pre-event}}} \right)$$

---

## 4. Fundamental Limitations of SAR in Dense Urban Terrain

> [!WARNING]
> **SAR change detection must NEVER be assumed to represent automatic ground truth in an urban environment.**

C-band radar backscatter in dense cities exhibits severe physical constraints:

1. **Double-Bounce Scattering vs. Specular Attenuation:**
   - On smooth open water surfaces (e.g., lakes, agricultural fields), specular reflection directs the radar pulse away from the antenna, resulting in very low backscatter (dark pixels, $-20\text{ to }-25\text{ dB}$).
   - However, in built-up urban corridors, standing water between vertical masonry walls creates a dihedral corner reflector (double-bounce), which can **increase** backscatter or maintain high backscatter, masking standing water on streets.
2. **Radar Shadow and Layover:**
   - Because SAR is a side-looking sensor ($30^\circ\text{ to }45^\circ$ incidence angles), multi-story buildings cast geometric radar shadows across narrow road canyons and rajakaluves, making standing water invisible to the satellite.
3. **Asphalt Highway Ambiguity:**
   - Dry, smooth asphalt expressways and airport runways also act as specular reflectors and appear as dark pixels, causing severe false-positive water classifications in urban areas.
4. **Wind-Roughened Water Surfaces:**
   - During active convective storm conditions, high surface winds create capillary ripples on standing water bodies, scattering microwave pulses back to the receiver and causing false negatives.

---

## 5. Mandatory Independent Validation Requirements

Before any Sentinel-1 change-detection product can be accepted as an empirical validation benchmark:

1. **Optical Cross-Validation:**
   - Verify detected water surfaces against high-resolution optical imagery (e.g., cloud-free PlanetScope $3\text{ m}$ or cloud-cleared Sentinel-2 multispectral MSI imagery) to eliminate asphalt and shadow false positives.
2. **Municipal Distress Log Verification:**
   - Correlate candidate flooded cells with geotagged citizen distress calls logged by the BBMP 24x7 control room on September 5, 2022.
3. **Topographic Depression Plausibility Check:**
   - Filter detected water surfaces using digital elevation data (HAND $< 2\text{ m}$ and positive topographic position index) to ensure candidate water pixels reside in physically realistic drainage sinks rather than atop dry elevated ridge lines.

