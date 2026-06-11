# LCA Activity Extraction Report

Generated: 2026-06-11T16:15:44+00:00

Model version: `lca_activity_extraction_v0.1`

## Purpose

This report lists candidate LCA activities for the pipeline repurposing model.

The extraction is licence-safe. It stores activity metadata only: names, locations, reference products, units, and mapping notes. It does not copy ecoinvent unit-process inventories, exchanges, or private impact factors.

## Sources Read

- ecoinvent: 19727 metadata rows

## Candidate Counts

- `decommissioned_pipeline`: 4 candidate(s)
- `diesel_machinery`: 10 candidate(s)
- `electricity`: 10 candidate(s)
- `freight_transport`: 10 candidate(s)
- `offshore_pipeline_construction`: 9 candidate(s)
- `pipeline_steel`: 10 candidate(s)
- `refurbishment_activity`: 10 candidate(s)
- `scrap_steel`: 10 candidate(s)

## Output Files

- `C:/Users/aj52/Documents/Repurposing Pipelines/model_layers/05_lca/lca_activity_candidates.csv`
- `C:/Users/aj52/Documents/Repurposing Pipelines/model_layers/05_lca/lca_activity_preferred_mapping.csv`
- `C:/Users/aj52/Documents/Repurposing Pipelines/model_layers/05_lca/lca_activity_extraction_report.md`

## How To Use This

1. Review the candidate activities.
2. Select the best activity for each `mapping_key`.
3. Use openLCA or Brightway privately to calculate the required impact factors.
4. Put private factors in `model_layers/05_lca/private/lca_impact_factors_private.csv`.

Rows marked as project packages, such as refurbishment, are not single database activities. Build their factor from the relevant work items, for example inspection, cleaning, drying, repair, replacement steel, vessel time, diesel use and logistics.

If the local lookup file does not include units, unit fields remain blank here and must be confirmed during private LCA review.

## Boundary Reminder

For the current pipeline-only LCA, include pipeline steel, construction/refurbishment, cleaning/drying/inspection/repair where data exist, operation energy if allocated, logistics, and end-of-life sensitivity.

Exclude capture plant, industrial emissions before capture, storage reservoir performance, and claimed avoided emissions from storing CO2 until the project moves to a full CCS-chain LCA.
