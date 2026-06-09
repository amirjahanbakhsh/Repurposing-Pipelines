# NSTA Candidate Ranking

Generated: 2026-06-09T13:46:32+00:00

Input data: `data/processed/nsta_pipeline_attributes.csv`

Ranking script: `scripts/rank_nsta_candidates.py`

## What This Ranking Means

This is a first-pass data ranking, not an engineering approval.

The script ranks only hydrocarbon pipelines (`GAS`, `CONDENSATE`, `MIXED HYDROCARBONS`) with usable positive values for:

- internal diameter;
- max operating pressure;
- wall thickness.

The score favours larger internal diameter, higher operating pressure, thicker wall, longer route, more reusable-looking status, and presence of start date.

## Candidate Counts

| Group | Count |
| --- | --- |
| All NSTA records | 9025 |
| Model-ready hydrocarbon candidates | 155 |
| Model-ready candidates with `ACTIVE` or `NOT IN USE` status | 152 |
| Model-ready records where `INF_TYPE = PIPELINE` | 149 |
| Model-ready pipeline records at least 1 km long | 61 |
| Model-ready pipeline records at least 10 km long | 37 |

## Top 30 Model-Ready Pipeline Candidates At Least 1 km Long

| Rank | Score | NSTA no. | Pipeline | Type | Fluid | Status | ID mm | Pressure barg | Thickness mm | Length km | Start |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 69.2 | PL774 | CATS PIPELINE | PIPELINE | GAS | ACTIVE | 857.6 | 179.3 | 28.4 | 405.0 | 1993-01-26 |
| 2 | 67.4 | PL1761 | 20in Gas Trunkline - Schiehallion PLEM to Sullom Voe terminal | PIPELINE | GAS | ACTIVE | 473 | 235 | 17.5 | 188.0 | 2001-01-01 |
| 3 | 67.4 | PL762 | SAGE PIPELINE | PIPELINE | GAS | ACTIVE | 716.5 | 172.3 | 22.7 | 323.7 | 1992-08-01 |
| 4 | 65.4 | PL3088 | CYGNUS TO ETS GAS PIPELINE | PIPELINE | GAS | ACTIVE | 565 | 139.3 | 22.2 | 50.2 | 2014-05-14 |
| 5 | 64.9 | PL2225 | BBL BALGZAND TO BACTON | PIPELINE | GAS | ACTIVE | 872.6 | 137.4 | 20.9 | 229.3 | 2006-07-14 |
| 6 | 62.0 | PL164 | MAGNUS TO BRENT A (NLGP) | PIPELINE | GAS | ACTIVE | 476 | 147 | 15.9 | 79.3 | 2000-04-17 |
| 7 | 60.7 | PL1339 | BACTON TO ZEEBRUGE | PIPELINE | GAS | ACTIVE | 972.48 | 147 | 21.76 | 231.6 |  |
| 10 | 58.7 | PL1849 | Central Gas Jumper from Manifold M1J to Manifold M1C | PIPELINE | GAS | ACTIVE | 517.56 | 257 | 20.62 | 6.1 |  |
| 11 | 56.7 | PL1360 | FPSO - 10in Production Flowline - 10in Flowline L43 | PIPELINE | MIXED HYDROCARBONS | NOT IN USE | 276.1 | 257 | 23.9 | 35.3 |  |
| 12 | 55.1 | PL3086 | CYGNUS A TO CYGNUS B GAS PIPELINE | PIPELINE | GAS | ACTIVE | 273 | 325 | 25.4 | 7.7 | 2014-05-16 |
| 13 | 54.2 | PL872 | TIFFANY GAS EXPORT | PIPELINE | GAS | ACTIVE | 244.5 | 248 | 14.3 | 36.4 | 1992-01-01 |
| 14 | 53.7 | PL3924 | 1in Gas Lift Line - Machar Gas Lift Manifold to Well W197 | PIPELINE | GAS | ACTIVE | 254 | 182 | 98.05 | 4.1 |  |
| 15 | 53.2 | PL1361 | FPSO - 8in Production Flowline - 8in Flowline L42 | PIPELINE | MIXED HYDROCARBONS | NOT IN USE | 236.5 | 257 | 34 | 22.8 |  |
| 16 | 53.2 | PL2141 | FPSO - 10in Production Flowline - 10in Flowline L27 | PIPELINE | MIXED HYDROCARBONS | NOT IN USE | 236.5 | 257 | 34 | 22.9 |  |
| 17 | 52.9 | PL2921 | EAST ROCHELLE TO SSIV ROCHELLE | PIPELINE | GAS | ACTIVE | 228.7 | 245 | 20.6 | 29.6 | 2012-09-23 |
| 18 | 52.9 | PL1257A | ERSKINE TO LOMOND GAS CONDENSATE LINE | PIPELINE | CONDENSATE | ACTIVE | 374.6 | 118 | 15.9 | 30.2 | 2001-09-25 |
| 19 | 52.8 | PL917 | NINIAN CENTRAL GAS IMPORT FROM BRENT WLGP | PIPELINE | GAS | ACTIVE | 371.4 | 136 | 17.5 | 25.5 | 1992-01-01 |
| 20 | 52.0 | PL1340 | BACTON TO ZEEBRUGE (onshore) | PIPELINE | GAS | ACTIVE | 972.48 | 140 | 27.46 | 1.4 |  |
| 21 | 51.2 | PL1760 | 12in Gas Export - Schiehallion M1C to Schiehallion PLEM | PIPELINE | GAS | ACTIVE | 295.3 | 235 | 14.3 | 17.0 | 2001-01-01 |
| 34 | 49.9 | PL918 | STRATHSPEY TO NINIAN CENTRAL (PL918) | PIPELINE | MIXED HYDROCARBONS | NOT IN USE | 225.4 | 201 | 23.8 | 15.6 | 1992-01-01 |
| 35 | 48.8 | PL1387 | FPSO - 8in Production Flowline - 8in Flowline L2 | PIPELINE | MIXED HYDROCARBONS | NOT IN USE | 236.5 | 257 | 18.3 | 20.0 |  |
| 36 | 48.4 | PL6385 | AFFLECK PRODUCTION PIPE-IN-PIPE FROM AFFLECK MANIFOLD TO TALBOT MANIFOLD | PIPELINE | MIXED HYDROCARBONS | ACTIVE | 177.9 | 345 | 20.6 | 21.0 |  |
| 37 | 47.6 | PL1384 | FPSO - 10in Production Flowline - 10in Flowline L4 | PIPELINE | MIXED HYDROCARBONS | NOT IN USE | 236.5 | 257 | 18.3 | 15.6 |  |
| 40 | 46.7 | PL2922 | WEST ROCHELLE TO EAST ROCHELLE PL2922 | PIPELINE | GAS | ACTIVE | 228.7 | 245 | 20.6 | 7.6 | 2012-10-10 |
| 41 | 46.4 | PL919 | STRATHSPEY TO NINIAN CENTRAL (PL919) | PIPELINE | MIXED HYDROCARBONS | NOT IN USE | 177.9 | 201 | 20.6 | 15.6 | 1992-01-01 |
| 42 | 46.3 | PL920 | STRATHSPEY TO NINIAN CENTRAL (PL920) | PIPELINE | MIXED HYDROCARBONS | NOT IN USE | 177.9 | 200 | 20.6 | 15.6 | 1992-01-01 |
| 43 | 46.3 | PL921 | STRATHSPEY TO NINIAN CENTRAL (PL921) | PIPELINE | MIXED HYDROCARBONS | NOT IN USE | 177.9 | 200 | 20.6 | 15.6 | 1992-01-01 |
| 44 | 46.1 | PL1386 | FPSO - 10in Production Flowline - 10in Flowline L5 | PIPELINE | MIXED HYDROCARBONS | NOT IN USE | 149.3 | 257 | 9.5 | 35.4 |  |
| 46 | 45.8 | PL1648 | TRITON FPSO TO BITTERN DCB OIL LINE 2 | PIPELINE | MIXED HYDROCARBONS | ACTIVE | 244.5 | 180 | 14.3 | 20.2 | 2003-03-04 |
| 47 | 45.8 | PL1652 | GW PROD LINE 1 DC1 VIA DC2 TO TRITON FPSO | PIPELINE | MIXED HYDROCARBONS | ACTIVE | 304.8 | 180 | 20 | 3.1 | 2020-09-01 |

## Known CCS / Reuse Name Check

| Search term | All NSTA matches | Hydrocarbon matches | Model-ready matches | Best / example match |
| --- | --- | --- | --- | --- |
| GOLDENEYE | 92 | 1 | 0 | not model-ready: 20" GAS GOLDENEYE - ST. FERGUS |
| ATLANTIC | 18 | 4 | 0 | not model-ready: 4" MEG ST. FERGUS - ATLANTIC MANIFOLD |
| CROMARTY | 3 | 1 | 0 | not model-ready: 12" GAS CROMARTY WELL 1 - ATLANTIC MANIFOLD |
| MILLER | 8 | 0 | 0 | not model-ready: Isolation control umbilical to 16" SSIVat Miller |
| HAMILTON | 9 | 0 | 0 | not model-ready: DOUGLAS TO HAMILTON |
| CAMELOT | 3 | 1 | 0 | not model-ready: CAMELOT CA GAS EXPORT TO LEMAN 27A |
| BEATRICE | 29 | 0 | 0 | not model-ready: JACKY TO BEATRICE AP PRODUCTION |
| ST FERGUS | 3 | 3 | 1 | rank 3: SAGE PIPELINE |
| ST. FERGUS | 200 | 5 | 0 | not model-ready: HFC TO ST. FERGUS SOUTH |
| ACORN | 0 | 0 | 0 |  |
| BRAE | 189 | 42 | 1 | rank 13: TIFFANY GAS EXPORT |
| SAGE | 15 | 13 | 5 | rank 3: SAGE PIPELINE |
| CAPTAIN | 100 | 7 | 0 | not model-ready: PL2072 - BUZZARD GAS EXPORT SSIV TO BUZZARD EXPORT PLEM |
| FORTIES | 60 | 13 | 0 | not model-ready: ETAP Marnock to Forties Unity 24in Oil Export Line |

## Early Observations

- Goldeneye is present in the NSTA data, including the `20" GAS GOLDENEYE - ST. FERGUS` line, but its NSTA engineering fields are zero in this extract, so it is not in the strict model-ready ranked set.
- This matches the project recollection that Goldeneye data was difficult to source and likely needed extra enrichment or assumptions in the student work.
- Atlantic and Cromarty names are present, but the obvious Shell gas lines in this extract also have zero engineering fields, so they are not model-ready from NSTA alone.
- The highest-ranked model-ready long pipeline records include CATS, SAGE, BBL, Schiehallion, Cygnus, Magnus/NLGP, and Bacton-Zeebrugge style trunk lines.
- This confirms that the missing student clean table probably depended on extra sources or assumptions for some high-value CCS candidates.
- The next step is targeted enrichment: take known CCS/reuse candidates first, then fill wall thickness, material grade, pressure, and start year from reports, decommissioning documents, and operator publications.

## Sources For Known-Name Checks

- BEIS/GOV.UK consultation and Annex A on re-use of oil and gas assets for CCUS: https://www.gov.uk/government/consultations/carbon-capture-usage-and-storage-ccus-projects-re-use-of-oil-and-gas-assets
- IEAGHG note on re-use case studies including Camelot, Atlantic & Cromarty, Hamilton, Goldeneye, and Beatrice: https://ieaghg.org/news/new-ieaghg-technical-report-2018-06-re-use-of-oil-gas-facilities-for-co2-transport-and-storage/
- NSTA Energy Pathfinder note on Atlantic and Cromarty decommissioning being held for CCUS re-use investigation: https://energypathfinder.nstauthority.co.uk/projects/207
- Shell Atlantic and Cromarty decommissioning page: https://www.shell.co.uk/about-us/sustainability/decommissioning/atlantic-and-cromarty.html
