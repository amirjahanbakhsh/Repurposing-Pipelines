# State Of Art Gap Analysis And Future Directions

Date: 2026-06-11

## Short Judgement

The project is on the right path, but the newest references show one important improvement:

> The model should become an evidence-based repurposing decision system, not only a pipeline screening calculator.

In simple terms, the tool should not only say "this pipeline may work". It should also say:

- what evidence supports that result;
- what evidence is missing;
- what inspections or tests are needed next;
- what repair, cleaning, drying, replacement or monitoring work may be required;
- how those work items change cost and LCA.

That is where we can move beyond much of the current state of art.

## What The New References Add

The new papers and reports point to a common message: repurposing is a formal requalification workflow.

| Theme from references | Meaning for our model |
| --- | --- |
| DNV-style requalification | Add a formal repurposing gate before cost and LCA. |
| Gas phase versus dense phase CO2 | Do not assume dense phase is always possible for old pipelines. |
| CO2 specification and water control | Add water, impurity and dew-point checks. |
| Cleaning and drying | Convert "refurbishment" into real work items. |
| Material and component compatibility | Check pipe steel, welds, valves, seals, coatings and equipment. |
| Fracture and decompression | Dense-phase CO2 needs special fracture screening. |
| Missing certificates and inspection data | Treat missing evidence as a model output, not a hidden weakness. |
| IMR planning | Add inspection, monitoring, maintenance and repair needs after screening. |
| Survival analysis | Add a statistical remaining-life check where direct inspection data are weak. |

## What We Still Miss

These are the main gaps compared with the latest state of art.

| Gap | Why it matters | Suggested action |
| --- | --- | --- |
| Formal repurposing gate | Current layers are good, but they do not yet fully mimic industrial requalification. | Add a `repurposing_gate` module. |
| CO2 phase decision | Gas phase and dense phase have different capacity, corrosion, fracture and cost implications. | Add phase status: `gas`, `dense`, `unknown`, `not_feasible`. |
| CO2 quality specification | Water and impurities can control corrosion and phase behaviour. | Add CO2 composition, water limit and dew-point margin fields. |
| Cleaning and drying work scope | LCA and cost need quantities, not a fixed refurbishment percentage. | Add work items such as cleaning, drying, debris removal and inspection. |
| Material/component compatibility | Pipe may pass, while valves, seals or coatings may not. | Add a compatibility matrix based on component type. |
| Fracture toughness evidence | Older pipelines may lack CVN or mill certificate data. | Add evidence status for toughness and dense-phase fracture screening. |
| Evidence confidence | A value from NSTA, a certificate and an assumption should not be treated equally. | Add primary/secondary/assumed evidence scoring. |
| IMR plan | Repurposing is not finished at start-up; it needs ongoing inspection and monitoring. | Add an IMR output package. |
| Network and hub context | A technically good pipeline may be weak if it does not fit a future CCS network. | Add optional source-sink and hub scoring. |
| Dynamic future use | Future systems may move from low-flow gas phase to high-flow dense phase. | Add phased operating scenarios. |

## Room For Improvement In Our Current Layers

Our current layers are useful, but they should become more connected through evidence and work scope.

| Current layer | Improvement |
| --- | --- |
| Data foundation | Add evidence type, evidence confidence and "data needed next". |
| Capacity/hydraulics | Separate gas-phase and dense-phase feasibility more clearly. |
| Corrosion/integrity | Add CO2 water/impurity screen, cleaning/drying trigger and fracture evidence status. |
| Cost/economics | Estimate reuse cost from itemised work scope, not a fixed percentage. |
| LCA | Use the same itemised work scope as cost, so cost and LCA are consistent. |
| Screening/decision | Add a formal gate: pass, marginal, fail or do-not-decide-yet. |
| Validation | Compare each module against external cases: Goldeneye, Liverpool Bay, PETRONAS, OCAP and LACQ. |

## How To Move Beyond State Of Art

The novelty should not be "we built another calculator". The novelty should be:

> A transparent, evidence-aware, future-ready screening tool for pipeline repurposing.

Strong future-facing ideas:

1. Evidence-aware screening

   The tool should show whether a result is based on measured data, reported data or assumptions. This makes the model more honest and easier to defend.

2. Value-of-information ranking

   The tool should tell the user which missing data would most change the decision. For example: wall thickness, material certificate, CVN toughness, ILI report or dew-point target.

3. Work-scope-connected cost and LCA

   Cleaning, drying, inspection, section replacement, valves and monitoring should feed both cost and LCA. This is stronger than using generic refurbishment percentages.

4. Phase-adaptive repurposing

   Some pipelines may start as gas-phase CO2 transport and later move to dense phase if more evidence, pressure capability or network demand becomes available.

5. Portfolio screening

   Instead of studying one pipeline only, the tool should screen all NSTA candidates and rank them by suitability, missing evidence, cost saving and LCA benefit.

6. CCS network foresight

   Future value depends on hubs, emitters, storage sites and timing. A pipeline with moderate technical score may be strategically valuable if it connects the right future cluster.

7. Reuse readiness index

   Create a simple score that tells operators, regulators and investors how close an asset is to being bankable for CO2 reuse.

8. AI-assisted but auditable extraction

   AI can help extract values from reports, drawings and PDFs, but every extracted value must carry a source and confidence label.

9. Conventional LCA now, dynamic LCA later

   The first defendable version should use conventional LCA. Later, add time-dependent electricity mix, phased build-out and avoided decommissioning scenarios.

10. Pipeline-plus-well future model

   Wells should be Phase 2. The long-term tool can rank pipelines, wells and storage connections together.

## Near-Term Implementation Priority

Recommended next sequence:

1. Add `repurposing_gate.py`.
2. Add a simple gate input CSV for CO2 phase, water limit, impurity status, evidence confidence and work-scope flags.
3. Add a component compatibility table.
4. Add evidence confidence scoring.
5. Pass itemised work-scope outputs into cost and LCA.
6. Re-run the 155 usable NSTA pipeline screen with the new gate fields.

## Note On The Student DNV Claim

The student's statement that the work followed a DNV approach is useful, but it should be treated as an auditable claim.

For our project, the important question is not whether DNV was mentioned. The important question is whether the model actually includes the DNV-style workflow:

- design basis;
- CO2 phase and specification;
- current condition assessment;
- hydraulic and flow assurance checks;
- integrity reassessment for CO2;
- corrosion, fracture and material compatibility checks;
- safety and release considerations;
- itemised modification work scope;
- documentation and traceability.

The detailed checklist is stored in `model_layers/07_independent_validation/student_dnv_claim_checklist.md`.

## Suggested Gate Outputs

The repurposing gate should output:

| Output | Plain meaning |
| --- | --- |
| `gate_status` | pass, marginal, fail or insufficient data. |
| `phase_status` | gas phase possible, dense phase possible, both possible or unknown. |
| `evidence_score` | how reliable the input evidence is. |
| `showstoppers` | issues that block reuse at screening level. |
| `required_next_data` | what the user should look for next. |
| `work_scope_items` | cleaning, drying, inspection, repair, replacement or monitoring needs. |
| `cost_inputs` | work items and quantities for the cost model. |
| `lca_inputs` | work items and quantities for the LCA model. |

## Sources Behind This Note

Local extracted project notes:

- `REF_OSTBY_TORBERGSEN_RONEID_LEINUM_2022_CO2_REQUALIFICATION`
- `REF_TORBERGSEN_LEINUM_RONEID_2025_GAS_PHASE_CO2_REQUALIFICATION`
- `REF_MONSMA_MURRAY_2026_GAS_PHASE_CO2_REPURPOSING`
- `REF_KUMAR_LOWERY_PASSUCCI_2025_ENI_LIVERPOOL_BAY_IMR`
- `REF_YUSOF_AZIZ_2025_PETRONAS_DENSE_PHASE_CO2_REPURPOSING`
- `REF_DALONZO_BUSCO_ELVIRA_CHERUBINI_2025_CO2_IMR`
- `REF_BURKINSHAW_GALLON_CARVELL_HUSSAIN_2024_HYDROGEN_DATA_EVIDENCE`
- `REF_KASS_ET_AL_2023_MATERIAL_COMPATIBILITY`
- `REF_MAHMOUD_DODDS_2022`

Recent open literature scan:

- Bogs et al. 2025, minimum-regret CO2 pipeline network planning.
- Anvari et al. 2026, scenario-linked physical CO2 network simulation.
- Kumar and Rosen Esquivel 2025, multicomponent CO2-rich pipeline transport modelling.

## Bottom Line

The biggest opportunity is to make the model decision-based, evidence-based and future-ready.

That means the next technical step should not be only "improve LCA" or "improve cost". It should be:

> build the repurposing gate that tells cost and LCA what real work is required.
