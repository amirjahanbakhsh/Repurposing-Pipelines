# Journal Paper Draft

Date: 2026-06-13

Draft status: working manuscript text. This file is intended to become a journal-paper style manuscript. It should be updated as the model, validation, results and references mature.

## Working Title

An evidence-aware screening framework for repurposing offshore hydrocarbon pipelines for carbon dioxide transport

## Short Title

Evidence-aware screening for CO2 pipeline repurposing

## Highlights

- A modular screening framework is developed for offshore pipeline repurposing for CO2 transport.
- The method screens public pipeline records while keeping data gaps and assumptions visible.
- Engineering, work-scope, cost and life cycle assessment layers are linked through traceable module outputs.
- A repurposing gate separates mathematical feasibility from evidence readiness for reuse.
- Scientific validation is separated from internal development checks and based on external tools, references and sensitivity analysis.

## Abstract

Repurposing existing offshore hydrocarbon pipelines could reduce the cost, material demand and delivery time of carbon capture and storage infrastructure. However, reuse is not a simple flow-capacity question. A pipeline that appears suitable from diameter, length and pressure data may still require evidence on condition, wall thickness, corrosion risk, CO2 phase behaviour, material compatibility, inspection history, cleaning, drying and modification scope before it can be considered a credible reuse candidate.

This study develops a transparent and modular screening framework for assessing offshore pipeline repurposing for CO2 transport. The framework uses public pipeline data, starting with the UK NSTA offshore pipeline dataset, and links sequential modules for data quality, CO2 transport capacity, corrosion screening, wall-thickness and remaining-life screening, repurposing evidence gating, refurbishment work-scope, cost screening and conventional life cycle assessment. Each module produces auditable outputs, including assumptions, warnings, source labels and downstream links to later modules.

The main methodological contribution is an evidence-aware decision structure. Instead of producing a single black-box suitability score, the framework distinguishes between technical possibility, evidence maturity and next data needs. This allows candidate pipelines to be ranked not only by apparent reuse potential, but also by the strength of the evidence behind that result and the additional inspection or engineering work required. The framework is designed for early-stage screening and portfolio comparison, not final design approval.

Internal software-development comparisons were used only to check implementation consistency and are excluded from scientific validation. Formal validation is defined separately and will use external property tools, cost tools, LCA databases, published case studies, physical consistency checks, sensitivity analysis and expert review.

## Keywords

Carbon capture and storage; CO2 transport; pipeline repurposing; offshore pipelines; screening model; life cycle assessment; refurbishment cost; evidence traceability

## 1. Introduction

Carbon capture and storage (CCS) requires large-scale CO2 transport infrastructure. In offshore regions with mature oil and gas activity, existing hydrocarbon pipelines may offer a potential route to faster and lower-material CCS deployment. Reusing pipelines may avoid part of the steel production, offshore installation, seabed disturbance and capital expenditure associated with new-build CO2 pipelines.

At the same time, pipeline reuse is technically uncertain. Existing pipelines were designed, operated and maintained for their original hydrocarbon service, not necessarily for dry or dense-phase CO2 transport. Change of product can affect corrosion risk, operating pressure, fracture behaviour, decompression behaviour, impurities, water control, seals, valves, coatings and monitoring requirements. Therefore, a robust screening method must do more than calculate whether a pipe is large enough.

The practical challenge is that early-stage screening usually relies on incomplete public information. Public datasets may report pipeline length, diameter, status and fluid, but may omit wall thickness, material grade, inspection records, certificate history, corrosion allowance, repair history or CO2 specification. A useful screening method must therefore combine engineering calculations with explicit data-quality labelling and clear uncertainty handling.

This paper develops an evidence-aware screening framework for offshore pipeline repurposing for CO2 transport. The framework is designed to rank multiple candidate pipelines, identify evidence gaps, connect engineering decisions to cost and life cycle assessment (LCA), and provide a transparent basis for selecting cases that justify deeper engineering study.

## 2. Research Gap

Existing work on pipeline repurposing shows that reuse decisions are case-specific and must consider requalification, integrity, materials, inspection evidence and operational limits. Recent industrial and conference studies emphasise CO2 specification, gas-phase versus dense-phase operation, water control, fracture risk, cleaning, drying, inspection and integrity management.

However, early-stage tools often remain incomplete in three ways.

First, engineering screening, cost estimation and LCA are often treated separately. This can create inconsistent assumptions. For example, a cost model may assume refurbishment work that is not represented in the LCA model, or an LCA comparison may assume reuse without accounting for cleaning, drying, inspection or replacement steel.

Second, missing evidence is often hidden inside assumptions. In practice, the difference between a measured wall thickness, a reported wall thickness and an assumed wall thickness can strongly affect the credibility of the result. A screening method should make that difference visible.

Third, single-case studies may not support portfolio decisions. CCS infrastructure planning needs to compare many assets, identify promising candidates and prioritise the next data-acquisition steps.

## 3. Contribution

The contribution of this study is a modular, auditable and evidence-aware screening framework for pipeline repurposing. The framework contributes:

- a public-data workflow for screening offshore pipeline records;
- a traceable input and output structure across all model layers;
- a repurposing gate that separates technical feasibility from evidence readiness;
- a quantified refurbishment work-scope layer that links engineering checks to cost and LCA;
- a conventional LCA structure that can use public screening factors first and licensed database factors later;
- a validation strategy that separates internal code checks from scientific validation.

The novelty is not a single new equation. The novelty is the integration of engineering screening, evidence confidence, decision gating, cost, LCA and traceability into one transparent workflow.

## 4. Methodology Overview

The framework is organised as a sequence of modules. Each module can run independently, but its outputs are saved and passed to later modules when required.

```text
pipeline data
  -> data quality and assumptions
  -> CO2 capacity screening
  -> corrosion screening
  -> wall-thickness and remaining-life screening
  -> repurposing evidence gate
  -> quantified refurbishment work-scope
  -> cost screening
  -> pre-LCA decision gate
  -> conventional LCA screening
  -> validation and reporting
```

This structure prevents the model from behaving as a black box. A result is not stored only as "pass" or "fail"; it is stored together with the data used, the assumptions made, the evidence quality, the warning messages and the references supporting the logic.

The framework is intended for early-stage screening. It does not replace detailed design, regulatory approval, operator requalification, fracture assessment, inspection planning or expert integrity review.

## 5. Data Basis

The first data source is the UK NSTA offshore pipeline dataset. The screening dataset includes model-ready hydrocarbon pipeline records with sufficient information to support initial comparison. Key fields include pipeline number, name, status, fluid, length, internal diameter, wall thickness, maximum operating pressure and start date where available.

Each important value receives a source and quality label. The current labels include reported, derived, calculated, assumed and missing. This allows the model to distinguish between evidence and assumptions.

Goldeneye is treated as a known CCS-relevant case context because it has appeared in previous UK CCS work. However, Goldeneye public and project-derived data contain gaps and assumptions. Therefore, it is used as a traceable case-study scenario rather than as proof that the model is scientifically valid.

## 6. Engineering Screening

The engineering screening layer estimates whether a pipeline has plausible CO2 transport capacity under selected operating assumptions. It uses pipeline geometry, length, pressure, temperature and CO2 property assumptions to estimate annual transport capacity and compare this with the required design flow.

The corrosion layer is currently a screening-level dry-CO2 check. It flags water and dew-point evidence gaps, water specification exceedance and conservative corrosion-rate concerns. It is not a detailed corrosion prediction model.

The integrity layer estimates remaining wall-thickness margin and remaining life using low, base and high uncertainty cases. Wall-thickness uncertainty is applied to all pipelines, not only to Goldeneye. This is important because public pipeline datasets do not always provide direct evidence for current wall thickness or minimum allowable wall basis.

## 7. Repurposing Evidence Gate

The repurposing gate is the main decision layer. It asks whether a pipeline is only mathematically possible or whether the evidence is mature enough to justify moving toward detailed reuse assessment.

The gate checks CO2 phase, CO2 specification, water and impurity evidence, wall-thickness evidence, inspection evidence, material and certificate evidence, fracture or decompression needs, component compatibility, cleaning and drying needs, monitoring needs and potential modification work.

The gate outputs a status, evidence score, evidence gaps, showstoppers, cited references and work-scope items. These outputs are intentionally conservative. A pipeline with strong apparent capacity can still be marked marginal or insufficient if important evidence is missing.

This gate follows the direction of recent requalification literature and industrial practice, where product change is treated as a formal requalification problem rather than simple reuse.

## 8. Cost And LCA Integration

The cost and LCA layers use the same quantified refurbishment work-scope. This avoids inconsistent assumptions between economic and environmental assessment.

The work-scope module converts gate outputs into activity rows. Examples include inspection per kilometre, cleaning and drying per kilometre, engineering studies, monitoring plans and replacement steel mass. These activity rows then connect to unit-cost factors and LCA impact factors.

The cost model currently supports screening factors and private factor files. Public screening factors allow early comparison, but they are not final contractor estimates.

The LCA model is conventional process-based LCA. The first comparison is reuse of an existing offshore pipeline versus construction of a new equivalent offshore CO2 pipeline. The initial functional unit is transport of 1 tonne of CO2 through the selected route. Public screening factors allow early model operation, while final publishable LCA results require licensed database factors or equivalent documented impact factors.

## 9. Validation Strategy

Scientific validation is separated from internal development checks.

During development, earlier internal project outputs were used only to check that the new code was not grossly inconsistent with the project starting point. This is a software-quality check. It is not treated as independent validation and is not used as scientific evidence that the model is correct.

Formal validation will be based on:

- unit tests and arithmetic checks for implemented equations;
- comparison of CO2 property assumptions with external property tools such as CoolProp or REFPROP;
- comparison of cost outputs with recognised CO2 transport cost tools or documented cost studies;
- comparison of LCA inventory and impact calculations with ecoinvent, openLCA, Brightway or documented equivalent workflows;
- comparison of model logic with published and industrial repurposing case studies;
- sensitivity analysis for uncertain wall thickness, corrosion rate, refurbishment work and LCA factors;
- expert review of assumptions, limits and interpretation.

This validation structure avoids the circular problem of validating a new model using outputs generated by an earlier internal implementation.

## 10. Expected Results Structure

The results section will report:

- completeness of the public pipeline dataset;
- ranked screening results for the model-ready pipeline portfolio;
- selected case-study results for known CCS-relevant candidates;
- sensitivity of decisions to wall thickness, corrosion rate, pressure and refurbishment scope;
- cost comparison between reuse and new-build screening cases;
- LCA comparison between reuse and new-build screening cases;
- evidence gaps and value-of-information priorities.

The results should be reported with clear status labels. A result based on public screening factors should not be presented as a final investment-grade result. A result based on private, traceable and validated factors can be presented with stronger confidence.

## 11. Limitations

The current framework is a screening method, not a replacement for detailed pipeline requalification. It does not yet include full fracture propagation modelling, full transient depressurisation, full impurity phase-equilibrium modelling, detailed vessel scheduling, final contractor cost estimates or final verified ecoinvent impact factors.

The framework also depends on the quality of available input data. Where public data are incomplete, the model reports uncertainty and evidence gaps rather than hiding them.

## 12. Planned Manuscript Development

The next manuscript steps are:

1. Insert final NSTA dataset completeness statistics.
2. Insert equations and parameter tables for each implemented module.
3. Convert source IDs into the target journal reference style.
4. Add validation results once external checks are completed.
5. Add final figures for the model architecture, gate logic and portfolio screening results.

## Current Source Base

The current reference base is stored in `references/literature_index.csv`. Key source IDs include:

- `REF_PETERHEAD_GOLDENEYE_2014`
- `REF_MAHMOUD_DODDS_2022`
- `REF_OSTBY_TORBERGSEN_RONEID_LEINUM_2022_CO2_REQUALIFICATION`
- `REF_TORBERGSEN_LEINUM_RONEID_2025_GAS_PHASE_CO2_REQUALIFICATION`
- `REF_MONSMA_MURRAY_2026_GAS_PHASE_CO2_REPURPOSING`
- `REF_KUMAR_LOWERY_PASSUCCI_2025_ENI_LIVERPOOL_BAY_IMR`
- `REF_YUSOF_AZIZ_2025_PETRONAS_DENSE_PHASE_CO2_REPURPOSING`
- `REF_DALONZO_BUSCO_ELVIRA_CHERUBINI_2025_CO2_IMR`
- `REF_BURKINSHAW_GALLON_CARVELL_HUSSAIN_2024_HYDROGEN_DATA_EVIDENCE`
- `REF_KASS_ET_AL_2023_MATERIAL_COMPATIBILITY`
- `REF_BOGS_ABDELSHAFY_WALTHER_2025_MINIMUM_REGRET_CO2_NETWORKS`
- `REF_ANVARI_ET_AL_2026_CO2_NETWORK_SIMULATION`
- `REF_KUMAR_ROSEN_ESQUIVEL_2025_CO2_RICH_MIXTURE_TRANSPORT`
