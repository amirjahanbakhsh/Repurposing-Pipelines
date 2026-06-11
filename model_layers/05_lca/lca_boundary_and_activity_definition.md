# LCA Boundary And Activity Definition

Date: 2026-06-11

## Short Answer

The extractor is general, but the LCA boundary tells it what is needed.

It should not extract every possible ecoinvent activity. That would create noise and make the model less defendable.

So the extractor is not boundary-free. It is a reusable search tool controlled by the activity list.

The correct logic is:

```text
Goal and functional unit
  -> system boundary
  -> life-cycle stages
  -> model activities
  -> ecoinvent/search terms
  -> candidate activity metadata
  -> private impact factors
```

## Boundary For Version 1

Version 1 is a pipeline-only conventional LCA.

Question:

> What is the environmental difference between reusing an existing offshore pipeline and building a new equivalent CO2 pipeline?

Functional unit:

> Transport 1 tonne of CO2 through the selected pipeline route.

Comparison:

- reuse existing pipeline;
- build new equivalent pipeline.

## Included Activities

| Activity group | Included? | Why |
| --- | --- | --- |
| Pipeline steel | yes | Main material difference between reuse and new-build. |
| New offshore pipeline construction | yes | Needed for the new-build comparison. |
| Refurbishment steel | yes | Repairs or modifications may need replacement steel. |
| Inspection, cleaning, drying and repair | yes | These are core repurposing work-scope items. |
| Electricity for operation | conditional | Include when compression, pumping or monitoring energy is allocated to the pipeline. |
| Diesel/vessels/machinery | conditional | Include when construction or refurbishment work requires equipment or vessels. |
| Freight/logistics | conditional | Include when material or waste transport is modelled. |
| Decommissioning/end-of-life | sensitivity | Include as a scenario because allocation choices can change results. |

## Excluded From Version 1

| Activity | Why excluded for now |
| --- | --- |
| Capture plant construction and operation | Outside pipeline-only comparison. |
| Industrial emissions before capture | Belongs to full CCS-chain LCA. |
| Storage reservoir behaviour | Belongs to storage/well module. |
| Injection wells | Future well-repurposing module. |
| Claimed avoided emissions from storing CO2 | Would change the goal from pipeline comparison to full climate-benefit accounting. |

## How Activities Are Defined

Activities are defined from three sources:

1. Engineering quantities from the model:
   - length;
   - diameter;
   - wall thickness;
   - steel mass;
   - capacity;
   - operation energy, when available.

2. Repurposing-gate work scope:
   - inspection;
   - cleaning;
   - drying;
   - material testing;
   - fracture/decompression study;
   - repair or section replacement;
   - monitoring and IMR.

3. LCA method rules:
   - same functional unit for reuse and new-build;
   - same system boundary for both options;
   - no double-counting of CO2 storage benefit;
   - explicit sensitivity for end-of-life and decommissioning.

## How The Extractor Uses This

The extractor reads:

```text
model_layers/05_lca/lca_activity_query_terms.csv
```

That file defines:

- `mapping_key`: model name for the activity;
- `activity_group`: materials, construction, operation, etc.;
- `boundary_role`: why the activity is inside the boundary;
- `search_terms`: words used to find candidate activities;
- `selection_type`: whether the row is a direct database candidate or a project-defined package;
- `basis`: why this activity is needed.

So, if the boundary changes, we edit the query file.

Example:

- If we later include wells, add `injection_well`.
- If we later include storage, add storage-site activities.
- If we later include dynamic LCA, add future electricity/steel scenario activities.

Some activities, such as refurbishment, are not one simple ecoinvent process. They are packages made from several work items, for example inspection, cleaning, drying, repair, diesel use, vessel time and replacement steel. These are marked as `project_package` so the model does not pretend one database activity is the full answer.

## Important Rule

The extractor finds candidate activities. It does not make the final LCA choice by itself.

A human LCA review is still needed to choose:

- correct geography;
- correct technology;
- correct unit;
- correct system model;
- correct allocation approach;
- correct impact method.

If the source lookup does not include units, the unit column will stay blank and must be confirmed in openLCA, Brightway or the original database.

## Current Implementation

The standalone script is:

```powershell
python scripts\extract_lca_activity_data.py --ecoinvent-dir "D:\path\to\Ecoinvent_apos_38"
```

It writes:

```text
model_layers/05_lca/lca_activity_candidates.csv
model_layers/05_lca/lca_activity_preferred_mapping.csv
model_layers/05_lca/lca_activity_extraction_report.md
```

These files contain shareable metadata only. They do not contain private ecoinvent unit-process data or impact factors.
