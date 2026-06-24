# Pipeline Screen: nsta_pl774

Generated: 2026-06-24T22:54:33+00:00

Input assumptions: `model_layers/06_screening_and_decision/nsta_screening_defaults.csv`

Outputs:

- `model_layers/06_screening_and_decision/pipeline_screen_nsta_pl774.csv`
- `model_layers/06_screening_and_decision/pipeline_screen_nsta_pl774_trace.json`
- `model_layers/06_screening_and_decision/refurbishment_work_scope_nsta_pl774.csv`

## Plain Result

Pipeline: `CATS PIPELINE`

Input mode: `nsta_candidate_plus_defaults`

NSTA pipeline number: `PL774`

Decision: `fail`

Confidence: `medium`

Meaning: Do not move to LCA until failed technical or cost checks are resolved.

## Main Numbers

| Item | Value |
| --- | --- |
| CO2 capacity | 37.75 MtCO2/year |
| Required design flow | 5.88 MtCO2/year |
| Remaining life | 0.00 years |
| Remaining life range | 0.00 to 531.44 years |
| Available wall thickness | -0.93 mm |
| Corrosion risk | medium |
| Repurposing gate | fail |
| Repurposing evidence score | 23.5 / 100 |
| CO2 phase screen | dense_phase_selected |
| Benchmark avoided new-build CAPEX | $910,078,962 |
| NETL cost check | not_supplied |
| LCA proxy saving | 93.9% |
| LCA screen | needs_data |

## Repurposing Gate

Meaning: Do not proceed until the showstoppers are resolved.

Evidence gaps:

- pipe_grade quality is assumed
- outlet_pressure_psia quality is assumed
- target_co2_phase quality is assumed
- co2_water_content_ppmv quality is assumed
- co2_water_spec_limit_ppmv quality is assumed
- water_dew_point_margin_c quality is assumed
- co2_composition_known is no
- material_certificates_available is unknown
- fracture_toughness_basis quality is assumed
- ili_mfl_available is unknown
- component_compatibility_screened is no

Work scope:

- confirm_co2_composition_and_impurities
- confirm_water_limit_and_dew_point
- cleaning_drying_and_debris_assessment
- ili_mfl_or_equivalent_inspection
- material_certificates_or_testing
- component_compatibility_review
- fracture_and_decompression_screen
- wall_thickness_verification
- co2_leak_detection_isolation_and_imr_plan

Quantified work-scope summary:

| Item | Value |
| --- | --- |
| Work-scope rows | 11 |
| Cost-driver rows | 10 |
| LCA-driver rows | 2 |
| Replacement/refurbishment steel | 12565.2 t |
| Refurbishment activity package | 405.0 km |

References used by the gate:

- REF_OSTBY_TORBERGSEN_RONEID_LEINUM_2022_CO2_REQUALIFICATION
- REF_TORBERGSEN_LEINUM_RONEID_2025_GAS_PHASE_CO2_REQUALIFICATION
- REF_MONSMA_MURRAY_2026_GAS_PHASE_CO2_REPURPOSING
- REF_KUMAR_LOWERY_PASSUCCI_2025_ENI_LIVERPOOL_BAY_IMR
- REF_YUSOF_AZIZ_2025_PETRONAS_DENSE_PHASE_CO2_REPURPOSING
- REF_DALONZO_BUSCO_ELVIRA_CHERUBINI_2025_CO2_IMR
- REF_BURKINSHAW_GALLON_CARVELL_HUSSAIN_2024_HYDROGEN_DATA_EVIDENCE
- REF_KASS_ET_AL_2023_MATERIAL_COMPATIBILITY

## Why This Decision?

- One or more upstream modules failed: integrity
- repurposing_gate.

## Next Data To Check

- verify wall thickness and inspection records
- check pipe grade, design factor, defects, and pressure basis
- replace simple Barlow screening with a proper requalification method
- resolve repurposing showstoppers
- collect missing requalification evidence
- define cleaning, drying, inspection, repair, and monitoring work scope

## Important Caveat

This is a screening result, not engineering approval. The decision is only as strong as the input assumptions.
