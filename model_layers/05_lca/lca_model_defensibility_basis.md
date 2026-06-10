# LCA Model Defensibility Basis

Date: 2026-06-10

## Purpose

This note defines the method basis for the first LCA module in this project.

The first version should be a conventional LCA. In simple terms, that means we estimate the environmental burden of the pipeline option using today's known data, today's background database, and clear assumptions. We do not yet model future electricity grids, future supply chains, or time-dependent climate effects.

Prospective LCA and dynamic LCA are important future extensions, but they should not be mixed into version 1.

## Method Position

| Topic | Version 1 choice | Why this is defendable |
| --- | --- | --- |
| LCA type | Conventional process-based LCA | This matches ISO 14040/14044 structure and is easiest to audit. |
| Main comparison | Reuse an existing offshore pipeline versus build a new equivalent CO2 pipeline | This isolates the repurposing question. |
| First use | Screening and comparison, not final project approval | Pipeline integrity and project data are still uncertain. |
| Background data | Local ecoinvent APOS 3.8, kept outside GitHub | Uses a recognised database while respecting the licence. |
| Calculation engine | Brightway or openLCA later; CSV mapping now | Lets us start transparent and later calculate with proper LCA software. |
| Future methods | Prospective and dynamic LCA kept as later modules | Avoids confusing the first conventional model. |

## Goal And Functional Unit

Recommended first goal:

> Compare the life-cycle environmental burdens of reusing an existing UK offshore pipeline for CO2 transport against constructing a new equivalent CO2 pipeline.

Recommended pipeline-only functional unit:

> Transport 1 tonne of CO2 through the selected route using the selected pipeline option.

Optional full-chain functional unit:

> Transport and store 1 tonne of CO2 through the selected pipeline and storage system.

The pipeline-only unit is best for early model validation because it tests the repurposing decision directly. The full-chain unit is useful later when capture, compression, injection, storage monitoring, leakage, and permanence are included.

## System Boundary

For the pipeline-only LCA, include:

- steel and major material production;
- new pipeline construction or existing pipeline refurbishment;
- cleaning, inspection, repair, tie-ins, and requalification where data exist;
- transport of materials and waste;
- electricity and fuel for operation, if compression or pumping energy is allocated to the pipeline case;
- maintenance over the project lifetime;
- decommissioning, abandonment, recycling, or disposal.

For the first pipeline-only model, exclude:

- capture plant construction and operation;
- industrial plant emissions before CO2 capture;
- reservoir storage performance;
- long-term monitoring of the storage complex;
- claimed avoided emissions from storing CO2.

Those excluded items can be added in a full CCS-chain module. Until then, captured CO2 should be treated as the service being transported, not automatically as an environmental credit.

## Scenarios

The first LCA should compare at least two cases.

| Scenario | What it represents | Main inventory difference |
| --- | --- | --- |
| Reuse case | Existing pipeline is cleaned, inspected, modified, and operated for CO2 | Lower new steel and construction burden, higher uncertainty in integrity/refurbishment. |
| New-build case | New offshore CO2 pipeline is built for the same service | Higher material and construction burden, clearer design data. |

Optional sensitivity cases:

- optimistic reuse;
- conservative reuse;
- new-build with low-carbon steel;
- new-build with different decommissioning assumptions;
- alternative electricity mix;
- different project lifetimes.

## Data Quality Rules

Every LCA input should carry a source and a confidence label.

Minimum labels:

- `measured`: project or operator data;
- `public_source`: NSTA, report, paper, standard, or database metadata;
- `engineering_estimate`: calculated from dimensions or engineering logic;
- `assumption`: temporary value used because real data are missing;
- `blocked`: no defendable value yet.

Minimum data-quality checks:

- geography: UK, Europe, global, or unknown;
- time: data year or database version;
- technology: offshore pipeline, generic pipeline, steel production, electricity, etc.;
- completeness: whether all required fields are present;
- sensitivity need: whether the value can change the result materially.

## Decision Gates

The LCA module should sit after the pre-LCA technical gate.

| Gate | Question | Output |
| --- | --- | --- |
| Pre-LCA gate | Is the pipeline technically credible enough to assess environmentally? | `proceed_to_lca`, `sensitivity_only`, or `blocked`. |
| Post-LCA gate | Does reuse still look favourable after environmental checks and uncertainty? | `favour_reuse`, `favour_new_build`, `inconclusive`, or `needs_data`. |

LCA should not rescue a technically weak pipeline. If integrity, pressure, corrosion, or missing data are serious problems, the LCA should be marked `sensitivity_only` or `blocked`.

## Self-Critical Checks

To make the LCA defendable, the report should always answer these questions.

1. Are reuse and new-build providing the same service?
2. Is the functional unit stated clearly?
3. Are the system boundaries the same for both cases?
4. Are we double-counting any CO2 benefit?
5. Are we excluding anything that could change the conclusion?
6. Are ecoinvent process choices documented and versioned?
7. Are local licensed data kept out of GitHub?
8. Are uncertain values tested with sensitivity cases?
9. Are results reported as screening results unless externally reviewed?
10. Can another person rerun the same case and get the same answer?

## Conventional Versus Future LCA Types

| LCA type | Meaning in plain language | Use in this project |
| --- | --- | --- |
| Conventional LCA | Uses current process data and current background datasets. | Version 1 basis. |
| Prospective LCA | Changes the background world, such as 2030 or 2050 electricity, steel, or shipping. | Future scenario module. |
| Dynamic LCA | Tracks when emissions happen and how timing changes climate impact. | Future climate-timing module. |

For now, the model should be conventional and static. We can still record the project year, database year, and lifetime so that prospective or dynamic analysis can be added later.

## Source Hierarchy

Use sources in this order:

1. Project-specific engineering data.
2. Public regulator/operator data, such as NSTA or operator reports.
3. Recognised LCA standards and guidance, such as ISO 14040/14044 and ILCD.
4. CCS-specific reports and guidelines, such as IOGP Report 672, NORSUS CCU LCA guidance, and Global CO2 Initiative TEA/LCA guidance.
5. Peer-reviewed papers for gaps, uncertainty, prospective LCA, or dynamic LCA.
6. Transparent assumptions, only when no better source exists.

## Sources Checked

| Source | How it helps |
| --- | --- |
| ISO 14040:2006 | Defines LCA principles and framework. |
| ISO 14044:2006 | Defines LCA requirements and guidelines. |
| JRC ILCD Handbook | Gives practical quality and consistency guidance for LCA studies. |
| IOGP Report 672 | Direct CCS lifecycle guidance, including transport and storage project boundaries. |
| NORSUS OR 28.22 | CCU/CCS reference-system and system-boundary guidance. |
| Global CO2 Initiative TEA/LCA guidance | CO2-utilisation transparency and harmonised TEA/LCA thinking. |
| ecoinvent APOS 3.8 | Local background inventory database for steel, electricity, transport, construction, and waste processes. |
| Brightway and openLCA | Candidate software engines for later reproducible LCA calculation. |
| Prospective and dynamic LCA literature | Future extensions, not version 1 basis. |

## Immediate Implementation Decision

The next LCA coding step should not be an impact result yet. It should be an inventory builder:

```text
pipeline engineering outputs
  -> LCA inventory quantities
  -> ecoinvent process mapping
  -> sensitivity cases
  -> local LCA calculation later
```

This keeps the model modular, transparent, and easier to validate.
