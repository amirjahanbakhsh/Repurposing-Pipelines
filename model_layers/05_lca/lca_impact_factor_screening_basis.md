# LCA Impact-Factor Screening Basis

This file explains the public screening impact factors used by:

```text
model_layers/05_lca/lca_impact_factors_screening_defaults.csv
```

These values are not final ecoinvent results. They are open screening defaults that let the model calculate an early kg CO2e estimate while private ecoinvent/openLCA/Brightway factors are still missing.

## How To Use

Use screening mode for early ranking:

```powershell
python scripts\run_ecoinvent_lca.py --nsta-id PL774 --factor-mode screening
```

Use private mode when ecoinvent/openLCA/Brightway factors are filled:

```powershell
python scripts\run_ecoinvent_lca.py --nsta-id PL774 --factor-mode private
```

## Current Boundary

The current comparison is:

- new offshore CO2 pipeline equivalent;
- reuse of an existing offshore pipeline after refurbishment.

The default included activities are:

- new-build pipeline steel;
- new offshore pipeline construction package;
- refurbishment steel;
- refurbishment activity package.

Operational compression electricity, decommissioning and end-of-life are mapped but not included in the default totals yet.

## Interpretation

If an LCA report says `screening_result`, it is a complete early estimate using public screening factors.

If it says `sensitivity_only`, the pipeline failed an upstream technical gate, so the LCA number should not be used to justify reuse.

Final publishable LCA claims should use private ecoinvent/openLCA/Brightway factors and a checked activity boundary.
