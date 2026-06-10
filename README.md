# Repurposing Pipelines

This repository is for building a professional screening tool for reusing existing UK offshore oil and gas pipelines for CO2 transport and CCS.

Start here:

- `START_HERE.md`
- `model_layers/00_project_overview/how_to_run_the_model.md`

## What This Project Does

The model screens pipeline candidates using:

- NSTA pipeline data;
- CO2 capacity and hydraulic checks;
- corrosion and wall-thickness uncertainty;
- simple integrity screening;
- cost comparison;
- pre-LCA decision logic;
- LCA inventory mapping and first proxy results;
- independent validation checks.

This is still a screening tool. A `pass` or `marginal` result means a pipeline is worth studying further. It is not engineering approval.

## Folder Structure

The repository is now organised by model layer rather than by file type.

| Folder | What it contains |
| --- | --- |
| `model_layers/00_project_overview/` | Run guide, architecture, strategy, novelty, similar tools. |
| `model_layers/01_data_foundation/` | NSTA raw/processed data, completeness report, candidate ranking. |
| `model_layers/02_capacity_hydraulics/` | CO2 property and capacity validation CSVs. |
| `model_layers/03_corrosion_integrity/` | Wall-thickness and integrity validation files. |
| `model_layers/04_cost_economics/` | NETL cost template and cost validation. |
| `model_layers/05_lca/` | LCA inventory CSVs, ecoinvent mapping, LCA method notes. |
| `model_layers/06_screening_and_decision/` | Goldeneye benchmark, NSTA screening results, pre-LCA gate outputs. |
| `model_layers/07_independent_validation/` | Validation plan, source register, dashboard, validation report. |
| `repurposing_pipelines/` | Reusable Python model code. |
| `scripts/` | PowerShell/Python commands to run the model. |
| `tests/` | Automated checks. |

## Simple Commands

Open PowerShell in the project folder:

```powershell
cd "C:\Users\aj52\Documents\Repurposing Pipelines"
```

Screen all model-ready NSTA hydrocarbon pipelines:

```powershell
python scripts\run_pipeline_screen.py --screen-all-nsta
```

Then open:

```text
model_layers/06_screening_and_decision/pipeline_screen_nsta_all.md
```

Run one selected pipeline:

```powershell
python scripts\run_pipeline_screen.py --nsta-id PL774
```

Then open:

```text
model_layers/06_screening_and_decision/pipeline_screen_nsta_pl774.md
```

Run the Goldeneye benchmark:

```powershell
python scripts\run_goldeneye_benchmark.py
```

Run independent validation:

```powershell
python scripts\run_independent_validation.py
```

Run tests:

```powershell
python -m unittest discover -s tests
```

## Where The LCA Files Are

The LCA files are now together:

- `model_layers/05_lca/lca_inventory_template.csv`
- `model_layers/05_lca/lca_process_mapping.csv`
- `model_layers/05_lca/lca_model_input_csv_validation.csv`
- `model_layers/05_lca/lca_literature_register.csv`
- `model_layers/05_lca/lca_method_reference_register.csv`
- `model_layers/05_lca/lca_data_strategy.md`
- `model_layers/05_lca/lca_model_defensibility_basis.md`

Important: licensed ecoinvent data are not committed to GitHub. The repo stores only shareable mapping metadata, templates, and model outputs.

## Current Status

Implemented so far:

- NSTA data extraction and completeness checking;
- ranking of model-ready hydrocarbon pipeline candidates;
- Goldeneye dissertation/poster benchmark cases;
- batch screening of 155 NSTA records;
- general wall-thickness uncertainty for all screened pipelines;
- first corrosion screening module;
- first LCA proxy module;
- NETL cost-reference template;
- independent validation reports and registers.

Next technical priorities:

- improve the wall-thickness/minimum-wall basis;
- validate capacity against an external CO2 transport model;
- compare costs against NETL CO2_T_COM;
- replace the LCA proxy with a proper ecoinvent/openLCA/Brightway workflow;
- keep wells as Phase 2 after pipeline screening is stable.
