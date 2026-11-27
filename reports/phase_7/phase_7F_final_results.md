# Phase 7F — Final Results & Performance Tables

**Document Identifier:** `reports/phase_7/phase_7F_final_results.md`  
**Authors:** Meteorological Verification Specialist & Statistical Validation Specialist  
**Status:** **`FINAL_AUDITED_NUMERICAL_RESULTS`**  

---

## 1. Master Results Summary Table

| Domain / Pipeline | Metric Name | Audited Value | Sample Size ($N$) | Evaluation Design | 95% Confidence Interval | Scientific Interpretation |
| :--- | :--- | :---: | :---: | :--- | :---: | :--- |
| **NWP Continuous Skill** | Mean Absolute Error (MAE) | **$18.64\text{ mm}$** | $256$ pairs | Pooled 16 stations $\times$ 16 dates | $[8.71, 30.64]\text{ mm}$ (Date-clustered) | Average error magnitude dominated by 2 convective deluge days. |
| **NWP Continuous Skill** | Root Mean Squared Error (RMSE) | **$33.19\text{ mm}$** | $256$ pairs | Pooled 16 stations $\times$ 16 dates | $[11.40, 49.57]\text{ mm}$ (Date-clustered) | Heavy penalty on unforecasted convective extremes. |
| **NWP Continuous Skill** | Mean Forecast Bias | **$-10.88\text{ mm}$** | $256$ pairs | Pooled 16 stations $\times$ 16 dates | $[-24.89, +1.27]\text{ mm}$ (Date-clustered) | Systematic under-prediction of monsoon precipitation volume. |
| **NWP Continuous Skill** | Pearson Correlation ($r$) | **$0.1421$** | $256$ pairs | Pooled 16 stations $\times$ 16 dates | $[-0.07, +0.50]$ (Date-clustered) | Weak linear correlation; spans zero under clustered uncertainty. |
| **NWP Continuous Skill** | Spearman Correlation ($\rho$) | **$0.3635$** | $256$ pairs | Pooled 16 stations $\times$ 16 dates | $p = 2.04 \times 10^{-9}$ (Two-tailed) | Moderate monotonic ranking skill between wet and dry regimes. |
| **NWP Contingency** | POD at $\ge 2.5\text{ mm}$ (Light Rain) | **$0.8837$** | $256$ pairs | Multi-threshold $2 \times 2$ table | — | High skill in capturing synoptic monsoon rain occurrence. |
| **NWP Contingency** | CSI at $\ge 2.5\text{ mm}$ (Light Rain) | **$0.7884$** | $256$ pairs | Multi-threshold $2 \times 2$ table | — | Solid threat score for light precipitation. |
| **NWP Contingency** | POD at $\ge 15.6\text{ mm}$ (Moderate) | **$0.4800$** | $256$ pairs | Multi-threshold $2 \times 2$ table | — | Detects roughly half of moderate rain events. |
| **NWP Contingency** | CSI at $\ge 15.6\text{ mm}$ (Moderate) | **$0.3947$** | $256$ pairs | Multi-threshold $2 \times 2$ table | — | Moderate threat score for routine monsoon rain. |
| **NWP Contingency** | POD at $\ge 64.5\text{ mm}$ (Heavy Rain) | **$0.0000$** | $256$ pairs | Multi-threshold $2 \times 2$ table | Hits=0, Misses=23 | Complete failure due to $750\text{ km}^2$ spatial scale smoothing. |
| **SAR Remote Sensing** | Apparent Water Sensitivity | **$76.92\%$** | $13$ positive cells | Cross-validation against ground truth | $10 / 13$ positive cells | Conflated with permanent lakes ($30.8\%$) and double bounce ($7.7\%$). |
| **SAR Remote Sensing** | True Specular Flood Sensitivity| **$38.46\%$** | $13$ positive cells | Specular drop outside lakes ($\Delta\sigma^0 < 0$) | $5 / 13$ positive cells | True flood water expansion sensitivity. |
| **SAR Remote Sensing** | Street Canyon Blindness | **$23.08\%$** | $13$ positive cells | Missed due to buildings & trees | $3 / 13$ positive cells | Total radar signal attenuation in narrow urban streets. |
| **Terrain Hydrology** | Static Routing Contributing Area| $1.0 - 186.0\text{ km}^2$| $1,170$ cells | Deterministic D8 flow accumulation | Exact | Delineates K-C Valley and Vrishabhavathi trunk channels. |
| **Terrain Hydrology** | Topographic Wetness Index (TWI) | $10.08 - 19.04$ | $1,170$ cells | $\ln(a / \tan \beta)$ | Exact | Identifies broad valley basins and lakebed depressions. |
| **Hydrological Validation** | Dynamic HIPI ROC-AUC | **$0.5604$** | $20$ cells ($13$ pos, $7$ neg)| ROC curve on verified ground truth | $[0.303, 0.817]$ (Hanley-McNeil) | Barely above chance ($0.500$); exploratory only. |
| **Software Verification** | Automated Pytest Suite | **$100\%$ PASS** | $109$ tests | Pytest across 16 test files | $0$ failures, $0$ errors | Full backward compatibility and regression protection. |
| **Manifest Integrity** | Cryptographic Checksum Match | **$100\%$ MATCH** | $68$ datasets | Bit-for-bit SHA-256 vs 5 manifests | $0$ mismatches | Zero data corruption across entire project lifecycle. |

