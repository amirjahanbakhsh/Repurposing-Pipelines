# Independent Validation Report

Generated: 2026-06-09T22:57:14+00:00

Model validation version: `independent_validation_v0.1`

## Purpose

This report starts the full independent validation workflow.

It separates three things:

- reproduction of the student/dissertation outputs;
- independent checks against external references;
- engineering issues that need expert review.

## Plain Summary

| Area | Result |
| --- | --- |
| CO2 properties | `information: 2, pass: 6` |
| Capacity | `pass: 4` |
| Integrity wall thickness | `review_required: 2` |
| Cost arithmetic | `pass: 2` |

Main finding:

> The Goldeneye CO2 property values are close to CoolProp, but the integrity minimum-wall-thickness basis needs review. A simple Barlow pressure sanity check gives a higher minimum wall thickness than the dissertation/poster values.

## CO2 Property Validation

Reference: CoolProp pure CO2 at the model average pipeline pressure and transport temperature.

Acceptance targets:

- density within 1%;
- viscosity within 3%;
- compressibility factor within 1%.

| Scenario | Parameter | Model | CoolProp | Abs diff % | Status |
| --- | --- | --- | --- | --- | --- |
| goldeneye_dissertation | density_kg_per_m3 | 904.013 | 908.286 | 0.470 | pass |
| goldeneye_dissertation | viscosity_micro_pa_s | 92.652 | 94.881 | 2.349 | pass |
| goldeneye_dissertation | compressibility_factor_z | 0.204 | 0.203 | 0.478 | pass |
| goldeneye_poster | density_kg_per_m3 | 904.013 | 908.286 | 0.470 | pass |
| goldeneye_poster | viscosity_micro_pa_s | 92.652 | 94.881 | 2.349 | pass |
| goldeneye_poster | compressibility_factor_z | 0.204 | 0.203 | 0.478 | pass |

Plain meaning:

The student/rebuilt CO2 property values are close enough for first-pass pure-CO2 screening. This does not yet validate impurity effects.

## Capacity Validation

| Scenario | Check | Model Mtpa | Reference Mtpa | Diff % | Status |
| --- | --- | --- | --- | --- | --- |
| goldeneye_dissertation | implementation_arithmetic_check | 9.131 | 9.131 | 0.000 | pass |
| goldeneye_dissertation | independent_property_sensitivity | 9.131 | 9.153 | -0.238 | pass |
| goldeneye_poster | implementation_arithmetic_check | 9.968 | 9.968 | 0.000 | pass |
| goldeneye_poster | independent_property_sensitivity | 9.968 | 9.992 | -0.238 | pass |

Plain meaning:

The arithmetic reproduces the equation. Replacing the student Z factor with CoolProp changes Goldeneye capacity by less than 1%, so property uncertainty is not the main issue for this case.

This still does not prove the selected capacity equation is the best engineering model. That needs comparison with external tools such as SCO2T or NETL where a like-for-like case can be built.

## Integrity Wall-Thickness Sanity Check

Reference: simple Barlow pressure check using X-grade SMYS and an assumed design factor of 0.72.

| Scenario | Student min wall mm | Barlow min wall mm | Student life years | Barlow life years | Status |
| --- | --- | --- | --- | --- | --- |
| goldeneye_dissertation | 6.230 | 10.230 | 77.940 | 37.938 | review_required |
| goldeneye_poster | 6.440 | 10.230 | 24.550 | 5.599 | review_required |

Plain meaning:

This is the biggest validation warning so far. The dissertation/poster minimum wall thickness is lower than the simple pressure sanity check. If the Barlow basis is appropriate, the remaining life becomes much shorter, especially for the poster case.

This does not mean the student is definitely wrong. It means we must verify:

- the exact pressure basis;
- whether outside diameter was used correctly;
- pipe grade and allowable stress;
- design factor;
- corrosion allowance;
- inspection and requalification rules.

Until this is resolved, integrity must remain `screening_unvalidated`.

## Cost Arithmetic Validation

| Scenario | Calculated total USD | Reported total USD | Diff USD | Status |
| --- | --- | --- | --- | --- |
| goldeneye_dissertation | 228,500,811 | 228,500,812 | -1 | pass |
| goldeneye_poster | 228,500,811 | 228,500,812 | -1 | pass |

Plain meaning:

The cost arithmetic is internally consistent. This only checks the sum and contingency. It does not yet validate whether the cost model itself is appropriate.

Next independent cost validation should use NETL CO2_T_COM.

## Current Validation Status

| Module | Status | Meaning |
| --- | --- | --- |
| CO2 properties | first independent pass | Pure CO2 values pass against CoolProp for Goldeneye conditions. |
| Capacity | arithmetic pass, external model pending | Code equation is reproducible; external transport-model comparison still needed. |
| Integrity | review required | Minimum wall basis is not yet defensible. |
| Cost | arithmetic pass, external model pending | Arithmetic is correct; NETL cost validation still needed. |
| LCA | not started | Needs functional unit and ecoinvent mapping. |
| Wells | not started | Needs well data and integrity screening logic. |

## Output Files

- `data/validation/co2_property_validation.csv`
- `data/validation/capacity_validation.csv`
- `data/validation/integrity_barlow_sanity_check.csv`
- `data/validation/cost_arithmetic_validation.csv`

## Next Validation Actions

1. Resolve the Goldeneye minimum wall thickness formulation.
2. Build a like-for-like NETL CO2_T_COM cost case.
3. Build a like-for-like SCO2T or NETL transport capacity case.
4. Add the first LCA inventory skeleton after the pre-LCA gate.
