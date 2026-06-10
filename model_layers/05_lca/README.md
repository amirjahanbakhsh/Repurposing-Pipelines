# 05 LCA

LCA inventory templates, ecoinvent process mapping, conditional LCA reports, and LCA method references.

The current LCA workflow is ecoinvent-linked but not yet decision-grade. It creates the pipeline inventory and checks which private impact factors are missing. Final kg CO2e numbers need a private ecoinvent/openLCA/Brightway factor file.

## Simple Commands

Create the private factor template:

```powershell
python scripts\run_ecoinvent_lca.py --create-factor-template
```

Run Goldeneye:

```powershell
python scripts\run_ecoinvent_lca.py --scenario goldeneye_poster
```

Run one NSTA pipeline:

```powershell
python scripts\run_ecoinvent_lca.py --nsta-id PL774
```

If the report says `blocked_missing_impact_factors`, that is expected until the private factor CSV is filled.

| File | Purpose |
| --- | --- |
| `lca_inventory_template.csv` | Main LCA inventory input template. |
| `lca_process_mapping.csv` | Shareable ecoinvent process-mapping metadata. |
| `lca_impact_factors_template.csv` | Blank template showing the private factors needed. |
| `lca_report_goldeneye_poster.md` | Current Goldeneye conditional LCA report. |
| `lca_report_nsta_pl774.md` | Current PL774 conditional LCA report. |
| `lca_inventory_*.csv` | Calculated inventory quantities for a run. |
| `lca_impacts_*.csv` | Row-by-row impact table; factors are missing until private data are supplied. |
| `lca_results_*.csv` | One-line LCA status and summary for a run. |
| `lca_trace_*.json` | Full trace for checking inputs and calculations. |
| `lca_model_input_csv_validation.csv` | Checks that the LCA CSV files have the required columns. |
| `ecoinvent_process_mapping_validation.csv` | Checks whether useful local ecoinvent process names are available. |
| `lca_literature_register.csv` | LCA literature and standards register. |
| `lca_method_reference_register.csv` | LCA method reference table used in validation. |
| `lca_reference_workbook_review.csv` | Review of the supplied LCA workbook. |
| `lca_data_strategy.md` | How to use ecoinvent safely without committing licensed data. |
| `lca_model_defensibility_basis.md` | Basis for a defendable conventional LCA model. |

Private impact factors belong in:

```text
model_layers/05_lca/private/lca_impact_factors_private.csv
```

This file is ignored by Git and should not be uploaded to GitHub.
