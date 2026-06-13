# 05 LCA

LCA inventory templates, ecoinvent process mapping, conditional LCA reports, and LCA method references.

The current LCA workflow is ecoinvent-linked but not yet final decision-grade. It can run with public screening impact factors for early estimates, or with private ecoinvent/openLCA/Brightway impact factors when those are available. Final publishable kg CO2e numbers need the private factor file and a checked activity boundary.

The quantified refurbishment work-scope CSVs are stored in `model_layers/06_screening_and_decision/`. They provide the current activity drivers for the refurbishment package, such as inspection length, cleaning/drying length, study counts, and replacement steel. The ecoinvent-linked LCA inventory can now use those work-scope rows for refurbishment steel and the aggregate refurbishment activity package.

## Simple Commands

Create the private factor template:

```powershell
python scripts\run_ecoinvent_lca.py --create-factor-template
```

Run Goldeneye:

```powershell
python scripts\run_ecoinvent_lca.py --scenario goldeneye_poster --factor-mode screening
```

Run one NSTA pipeline:

```powershell
python scripts\run_ecoinvent_lca.py --nsta-id PL774 --factor-mode screening
```

Use `--factor-mode private` after filling the private impact-factor CSV.

Extract shareable activity metadata from local ecoinvent:

```powershell
python scripts\extract_lca_activity_data.py --ecoinvent-dir "D:\path\to\Ecoinvent_apos_38"
```

If the report says `screening_result`, public screening factors were used. If it says `sensitivity_only`, an upstream technical gate failed and the LCA is only shown to understand scale.

| File | Purpose |
| --- | --- |
| `lca_inventory_template.csv` | Main LCA inventory input template. |
| `lca_process_mapping.csv` | Shareable ecoinvent process-mapping metadata. |
| `lca_activity_query_terms.csv` | Editable boundary/activity list; includes direct database searches and project-defined packages. |
| `lca_activity_candidates.csv` | Extracted candidate activity metadata from local/private sources; shareable metadata only. |
| `lca_activity_preferred_mapping.csv` | Rank-1 activity candidate per mapping key; still requires LCA review. |
| `lca_activity_extraction_report.md` | Report from the standalone activity extractor. |
| `lca_impact_factors_template.csv` | Blank template showing the private factors needed. |
| `lca_impact_factors_screening_defaults.csv` | Public screening impact factors for complete early runs. |
| `lca_impact_factor_screening_basis.md` | Plain-language basis and caveats for the screening factors. |
| `lca_factor_fill_guide.md` | Simple guide for filling private LCA impact factors safely. |
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
| `lca_boundary_and_activity_definition.md` | Plain-language definition of LCA boundary and activity-selection basis. |
| `lca_model_defensibility_basis.md` | Basis for a defendable conventional LCA model. |

Private impact factors belong in:

```text
model_layers/05_lca/private/lca_impact_factors_private.csv
```

This file is ignored by Git and should not be uploaded to GitHub.
