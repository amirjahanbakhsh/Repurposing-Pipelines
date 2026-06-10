# Start Here

This page is the simple map for the project.

If you are new to the repository, do not start by opening every folder. Start with the files below.

## Most Important Files

| What you want | Open this |
| --- | --- |
| Understand the project quickly | `README.md` |
| Run the model step by step | `model_layers/00_project_overview/how_to_run_the_model.md` |
| See the latest all-pipeline screening result | `model_layers/06_screening_and_decision/pipeline_screen_nsta_all.md` |
| See the PL774 / CATS example result | `model_layers/06_screening_and_decision/pipeline_screen_nsta_pl774.md` |
| See the Goldeneye benchmark result | `model_layers/06_screening_and_decision/goldeneye_benchmark.md` |
| See the first ecoinvent-linked LCA reports | `model_layers/05_lca/lca_report_nsta_pl774.md` |
| See validation status | `model_layers/07_independent_validation/independent_validation_report.md` |
| Find LCA CSV files | `model_layers/05_lca/` |
| Understand the modular model design | `model_layers/00_project_overview/system_architecture.md` |

## Normal Workflow

1. Read `README.md`.
2. Run the full NSTA screening:

```powershell
python scripts\run_pipeline_screen.py --screen-all-nsta
```

3. Open:

```text
model_layers/06_screening_and_decision/pipeline_screen_nsta_all.md
```

4. Choose one NSTA pipeline number, for example `PL774`.
5. Run one detailed pipeline case:

```powershell
python scripts\run_pipeline_screen.py --nsta-id PL774
```

6. Open the single-pipeline report:

```text
model_layers/06_screening_and_decision/pipeline_screen_nsta_pl774.md
```

7. Optional: run the ecoinvent-linked LCA report for the same pipeline:

```powershell
python scripts\run_ecoinvent_lca.py --nsta-id PL774
```

8. Open:

```text
model_layers/05_lca/lca_report_nsta_pl774.md
```

## What The Folders Mean

| Folder | Plain meaning |
| --- | --- |
| `model_layers/00_project_overview/` | Start here: run guide, architecture, strategy. |
| `model_layers/01_data_foundation/` | NSTA data, completeness checks, candidate ranking. |
| `model_layers/02_capacity_hydraulics/` | CO2 properties and capacity validation. |
| `model_layers/03_corrosion_integrity/` | Wall thickness, corrosion, and integrity checks. |
| `model_layers/04_cost_economics/` | Cost inputs and cost validation. |
| `model_layers/05_lca/` | LCA inventory, ecoinvent mapping, and LCA references. |
| `model_layers/06_screening_and_decision/` | Goldeneye, NSTA screening results, and decision gates. |
| `model_layers/07_independent_validation/` | Validation plan, dashboard, and summary report. |
| `repurposing_pipelines/` | The Python model code. |
| `scripts/` | Commands you run from PowerShell. |
| `tests/` | Checks that help confirm the code still works. |

## Important Warning

This is still a screening tool. A `pass` or `marginal` result means a pipeline is worth studying further. It does not mean the pipeline is approved for CO2 service.
