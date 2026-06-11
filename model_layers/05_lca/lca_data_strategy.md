# LCA Data Strategy

Date: 2026-06-10

## Purpose

This document explains how we should use ecoinvent and other LCA references for future modelling.

The main rule is:

> Keep the model open, but keep licensed LCA databases private.

So GitHub should contain our scripts, assumptions, dataset mapping, and reports. It should not contain the ecoinvent unit-process database.

## Best Approach

Use a three-layer structure.

| Layer | What it stores | Can it go to GitHub? |
| --- | --- | --- |
| Project inventory | Our quantities, such as steel mass, electricity use, diesel use, transport distance, and waste mass. | Yes |
| Process mapping | Which ecoinvent process should be used for each inventory item. | Yes, as metadata only |
| Licensed database | Full ecoinvent process data and impact factors. | No |

This means our model can say:

```text
pipeline_steel -> market for steel, low-alloyed
electricity -> market group for electricity, medium voltage
decommissioned_pipeline -> market for decommissioned pipeline, natural gas
```

But it should not copy the full ecoinvent process inventories into the repository.

## CSV Files The Model Can Use

Four shareable CSV files have been added:

```text
model_layers/05_lca/lca_inventory_template.csv
model_layers/05_lca/lca_process_mapping.csv
model_layers/05_lca/lca_activity_query_terms.csv
model_layers/05_lca/lca_impact_factors_template.csv
```

How they should be used:

- `lca_inventory_template.csv` lists the quantities our model must calculate or request from the user.
- `lca_process_mapping.csv` links each inventory item to a candidate ecoinvent process name, location, reference product, and unit.
- `lca_activity_query_terms.csv` defines the boundary-driven activities, search terms, and whether each item is a direct database candidate or a project-defined package.
- `lca_impact_factors_template.csv` shows the private impact factors needed, but leaves the values blank.

These files are safe to keep in GitHub because they contain model structure and mapping metadata only. They do not contain licensed ecoinvent impact factors or unit-process inventories.

The private factor file should be kept here:

```text
model_layers/05_lca/private/lca_impact_factors_private.csv
```

Create it with:

```powershell
python scripts\run_ecoinvent_lca.py --create-factor-template
```

This private file is ignored by Git.

## What We Need For Pipeline Reuse LCA

For the first LCA version, the model should compare:

- reuse existing pipeline;
- build a new equivalent CO2 pipeline.

Minimum inventory items:

| Inventory item | Why it is needed |
| --- | --- |
| pipeline steel mass | Main material difference between reuse and new-build. |
| coating/insulation proxy | May be relevant for new-build and refurbishment. |
| construction/refurbishment activity | Captures installation or modification burden. |
| electricity | Compression, pumping, operation, and auxiliary loads. |
| diesel machinery | Construction/refurbishment equipment proxy. |
| freight transport | Movement of materials and waste. |
| decommissioned pipeline | Reuse, abandonment, or disposal scenario. |
| scrap steel/waste steel | End-of-life and recycling treatment. |
| storage/injection infrastructure | Needed when pipeline screening is linked to full CCS chain. |

## Useful Local Evidence

The local ecoinvent folder supplied for this project is:

```text
D:\Amir\Heriot-Watt University Team Dropbox\RES_EPS_RCCS_Susana_Garcia\RCCS_Capture_Amir Jahanbakhsh\3. USorb-DAC Work\Ecoinvent_data_exported\Ecoinvent_apos_38
```

The validation script reads:

```text
FilenameToActivtiyLookup.csv
datasets/
```

It checks whether suitable process candidates exist. It does not copy `.spold` files into the repository.

The standalone extractor is:

```powershell
python scripts\extract_lca_activity_data.py --ecoinvent-dir "D:\path\to\Ecoinvent_apos_38"
```

It writes shareable metadata only:

```text
model_layers/05_lca/lca_activity_candidates.csv
model_layers/05_lca/lca_activity_preferred_mapping.csv
model_layers/05_lca/lca_activity_extraction_report.md
```

The extractor is general because the query CSV can be edited. It is not boundary-free. The system boundary defines which activities should be searched. For example, refurbishment is treated as a project package because cleaning, drying, inspection, repair, vessel time and replacement steel cannot be represented by one single ecoinvent row without review.

## Useful LCA Workbook

The supplied workbook:

```text
C:\Users\aj52\OneDrive - Heriot-Watt University\USorb-DAC\1-s2.0-S1750583623002098-mmc2.xlsx
```

is useful because it contains example inventory structures:

- capture cases per tonne of captured CO2;
- auxiliary processes;
- permanent storage at Northern Lights per tonne of injected CO2;
- pipeline, injection well, electricity, diesel, steel, and decommissioned pipeline entries.

Use it as a template for structure, not as a direct copy of values.

## Useful LCA Method References

The supplied PDFs are useful for method validation:

- NORSUS, `Guidelines for Life Cycle Assessment (LCA) of CCU systems`, OR 28.22, 2022.
- IOGP Report 672, `Overview of lifecycle assessment for carbon capture and storage projects`, March 2024.

The wider method basis is now tracked in:

```text
model_layers/05_lca/lca_model_defensibility_basis.md
model_layers/05_lca/lca_literature_register.csv
model_layers/05_lca/lca_method_reference_register.csv
```

They support decisions on:

- functional unit;
- system boundary;
- reference system;
- baseline;
- shared transport and storage networks;
- allocation or proportional treatment;
- reporting across the CCS project life cycle.

The first LCA module should stay conventional and process-based. Prospective LCA and dynamic LCA are useful future extensions, but adding them too early would make the first model harder to validate.

## Current Data Flow

1. Pipeline model calculates engineering quantities.
2. LCA inventory builder converts those quantities into LCA inputs.
3. Dataset mapper links each input to an ecoinvent process.
4. A private factor CSV provides ecoinvent/openLCA/Brightway-derived climate factors.
5. The script writes inventory, impact, result, report, and trace files.
6. GitHub stores only the model code, mapping, blank templates, and shareable reports.

Run one example:

```powershell
python scripts\run_ecoinvent_lca.py --nsta-id PL774
```

If the private factors are not filled, the report status is:

```text
blocked_missing_impact_factors
```

This is deliberate. It prevents the model from pretending that proxy values are final ecoinvent results.

## First Functional Unit

Recommended future full-chain functional unit:

> Transport and store 1 tonne of CO2 through a selected pipeline route over the selected project lifetime.

For pipeline-only comparison:

> Provide CO2 transport capacity for 1 tonne of CO2 over the selected route, comparing reuse of the existing pipeline with construction of a new equivalent pipeline.

## Important Caveat

LCA should not be used to make a positive decision if the pipeline fails the pre-LCA technical gate.

The first LCA module should therefore run after the pre-LCA gate and should clearly say whether the LCA is:

- decision-grade;
- sensitivity-only;
- blocked by missing technical evidence.
