# Refurbishment Unit-Cost Screening Basis

This file explains the public screening unit-cost defaults used by:

```text
model_layers/04_cost_economics/refurbishment_unit_cost_screening_defaults.csv
```

These values are not contractor prices and are not final project estimates. They are open screening defaults that let the model produce complete early cost ranges while private rates are still missing.

## How To Use

Use screening mode for early ranking:

```powershell
python scripts\run_refurbishment_cost.py --case nsta_pl774 --factor-mode screening
```

Use private mode when project rates are available:

```powershell
python scripts\run_refurbishment_cost.py --case nsta_pl774 --factor-mode private
```

## Basis

The factors are deliberately broad low/base/high ranges. They represent engineering work packages such as inspection, cleaning/drying, material testing, fracture/decompression study, IMR planning and replacement steel.

The current source quality is `screening_default_unvalidated`. Before publication or investment use, replace them with one or more of:

- contractor/supplier quotations;
- operator project estimates;
- NETL CO2 transport model comparison;
- documented cost benchmarks from similar offshore pipeline requalification work.

## Interpretation

If a cost report says `screening_result`, it is useful for comparing pipelines.

If it says `sensitivity_only`, the pipeline failed an upstream technical gate, so the cost number is shown only to understand scale.
