# Project Status

Last updated: 2026-07-29

## Development State

- The project is organised by model layer under `model_layers/`.
- The model can screen all model-ready NSTA hydrocarbon pipelines and selected single-pipeline cases.
- The Streamlit dashboard supports visual review, pipeline selection, map-based route display, saved outputs, and data-input/navigation work.
- The evidence-based repurposing gate runs before cost/LCA decisions and produces quantified refurbishment work-scope rows.
- Public screening cost and LCA factors give complete early estimates; private factors remain needed before final cost or LCA claims.
- Independent validation reports and registers are in place for the current screening-level model.

## Data And GitHub Policy

- Public/shareable project data, scripts, model outputs, assumptions, mappings, Markdown notes, and validation CSVs belong in GitHub.
- Public NSTA route geometry should be stored with Git LFS because the full GeoJSON is large.
- PDFs are local-only. GitHub should store citation records, extracted notes, and model-relevant facts, not source PDFs.
- Licensed ecoinvent/openLCA/Brightway source data and private ecoinvent-derived impact factors are local-only.
- Private or commercial refurbishment unit-cost files are local-only.

## Current Cleanup Work

- `.gitignore` is being updated to protect PDFs, ecoinvent data, private LCA factors, and private cost factors.
- Previously tracked PDFs are being removed from Git tracking while remaining on the local machine.
- The `codex-store-project-data` branch is being cleaned so it can be merged without publishing private cost data, then deleted afterwards.

## Next Technical Priorities

- Review and replace screening cost/LCA factor assumptions with defensible project-specific factors.
- Improve the wall-thickness/minimum-wall basis and validation.
- Validate capacity and cost against external tools such as CO2 transport models and NETL CO2_T_COM.
- Keep wells as Phase 2 after pipeline screening is stable.
