# Ecoinvent-Based Conditional LCA: nsta_pl774

Generated: 2026-06-13T15:59:01+00:00

## Plain Result

Status: `blocked_missing_impact_factors`

This is an ecoinvent-linked conditional LCA workflow. If the status is `screening_result`, public screening factors were used. This gives a complete early estimate, but final publishable kg CO2e results still need private ecoinvent/openLCA/Brightway-derived impact factors.

## Main Numbers

| Item | Value |
| --- | --- |
| Pre-LCA decision | fail |
| New-build base impact | 0.00 tCO2e |
| Reuse base impact | 0.00 tCO2e |
| Base saving | 0.00 tCO2e |
| Base saving percent | 0.0% |
| Missing factor keys | pipeline_steel; offshore_pipeline_construction; refurbishment_activity |
| Factor quality | none |

## Required Inventory Rows

| Alternative | Inventory item | Mapping key | Base quantity | Unit | Factor status |
| --- | --- | --- | --- | --- | --- |
| new_build | pipeline_steel_mass | pipeline_steel | 251,303,454.37 | kg | missing |
| new_build | offshore_pipeline_construction | offshore_pipeline_construction | 404.97 | km | missing |
| reuse | refurbishment_steel | pipeline_steel | 12,565,172.72 | kg | missing |
| reuse | pipeline_refurbishment_activity | refurbishment_activity | 404.97 | km | missing |

## Output Files

- `model_layers/05_lca/lca_inventory_nsta_pl774.csv`
- `model_layers/05_lca/lca_impacts_nsta_pl774.csv`
- `model_layers/05_lca/lca_results_nsta_pl774.csv`
- `model_layers/05_lca/lca_trace_nsta_pl774.json`

## Private Factor File

Expected private factor file:

```text
model_layers/05_lca/private/lca_impact_factors_private.csv
```

This file should contain ecoinvent/openLCA/Brightway-derived impact factors and should not be committed to GitHub.

## Important Caveat

The result is conditional until wall thickness is validated and all required private impact factors are supplied.
