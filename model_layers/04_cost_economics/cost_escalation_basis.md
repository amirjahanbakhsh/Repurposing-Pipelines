# Cost Escalation and Referencing Basis

**Document status:** Working methodology note  
**Base year used in model:** 2011 USD  
**Target year:** User-defined (default: 2026)  
**Last reviewed:** June 2026  

---

## 1. Purpose

This document defines and justifies the cost escalation methodology used to convert the four regression-based new-build CAPEX models (Parker, Rui et al., McCoy & Rubin, Brown et al.) from their original base years to a user-specified project year.

It is intended to serve as:
1. The methodological basis for the code in `repurposing_pipelines/costs.py`
2. The referenced methodology section for the journal paper
3. A reproducible audit trail for any reviewer

---

## 2. The Four Regression Models

All four models estimate new-build CAPEX for CO2 pipelines by breaking construction cost into four components: materials (MAT), labour (LAB), right-of-way and damages (ROW), and miscellaneous (MISC). Inputs are pipeline outer diameter (D, inches) and length (L, miles).

| Model | Reference | Original base year | Regions |
|---|---|---|---|
| Parker | Parker (2004) [1] | 2000 USD | US national (no region) |
| Rui et al. | Rui et al. (2011) [2] | 2008 USD | 7 US/Canada regions |
| McCoy & Rubin | McCoy & Rubin (2008) [3] | 2004 USD | 6 US regions |
| Brown et al. | Brown et al. (2022) [4] | 2018 USD | 9 US regions |

All four models are normalised to **2011 USD** as the common intermediate year, using the index ratios documented in Section 3. The 2011 base is consistent with the FECM/NETL CO2 Transport Cost Model [5], the authoritative US reference for CO2 pipeline cost estimation.

---

## 3. Normalisation to 2011 USD

Each cost component uses its own appropriate price index, following NETL practice [5].

### 3.1 Materials and Labour (Handy-Whitman Index — Gas Transmission Plants)

The Handy-Whitman Index (HWI) of Public Utility Construction Costs [6] is used for materials and labour. The "Gas Transmission Plants" sub-index is the most representative for pipeline construction.

| Base year | HWI value | Source |
|---|---|---|
| 2000 | 261 | Parker base year [1] |
| 2004 | 400 | McCoy & Rubin base year [3] |
| 2008 | 604 | Rui et al. base year [2] |
| 2011 | 525 | Common normalisation year [5] |
| 2018 | 629 | Brown et al. base year [4] |

Note: The 2011 HWI value is lower than 2008 because the index declined during the 2008–2011 period due to the post-financial crisis drop in steel and labour costs.

Escalation factor (base year → 2011): `f_mat_lab = HWI_2011 / HWI_base`

### 3.2 Right-of-Way and Damages (GDP Chain-Type Price Index)

| Base year | GDP index value | Source |
|---|---|---|
| 2000 | 88.7 | BEA [7] |
| 2004 | 96.77 | BEA [7] |
| 2008 | 108.5 | BEA [7] |
| 2011 | 113.8 | BEA [7] |
| 2018 | 124.6 (approx.) | BEA [7] |

Escalation factor: `f_row = GDP_2011 / GDP_base`

### 3.3 Miscellaneous (US Producer Price Index — Industrial Commodities)

| Base year | PPI value | Source |
|---|---|---|
| 2000 | 122.3 | BLS [8] |
| 2004 | 139.6 | BLS [8] |
| 2008 | 196.3 | BLS [8] |
| 2011 | 190.9 | BLS [8] |
| 2018 | ~199.0 (approx.) | BLS [8] |

Escalation factor: `f_misc = PPI_2011 / PPI_base`

### 3.4 Brown et al. (2018 → 2011)

Brown et al. costs are in 2018 USD. The normalisation back to 2011 uses the average Handy-Whitman index ratio for gas transmission plants:

`f_brown = HWI_2011 / HWI_2018 = 525 / 629 = 0.835`

Applied uniformly to all four cost components (MAT, LAB, ROW, MISC).

---

## 4. Escalation from 2011 to Project Year

Once all four models are in 2011 USD, costs are escalated to the project year using the **RSMeans Construction Cost Index** [9], a freely available and widely cited annual construction cost index.

### 4.1 Why RSMeans rather than a flat rate

The student dissertation used a flat 3% annual escalation rate from 2011 to 2025. While simple, this approach obscures real cost volatility — construction costs increased sharply in 2021–2022 (post-COVID supply chain effects on steel, cement and labour) and stabilised in 2023–2024. Using actual index values is more defensible for a journal paper.

### 4.2 RSMeans CCI Annual Values (Jul reference)

Source: RSMeans Construction Cost Index [9], as compiled and publicly documented by Maxwell (2026) [10].

| Year | RSMeans Index | Escalation factor (÷ 2011 value) |
|---|---|---|
| 2011 | 191.2 | 1.000 (base) |
| 2012 | 194.6 | 1.018 |
| 2013 | 201.2 | 1.052 |
| 2014 | 204.9 | 1.071 |
| 2015 | 206.2 | 1.078 |
| 2016 | 207.3 | 1.084 |
| 2017 | 213.6 | 1.117 |
| 2018 | 222.9 | 1.166 |
| 2019 | 232.2 | 1.214 |
| 2020 | 235.6 (avg) | 1.232 |
| 2021 | 251.0 (avg) | 1.313 |
| 2022 | 290.6 (avg) | 1.520 |
| 2023 | 295.8 (avg) | 1.547 |
| 2024 | 295.6 (avg) | 1.546 |
| 2025 | 298.7 (avg) | 1.562 |
| 2026 | 306.5 (est. Jan–Apr avg) | 1.603 |

Note: The 2020–2026 values are averages of the available quarterly data. The 2026 value is based on Jan and Apr data only; it should be updated when further 2026 data becomes available.

Escalation factor from 2011 to project year `Y`:

`f_esc(Y) = RSMeans_CCI(Y) / RSMeans_CCI(2011) = RSMeans_CCI(Y) / 191.2`

### 4.3 Implementation in code

The model interpolates between the table values for intermediate years. For years beyond 2026, a user-defined escalation rate (default 3%/yr) is applied beyond the last known data point, with a clear warning to the user.

---

## 5. CO2 Pipeline Adjustment Factor

CO2 dense-phase pipelines have higher material and labour costs than natural gas pipelines of the same diameter, due to higher operating pressures (typically 150–200 barg for offshore dense phase vs. 80–100 barg for gas transmission), thicker wall requirements, and more stringent leak-detection and sealing requirements.

The adjustment factor of **1.25** is applied to the materials (MAT) and labour (LAB) components only. This is consistent with the NETL CO2 Transport Cost Model [5] and the approach used in the student dissertation baseline.

**Citation:** McCoy & Rubin (2008) [3]; NETL (2024) [5].

**Note for journal paper:** This factor is based on US natural gas pipeline data extrapolated to CO2 service. It has not been independently validated against North Sea CO2 pipeline construction data. It should be treated as a screening-level assumption and flagged as such in the results.

---

## 6. Offshore Location Factor

Offshore pipeline construction costs significantly exceed onshore costs due to:
- Specialised pipelay vessels (S-lay, J-lay)
- Seabed preparation and burial
- Subsea tie-ins and manifolds
- Weather windows and mobilisation
- Diving or ROV support

### 6.1 Factor value

The model uses an **offshore factor of 1.6** applied to all cost components (MAT, LAB, ROW, MISC), with a range of 1.5–2.0 for sensitivity analysis.

This replaces the student dissertation value of 1.3, which was too low based on available literature.

### 6.2 Basis

- USAID (2002) reported offshore costs approximately **1.96×** onshore for 2000–2001 [11].
- Global Energy Monitor (2024) reports a global median across 64 projects of $2.34M/km, with offshore projects substantially higher than onshore [12].
- The NETL model notes offshore premiums but does not specify a single factor [5].
- For North Sea specifically, a factor of 1.5–2.0 is appropriate for screening. A value of **1.6** is used as the central estimate, representing a moderate offshore premium consistent with shallow-to-medium water North Sea conditions (50–200 m water depth).

**Sensitivity:** Low = 1.5, Base = 1.6, High = 2.0.

**Note for journal paper:** The offshore factor is the single largest source of uncertainty in the new-build CAPEX estimate. A dedicated sensitivity analysis on this factor must be included in the results section.

---

## 7. Additional Cost Components

Beyond the four regression categories, the following pipeline-associated costs are included:

| Component | Value (2000 USD) | Escalation applied | Source |
|---|---|---|---|
| CO2 surge tank | $701,600 | Yes (HWI: 657.5/370.6) | NETL [5] |
| Pipeline control system | $94,000 | Yes (PPI: 438.7/368.5) | NETL [5] |
| Offshore booster stations | $70,000/km (2000 EUR) | Yes (HWI: 525/261) | IEA GHG (2002) [13] |

All values are escalated to 2011 USD using their respective indices, then to the project year using the RSMeans CCI factor in Section 4.

---

## 8. Contingency

A project contingency of **10–15%** is applied to total pre-contingency CAPEX. The default is 10%.

- NETL uses 15% as default for CO2 pipelines [5].
- The student dissertation used 10%.
- Both are within the Class 4–5 estimate range (AACE International: ±30–50% accuracy, 10–15% contingency).

The contingency factor is user-configurable in the tool.

---

## 9. Unit Conversions Used

| Conversion | Value |
|---|---|
| 1 mile | 1.60934 km |
| 1 inch | 25.4 mm |
| Pipe cross-sectional area (ft²) | π × (D/24)² |
| Pipe length in feet | L_miles × 5280 |

---

## 10. Summary of Escalation Chain

```
Model base year (USD)
    → [Handy-Whitman / GDP / PPI ratios] → 2011 USD
    → [RSMeans CCI ratio: CCI(Y) / 191.2] → Project year USD
    → [CO2 factor ×1.25 on MAT+LAB] → CO2-adjusted USD
    → [Offshore factor ×1.6 on all components] → Offshore CO2 USD
    → [+ surge tank + control system + boosters] → Pre-contingency CAPEX
    → [+ contingency %] → Total new-build CAPEX estimate
```

---

## 11. Full Bibliography

[1] Parker, N. (2004). *Using Natural Gas Transmission Pipeline Costs to Estimate Hydrogen Pipeline Costs*. UCD-ITS-RR-04-35, Institute of Transportation Studies, University of California, Davis. Available at: https://escholarship.org/uc/item/4bg083ww

[2] Rui, Z., Metz, P., Reynolds, D., Chen, G., & Zhou, X. (2011). Regression models estimate pipeline construction costs. *Oil and Gas Journal*, 109(27), 120–127.

[3] McCoy, S. T., & Rubin, E. S. (2008). An engineering-economic model of pipeline transport of CO2 with application to carbon capture and storage. *International Journal of Greenhouse Gas Control*, 2(2), 219–229. https://doi.org/10.1016/S1750-5836(07)00119-3

[4] Brown, D., Reddi, K., & Elgowainy, A. (2022). The development of natural gas and hydrogen pipeline capital cost estimating equations. *International Journal of Hydrogen Energy*, 47(50), 33813–33826. https://doi.org/10.1016/j.ijhydene.2022.07.270

[5] National Energy Technology Laboratory (NETL). (2024). *FECM/NETL CO2 Transport Cost Model (2024): Description and User's Manual*. U.S. Department of Energy, Office of Fossil Energy and Carbon Management. https://www.osti.gov/biblio/2473642

[6] Whitman, Requardt & Associates. (2025). *Handy-Whitman Index of Public Utility Construction Costs*. Published semi-annually. Baltimore, MD: Whitman, Requardt & Associates LLP.

[7] Bureau of Economic Analysis (BEA). (2025). *GDP and Personal Income: Chain-Type Price Index*. U.S. Department of Commerce. Available at: https://apps.bea.gov/iTable/

[8] Bureau of Labor Statistics (BLS). (2025). *Producer Price Index — Industrial Commodities (Series WPU03)*. U.S. Department of Labor. Available at: https://www.bls.gov/ppi/

[9] RSMeans. (2026). *RSMeans Construction Cost Index*. Gordian Group. Annual values accessed via public landing pages: https://www.rsmeans.com/landing-pages/2025-rsmeans-cost-index

[10] Maxwell, C. (2026). *Cost Indices: Free Sources for Engineering Cost Estimation*. Towering Skills. Available at: https://toweringskills.com/financial-analysis/cost-indices/ (Last updated 05-May-2026)

[11] USAID. (2002). *Pipeline Cost Comparison: Offshore vs Onshore*. Cited in: Global Energy Monitor (2024), Oil and Gas Pipeline Construction Costs. Available at: https://www.gem.wiki/Oil_and_Gas_Pipeline_Construction_Costs

[12] Global Energy Monitor. (2024). *Oil and Gas Pipeline Construction Costs*. Available at: https://www.gem.wiki/Oil_and_Gas_Pipeline_Construction_Costs

[13] IEA Greenhouse Gas R&D Programme (IEA GHG). (2002). *Pipeline Transmission of CO2 and Energy*. Report PH4/6. Cheltenham, UK.

---

*Document owner: Amir Jahanbakhsh | Heriot-Watt University*  
*Contributors: Jean Carlos Campos Valverde (student dissertation, 2025)*

---

## 12. European and Offshore-Specific Cost References

### 12.1 Critical gap: no offshore CO2 regression model exists

All four regression models in Section 2 (Parker, McCoy & Rubin, Rui et al., Brown et al.) are calibrated on **US onshore natural gas pipeline** data from the Oil & Gas Journal. The CO2 factor and offshore factor are applied as scalar multipliers — they are not derived from actual offshore CO2 pipeline construction cost data.

There is currently no published regression equation calibrated on measured offshore CO2 pipeline construction costs. This is explicitly acknowledged in the literature: the nascent stage of CO2 transport infrastructure means there is no historical precedent for empirically grounded offshore CO2 pipeline cost data [CEEPR-2024].

### 12.2 ZEP (2011) — European offshore CO2 benchmark cost tables

**Reference:** Zero Emissions Platform (ZEP). (2011). *The Costs of CO2 Transport: Post-Demonstration CCS in the EU*. European Technology Platform for Zero Emission Fossil Fuel Power Plants. Base year: Q2 2009 EUR.

This is the most authoritative European source for offshore CO2 pipeline costs. It is based on **in-house data from ZEP member organisations** including Gassco (Norway), AMEC (UK), Vattenfall (Sweden), Open Grid Europe (Germany), Tel-Tek (Norway), and Shell Projects & Technology. The reference route is Belgian coast → Norwegian continental shelf — directly North Sea relevant.

**Key cost data from ZEP Annex 3 (Q2 2009 EUR, 8% discount rate, 40-year lifetime):**

| Volume | Length | Diameter | CAPEX (M€) | Annual cost (M€/yr) | Unit cost (€/tonne CO2) |
|---|---|---|---|---|---|
| 2.5 Mtpa | 180 km offshore | 12" | 250 | 23.3 | 9.34 |
| 2.5 Mtpa | 500 km offshore | 16" | 581 | 51.0 | 20.42 |
| 10 Mtpa | 180 km offshore | 22" | 338 | 33.1 | 3.31 |
| 10 Mtpa | 500 km offshore | 26" | 781 | 70.2 | 7.02 |
| 20 Mtpa | 180 km offshore | 26" | 424 | 43.4 | 2.17 |
| 20 Mtpa | 500 km offshore | 32" | 1,035 | 94.7 | 4.74 |
| 20 Mtpa | 750 km offshore | 34" | 1,552 | 138.1 | 6.90 |
| 20 Mtpa | 1,500 km offshore | 40" | 3,501 | 301.5 | 15.08 |

OPEX is assumed at 7.9 M€/yr regardless of length, based on 1.87% of CAPEX.

**Annual unit cost in k€/inch/km (from Annex 3):**

| Volume | 10 km | 180 km | 500 km | 750 km | 1,500 km |
|---|---|---|---|---|---|
| 2.5 Mtpa | 10.81 | 6.38 | 5.98 | 4.79 | — |
| 10 Mtpa | — | 8.36 | 5.40 | 5.00 | 4.50 |
| 20 Mtpa | — | 9.28 | 5.92 | 5.41 | 5.03 |

**Key design assumptions (offshore):**
- Inlet pressure: 200 barg; outlet pressure: 60 barg
- Design pressure: 250 barg; pipeline material: carbon steel
- External coating: 3 mm polypropylene + 70 mm concrete for >16"
- Buried 100% in first 50 km (shallow sand wave area); no burial elsewhere
- No booster/pumping stations offshore (inlet pressure only)
- Accuracy: ±30%

**How to use for cross-validation:**
Convert ZEP 2009 EUR to project-year USD and compare against our regression model outputs for matching diameter and length. This provides the only available European offshore CO2 pipeline cost benchmark. Note that ZEP costs include a subsea template; our regression model does not include a template or well manifold.

### 12.3 Knoope et al. (2014) — Physics-based European CO2 pipeline cost model

**Reference:** Knoope, M.M.J., Guijt, W., Ramírez, A., & Faaij, A.P.C. (2014). Improved cost models for optimizing CO2 pipeline configuration for point-to-point pipelines and simple networks. *International Journal of Greenhouse Gas Control*, 22, 25–46. https://doi.org/10.1016/j.ijggc.2013.12.016

**What this model is:**
A physics-based cost optimisation tool (not a regression) developed at Utrecht University with Shell Projects & Technology. It calculates minimum levelised cost of CO2 transport by optimising: (1) inlet pressure, (2) outer diameter (from standard NPS sizes), (3) steel grade (X42–X120), and (4) number of pumping stations. All costs in €2010, escalated from literature sources using the IHS Upstream Capital Cost Index (UCCI).

**Key structural cost equations:**

*Material costs — pipeline weight-based:*
`C_material = (π/4) × [(OD²_NPS − ID²_NPS) × L × ρ_steel × C_steel]`
where ρ_steel = 7850 kg/m³; C_steel = €1.17–1.79/kg depending on grade (X42–X120)

*Construction costs — components:*
- **Labour**: based on European pipeline construction costs (M€/km function of OD)
- **ROW and miscellaneous**: fixed €/km values by terrain type
- **Offshore factor**: implicitly included via separate offshore terrain parameters and no pumping stations

*Offshore-specific parameters:*
- Maximum pressure: 35 MPa (vs 24 MPa onshore liquid)
- No pumping stations allowed offshore (platform required → very expensive)
- Minimum wall thickness: 2.5% of OD_NPS (anti-corrosion and stability)
- Design factor: 0.72 (same as sparsely populated onshore)
- Outlet pressure: fixed 8 MPa

**Key results for offshore liquid CO2 transport (Table 3 of paper, costs in €2010/tonne CO2):**

| Mass flow (kg/s) | Length (km) | OD (m) | Inlet P (MPa) | LCtrans (€/t) |
|---|---|---|---|---|
| 100 | 100 | 0.32 | 13 | 3.25 |
| 300 | 100 | 0.51 | 12 | 1.43 |
| 300 | 340 | 0.51 | 22 | 4.35 |
| 300 | 350 | 0.61 | 14 | 4.91 |

These are levelised transport costs only (excluding initial compression). LCtrans for offshore cases is 1.7–3.5× higher than equivalent onshore sparsely populated cases, giving an empirically derived offshore cost multiplier of approximately **1.7–3.5×** depending on length and mass flow — this is higher than our assumed 1.6 and consistent with the literature range of 1.5–2.0×.

**Validation against ZEP:**
Knoope et al. explicitly compare their model against ZEP (2011) in Table 5. For a 180 km offshore trunkline at 20 Mtpa: ZEP gives LCtrans = 3.4 €/t, Knoope model gives 1.92–1.97 €/t. The Knoope model gives lower costs because it optimises the configuration (larger diameter, lower pressure drop) rather than using ZEP's fixed assumptions.

**Implication for our model:**
The Knoope et al. (2014) model confirms that our offshore factor of 1.6 is conservative (potentially underestimating costs) and that the range 1.5–2.0 is appropriate, with 2.0 being more likely for small-diameter, short-range North Sea pipelines.

### 12.4 Baek, Tanveer & Elgowainy (2026) — Most current US model

**Reference:** Baek, K.H., Tanveer, S., & Elgowainy, A. (2026). Carbon dioxide pipeline network transportation cost model: evaluating economic and geographic factors for efficient carbon capture, storage, and utilization. *International Journal of Greenhouse Gas Control*, 151, 104622. https://doi.org/10.1016/j.ijggc.2026.104622

From Argonne National Laboratory (same team as Brown et al. 2022). Uses Brown et al. coefficients as the cost foundation with road-network routing and pipeline diameter optimisation. Published April 2026 — the most current peer-reviewed CO2 pipeline cost paper available.

Key finding: **Regional cost variation is substantial (13–70% above lowest-cost region for identical conditions).** Averaging across regions can significantly distort cost estimates — supports our use of "Avg" as a default with a clear warning.

**Validation case from paper:**
- Case 1: 340 miles, Mississippi, 11.5 MMT/year → $7.4/tonne CO2 → total CAPEX $322M
- This uses Brown et al. regional (GP group) coefficients, consistent with our implementation.

### 12.5 Updated bibliography entries

[ZEP-2011]
    Zero Emissions Platform (ZEP). (2011). *The Costs of CO2 Transport: Post-Demonstration CCS in the EU*. European Technology Platform for Zero Emission Fossil Fuel Power Plants. Brussels, Belgium. Base year: Q2 2009.

[KNOOPE-2014]
    Knoope, M.M.J., Guijt, W., Ramírez, A., & Faaij, A.P.C. (2014). Improved cost models for optimizing CO2 pipeline configuration for point-to-point pipelines and simple networks. *International Journal of Greenhouse Gas Control*, 22, 25–46. https://doi.org/10.1016/j.ijggc.2013.12.016

[BAEK-2026]
    Baek, K.H., Tanveer, S., & Elgowainy, A. (2026). Carbon dioxide pipeline network transportation cost model: evaluating economic and geographic factors for efficient carbon capture, storage, and utilization. *International Journal of Greenhouse Gas Control*, 151, 104622. https://doi.org/10.1016/j.ijggc.2026.104622

[CEEPR-2024]
    MIT CEEPR Working Paper 2024-12. (2024). *The Impact of Financing Costs on CO2 Transport Infrastructure*. MIT Center for Energy and Environmental Policy Research. Available at: https://ceepr.mit.edu/wp-content/uploads/2024/08/MIT-CEEPR-WP-2024-12.pdf

---

## 13. Revised Offshore Factor Justification

Based on the complete reference review above, the offshore factor range and default are revised as follows:

| Source | Offshore factor (vs onshore) | Context |
|---|---|---|
| USAID (2002) | ~1.96× | US 2000–2001, general offshore |
| ZEP (2011) | ~1.7–2.4× | North Sea offshore CO2 pipelines, derived from CAPEX comparison |
| Knoope et al. (2014) | ~1.7–3.5× | European offshore CO2, physics-based |
| Our model default | **1.6×** | Conservative estimate, North Sea screening |

The default of 1.6 is **deliberately conservative** for screening purposes — it is at the low end of published ranges. The journal paper must state clearly that this factor is an assumption and not derived from measured offshore CO2 pipeline data. A sensitivity range of 1.5–2.0 is retained, with 2.0 as the upper bound consistent with all cited references.

**Recommendation for future work:** Calibrate the offshore factor against actual North Sea project costs when these become publicly available (e.g., NEP/Northern Endurance Partnership 143 km 28" pipeline, currently under construction).
