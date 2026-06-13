# Ecoinvent-Based Conditional LCA: goldeneye_dissertation

Generated: 2026-06-13T14:30:38+00:00

## Plain Result

Status: `screening_result`

This is an ecoinvent-linked conditional LCA workflow. If the status is `screening_result`, public screening factors were used. This gives a complete early estimate, but final publishable kg CO2e results still need private ecoinvent/openLCA/Brightway-derived impact factors.

## Main Numbers

| Item | Value |
| --- | --- |
| Pre-LCA decision | marginal |
| New-build base impact | 64,326.19 tCO2e |
| Reuse base impact | 4,741.51 tCO2e |
| Base saving | 59,584.68 tCO2e |
| Base saving percent | 92.6% |
| Missing factor keys | none |
| Factor quality | screening_default_unvalidated |

## Required Inventory Rows

| Alternative | Inventory item | Mapping key | Base quantity | Unit | Factor status |
| --- | --- | --- | --- | --- | --- |
| new_build | pipeline_steel_mass | pipeline_steel | 27,079,095.90 | kg | available |
| new_build | offshore_pipeline_construction | offshore_pipeline_construction | 101.68 | km | available |
| reuse | refurbishment_steel | pipeline_steel | 1,353,954.79 | kg | available |
| reuse | pipeline_refurbishment_activity | refurbishment_activity | 101.68 | km | available |

## Output Files

- `model_layers/05_lca/lca_inventory_goldeneye_dissertation.csv`
- `model_layers/05_lca/lca_impacts_goldeneye_dissertation.csv`
- `model_layers/05_lca/lca_results_goldeneye_dissertation.csv`
- `model_layers/05_lca/lca_trace_goldeneye_dissertation.json`

## Private Factor File

Expected private factor file:

```text
model_layers/05_lca/lca_impact_factors_screening_defaults.csv
```

This file should contain ecoinvent/openLCA/Brightway-derived impact factors and should not be committed to GitHub.

## Important Caveat

The result is conditional until wall thickness is validated and all required private impact factors are supplied.
