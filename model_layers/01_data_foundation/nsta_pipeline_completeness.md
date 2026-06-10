# NSTA Pipeline Completeness Report

Generated: 2026-06-09T13:28:58+00:00

Source layer: https://services-eu1.arcgis.com/OZMfUznmLTnWccBc/arcgis/rest/services/UKCS%20offshore%20infrastructure%20pipeline%20linear%20ED50/FeatureServer/0

Extraction script: `scripts/extract_nsta_pipeline_data.py`

Total pipeline features: 9025

Hydrocarbon candidate features (`GAS`, `CONDENSATE`, `MIXED HYDROCARBONS`): 1627

Hydrocarbon features with status `ACTIVE` or `NOT IN USE`: 1506

Geometry extracted in this run: no

## Completeness - All Pipeline Features

| Field | Present | Missing | Completeness |
| --- | --- | --- | --- |
| FLUID | 5699 | 3326 | 63.1% |
| STATUS | 9025 | 0 | 100.0% |
| INT_DIAM | 6391 | 2634 | 70.8% |
| MX_OP_PRES | 6398 | 2627 | 70.9% |
| THICKNESS | 6468 | 2557 | 71.7% |
| START_DATE | 2042 | 6983 | 22.6% |

## Completeness - Hydrocarbon Candidate Features

| Field | Present | Missing | Completeness |
| --- | --- | --- | --- |
| FLUID | 1627 | 0 | 100.0% |
| STATUS | 1627 | 0 | 100.0% |
| INT_DIAM | 1439 | 188 | 88.4% |
| MX_OP_PRES | 1438 | 189 | 88.4% |
| THICKNESS | 1444 | 183 | 88.8% |
| START_DATE | 512 | 1115 | 31.5% |

## Usable Completeness - All Pipeline Features

| Field | Usable | Not usable | Usable completeness |
| --- | --- | --- | --- |
| FLUID | 5699 | 3326 | 63.1% |
| STATUS | 9025 | 0 | 100.0% |
| INT_DIAM | 782 | 8243 | 8.7% |
| MX_OP_PRES | 652 | 8373 | 7.2% |
| THICKNESS | 524 | 8501 | 5.8% |
| START_DATE | 2042 | 6983 | 22.6% |

## Usable Completeness - Hydrocarbon Candidate Features

| Field | Usable | Not usable | Usable completeness |
| --- | --- | --- | --- |
| FLUID | 1627 | 0 | 100.0% |
| STATUS | 1627 | 0 | 100.0% |
| INT_DIAM | 285 | 1342 | 17.5% |
| MX_OP_PRES | 323 | 1304 | 19.9% |
| THICKNESS | 202 | 1425 | 12.4% |
| START_DATE | 512 | 1115 | 31.5% |

## Usable Completeness - Active / Not-In-Use Hydrocarbon Features

| Field | Usable | Not usable | Usable completeness |
| --- | --- | --- | --- |
| FLUID | 1506 | 0 | 100.0% |
| STATUS | 1506 | 0 | 100.0% |
| INT_DIAM | 281 | 1225 | 18.7% |
| MX_OP_PRES | 318 | 1188 | 21.1% |
| THICKNESS | 198 | 1308 | 13.1% |
| START_DATE | 456 | 1050 | 30.3% |

## Combined Readiness For Screening

| Subset | Total | Usable ID + pressure + thickness | Usable ID + pressure + thickness + start date |
| --- | --- | --- | --- |
| Hydrocarbon candidates | 1627 | 155 | 46 |
| Active / not-in-use hydrocarbon | 1506 | 152 | 44 |

## Valid Numeric Field Ranges - All Pipeline Features

| Field | Count | Min | Median | Max |
| --- | --- | --- | --- | --- |
| INT_DIAM | 782 | 6.35 | 140.0 | 972.48 |
| MX_OP_PRES | 652 | 10.0 | 257.0 | 3750.0 |
| THICKNESS | 524 | 0.6 | 15.9 | 98.05 |
| LENGTH_M | 7056 | 0.8 | 90.257798165 | 543048.2 |

## Fluid Values

| Fluid | Count |
| --- | --- |
| GAS | 1068 |
| WATER | 721 |
| OTHER FLUID | 646 |
| HYDRAULIC | 632 |
| CHEMICAL | 586 |
| MIXED HYDROCARBONS | 500 |
| OIL | 490 |
| SERVICES | 335 |
| ELECTRICAL/CONTROLS | 299 |
| SEAWATER | 180 |
| METHANOL | 142 |
| CONDENSATE | 59 |

## Status Values

| Status | Count |
| --- | --- |
| ACTIVE | 6298 |
| NOT IN USE | 2192 |
| ABANDONED | 483 |
| PRECOMMISSIONED | 26 |
| REMOVED | 19 |
| PROPOSED | 7 |

## Notes

- `START_DATE`, `END_DATE`, and `UPD_DATE` are converted from ArcGIS timestamps to ISO dates in the CSV.
- Completeness only checks whether a value is present. It does not prove the value is correct.
- Usable completeness treats `-9999`, zero, negative, and blank values as not usable for numeric engineering fields.
- Wall thickness, internal diameter, and max operating pressure should still be validated for key candidate pipelines before use in engineering calculations.
- Missing or assumed values should be shown clearly in the future app.
- Run `python scripts/extract_nsta_pipeline_data.py --include-geometry` when full map geometry is needed.
- The full GeoJSON geometry extract is large and is ignored by Git in `.gitignore`; use Git LFS or regenerate locally if it needs to be shared.
