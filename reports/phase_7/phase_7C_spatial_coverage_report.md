# Phase 7C — Spatial Coverage & Observational Censorship Report

**Auditor:** Geospatial Data Scientist & Research Team  
**Study Domain:** Bengaluru Urban Region ($1,170\text{ km}^2$, 1,170 equal-area 1-km cells)  
**Status:** **`PASS_WITH_DOCUMENTED_LIMITATIONS`**  

---

## 1. Domain Coverage Analysis

The Bengaluru Urban study domain comprises 1,170 1-km grid cells in EPSG:6933. Spatial overlay against independent ground truth revealed:
- **Total Observed Domain Area:** $20\text{ km}^2$ ($1.71\%$)
- **Unobserved Domain Area:** $1,150\text{ km}^2$ ($98.29\%$)
- **Observational Censorship Ratio:** **$57.5 : 1$** (57.5 unobserved cells for every observed cell)

---

## 2. Spatial Clustering and Socio-Technical Reporting Bias

Inspection of the 13 positive flood cells revealed extreme spatial clustering:
- **Eastern Corridor Concentration:** 10 of the 13 positive cells ($76.9\%$) are concentrated along the Outer Ring Road (ORR) and Mahadevapura / Bellandur / Varthur technology corridors.
- **Reporting Mechanism Bias:** These areas house multinational IT tech parks, high-value gated villa layouts, and active resident associations with smartphones and social media presence.
- **Peripheral Valley Censorship:** Rural and peri-urban valleys in the south (Anekal taluk), northwest (Hesaraghatta / Arkavathi basin), and northeast (Budigere) had zero recorded observations during the 2022 deluge.

---

## 3. The Fallacy of Domain-Wide Negative Imputation

If an analyst assumes that the 1,150 unobserved cells were "dry" (treating lack of news reports as absence of water), it injects massive systemic bias:
1. Lowland agricultural valleys that experienced inundation without media coverage are falsely labeled as negative training examples.
2. Machine learning classifiers trained on such data learn to correlate flood risk with "distance to tech parks" or "high population density" rather than physical terrain hydrology.
3. This creates severe algorithmic distortion and false safety in unmonitored communities.

---

## 4. Formal Recommendation

All downstream spatial analysis, dashboard visualizations, and research conclusions must treat the 1,150 cells as **`UNOBSERVED / UNKNOWN`**, strictly prohibiting negative label imputation.

