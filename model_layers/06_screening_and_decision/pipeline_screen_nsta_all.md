# NSTA Pipeline Batch Screening

Generated: 2026-06-11T16:37:11+00:00

Candidate file: `model_layers/01_data_foundation/nsta_candidate_ranked.csv`

Default assumptions: `model_layers/06_screening_and_decision/nsta_screening_defaults.csv`

Outputs:

- `model_layers/06_screening_and_decision/pipeline_screen_nsta_all.csv`
- `model_layers/06_screening_and_decision/pipeline_screen_nsta_all_trace.json`
- `model_layers/06_screening_and_decision/refurbishment_work_scope_nsta_all.csv`

## Plain Result

This report screens all model-ready NSTA hydrocarbon pipeline candidates in one run.

This is the right first use of the tool: screen many pipelines, rank them, then inspect one pipeline in detail.

The full CSV keeps all screened records, including short connecting segments. The table below focuses on strategic pipelines at least 1 km long and keeps the longest record for each NSTA pipeline number.

Wall thickness is treated as uncertain for every pipeline, not only Goldeneye. Goldeneye simply uses a wider uncertainty band because its source data are less clear.

## Candidate Count

Screened pipelines: `155`

Strategic screened records at least 1 km long: `61`

Unique strategic NSTA pipeline numbers after keeping the longest record per number: `60`

## Pre-LCA Decisions

| Value | Count |
| --- | --- |
| fail | 43 |
| insufficient_data | 1 |
| marginal | 111 |

## Pre-LCA Decisions For Unique Strategic Pipelines

| Value | Count |
| --- | --- |
| fail | 29 |
| marginal | 31 |

## Corrosion Risk

| Value | Count |
| --- | --- |
| medium | 154 |
| not_assessed | 1 |

## Refurbishment Work-Scope Rows

Total work-scope rows: `1593`

These rows are written to the work-scope CSV. They are quantity drivers for future itemised cost and LCA, not final contractor estimates.

## Top 30 Strategic Screened Pipelines

| NSTA rank | NSTA no. | Pipeline | Fluid | Status | Length km | Decision | Capacity Mtpa | Life low | Life base | Life high | Corr. risk | Reuse gate | Evidence score | LCA saving % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PL774 | CATS PIPELINE | GAS | ACTIVE | 405.0 | fail | 37.75 | 0.0 | 0.0 | 531.4 | medium | fail | 23.5 | 93.9 |
| 2 | PL1761 | 20in Gas Trunkline - Schiehallion PLEM to Sullom Voe terminal | GAS | ACTIVE | 188.0 | fail | 17.10 | 0.0 | 0.0 | 211.2 | medium | fail | 23.5 | 92.1 |
| 3 | PL762 | SAGE PIPELINE | GAS | ACTIVE | 323.7 | fail | 25.66 | 0.0 | 0.0 | 409.0 | medium | fail | 23.5 | 93.4 |
| 4 | PL3088 | CYGNUS TO ETS GAS PIPELINE | GAS | ACTIVE | 50.2 | marginal | 27.25 | 2.9 | 72.5 | 696.1 | medium | marginal | 23.5 | 93.0 |
| 5 | PL2225 | BBL BALGZAND TO BACTON | GAS | ACTIVE | 229.3 | fail | 37.08 | 0.0 | 0.0 | 368.4 | medium | fail | 23.5 | 93.5 |
| 6 | PL164 | MAGNUS TO BRENT A (NLGP) | GAS | ACTIVE | 79.3 | marginal | 15.21 | 0.0 | 19.8 | 384.2 | medium | marginal | 23.5 | 91.9 |
| 7 | PL1339 | BACTON TO ZEEBRUGE | GAS | ACTIVE | 231.6 | fail | 53.11 | 0.0 | 0.0 | 266.4 | medium | fail | 23.5 | 93.7 |
| 10 | PL1849 | Central Gas Jumper from Manifold M1J to Manifold M1C | GAS | ACTIVE | 6.1 | fail | 131.48 | 0.0 | 0.0 | 240.2 | medium | fail | 23.5 | 92.7 |
| 11 | PL1360 | FPSO - 10in Production Flowline - 10in Flowline L43 | MIXED HYDROCARBONS | NOT IN USE | 35.3 | marginal | 11.33 | 8.6 | 86.2 | 776.6 | medium | marginal | 23.5 | 91.7 |
| 12 | PL3086 | CYGNUS A TO CYGNUS B GAS PIPELINE | GAS | ACTIVE | 7.7 | marginal | 30.29 | 0.0 | 70.8 | 754.3 | medium | marginal | 23.5 | 91.8 |
| 13 | PL872 | TIFFANY GAS EXPORT | GAS | ACTIVE | 36.4 | marginal | 7.93 | 0.0 | 11.8 | 323.2 | medium | marginal | 23.5 | 89.7 |
| 14 | PL3924 | 1in Gas Lift Line - Machar Gas Lift Manifold to Well W197 | GAS | ACTIVE | 4.1 | marginal | 18.27 | 343.5 | 829.7 | 4861.9 | medium | marginal | 23.5 | 94.2 |
| 15 | PL1361 | FPSO - 8in Production Flowline - 8in Flowline L42 | MIXED HYDROCARBONS | NOT IN USE | 22.8 | marginal | 9.58 | 59.5 | 195.6 | 1361.5 | medium | marginal | 23.5 | 92.3 |
| 16 | PL2141 | FPSO - 10in Production Flowline - 10in Flowline L27 | MIXED HYDROCARBONS | NOT IN USE | 22.9 | marginal | 9.55 | 59.5 | 195.6 | 1361.5 | medium | marginal | 23.5 | 92.3 |
| 17 | PL2921 | EAST ROCHELLE TO SSIV ROCHELLE | GAS | ACTIVE | 29.6 | marginal | 7.34 | 15.9 | 87.5 | 716.6 | medium | marginal | 23.5 | 90.8 |
| 18 | PL1257A | ERSKINE TO LOMOND GAS CONDENSATE LINE | CONDENSATE | ACTIVE | 30.2 | marginal | 9.77 | 11.0 | 65.3 | 543.5 | medium | marginal | 23.5 | 91.3 |
| 19 | PL917 | NINIAN CENTRAL GAS IMPORT FROM BRENT WLGP | GAS | ACTIVE | 25.5 | marginal | 12.95 | 7.4 | 64.5 | 571.6 | medium | marginal | 23.5 | 91.6 |
| 20 | PL1340 | BACTON TO ZEEBRUGE (onshore) | GAS | ACTIVE | 1.4 | marginal | 633.49 | 0.0 | 18.9 | 612.2 | medium | marginal | 23.5 | 94.0 |
| 21 | PL1760 | 12in Gas Export - Schiehallion M1C to Schiehallion PLEM | GAS | ACTIVE | 17.0 | marginal | 17.51 | 0.0 | 2.2 | 290.5 | medium | marginal | 23.5 | 90.3 |
| 34 | PL918 | STRATHSPEY TO NINIAN CENTRAL (PL918) | MIXED HYDROCARBONS | NOT IN USE | 15.6 | marginal | 7.79 | 36.3 | 128.4 | 921.2 | medium | marginal | 23.5 | 91.2 |
| 35 | PL1387 | FPSO - 8in Production Flowline - 8in Flowline L2 | MIXED HYDROCARBONS | NOT IN USE | 20.0 | marginal | 10.22 | 0.0 | 52.2 | 545.6 | medium | marginal | 23.5 | 90.5 |
| 36 | PL6385 | AFFLECK PRODUCTION PIPE-IN-PIPE FROM AFFLECK MANIFOLD TO TALBOT MANIFOLD | MIXED HYDROCARBONS | ACTIVE | 21.0 | marginal | 6.71 | 2.2 | 66.2 | 640.7 | medium | marginal | 23.5 | 90.0 |
| 37 | PL1384 | FPSO - 10in Production Flowline - 10in Flowline L4 | MIXED HYDROCARBONS | NOT IN USE | 15.6 | marginal | 11.60 | 0.0 | 52.2 | 545.6 | medium | marginal | 23.5 | 90.5 |
| 40 | PL2922 | WEST ROCHELLE TO EAST ROCHELLE PL2922 | GAS | ACTIVE | 7.6 | marginal | 14.49 | 15.9 | 87.5 | 716.6 | medium | marginal | 23.5 | 90.8 |
| 41 | PL919 | STRATHSPEY TO NINIAN CENTRAL (PL919) | MIXED HYDROCARBONS | NOT IN USE | 15.6 | fail | 4.32 | 33.8 | 114.7 | 809.2 | medium | fail | 23.5 | 90.0 |
| 42 | PL920 | STRATHSPEY TO NINIAN CENTRAL (PL920) | MIXED HYDROCARBONS | NOT IN USE | 15.6 | fail | 4.28 | 34.0 | 115.1 | 810.5 | medium | fail | 23.5 | 90.0 |
| 43 | PL921 | STRATHSPEY TO NINIAN CENTRAL (PL921) | MIXED HYDROCARBONS | NOT IN USE | 15.6 | fail | 4.30 | 34.0 | 115.1 | 810.5 | medium | fail | 23.5 | 90.0 |
| 44 | PL1386 | FPSO - 10in Production Flowline - 10in Flowline L5 | MIXED HYDROCARBONS | NOT IN USE | 35.4 | fail | 2.43 | 0.0 | 9.6 | 220.5 | medium | fail | 23.5 | 86.4 |
| 46 | PL1648 | TRITON FPSO TO BITTERN DCB OIL LINE 2 | MIXED HYDROCARBONS | ACTIVE | 20.2 | marginal | 7.37 | 3.2 | 48.5 | 452.9 | medium | marginal | 23.5 | 89.7 |
| 47 | PL1652 | GW PROD LINE 1 DC1 VIA DC2 TO TRITON FPSO | MIXED HYDROCARBONS | ACTIVE | 3.1 | marginal | 32.88 | 20.0 | 92.2 | 722.1 | medium | marginal | 23.5 | 91.4 |

## How To Use This

1. Start with the top table.
2. Pick a pipeline number such as `PL774`.
3. Run the single-pipeline command for a detailed report:

```powershell
python scripts\run_pipeline_screen.py --nsta-id PL774
```

## Important Caveat

This is still screening. The strongest candidates are not approved pipelines. They are candidates for data enrichment, technical validation, NETL cost comparison, and proper LCA.
