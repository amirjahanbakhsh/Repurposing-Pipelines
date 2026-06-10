# Independent Validation Report

Generated: 2026-06-10T09:39:17+00:00

Model validation version: `independent_validation_v0.2`

## Purpose

This report starts the full independent validation workflow.

It separates three things:

- reproduction of the student/dissertation outputs;
- independent checks against external references;
- engineering issues that need expert review.

## Plain Summary

| Area | Result |
| --- | --- |
| NSTA data extraction | `data_gap_confirmed: 1, pass: 6` |
| Assumption traceability | `pass: 3` |
| Assumption evidence register | `external_benchmark_needed: 2, first_independent_pass: 1, not_implemented: 1, review_required: 2, validated_for_screening: 1, visible_but_needs_source_upgrade: 1` |
| CO2 properties | `information: 2, pass: 6` |
| Capacity | `pass: 4` |
| Integrity wall thickness | `review_required: 2` |
| Cost arithmetic | `pass: 2` |
| Pre-LCA gate | `pass: 4` |
| ecoinvent data mapping | `blocked_by_data_access: 1` |
| LCA workbook review | `blocked_by_data_access: 1` |
| LCA method references | `future_reference: 4, inventory_template: 1, local_data_source: 1, method_reference: 5` |
| LCA model input CSVs | `pass: 4` |
| Overall module status | `arithmetic_pass_external_pending: 2, automated_pass: 1, blocked_by_data_access: 1, first_independent_pass: 1, not_implemented: 2, review_required: 3, validated_for_screening: 4` |

Main finding:

> The Goldeneye CO2 property values are close to CoolProp, but the integrity minimum-wall-thickness basis needs review. A simple Barlow pressure sanity check gives a higher minimum wall thickness than the dissertation/poster values.

Important boundary:

> This report removes vague pending labels, but it does not claim full engineering approval. Items marked `review_required`, `external_benchmark_needed`, `blocked_by_data_access`, or `not_implemented` are not validated.

## Overall Module Status

| Module | Status | Remaining limitation | Next action |
| --- | --- | --- | --- |
| data_extraction | validated_for_screening | source data values are not independently verified against operator records | spot-check priority pipelines against operator/public documents |
| assumption_register | validated_for_screening | many values remain assumptions rather than operator-confirmed data | replace Goldeneye and NSTA defaults with project-specific evidence |
| co2_properties | first_independent_pass | REFPROP and impurity/mixture validation still needed | add REFPROP or NIST table cross-check when available |
| hydraulics_capacity | arithmetic_pass_external_pending | external transport model comparison still needed | build like-for-like SCO2T or NETL case |
| integrity_wall_thickness | review_required | not a full requalification calculation | confirm correct design code, pressure basis, diameter basis, SMYS, and design factor |
| corrosion | review_required | not a calibrated NORSOK/DNV corrosion model and does not model impurities, pH, shear stress, or local free water | replace placeholder water/corrosion defaults with project stream-quality evidence and specialist model review |
| future_co2_integrity | review_required | free water, impurities, fracture, defects, and weld condition are not modelled | define stream-quality and inspection-data gates before allowing pass |
| cost | arithmetic_pass_external_pending | NETL CO2_T_COM and original literature examples still needed | build NETL CO2_T_COM 2024 benchmark input sheet |
| pre_lca_gate | automated_pass | gate thresholds may evolve when LCA and integrity modules mature | keep gate tests updated as modules are added |
| lca | validated_for_screening | proxy factors are open screening assumptions, not final ecoinvent/Brightway impact results | use the proxy for ranking, then run full ecoinvent/Brightway LCA for shortlisted pipelines |
| lca_data | blocked_by_data_access | final dataset choice needs LCA review and licensed database access on the modelling machine | use mapping file to build a Brightway/openLCA inventory skeleton |
| lca_calculation | validated_for_screening | licensed-database calculation is not implemented yet | choose Brightway first for ecoinvent calculation, then cross-check with openLCA |
| wells_repurposing | not_implemented | well data and integrity rules are not loaded | define well fields and a separate well integrity gate |
| interface | not_implemented | UI cannot be validated until it is built | when UI starts, test that app outputs equal CLI/report outputs |

Plain meaning:

There is no hidden pending work in this table. Each module has a clear state. Some modules are validated for screening, some need review, and some cannot be validated yet because they are not built or need external/licensed evidence.

## NSTA Data Extraction Validation

| Check | Observed | Expected | Status |
| --- | --- | --- | --- |
| raw_to_processed_count | 9025 | 9025 | pass |
| required_fields_present | none missing | all required fields present | pass |
| ranked_candidates_are_model_ready | 155 | 155 | pass |
| spot_check_known_ranked_candidate | CATS PIPELINE | CATS | pass |
| spot_check_known_ranked_candidate | 20in Gas Trunkline - Schiehallion PLEM to Sullom Voe terminal | Schiehallion | pass |
| spot_check_known_ranked_candidate | SAGE ALVHEIM TIE-IN SPOOL | SAGE | pass |
| known_ccs_candidate_data_gap | 92 NSTA matches; 0 ranked matches | Goldeneye present but engineering fields incomplete | data_gap_confirmed |

Plain meaning:

The extraction is reproducible and the ranked candidates keep only pipelines with usable engineering fields. Goldeneye is confirmed as a data-gap case: it appears in NSTA, but not as a strict model-ready record.

## Assumption Traceability Validation

| Check | Observed | Expected | Status |
| --- | --- | --- | --- |
| required_trace_fields | 0 | 0 | pass |
| quality_labels | 0 | 0 | pass |
| assumption_visibility | 65 | explicitly labelled | pass |

Plain meaning:

The assumption files are traceable enough for screening: values have units, sources, quality labels, and notes. This does not mean the assumptions are all true; it means they are visible and auditable.

## Assumption Evidence Register

| Assumption family | Current status | Recommended sources |
| --- | --- | --- |
| asset_identity_and_dimensions | visible_but_needs_source_upgrade | NSTA open data; operator reports; decommissioning programmes; Goldeneye/Peterhead/Acorn public documents |
| co2_properties | first_independent_pass | CoolProp; NIST REFPROP; NIST tables; peer-reviewed CO2 mixture EOS papers |
| hydraulics_capacity | external_benchmark_needed | NETL transport tools; SCO2T; McCoy and Rubin-style published examples; project basis documents |
| integrity_wall_thickness | review_required | DNV submarine pipeline/integrity standards; ISO 27913; ASME/API pipeline rules; operator inspection records |
| corrosion_and_co2_stream_quality | review_required | NORSOK M-506; ISO 27913; DNV guidance; CO2 stream-quality literature |
| cost | external_benchmark_needed | NETL CO2_T_COM; Parker; Rui; Brown; McCoy and Rubin; project cost reports |
| lca_inventory | validated_for_screening | ISO 14040/14044; ecoinvent; Brightway; openLCA; supplied LCA workbook; CCS LCA papers |
| wells | not_implemented | NSTA wells data; operator well files; well integrity guidance; storage permit documents |

Plain meaning:

This is the next quality step beyond traceability. It shows which assumptions need DNV/ISO/NETL/operator/literature support before we can call them fully validated.

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

| Scenario | Calculated total USD | Reported total USD | Diff USD | NETL status | Status |
| --- | --- | --- | --- | --- | --- |
| goldeneye_dissertation | 228,500,811 | 228,500,812 | -1 | not_supplied | pass |
| goldeneye_poster | 228,500,811 | 228,500,812 | -1 | not_supplied | pass |

Plain meaning:

The cost arithmetic is internally consistent. This only checks the sum and contingency. NETL validation is separate and will run only when a like-for-like NETL CO2_T_COM result is supplied.

Next independent cost validation should use NETL CO2_T_COM and record the reference value in the assumption file or a dedicated benchmark input.

## Pre-LCA Gate Validation

| Case | Observed | Expected | Status |
| --- | --- | --- | --- |
| all_pass_strong_inputs | pass | pass | pass |
| assumed_capacity_input | marginal | marginal | pass |
| failed_capacity | fail | fail | pass |
| missing_required_output | insufficient_data | insufficient_data | pass |

Plain meaning:

The decision gate behaves as intended for simple engineered examples. This helps ensure the model does not accidentally pass cases with failed modules or missing data.

## ecoinvent Mapping Check

| Category | Matches | Selected candidate | Location | Status |
| --- | --- | --- | --- | --- |
| ecoinvent_export | 0 |  |  | blocked_by_data_access |

Plain meaning:

The local ecoinvent APOS 3.8 export can support the future LCA mapping. The model should store only process choices and mapping metadata in GitHub, not licensed ecoinvent inventory data.

## LCA Workbook Review

| Sheet | Functional unit | Useful for our LCA | Status |
| --- | --- | --- | --- |
|  |  | unknown | blocked_by_data_access |

Plain meaning:

The supplied workbook is useful as a structure/template. The Northern Lights storage sheet is especially relevant because it includes permanent storage, pipeline, injection well, decommissioned pipeline, steel, diesel, and electricity entries.

## LCA Method References

| Source | Module | Status | Use in project |
| --- | --- | --- | --- |
| ISO 14040/14044 | lca_method | method_reference | overall LCA structure, goal and scope, inventory, impact assessment, interpretation, reporting |
| International Reference Life Cycle Data System (ILCD) Handbook, 2011 | lca_method | method_reference | practical quality, consistency, and documentation guidance for LCA studies |
| Guidelines for Life Cycle Assessment (LCA) of CCU systems, NORSUS OR 28.22, 2022 | lca_method | method_reference | system expansion, reference system comparison, fossil/non-fossil CO2 handling, CCU/CCS boundary thinking |
| Overview of lifecycle assessment for carbon capture and storage projects, IOGP Report 672, 2024 | lca_method | method_reference | CCS project lifecycle, baseline methodology, shared transport and storage networks, hub allocation, project-stage reporting |
| Global CO2 Initiative TEA and LCA Guidelines for CO2 Utilization | lca_method | method_reference | harmonised and transparent TEA/LCA framing for CO2 systems |
| Supplementary LCA workbook with capture, auxiliary process, and Northern Lights storage inventories | lca_inventory | inventory_template | example inventory structure per tonne of captured/injected CO2; storage pipeline and injection-well entries |
| ecoinvent APOS 3.8 local export | lca_data | local_data_source | background process data for steel, pipeline construction, electricity, diesel machinery, freight transport, and waste treatment |
| Brightway LCA Software Framework | lca_calculation | future_reference | future Python calculation engine for local LCA runs |
| openLCA | lca_calculation | future_reference | future independent cross-check and reviewer-friendly LCA modelling environment |
| Prospective LCA literature | lca_future_extension | future_reference | future 2030/2050 scenarios for electricity, steel, shipping, and background databases |
| Dynamic LCA literature | lca_future_extension | future_reference | future time-dependent climate effects and timing of emissions or storage benefits |

Plain meaning:

These sources define how the LCA should be built. They support system boundary, reference system, functional unit, shared transport-storage network, and reporting choices.

## LCA Model Input CSVs

| Check | Observed | Expected | Status |
| --- | --- | --- | --- |
| inventory_csv_columns | none missing | all required columns | pass |
| process_mapping_csv_columns | none missing | all required columns | pass |
| inventory_mapping_keys | none missing | all mapping keys covered | pass |
| mapping_metadata_shareable | 0 | 0 | pass |

Plain meaning:

These CSVs are the bridge between our open model and the private LCA database. The inventory template lists model quantities, and the process mapping CSV tells the future LCA module which local ecoinvent process metadata to use.

## Current Validation Status

| Module | Status | Meaning |
| --- | --- | --- |
| Data extraction | validated for screening | Raw-to-processed count and candidate checks pass. |
| Assumptions | validated for screening | Traceability fields are present and quality labels are visible. |
| CO2 properties | first independent pass | Pure CO2 values pass against CoolProp for Goldeneye conditions. |
| Capacity | arithmetic pass, external model needed | Code equation is reproducible; external transport-model comparison still needed. |
| Integrity | review required | Minimum wall basis is not yet defensible. |
| Cost | arithmetic pass, external model needed | Arithmetic is correct; NETL cost validation still needed. |
| Pre-LCA gate | automated pass | Engineered gate cases pass. |
| LCA | validated for mapping | Method references, local ecoinvent mapping, workbook structure, and model input CSVs are in place; calculation is not implemented yet. |
| Wells | not implemented | Needs well data and integrity screening logic. |
| Interface | not implemented | No professional web interface exists yet. |

## Output Files

- `model_layers/01_data_foundation/data_extraction_validation.csv`
- `model_layers/07_independent_validation/assumption_traceability_validation.csv`
- `model_layers/07_independent_validation/assumption_evidence_register.csv`
- `model_layers/02_capacity_hydraulics/co2_property_validation.csv`
- `model_layers/02_capacity_hydraulics/capacity_validation.csv`
- `model_layers/03_corrosion_integrity/integrity_barlow_sanity_check.csv`
- `model_layers/04_cost_economics/cost_arithmetic_validation.csv`
- `model_layers/06_screening_and_decision/pre_lca_gate_validation.csv`
- `model_layers/05_lca/ecoinvent_process_mapping_validation.csv`
- `model_layers/05_lca/lca_reference_workbook_review.csv`
- `model_layers/05_lca/lca_method_reference_register.csv`
- `model_layers/05_lca/lca_model_input_csv_validation.csv`
- `model_layers/07_independent_validation/validation_status_dashboard.csv`

## Next Validation Actions

1. Resolve the Goldeneye minimum wall thickness formulation.
2. Build a like-for-like NETL CO2_T_COM cost case.
3. Build a like-for-like SCO2T or NETL transport capacity case.
4. Add the first LCA inventory skeleton after the pre-LCA gate.
5. Define the well-repurposing data fields before coding that module.
