# Repurposing Gate Model

Date: 2026-06-11

## Plain Meaning

The repurposing gate asks:

> Is this pipeline only mathematically possible, or is there enough real evidence to treat reuse as a serious option?

It does not approve a pipeline. It tells us what is missing before approval could even be discussed.

## What The Gate Checks

| Check | Plain meaning |
| --- | --- |
| CO2 phase | Is this gas-phase or dense-phase CO2 service? |
| CO2 quality | Do we know water content, impurities and dew-point basis? |
| Pipe condition | Do we have wall thickness, minimum wall and remaining-life evidence? |
| Inspection evidence | Do we have ILI/MFL or similar inspection results? |
| Material evidence | Do we have certificates or testing basis? |
| Fracture evidence | Do we have fracture/decompression basis, especially for dense phase? |
| Components | Have valves, seals, coatings and equipment been checked for CO2 compatibility? |
| Work scope | What cleaning, drying, inspection, repair or monitoring work is needed? |

## Outputs

| Output | Meaning |
| --- | --- |
| `repurposing_gate_status` | pass, marginal, fail or insufficient data. |
| `repurposing_evidence_score` | 0 to 100 score showing strength of evidence. |
| `repurposing_phase_status` | gas/dense/unknown phase screening result. |
| `repurposing_evidence_gaps` | missing or weak evidence. |
| `repurposing_work_scope_items` | work items that should feed cost and LCA. |
| `repurposing_gate_cited_references` | reference IDs used by the gate logic. |

## Link To Quantified Work Scope

The gate produces named work items. The next module, `work_scope`, converts those names into quantity drivers.

For example:

| Gate item | Quantity driver |
| --- | --- |
| `ili_mfl_or_equivalent_inspection` | pipeline length in km |
| `cleaning_drying_and_debris_assessment` | pipeline length in km |
| `fracture_and_decompression_screen` | one study |
| `replacement_or_refurbishment_steel` | calculated kg of steel |

The detailed table is written to files named `refurbishment_work_scope_*.csv`.

## References Used In The Code

The code cites source IDs from `references/literature_index.csv`, including:

- `REF_OSTBY_TORBERGSEN_RONEID_LEINUM_2022_CO2_REQUALIFICATION`
- `REF_TORBERGSEN_LEINUM_RONEID_2025_GAS_PHASE_CO2_REQUALIFICATION`
- `REF_MONSMA_MURRAY_2026_GAS_PHASE_CO2_REPURPOSING`
- `REF_KUMAR_LOWERY_PASSUCCI_2025_ENI_LIVERPOOL_BAY_IMR`
- `REF_YUSOF_AZIZ_2025_PETRONAS_DENSE_PHASE_CO2_REPURPOSING`
- `REF_DALONZO_BUSCO_ELVIRA_CHERUBINI_2025_CO2_IMR`
- `REF_BURKINSHAW_GALLON_CARVELL_HUSSAIN_2024_HYDROGEN_DATA_EVIDENCE`
- `REF_KASS_ET_AL_2023_MATERIAL_COMPATIBILITY`

## Current Limitation

The gate is a screening model. It does not approve reuse. The new work-scope module calculates first quantity drivers, but it still does not provide detailed inspection cost, cleaning cost, drying energy, vessel duration, contractor quotation, or final engineering approval.
