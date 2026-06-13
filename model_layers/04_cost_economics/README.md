# 04 Cost And Economics

Cost-model inputs, NETL comparison placeholders, refurbishment unit-cost factors, and cost validation files.

## Simple Commands

Create the private unit-cost template:

```powershell
python scripts\run_refurbishment_cost.py --create-factor-template
```

Run the PL774 refurbishment cost check:

```powershell
python scripts\run_refurbishment_cost.py --case nsta_pl774 --factor-mode screening
```

Run all NSTA work-scope cost checks:

```powershell
python scripts\run_refurbishment_cost.py --case nsta_all --factor-mode screening
```

Use `--factor-mode private` after filling the private unit-cost CSV.

If the report says `screening_result`, public screening defaults were used. If it says `sensitivity_only`, an upstream technical gate failed and the cost is only shown to understand scale.

| File | Purpose |
| --- | --- |
| `netl_cost_reference_template.csv` | Place to record official NETL cost-model comparison values. |
| `cost_arithmetic_validation.csv` | Checks cost summation and contingency arithmetic. |
| `refurbishment_unit_cost_template.csv` | Blank public template for work-scope unit-cost factors. |
| `refurbishment_unit_cost_screening_defaults.csv` | Public screening unit-cost defaults for complete early runs. |
| `refurbishment_unit_cost_screening_basis.md` | Plain-language basis and caveats for the screening defaults. |
| `refurbishment_cost_report_*.md` | Report showing whether unit-cost factors are available. |
| `refurbishment_costs_*.csv` | Row-by-row work-scope cost table. |
| `refurbishment_cost_summary_*.csv` | Scenario-level refurbishment cost summary. |

Private unit-cost values belong in:

```text
model_layers/04_cost_economics/private/refurbishment_unit_costs_private.csv
```

This file is ignored by Git and should not be uploaded to GitHub.
