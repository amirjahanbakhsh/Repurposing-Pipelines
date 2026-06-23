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
- quantified refurbishment work-scope drivers;
- pre-LCA decision logic;
- LCA inventory, ecoinvent-linked conditional reports, and first proxy results;
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
| `references/` | Project-wide literature, standards, source acquisition notes, and citation tracking. |
| `app/` | Streamlit interface for visual pipeline selection and gate-by-gate model review. |
| `repurposing_pipelines/` | Reusable Python model code. |
| `scripts/` | PowerShell/Python commands to run the model. |
| `tests/` | Automated checks. |
| `write_up/` | Draft report text, starting with the methodology. |

## Simple Commands

Open PowerShell in the project folder:

```powershell
cd "C:\Users\aj52\Documents\Repurposing Pipelines"
```

Install dashboard packages once:

```powershell
python -m pip install -r requirements.txt
```

Open the visual dashboard:

```powershell
python -m streamlit run app\streamlit_app.py
```

Then choose a pipeline from the dropdown or click a route on the map when map selection is available.

The dashboard shows the selected pipeline information, missing-data warnings, equations, input tables, and separate run buttons for the technical screening, cost, and LCA layers.

If the NSTA geometry is updated, rebuild the dashboard route file:

```powershell
python scripts\build_dashboard_assets.py
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

Create the private LCA factor template:

```powershell
python scripts\run_ecoinvent_lca.py --create-factor-template
```

Run the ecoinvent-linked LCA workflow for one pipeline:

```powershell
python scripts\run_ecoinvent_lca.py --nsta-id PL774 --factor-mode screening
```

Create the private refurbishment unit-cost template:

```powershell
python scripts\run_refurbishment_cost.py --create-factor-template
```

Run refurbishment cost factors for one pipeline:

```powershell
python scripts\run_refurbishment_cost.py --case nsta_pl774 --factor-mode screening
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
- `model_layers/05_lca/lca_impact_factors_template.csv`
- `model_layers/05_lca/lca_impact_factors_screening_defaults.csv`
- `model_layers/05_lca/lca_impact_factor_screening_basis.md`
- `model_layers/05_lca/lca_factor_fill_guide.md`
- `model_layers/05_lca/lca_report_goldeneye_poster.md`
- `model_layers/05_lca/lca_report_nsta_pl774.md`
- `model_layers/05_lca/lca_model_input_csv_validation.csv`
- `model_layers/05_lca/lca_literature_register.csv`
- `model_layers/05_lca/lca_method_reference_register.csv`
- `model_layers/05_lca/lca_data_strategy.md`
- `model_layers/05_lca/lca_model_defensibility_basis.md`

Important: licensed ecoinvent data are not committed to GitHub. The repo stores only shareable mapping metadata, templates, and model outputs.

## Data Storage Rule

All shareable project data and generated CSV, JSON, GeoJSON, and Markdown outputs should be kept locally and committed to GitHub. The full public NSTA route GeoJSON is stored with Git LFS because it is too large for normal GitHub file storage.

The exception is licensed ecoinvent/openLCA/Brightway source data and private ecoinvent-derived impact factors. Those files stay local only; the repository stores shareable process mappings, blank templates, screening defaults, and reports instead.

## Current Status

Implemented so far:

- NSTA data extraction and completeness checking;
- ranking of model-ready hydrocarbon pipeline candidates;
- Goldeneye dissertation/poster benchmark cases;
- batch screening of 155 NSTA records;
- first evidence-based repurposing gate with cited references and work-scope outputs;
- quantified refurbishment work-scope CSVs for cost and LCA drivers;
- private unit-cost factor workflow for refurbishment work-scope rows;
- public screening unit-cost and LCA factor defaults for complete early runs;
- professional Streamlit MVP with map/dropdown selection and gate-by-gate layer panels;
- general wall-thickness uncertainty for all screened pipelines;
- first corrosion screening module;
- first LCA proxy module and ecoinvent-linked conditional LCA workflow;
- NETL cost-reference template;
- independent validation reports and registers.

Next technical priorities:

- fill project-specific private unit costs and ecoinvent/openLCA/Brightway LCA factors;
- improve the wall-thickness/minimum-wall basis;
- validate capacity and cost against external tools such as CO2 transport models and NETL CO2_T_COM;
- keep wells as Phase 2 after pipeline screening is stable.
