# Goldeneye Benchmark

Generated: 2026-06-09T16:16:31+00:00

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
- Reported values are the values from the dissertation or poster.
- Calculated values are produced by our Python code.
- Small differences are expected because of rounding.

## Capacity Benchmark

| Scenario | ID in | Average pressure MPa | Calculated capacity Mtpa | Reported capacity Mtpa | Meets 5 Mtpa target? |
| --- | --- | --- | --- | --- | --- |
| goldeneye_dissertation | 18.250 | 9.956 | 9.131 | 9.125 | yes |
| goldeneye_poster | 18.876 | 9.956 | 9.968 | 9.961 | yes |

## Integrity / Lifetime Benchmark

| Scenario | Nominal wall mm | Wall loss mm | Available wall mm | Future corrosion mm/yr | Calculated life years | Reported life years |
| --- | --- | --- | --- | --- | --- | --- |
| goldeneye_dissertation | 22.23 | 8.21 | 7.79 | 0.10 | 77.94 | 78.00 |
| goldeneye_poster | 14.28 | 2.93 | 4.91 | 0.20 | 24.55 | 24.54 |

## Cost Benchmark

| Scenario | Subtotal | Contingency | Calculated total | Reported total |
| --- | --- | --- | --- | --- |
| goldeneye_dissertation | $207,728,010 | $20,772,801 | $228,500,811 | $228,500,812 |
| goldeneye_poster | $207,728,010 | $20,772,801 | $228,500,811 | $228,500,812 |

## Interpretation

- The dissertation and poster use different Goldeneye wall-thickness assumptions.
- The dissertation case uses a thicker nominal wall (`22.23 mm`) and lower future CO2 corrosion rate (`0.10 mm/year`), which gives a much longer remaining life.
- The poster case uses a lower nominal wall (`14.28 mm`) and higher future CO2 corrosion rate (`0.20 mm/year`), which gives about `24.5 years`.
- The capacity difference is mainly caused by the internal diameter/friction assumptions: `18.25 in` in the dissertation case versus about `18.876 in` in the poster case.
- Cost is consistent between the two versions because both use the same Parker-style new-build cost breakdown.

## Traceability

Each scenario now has traceable module results for:

- capacity;
- integrity;
- cost.

The JSON trace records the inputs, outputs, assumptions, warnings, and formula notes used by each module. This is the first building block for the future web app evidence panel.

## NETL Benchmark Plan

We should use NETL tools as external checks:

- REPACT: compare our Goldeneye transport capacity, pressure, and phase-screening behaviour.
- NETL CO2 Transport Cost Model / CO2_T_COM: compare our cost estimate and sensitivity to diameter, length, escalation, contingency, and booster stations.

The project should not depend on Excel workbooks as the core engine. The professional app should use transparent Python modules, with NETL outputs used as validation evidence.

## Next Technical Step

Add a simple pre-LCA gate that consumes the capacity, integrity, and cost module results and returns:

- `pass`;
- `marginal`;
- `fail`;
- `insufficient_data`.
