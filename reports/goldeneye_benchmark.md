# Goldeneye Benchmark

Generated: 2026-06-10T08:48:48+00:00

Assumptions: `data/benchmarks/goldeneye_assumptions.csv`

Runner script: `scripts/run_goldeneye_benchmark.py`

Core modules: `repurposing_pipelines/`

Outputs:

- `data/benchmarks/goldeneye_benchmark_outputs.csv`
- `data/benchmarks/goldeneye_benchmark_trace.json`

## Purpose

This benchmark makes the Goldeneye assumptions explicit and reproducible before we generalise the model to other NSTA pipelines.

It compares two available versions:

- `goldeneye_dissertation`
- `goldeneye_poster`

The benchmark currently reproduces the headline capacity, remaining-life, and cost results using the values reported in the dissertation/poster. It is still a screening model, not an engineering approval model.

## How To Read This Report

- Capacity means how much CO2 the pipeline could carry each year.
- Integrity/lifetime means whether enough wall thickness remains for screening.
- Cost means the estimated avoided cost of building a new equivalent pipeline.
- Pre-LCA gate means the simple decision on whether the case is ready for LCA.
- Reported values are the values from the dissertation or poster.
- Calculated values are produced by our Python code.
- Small differences are expected because of rounding.

## Capacity Benchmark

| Scenario | ID in | Average pressure MPa | Calculated capacity Mtpa | Reported capacity Mtpa | Meets 5 Mtpa target? |
| --- | --- | --- | --- | --- | --- |
| goldeneye_dissertation | 18.250 | 9.956 | 9.131 | 9.125 | yes |
| goldeneye_poster | 18.876 | 9.956 | 9.968 | 9.961 | yes |

## Integrity / Lifetime Benchmark

| Scenario | Nominal wall mm | Wall loss mm | Available wall mm | Corrosion risk | Low corr. | Base corr. | High corr. | Conservative life | Base life | Optimistic life |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| goldeneye_dissertation | 22.23 | 8.21 | 7.79 | medium | 0.020 | 0.100 | 0.200 | 0.00 | 77.94 | 901.47 |
| goldeneye_poster | 14.28 | 2.93 | 4.91 | medium | 0.050 | 0.200 | 0.400 | 0.00 | 24.55 | 247.25 |

## Cost Benchmark

| Scenario | Subtotal | Contingency | Calculated total | Reported total | NETL status |
| --- | --- | --- | --- | --- | --- |
| goldeneye_dissertation | $207,728,010 | $20,772,801 | $228,500,811 | $228,500,812 | not_supplied |
| goldeneye_poster | $207,728,010 | $20,772,801 | $228,500,811 | $228,500,812 | not_supplied |

## LCA Screening Proxy

| Scenario | New steel t | Refurb steel t | New-build proxy tCO2e | Reuse proxy tCO2e | Saving % | LCA screen |
| --- | --- | --- | --- | --- | --- | --- |
| goldeneye_dissertation | 27,073 | 1,354 | 64,313 | 4,741 | 92.6 | favour_reuse |
| goldeneye_poster | 17,673 | 884 | 45,514 | 3,801 | 91.6 | favour_reuse |

Plain meaning:

This is the first calculated LCA-style screening result. It is useful for ranking and sensitivity, but it is not yet a final ecoinvent/Brightway result.

## Pre-LCA Gate

| Scenario | Decision | Confidence | Meaning |
| --- | --- | --- | --- |
| goldeneye_dissertation | marginal | medium | Move to LCA only as a sensitivity case until assumptions are checked. |
| goldeneye_poster | marginal | medium | Move to LCA only as a sensitivity case until assumptions are checked. |

Plain meaning:

- `pass`: good enough to move into LCA screening.
- `marginal`: technically promising, but important assumptions still need checking.
- `fail`: do not move into LCA until the failed screen is fixed.
- `insufficient_data`: do not move into LCA because key data are missing.

## Interpretation

- The dissertation and poster use different Goldeneye wall-thickness assumptions.
- The dissertation case uses a thicker nominal wall (`22.23 mm`) and lower future CO2 corrosion rate (`0.10 mm/year`), which gives a much longer base remaining life.
- The poster case uses a lower nominal wall (`14.28 mm`) and higher future CO2 corrosion rate (`0.20 mm/year`), which gives about `24.5 years` in the base case.
- The uncertainty range is now reported separately because the Goldeneye wall basis is not cleanly resolved.
- The capacity difference is mainly caused by the internal diameter/friction assumptions: `18.25 in` in the dissertation case versus about `18.876 in` in the poster case.
- Cost is consistent between the two versions because both use the same Parker-style new-build cost breakdown.
- Both Goldeneye cases are currently `marginal`, because the calculations pass but key assumptions still need independent validation before detailed LCA.

## Traceability

Each scenario now has traceable module results for:

- capacity;
- corrosion;
- integrity;
- cost;
- pre-LCA gate.
- LCA screening proxy.

The JSON trace records the inputs, outputs, assumptions, warnings, and formula notes used by each module. This is the first building block for the future web app evidence panel.

## NETL Benchmark Plan

We should use NETL tools as external checks:

- REPACT: compare our Goldeneye transport capacity, pressure, and phase-screening behaviour.
- NETL CO2 Transport Cost Model / CO2_T_COM: compare our cost estimate and sensitivity to diameter, length, escalation, contingency, and booster stations.

The project should not depend on Excel workbooks as the core engine. The professional app should use transparent Python modules, with NETL outputs used as validation evidence.

## Next Technical Step

Run the batch screening command for all model-ready NSTA pipelines, then prioritise the top candidates for data enrichment.
