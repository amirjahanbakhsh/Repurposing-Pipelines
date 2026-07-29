# Project Status

Last updated: 2026-07-29

## Development State

- The local public repository is now the clean reclone at `C:\Users\aj52\Documents\Repurposing Pipelines`.
- The project is organised by model layer under `model_layers/`.
- The model can screen all model-ready NSTA hydrocarbon pipelines and selected single-pipeline cases.
- The NSTA wall-thickness pressure sanity check now screens all 155 ranked candidates; the current run flags 6 `fail_sanity` rows and 12 `review_required` tight-margin rows.
- The Streamlit dashboard supports visual review, pipeline selection, map-based route display, saved outputs, and data-input/navigation work.
- The evidence-based repurposing gate runs before cost/LCA decisions and produces quantified refurbishment work-scope rows.
- Public screening cost and LCA factors give complete early estimates; private factors remain needed before final cost or LCA claims.
- Independent validation reports and registers are in place for the current screening-level model.

## Current Repository State

- The public GitHub `main` branch is the clean working branch.
- The old `codex-store-project-data` branch has no remaining role in development after cleanup and deletion.
- Source PDFs, licensed ecoinvent/openLCA/Brightway data, private ecoinvent-derived factors, and private refurbishment unit-cost files must not be committed.
- The local private evidence vault is outside the repository at `C:\Users\aj52\Documents\Repurposing Pipelines Private Evidence`.
- The private evidence vault should hold source PDFs, licensed ecoinvent files, openLCA/Brightway exports where license-restricted, and private/commercial factor CSVs.
- GitHub should hold only public/shareable data, extracted facts, citation records, mappings, assumptions, validation registers, scripts, tests, and generated model outputs.

## Data And GitHub Policy

- Public/shareable project data, scripts, model outputs, assumptions, mappings, Markdown notes, and validation CSVs belong in GitHub.
- Public NSTA route geometry should be stored with Git LFS because the full GeoJSON is large.
- PDFs are local-only. GitHub should store citation records, extracted notes, and model-relevant facts, not source PDFs.
- Licensed ecoinvent/openLCA/Brightway source data and private ecoinvent-derived impact factors are local-only.
- Private or commercial refurbishment unit-cost files are local-only.
- When private sources support a model value, store the source file in the private vault and store only the citation, extracted fact, and allowed summary in GitHub.

## Next Technical Priorities

- Review and replace screening cost/LCA factor assumptions with defensible project-specific factors.
- Resolve the NSTA candidates flagged by the wall-thickness pressure sanity check.
- Improve the wall-thickness/minimum-wall basis beyond the simple Barlow triage check.
- Validate capacity and cost against external tools such as CO2 transport models and NETL CO2_T_COM.
- Keep wells as Phase 2 after pipeline screening is stable.
