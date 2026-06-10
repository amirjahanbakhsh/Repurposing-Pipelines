# Pipeline Screen: goldeneye_poster

Generated: 2026-06-10T09:40:06+00:00

Input assumptions: `model_layers/06_screening_and_decision/goldeneye_assumptions.csv`

Outputs:

- `model_layers/06_screening_and_decision/pipeline_screen_goldeneye_poster.csv`
- `model_layers/06_screening_and_decision/pipeline_screen_goldeneye_poster_trace.json`

## Plain Result

Pipeline: `20" GAS GOLDENEYE - ST. FERGUS`

Input mode: `scenario_assumptions`

NSTA pipeline number: `not applicable`

Decision: `marginal`

Confidence: `medium`

Meaning: Move to LCA only as a sensitivity case until assumptions are checked.

## Main Numbers

| Item | Value |
| --- | --- |
| CO2 capacity | 9.97 MtCO2/year |
| Required design flow | 5.88 MtCO2/year |
| Remaining life | 24.55 years |
| Remaining life range | 0.00 to 247.25 years |
| Available wall thickness | 4.91 mm |
| Corrosion risk | medium |
| Benchmark avoided new-build CAPEX | $228,500,811 |
| NETL cost check | not_supplied |
| LCA proxy saving | 91.6% |
| LCA screen | favour_reuse |

## Why This Decision?

- Capacity passes: 9.97 MtCO2/year versus 5.88 MtCO2/year required.
- Integrity passes at screening level: 24.55 years remaining life and 4.91 mm available wall.
- Cost screen is positive: benchmark avoided new-build CAPEX is $228,500,811.
- Some important values are assumed or sensitivity inputs: capacity_factor, contingency_fraction, future_co2_corrosion_rate_high_mm_per_year, future_co2_corrosion_rate_low_mm_per_year, future_co2_corrosion_rate_mm_per_year, historical_wall_loss_uncertainty_fraction, inner_diameter_in, minimum_wall_thickness_uncertainty_fraction, nominal_wall_thickness_uncertainty_fraction.
- Upstream modules still contain validation warnings.

## Next Data To Check

- verify wall thickness and inspection records
- validate CO2 density, viscosity, compressibility, and phase behaviour
- compare cost with NETL CO2_T_COM or another external benchmark
- define reuse modification cost before detailed LCA

## Important Caveat

This is a screening result, not engineering approval. The decision is only as strong as the input assumptions.
