# Pipeline Screen: nsta_pl774

Generated: 2026-06-10T09:39:27+00:00

Input assumptions: `model_layers/06_screening_and_decision/nsta_screening_defaults.csv`

Outputs:

- `model_layers/06_screening_and_decision/pipeline_screen_nsta_pl774.csv`
- `model_layers/06_screening_and_decision/pipeline_screen_nsta_pl774_trace.json`

## Plain Result

Pipeline: `CATS PIPELINE`

Input mode: `nsta_candidate_plus_defaults`

NSTA pipeline number: `PL774`

Decision: `fail`

Confidence: `medium`

Meaning: Do not move to LCA until failed technical or cost checks are resolved.

## Main Numbers

| Item | Value |
| --- | --- |
| CO2 capacity | 37.75 MtCO2/year |
| Required design flow | 5.88 MtCO2/year |
| Remaining life | 0.00 years |
| Remaining life range | 0.00 to 531.44 years |
| Available wall thickness | -0.93 mm |
| Corrosion risk | medium |
| Benchmark avoided new-build CAPEX | $910,078,962 |
| NETL cost check | not_supplied |
| LCA proxy saving | 93.9% |
| LCA screen | needs_data |

## Why This Decision?

- One or more upstream modules failed: integrity.

## Next Data To Check

- verify wall thickness and inspection records
- check pipe grade, design factor, defects, and pressure basis
- replace simple Barlow screening with a proper requalification method

## Important Caveat

This is a screening result, not engineering approval. The decision is only as strong as the input assumptions.
