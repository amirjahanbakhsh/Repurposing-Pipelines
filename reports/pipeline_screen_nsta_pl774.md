# Pipeline Screen: nsta_pl774

Generated: 2026-06-09T17:09:21+00:00

Input assumptions: `data/inputs/nsta_screening_defaults.csv`

Outputs:

- `data/processed/pipeline_screen_nsta_pl774.csv`
- `data/processed/pipeline_screen_nsta_pl774_trace.json`

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
| Available wall thickness | -0.93 mm |
| Benchmark avoided new-build CAPEX | $910,078,962 |

## Why This Decision?

- One or more upstream modules failed: integrity.

## Next Data To Check

- verify wall thickness and inspection records
- check pipe grade, design factor, defects, and pressure basis
- replace simple Barlow screening with a proper requalification method

## Important Caveat

This is a screening result, not engineering approval. The decision is only as strong as the input assumptions.
