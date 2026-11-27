# Phase 7F — Academic Viva & Technical Defense Preparation

**Document Identifier:** `reports/phase_7/phase_7F_viva_preparation.md`  
**Purpose:** Comprehensive Technical Defense Q&A for Academic Viva and Project Presentation  
**Status:** **`DEFENSE_PREPARATION_DOCUMENT`**  

---

## 1. Core Research Questions & Authoritative Answers

### Q1: Why does your project title mention "AI-Based", yet you strictly block supervised machine learning flood prediction?
**Answer:**  
In scientific research, establishing when *not* to deploy machine learning is as critical as training a model. Our empirical audit revealed that $98.29\%$ of the urban domain ($1,150$ out of $1,170$ cells) lacks verified flood observations. In civic disaster reporting, media coverage focuses heavily on high-income tech corridors and arterial roads, while peripheral valleys go unrecorded. 
If we trained a supervised binary classifier (e.g. Random Forest, Neural Network), we would be forced to assume that all unmonitored cells were "dry". This injects massive false-negative label noise, training the AI to memorize "proximity to tech parks" rather than physical hydrology. By strictly enforcing the gate as `BLOCKED_BY_INSUFFICIENT_EVIDENCE`, our project defends scientific integrity over superficial cosmetic metrics.

### Q2: Why did your 24h GFS rainfall forecast achieve a Probability of Detection of 0.00 at 64.5 mm? Does this mean the model is useless?
**Answer:**  
No, a $\text{POD} = 0.00$ does not mean the model has zero skill. In fact, GFS achieved a $\text{POD} = 88.4\%$ for rain occurrence ($\ge 2.5\text{ mm}$) and $\text{POD} = 48.0\%$ for routine monsoon rain ($\ge 15.6\text{ mm}$). 
The zero POD at $64.5\text{ mm}$ is a well-documented physical phenomenon called **convective scale mismatch**. A single GFS $0.25^\circ$ grid box averages precipitation over $\sim 750\text{ km}^2$. The extreme deluges in Bengaluru were caused by localized mesoscale convective storms with intense cores of $2 - 5\text{ km}$ diameter (producing $130 - 162\text{ mm}$ at individual point gauges). When an isolated $150\text{ mm}$ cloudburst is smeared over $750\text{ km}^2$, the grid-box mean is physically $\approx 25 - 35\text{ mm}$. Because GFS predicts the area average, its maximum forecasted depth reached $38.7\text{ mm}$, mathematically never crossing the $64.5\text{ mm}$ point threshold. This proves that global NWP cannot be used directly as a flash-flood trigger without convective-permitting downscaling.

### Q3: Why did your reported Sentinel-1 SAR sensitivity drop from 76.9% to 38.5% upon closer audit?
**Answer:**  
The apparent sensitivity of $76.9\%$ was achieved by evaluating 10 agreement matches out of 13 positive ground truth cells. However, when we deconstructed the physical radar scattering:
- 4 of those 10 cells were pre-existing permanent water bodies (Bellandur Lake, Varthur Lake, Kasavanahalli Lake). The radar backscatter did not drop during the event ($\Delta\sigma^0 = 0.00\text{ dB}$); it was already dark water in the pre-event baseline.
- 1 cell (Divyasree 77 East) actually experienced a backscatter *increase* ($+0.02\text{ dB}$) due to building double-bounce corner reflection.
- Only 5 out of 13 cells ($38.5\%$) exhibited true negative backscatter drops caused by flood water expansion on dry land.
Furthermore, in 3 dense urban street canyon cells (HBR Layout, Doddanekkundi, Munnekolala), radar backscatter showed zero change ($\Delta\sigma^0 = 0.00\text{ dB}$) because multi-story buildings and mature tree canopies completely attenuated the $5.6\text{ cm}$ C-band radar pulses.

### Q4: Why is your hydrological ROC-AUC score 0.560, and why is that statistically indistinguishable from random chance?
**Answer:**  
The continuous Hydrological Inundation Potential Index (HIPI) combines Topographic Wetness Index (TWI), depression depth, and forecast runoff. When evaluated against the 20 ground truth cells (13 positives, 7 negatives), it scored $\text{ROC-AUC} = 0.560$. 
Using the Hanley & McNeil (1982) formulation for sample size $N=20$, the standard error is $\text{SE} = 0.129$, yielding an analytical 95% confidence interval of $[0.303, 0.817]$. Because $0.500$ (random guessing) lies well within this confidence interval, the null hypothesis cannot be rejected. 
Physically, this demonstrates that macro-topography on a 1-km grid cannot predict urban street flooding. In Bengaluru, flooding was caused by 2-meter compound walls, road embankments, and culvert blockages—micro-scale hydraulic features that are smoothed out on a 1-km digital elevation model.

### Q5: Why did you implement clustered bootstrapping instead of standard independent bootstrapping for rainfall errors?
**Answer:**  
Standard bootstrap sampling assumes observations are independent and identically distributed (i.i.d.). However, all 16 rain gauges on a given date experience the same synoptic storm, and stations clustered within the same GFS grid cell receive the exact same forecast. 
When we ran a date-clustered block bootstrap across 2,000 iterations, the 95% confidence interval for MAE widened from $[15.34, 22.31]\text{ mm}$ to $[8.71, 30.64]\text{ mm}$—an **uncertainty inflation of $3.1\times$**. For Pearson correlation, the CI widened by **$4.2\times$** to $[-0.07, +0.50]$, proving that treating clustered data as independent creates an illusion of statistical certainty.

---

## 2. Key Takeaway Messages for the Examiners

1. **Software Verification $\ne$ Scientific Validation:** 109 passing unit tests prove the code runs without bugs, but our scientific audit proves that global GFS and spaceborne SAR have fundamental physical limits in urban environments.
2. **Empirical Authenticity Over Synthetic Optimization:** We refused to manufacture synthetic flood labels or tune parameters to artificially inflate scores.
3. **Transparent Limitations:** The platform provides a scientifically defensible foundation that clearly delineates what can and cannot be demonstrated with currently available public satellite and weather data.

