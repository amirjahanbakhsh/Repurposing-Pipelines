# Pipeline Screen: goldeneye_poster

Generated: 2026-06-09T16:56:43+00:00

Input assumptions: `data/benchmarks/goldeneye_assumptions.csv`

Outputs:

- `data/processed/pipeline_screen_goldeneye_poster.csv`
- `data/processed/pipeline_screen_goldeneye_poster_trace.json`

## Plain Result

Pipeline: `20" GAS GOLDENEYE - ST. FERGUS`

Decision: `marginal`

Confidence: `medium`

Meaning: Move to LCA only as a sensitivity case until assumptions are checked.

## Main Numbers

| Item | Value |
| --- | --- |
| CO2 capacity | 9.97 MtCO2/year |
| Required design flow | 5.88 MtCO2/year |
| Remaining life | 24.55 years |
| Available wall thickness | 4.91 mm |
| Benchmark avoided new-build CAPEX | $228,500,811 |

## Why This Decision?

- Capacity passes: 9.97 MtCO2/year versus 5.88 MtCO2/year required.
- Integrity passes at screening level: 24.55 years remaining life and 4.91 mm available wall.
- Cost screen is positive: benchmark avoided new-build CAPEX is $228,500,811.
- Some important values are assumed or sensitivity inputs: capacity_factor, contingency_fraction, future_co2_corrosion_rate_mm_per_year, inner_diameter_in.
- Upstream modules still contain validation warnings.

## Next Data To Check

- verify wall thickness and inspection records
- validate CO2 density, viscosity, compressibility, and phase behaviour
- compare cost with NETL CO2_T_COM or another external benchmark
- define reuse modification cost before detailed LCA

## Important Caveat

This is a screening result, not engineering approval. The decision is only as strong as the input assumptions.
