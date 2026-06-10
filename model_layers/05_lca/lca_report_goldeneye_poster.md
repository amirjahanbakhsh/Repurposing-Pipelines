# Ecoinvent-Based Conditional LCA: goldeneye_poster

Generated: 2026-06-10T14:57:11+00:00

## Plain Result

Status: `blocked_missing_impact_factors`

This is an ecoinvent-linked conditional LCA workflow. It needs private ecoinvent-derived impact factors before final kg CO2e results can be trusted.

## Main Numbers

| Item | Value |
| --- | --- |
| Pre-LCA decision | marginal |
| New-build base impact | 0.00 tCO2e |
| Reuse base impact | 0.00 tCO2e |
| Base saving | 0.00 tCO2e |
| Base saving percent | 0.0% |
| Missing factor keys | pipeline_steel; offshore_pipeline_construction; refurbishment_activity |

## Required Inventory Rows

| Alternative | Inventory item | Mapping key | Base quantity | Unit | Factor status |
| --- | --- | --- | --- | --- | --- |
| new_build | pipeline_steel_mass | pipeline_steel | 17,679,628.82 | kg | missing |
| new_build | offshore_pipeline_construction | offshore_pipeline_construction | 101.68 | km | missing |
| reuse | refurbishment_steel | pipeline_steel | 883,981.44 | kg | missing |
| reuse | pipeline_refurbishment_activity | refurbishment_activity | 101.68 | km | missing |

## Output Files

- `model_layers/05_lca/lca_inventory_goldeneye_poster.csv`
- `model_layers/05_lca/lca_impacts_goldeneye_poster.csv`
- `model_layers/05_lca/lca_results_goldeneye_poster.csv`
- `model_layers/05_lca/lca_trace_goldeneye_poster.json`

## Private Factor File

Expected private factor file:

```text
model_layers/05_lca/private/lca_impact_factors_private.csv
```

This file should contain ecoinvent/openLCA/Brightway-derived impact factors and should not be committed to GitHub.

## Important Caveat

The result is conditional until wall thickness is validated and all required private impact factors are supplied.
