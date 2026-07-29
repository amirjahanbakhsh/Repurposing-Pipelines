# NSTA Wall-Thickness Pressure Check

Generated: 2026-07-29T14:56:36+00:00

Model version: `wall_thickness_pressure_check_v0.1`

Candidate file: `model_layers/01_data_foundation/nsta_candidate_ranked.csv`

Default assumptions: `model_layers/06_screening_and_decision/nsta_screening_defaults.csv`

CSV output: `model_layers/03_corrosion_integrity/nsta_wall_thickness_pressure_check.csv`

## Purpose

This check applies a simple Barlow-style pressure wall-thickness calculation to the model-ready NSTA candidate list.

It is not a design-code calculation and it is not engineering approval. It is a triage check: it identifies candidates whose reported wall thickness is close to, or below, the pressure-based screening minimum before detailed integrity, inspection, and requalification evidence is gathered.

## Status Counts

| Status | Count |
| --- | --- |
| fail_sanity | 6 |
| pass_sanity | 137 |
| review_required | 12 |

## Flagged Candidates

| Rank | NSTA no. | Pipeline | Length km | Wall mm | Min wall mm | Margin % | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | PL1849 | Central Gas Jumper from Manifold M1J to Manifold M1C | 6.1 | 20.62 | 24.201952 | -17.4 | fail_sanity |
| 7 | PL1339 | BACTON TO ZEEBRUGE | 231.6 | 21.76 | 25.243309 | -16.0 | fail_sanity |
| 2 | PL1761 | 20in Gas Trunkline - Schiehallion PLEM to Sullom Voe terminal | 188.0 | 17.5 | 20.125751 | -15.0 | fail_sanity |
| 32 | PL2759J2 | LAGGAN MANIFOLD TO ILT 1-1/2 ON PL2759 | 0.1 | 21.44 | 23.745578 | -10.8 | fail_sanity |
| 33 | PL2759J1 | TORMORE MANIFOLD TO TORMORE FLET 1-1 | 0.1 | 21.44 | 23.745578 | -10.8 | fail_sanity |
| 5 | PL2225 | BBL BALGZAND TO BACTON | 229.3 | 20.9 | 21.245447 | -1.7 | fail_sanity |
| 3 | PL762 | SAGE PIPELINE | 323.7 | 22.7 | 22.165714 | 2.4 | review_required |
| 1 | PL774 | CATS PIPELINE | 405.0 | 28.4 | 27.676798 | 2.5 | review_required |
| 21 | PL1760 | 12in Gas Export - Schiehallion M1C to Schiehallion PLEM | 17.0 | 14.3 | 12.832147 | 10.3 | review_required |
| 20 | PL1340 | BACTON TO ZEEBRUGE (onshore) | 1.4 | 27.46 | 24.319322 | 11.4 | review_required |
| 53 | PL1645 | TRITON FPSO TO GANNET DIVERTER | 12.0 | 10.9 | 9.215064 | 15.5 | review_required |
| 107 | PL1645 | GAS EXPORT FLEXIBLE RISER | 0.6 | 10.9 | 9.215064 | 15.5 | review_required |
| 59 | PL3080JMDC5 | STELLA MDC TO WELL A3Y (SCP2) PRODUCTION | 0.1 | 14.3 | 11.929443 | 16.6 | review_required |
| 60 | PL3080JMDC4 | STELLA MDC TO WELL A2Z (SCP3) PRODUCTION | 0.1 | 14.3 | 11.929443 | 16.6 | review_required |
| 61 | PL3080JNDC1 | STELLA NDC MANIFOLD TO WELL B1X (SNP2) PRODUCTION | 0.1 | 14.3 | 11.929443 | 16.6 | review_required |
| 8 | PL774 | CATS PIPELINE | 0.1 | 33.9 | 28.009743 | 17.4 | review_required |
| 100 | PL2201 | W124 to Machar Production Manifold 6in Production Line | 0.1 | 12.3 | 9.90271 | 19.5 | review_required |
| 101 | PL1357JW122 | W122 to Machar Production Manifold 6in Production Line | 0.1 | 12.3 | 9.90271 | 19.5 | review_required |

## Formula

`minimum wall = pressure * outside diameter / (2 * SMYS * design factor)`

The current screening basis uses:

- pressure from NSTA `MX_OP_PRES` in barg plus atmospheric pressure for consistency with the current NSTA screening model;
- outside diameter estimated as `internal diameter + 2 * reported wall thickness`;
- default pipe grade and SMYS from `nsta_screening_defaults.csv`;
- default design factor from `nsta_screening_defaults.csv`;
- review flag when the pressure margin is below the configured wall-pressure margin threshold.

## Next Use

Use this report to prioritise integrity evidence collection. For flagged rows, check the true design pressure basis, diameter basis, wall schedule, material grade, corrosion allowance, inspection records, defects, and code/requalification method.
