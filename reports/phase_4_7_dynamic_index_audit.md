# Phase 4.7.4 — Scientific Audit: Dynamic Prioritization Formula & Non-Conflation Invariants

**Platform:** Bengaluru Urban Flood Risk Intelligence Platform  
**Component:** Dynamic Risk-Intelligence Engine ([`src/floodrisk/processing/dynamic_risk.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/dynamic_risk.py))  
**Audited Dataset:** [`data/processed/dynamic_risk_intelligence_bengaluru.parquet`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/data/processed/dynamic_risk_intelligence_bengaluru.parquet)  
**Audit Classification:** **REQUIRES_CORRECTION (Corrected & Documented with Limitations)**

---

## 1. Audit Context & Scientific Objective

In Phase 4.3, the platform implemented a dynamic risk-intelligence engine. While the report described the separation of four information layers, it also presented a combined composite formula:

$$S_{\text{dynamic}} = 0.35 \cdot S_{\text{static}} + 0.25 \cdot S_{\text{obs}} + 0.30 \cdot S_{\text{fcst}} + 0.10 \cdot I_{\text{evidence}}$$

The scientific objective of this audit is to answer the six fundamental methodological questions regarding this formula:
1. How are observed rainfall and forecast rainfall normalized?
2. Are they normalized against identical physical thresholds?
3. Does static susceptibility share physical units or interpretations with dynamic meteorological fluxes?
4. Does an incident evidence flag introduce reporting-density bias?
5. Is incident evidence historical, current, or event-specific?
6. Does including incident evidence in the score create evaluation circularity?

---

## 2. Answers to the Six Methodological Questions

### Question 1: How are observed and forecast rainfall normalized?
Inspection of [`src/floodrisk/processing/dynamic_risk.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/dynamic_risk.py) reveals:
- **Observed Exposure:**
  $$S_{\text{obs}} = 0.55 \cdot \text{clip}\left(\frac{R_{\text{obs}}}{100.0\text{ mm}}, 0, 1\right) + 0.45 \cdot \text{clip}\left(\frac{\text{API}}{150.0\text{ mm}}, 0, 1\right)$$
- **Forecast Exposure:**
  $$S_{\text{fcst}} = \text{clip}\left(\frac{P_{24\text{h}}}{65.0\text{ mm}}, 0, 1\right)$$

### Question 2: Are they normalized against the same thresholds?
**No.** They are normalized against different baselines:
- Observed rainfall is normalized against historical monsoon maxima ($100\text{ mm}$ for 24h rain, $150\text{ mm}$ for antecedent soil moisture).
- Forecast rainfall is normalized against $65.0\text{ mm}$ (the IMD Heavy Rainfall boundary).
- **Physical Consequence:** A forecast of $65\text{ mm}$ reaches $S_{\text{fcst}} = 1.0$, whereas an observed rainfall of $65\text{ mm}$ yields only $S_{\text{obs}} \approx 0.36 + 0.15 = 0.51$. The dynamic score is twice as sensitive to forecast increments as to observed historical increments.

### Question 3: Does static susceptibility share interpretations with dynamic fluxes?
**No.**
- $S_{\text{static}}$ is a dimensionless index reflecting terrain low-lyingness and land-cover imperviousness. It is time-invariant over years.
- $S_{\text{fcst}}$ and $S_{\text{obs}}$ reflect transient precipitation fluxes ($\text{mm/day}$) changing hourly.
- Linearly adding a static terrain index to a forward rain flux is a **heuristic Multi-Criteria Decision Analysis (MCDA)** technique; it is **not** a physical hydrodynamic solution (e.g., Saint-Venant shallow water equations or SWMM hydraulic routing).

### Question 4: Does incident evidence introduce reporting-density bias?
**Yes, severe reporting bias exists.**
- The 21 catalogued flood incidents originate primarily from social media, municipal complaint logs, and press reports during August–September 2022.
- High-income IT corridors (e.g., Outer Ring Road, Bellandur, Yamalur) have high smartphone density and media attention, generating multiple geocoded reports.
- Under-represented, lower-income peri-urban settlements in the northern and western bounding box may experience waterlogging without formal press documentation.
- Rewarding cells with $+0.10 \cdot I_{\text{evidence}}$ amplifies socioeconomic reporting bias into the model.

### Question 5: Is incident evidence historical, current, or event-specific?
**It is historical.**
- All 21 verified incidents occurred between 2 August 2022 and 5 September 2022.
- These records demonstrate historical vulnerability to intense rainfall. They do **not** indicate that water is standing on the ground today.

### Question 6: Does including incident evidence in the score create evaluation circularity?
**YES. This is the most critical scientific flaw of a combined index.**
- If $I_{\text{evidence}}$ is added to $S_{\text{dynamic}}$, the score of cell $i$ is artificially inflated because it has a historical flood report.
- If the model is subsequently evaluated by checking whether cells with high $S_{\text{dynamic}}$ contain flood incidents, the model is evaluated on data it was explicitly handed.
- **Verification of Actual Code:** Inspection of [`src/floodrisk/processing/dynamic_risk.py`](file:///c:/Users/allan/Documents/Projects/urban-flood-risk-platform/src/floodrisk/processing/dynamic_risk.py) shows that the production code **deliberately excluded** $I_{\text{evidence}}$ from the composite calculation:

```python
# Deliberately EXCLUDES incident evidence to prevent circularity:
dynamic_priority = (
    0.35 * df["static_susceptibility_score"] +
    0.30 * df["observed_rainfall_exposure_score"] +
    0.35 * df["forecast_exposure_score_24h"]
).clip(0.0, 1.0).astype(np.float32)
```

The narrative report described the four-component theoretical formula, but the software engine correctly isolated Layer 4 as an independent ground truth audit layer.

---

## 3. Methodological Safeguards & Status Downgrade

To ensure scientific defensibility:
1. **Primary Outputs are the Four Separate Layers:**
   - Layer 1: Static Physical Susceptibility (SRTM elevation, WorldCover built-up fraction, MCDA score)
   - Layer 2: Observed Monsoonal Precipitation Exposure ($R_{\text{obs}}$, API decay)
   - Layer 3: Forecast Precipitation Exposure ($P_{24\text{h}}$, intensity category, lead time)
   - Layer 4: Ground Flood Evidence (21 historical incident points with uncertainty radii)
2. **Downgrade of Combined Score:**
   - The composite index is explicitly labelled:  
     `dynamic_score_status: "OPTIONAL_UNCALIBRATED_PRIORITIZATION_INDEX"`
   - It is presented in documentation and the web console as an exploratory screening tool for resource ranking, **never as a calibrated flood probability or flood inundation prediction**.

