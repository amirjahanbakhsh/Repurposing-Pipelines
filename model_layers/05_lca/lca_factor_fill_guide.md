# LCA Factor Fill Guide

Date: 2026-06-12

## Plain Meaning

The model already calculates LCA quantities. Final kg CO2e results need private impact factors from ecoinvent/openLCA/Brightway.

Those private values belong here:

```text
model_layers/05_lca/private/lca_impact_factors_private.csv
```

This file is ignored by GitHub.

## Factors Needed First

| Mapping key | Unit | Why needed |
| --- | --- | --- |
| `pipeline_steel` | kg | New-build steel and refurbishment steel. |
| `offshore_pipeline_construction` | km | New equivalent offshore pipeline construction. |
| `refurbishment_activity` | km | Aggregate reuse package: inspection, cleaning, drying, repair and recommissioning. |

## How To Fill

1. Open the private factor CSV.
2. For each `mapping_key`, calculate an IPCC 2021 GWP100 climate-change factor in openLCA or Brightway.
3. Put the result in `impact_factor_kgco2e_per_unit`.
4. Keep notes on activity choice, database version, system model and impact method.
5. Rerun:

```powershell
python scripts\run_ecoinvent_lca.py --scenario goldeneye_poster
python scripts\run_ecoinvent_lca.py --nsta-id PL774
```

## Important Rule

Do not commit ecoinvent unit-process inventories, exchanges, or private impact factors to GitHub.

## Current Status

The LCA reports correctly show `blocked_missing_impact_factors` until the private factor values are filled.

