# Refurbishment Work-Scope Model

Date: 2026-06-11

## Plain Meaning

The repurposing gate says what is missing or required. The refurbishment work-scope model turns that into a table with quantities.

Example:

```text
ILI/MFL inspection needed -> inspect 101.68 km
cleaning/drying needed -> clean/dry 101.68 km
replacement steel allowance -> calculate kg of steel
```

## Why This Matters

Cost and LCA need quantities, not only words. This table is the bridge between technical screening and later cost/LCA calculations.

## What The Table Contains

| Column type | Meaning |
| --- | --- |
| Work item | What needs to be done or checked. |
| Quantity | The driver, such as km, kg, study, campaign, review or plan. |
| Cost driver | How this item should later be priced. |
| LCA mapping key | Which LCA process group it links to. |
| Reference IDs | Literature sources supporting why the item exists. |
| Data quality | Whether the number is a screening driver, aggregate package, or calculated allowance. |

## Important Rule

The table is **not** a contractor quote and **not** a final LCA result. It is a structured screening table.

Detailed unit costs, vessel days, repair methods and ecoinvent impact factors still need project-specific data.

## Main Output Files

| File | Meaning |
| --- | --- |
| `refurbishment_work_scope_goldeneye_benchmark.csv` | Work-scope rows for Goldeneye dissertation/poster cases. |
| `refurbishment_work_scope_nsta_pl774.csv` | Work-scope rows for the PL774/CATS example. |
| `refurbishment_work_scope_nsta_all.csv` | Work-scope rows for all screened NSTA candidates. |

