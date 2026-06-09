# Independent Validation Plan

Date: 2026-06-09

## Purpose

This document defines how we will prove the model is technically credible.

Important rule:

> Reproducing the dissertation or poster is not independent validation, because those outputs came from the student code.

So we will use two separate labels:

- `reproduction`: our model matches the student/dissertation result;
- `independent_validation`: our model matches an external source, standard, published example, reference software, or independently checked dataset.

Only independent validation can support a claim that our model is technically accurate.

## Validation Levels

| Level | Meaning | Example |
| --- | --- | --- |
| Level 0: code check | The code runs and unit tests pass | Unit conversion tests pass |
| Level 1: reproduction | We can reproduce student/dissertation outputs | Goldeneye gives the same capacity as the poster |
| Level 2: independent benchmark | We match external references | CO2 density matches REFPROP or CoolProp |
| Level 3: expert review | A domain expert reviews assumptions and limits | Integrity basis checked against pipeline requalification guidance |

Current position:

- Our code quality and traceability are already stronger than the student notebooks.
- Our technical accuracy is not yet proven.
- Each module should remain marked as `screening_unvalidated` until it passes Level 2.

## Module Validation Matrix

| Module | Independent source | What we validate | Initial pass target |
| --- | --- | --- | --- |
| Data extraction | NSTA source data, NSTA metadata, operator/public records | record counts, IDs, units, duplicate features, completeness | pipeline IDs and key fields match source records; missing data clearly labelled |
| Assumption register | dissertation, poster, student GeoJSON, NSTA, operator sources | source of every assumed value | every value has source, quality, and confidence label |
| CO2 properties | NIST REFPROP, CoolProp, NIST tables where available | density, viscosity, Z factor, phase state | density within about 1%; viscosity within about 3%; phase state agrees |
| Hydraulics/capacity | published McCoy and Rubin examples, independent hand calculations, external CO2 transport tools where available | mass flow, Reynolds number, pressure basis, unit conversion | formula reproduction within 1%; external benchmark difference explained |
| Integrity/wall thickness | ASME/API/DNV/ISO pipeline guidance and independent hand calculations | minimum wall thickness, inside/outside diameter basis, pressure basis | exact unit consistency; no pass if inspection data is missing |
| Corrosion | NORSOK M-506 examples and CO2 pipeline stream-quality guidance | pH, fugacity, shear stress, corrosion rate, future CO2 corrosion assumptions | benchmark cases match; future CO2 corrosion labelled as assumption if not modelled |
| Cost | Parker, Rui, McCoy and Rubin, Brown original examples; NETL CO2 transport model where available | material, labour, ROW, miscellaneous, booster, escalation, contingency | reproduce published examples; currency/year basis fully traceable |
| Pre-LCA gate | engineered test cases and manual decision review | pass, marginal, fail, insufficient data logic | all artificial cases give expected decision |
| LCA | ISO 14040/14044, ecoinvent, Brightway or openLCA | functional unit, system boundary, inventory, impact method, uncertainty | same simple case agrees across calculation route; ecoinvent version recorded |
| Wells module | NSTA well data, completion/decommissioning records, well integrity guidance | well status, age, depth, abandonment, integrity risk | no reuse recommendation without well integrity evidence |
| Interface | command-line model outputs and saved reports | UI outputs equal model outputs | same input gives same result in CLI, report, and app |

The detailed tracking table is stored in `data/validation/independent_validation_matrix.csv`.

The detailed source register is stored in `data/validation/validation_source_register.csv` and explained in `docs/validation_source_register.md`.

The first executable validation report is stored in `reports/independent_validation_report.md`.

## Module Notes

### 1. Data Validation

Data validation must come before technical validation. A correct equation with poor data still gives a poor answer.

Checks needed:

- confirm NSTA pipeline IDs and names;
- confirm units for diameter, length, pressure, wall thickness, and start date;
- separate real source data from assumptions;
- compare student 27-pipeline GeoJSON against the full NSTA extraction;
- flag suspicious fields, especially repeated wall thickness or zero maximum operating pressure;
- keep Goldeneye as a benchmark scenario, not as a clean NSTA record.

### 2. CO2 Property Validation

The student used a detailed property route, but it was not independently checked. We should validate our property values before trusting capacity results.

Validation cases should include:

- low-pressure gas CO2;
- near-critical CO2;
- dense-phase CO2;
- high-pressure liquid-like CO2;
- Goldeneye operating point;
- one sensitivity case with impurities, when mixture capability is added.

Initial independent references:

- NIST REFPROP;
- CoolProp;
- NIST data tables where available.

### 3. Hydraulics And Capacity Validation

The capacity model should be validated in two steps:

1. Check the equation and units with independent hand calculations.
2. Compare selected cases with external CO2 transport tools or published examples.

Important checks:

- inlet pressure must be higher than outlet pressure;
- pressure must be absolute where required;
- inside diameter must be used for flow;
- roughness and friction factor basis must be explicit;
- temperature and phase assumptions must be stated;
- impurities must be flagged as outside the current simple pure-CO2 model.

### 4. Integrity And Corrosion Validation

This is the highest-risk technical area.

The current integrity model is a screening calculation. It must not be presented as a full requalification model.

Independent validation needs:

- minimum wall thickness check with correct pressure, diameter, material grade, and design factor;
- distinction between outside diameter and inside diameter;
- inspection data requirement;
- historical corrosion and future CO2 corrosion treated separately;
- NORSOK M-506 benchmark checks if we use NORSOK-style corrosion;
- clear warning where CO2 stream quality, free water, impurities, weld condition, dents, cracks, and fracture control are unknown.

### 5. Cost Validation

The student code contains useful cost models, but cost validation must be stricter than code reproduction.

Checks needed:

- reproduce each original cost paper example where possible;
- record base year, escalation index, currency, and geography;
- keep new-build CAPEX separate from reuse cost;
- add uncertainty ranges;
- compare against NETL CO2 transport cost tools if accessible;
- do not use one single cost number as a decision without uncertainty.

### 6. LCA Validation

LCA should be added after the pre-LCA gate.

Independent LCA validation needs:

- ISO 14040/14044-compliant goal and scope;
- functional unit, e.g. "transport 1 MtCO2 per year over X years";
- clear comparison:
  - reuse existing pipeline;
  - build new equivalent CO2 pipeline;
- ecoinvent dataset names and version recorded;
- Brightway or openLCA calculation route recorded;
- sensitivity tests for steel mass, construction activity, refurbishment, electricity, and lifetime.

LCA should answer:

> What environmental impact is avoided, added, or shifted by reusing this asset instead of building a new one?

## First Validation Sprint

Recommended order:

1. Validate CO2 properties for Goldeneye operating conditions against CoolProp first.
2. Validate the capacity equation and unit conversions using the same Goldeneye inputs.
3. Create a Goldeneye assumption register with source and confidence for every value.
4. Validate cost model arithmetic and escalation before comparing with NETL tools.
5. Define the integrity validation boundary: screening only until inspection/requalification evidence exists.

This gives us a clean technical foundation before we build more interface features.

## External Sources To Track

| Source | Role in validation |
| --- | --- |
| [NIST REFPROP](https://www.nist.gov/srd/refprop) | Primary reference for thermodynamic and transport properties |
| [CoolProp](https://coolprop.org/) | Open-source property benchmark, easier to automate in Python |
| [ISO 27913:2024](https://www.iso.org/standard/84840.html) | CO2 pipeline transportation requirements and recommendations |
| [ISO 14040](https://www.iso.org/standard/37456.html) and [ISO 14044](https://www.iso.org/standard/38498.html) | LCA principles, framework, requirements, and guidelines |
| [ecoinvent](https://ecoinvent.org/) | LCA inventory datasets |
| [Brightway](https://docs.brightway.dev/en/latest/) | Python-native LCA calculation framework |
| [openLCA](https://www.openlca.org/) | Independent LCA software for cross-checking |
| [NETL CO2_T_COM 2024](https://www.osti.gov/biblio/2473642) | Independent cost benchmark for liquid-phase CO2 pipeline transport |
| NORSOK M-506 | Corrosion benchmark if official examples/spreadsheets are available |

## Current Decision

We should not claim:

> our model is more accurate than the student model.

We can claim:

> our model is more complete, traceable, testable, and suitable for independent validation.

After the validation matrix is completed, we can make stronger accuracy claims module by module.
