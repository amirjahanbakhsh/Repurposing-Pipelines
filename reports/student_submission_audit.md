# Student Submission Audit

## Notebook Structure

| Notebook | Cells | Code cells | Markdown cells | Output cells | Install commands | Generated files |
| --- | --- | --- | --- | --- | --- | --- |
| pipe_ev2.ipynb | 5 | 5 | 0 | 4 | 1 | 2 |
| corrosion_norsok2.ipynb | 11 | 11 | 0 | 9 | 0 | 0 |
| cost_model.ipynb | 15 | 15 | 0 | 14 | 2 | 0 |

## GeoJSON Completeness

| Field | Present | Missing or zero | Total |
| --- | --- | --- | --- |
| NSTAPIPNO | 27 | 0 | 27 |
| PIPE_NAME | 27 | 0 | 27 |
| FLUID | 27 | 0 | 27 |
| STATUS | 27 | 0 | 27 |
| DIAMETERMM | 27 | 0 | 27 |
| INT_DIAM | 27 | 0 | 27 |
| MX_OP_PRES | 1 | 26 | 27 |
| THICKNESS | 27 | 0 | 27 |
| OD_IN | 27 | 0 | 27 |
| ID_IN | 27 | 0 | 27 |
| PIPE_GRADE | 27 | 0 | 27 |
| START_DATE | 27 | 0 | 27 |

## Dataset Summary

- Total student GeoJSON records: 27
- Fluid counts: {'GAS': 20, 'OIL': 4, 'WATER': 3}
- Status counts: {'ACTIVE': 21, 'NOT IN USE': 6}
- Unique wall thickness values: 22.225
- Unique maximum operating pressure values: 0.0, 235.0
- Records found in full NSTA attribute table: 27
- Records found in model-ready ranked NSTA candidates: 1

## Goldeneye Records

| NSTAPIPNO | PIPE_NAME | STATUS | LENGTH_M | MX_OP_PRES | THICKNESS |
| --- | --- | --- | --- | --- | --- |
| PL1978 | 20" GAS GOLDENEYE - ST. FERGUS | NOT IN USE | 101676.7 | 0.0 | 22.225 |

## Data Differences To Investigate

These are differences between the student GeoJSON and the best-matched row in our full NSTA attribute extraction.

| NSTAPIPNO | PIPE_NAME | Field | Student | NSTA |
| --- | --- | --- | --- | --- |
| PL1761 | 20in Gas Trunkline - Schiehallion PLEM to Sullom Voe terminal | THICKNESS | 22.225 | 17.5 |
| PL1761 | 20in Gas Trunkline - Schiehallion PLEM to Sullom Voe terminal | START_DATE | 2001 | 2001-01-01 |
| PL19 | EKOFISK 2/4J TO TEESSIDE | THICKNESS | 22.225 | 0 |
| PL19 | EKOFISK 2/4J TO TEESSIDE | START_DATE | 1998 |  |
| PL21 | HEWETT NORTHERN EXPORT B-LINE TO BACTON | FLUID | GAS | SEAWATER |
| PL21 | HEWETT NORTHERN EXPORT B-LINE TO BACTON | THICKNESS | 22.225 | 0 |
| PL21 | HEWETT NORTHERN EXPORT B-LINE TO BACTON | START_DATE | 1968 | 1968-01-01 |
| PL20 | HEWETT SOUTHERN EXPORT A-LINE TO BACTON | FLUID | GAS | WATER |
| PL20 | HEWETT SOUTHERN EXPORT A-LINE TO BACTON | THICKNESS | 22.225 | 0 |
| PL20 | HEWETT SOUTHERN EXPORT A-LINE TO BACTON | START_DATE | 1973 | 1968-01-01 |
| PL1762 | EOS | MX_OP_PRES | 0.0 | 235 |
| PL1762 | EOS | THICKNESS | 22.225 | 0 |
| PL1762 | EOS | START_DATE | 2000 | 2000-04-12 |
| PL10 | NINIAN TO GRUTWICK MOL | MX_OP_PRES | 0.0 | 106 |
| PL10 | NINIAN TO GRUTWICK MOL | THICKNESS | 22.225 | 0 |
| PL10 | NINIAN TO GRUTWICK MOL | START_DATE | 1976 | 2000-04-17 |
| PL2071 | LANGELED PIPELINE | THICKNESS | 22.225 | 0 |
| PL2071 | LANGELED PIPELINE | START_DATE | 2006 | 2005-09-01 |
| PL1270 | BRITANNIA TO ST FERGUS | THICKNESS | 22.225 | 0 |
| PL1270 | BRITANNIA TO ST FERGUS | START_DATE | 2003 | 2003-10-01 |
| PL1966 | CALDER TO RIVERS ONSHORE TERMINAL | THICKNESS | 22.225 | 0 |
| PL1966 | CALDER TO RIVERS ONSHORE TERMINAL | START_DATE | 2002 | 2002-01-01 |
| PL929 | THEDDLETHORPE TO MURDOCH MD | THICKNESS | 22.225 | 0 |
| PL929 | THEDDLETHORPE TO MURDOCH MD | START_DATE | 1993 | 1993-01-01 |
| PL454 | LOGGS PP TO THEDDLETHORPE GAS LINE | THICKNESS | 22.225 | 0 |
| PL454 | LOGGS PP TO THEDDLETHORPE GAS LINE | START_DATE | 1988 | 1987-01-01 |
| PL27 | VIKING AR TO THEDDLETHORPE GAS LINE | THICKNESS | 22.225 | 0 |
| PL27 | VIKING AR TO THEDDLETHORPE GAS LINE | START_DATE | 1971 | 1971-01-01 |
| PL721 | FORTIES C TO CRUDEN BAY (PL721) | THICKNESS | 22.225 | 0 |
| PL721 | FORTIES C TO CRUDEN BAY (PL721) | START_DATE | 1992 | 2000-04-17 |
| PL311 | SEAN P TO BACTON TERMINAL TRUNKLINE | THICKNESS | 22.225 | 0 |
| PL311 | SEAN P TO BACTON TERMINAL TRUNKLINE | START_DATE | 1986 |  |
| PL876 | LANCELOT TO BACTON | THICKNESS | 22.225 | 0 |
| PL876 | LANCELOT TO BACTON | START_DATE | 1992 |  |
| PL447 | CLEETON CP TO DIMLINGTON | THICKNESS | 22.225 | 0 |
| PL447 | CLEETON CP TO DIMLINGTON | START_DATE | 1988 |  |
| PL23 | LEMAN 49/27 AP TO BACTON A1 | THICKNESS | 22.225 | 0 |
| PL23 | LEMAN 49/27 AP TO BACTON A1 | START_DATE | 1968 |  |
| PL145 | WEST SOLE TO EASINGTON 24IN GAS LINE | THICKNESS | 22.225 | 0 |
| PL145 | WEST SOLE TO EASINGTON 24IN GAS LINE | START_DATE | 1967 |  |

## Main Interpretation

- The notebooks are prototypes, not production-ready model code.
- The GeoJSON looks like a manually enriched shortlist, not a clean source dataset.
- Goldeneye is present but still has missing core engineering data.
- The student work is useful as a reference, but every model and assumption needs validation before reuse.
