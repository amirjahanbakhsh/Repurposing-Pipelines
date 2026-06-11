# Pipeline Screen: goldeneye_poster

Generated: 2026-06-11T16:36:55+00:00

Input assumptions: `model_layers/06_screening_and_decision/goldeneye_assumptions.csv`

Outputs:

- `model_layers/06_screening_and_decision/pipeline_screen_goldeneye_poster.csv`
- `model_layers/06_screening_and_decision/pipeline_screen_goldeneye_poster_trace.json`
- `model_layers/06_screening_and_decision/refurbishment_work_scope_goldeneye_poster.csv`

## Plain Result

Pipeline: `20" GAS GOLDENEYE - ST. FERGUS`

Input mode: `scenario_assumptions`

NSTA pipeline number: `not applicable`

Decision: `marginal`

Confidence: `medium`

Meaning: Move to LCA only as a sensitivity case until assumptions are checked.

## Main Numbers

| Item | Value |
| --- | --- |
| CO2 capacity | 9.97 MtCO2/year |
| Required design flow | 5.88 MtCO2/year |
| Remaining life | 24.55 years |
| Remaining life range | 0.00 to 247.25 years |
| Available wall thickness | 4.91 mm |
| Corrosion risk | medium |
| Repurposing gate | marginal |
| Repurposing evidence score | 29.5 / 100 |
| CO2 phase screen | dense_phase_selected |
| Benchmark avoided new-build CAPEX | $228,500,811 |
| NETL cost check | not_supplied |
| LCA proxy saving | 91.6% |
| LCA screen | favour_reuse |

## Repurposing Gate

Meaning: Promising only as a screening case, but important evidence is missing.

Evidence gaps:

- inner_diameter_in quality is assumed_or_standard
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
| Replacement/refurbishment steel | 884.0 t |
| Refurbishment activity package | 101.7 km |

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

- Capacity passes: 9.97 MtCO2/year versus 5.88 MtCO2/year required.
- Integrity passes at screening level: 24.55 years remaining life and 4.91 mm available wall.
- Cost screen is positive: benchmark avoided new-build CAPEX is $228,500,811.
- Some important values are assumed or sensitivity inputs: capacity_factor, co2_composition_known, co2_water_content_ppmv, co2_water_spec_limit_ppmv, component_compatibility_screened, contingency_fraction, fracture_toughness_basis, future_co2_corrosion_rate_high_mm_per_year, future_co2_corrosion_rate_low_mm_per_year, future_co2_corrosion_rate_mm_per_year, historical_wall_loss_uncertainty_fraction, ili_mfl_available, inner_diameter_in, material_certificates_available, minimum_wall_thickness_uncertainty_fraction, nominal_wall_thickness_uncertainty_fraction, section_replacement_fraction, target_co2_phase, water_dew_point_margin_c.
- Upstream modules still contain validation warnings.
- Repurposing gate is marginal: Promising only as a screening case, but important evidence is missing..

## Next Data To Check

- verify wall thickness and inspection records
- validate CO2 density, viscosity, compressibility, and phase behaviour
- complete the repurposing gate evidence checklist
- compare cost with NETL CO2_T_COM or another external benchmark
- define itemised reuse modification cost before detailed LCA

## Important Caveat

This is a screening result, not engineering approval. The decision is only as strong as the input assumptions.
