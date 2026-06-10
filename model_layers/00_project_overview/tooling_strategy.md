# Tooling Strategy

Date: 2026-06-09

## Purpose

This document explains how the project should use existing CCS pipeline tools and databases while still building a competitive in-house tool.

The main decision is:

> Use existing tools as benchmarks and references, but build our own transparent Python modules as the core engine.

This gives us control over assumptions, traceability, uncertainty, and the user interface.

## Why Not Just Use Existing Tools?

Existing tools are useful, but they usually do not give everything we need in one place.

Common gaps are:

- limited UKCS/NSTA pipeline data integration;
- limited traceability from raw data to result;
- limited handling of missing data and assumptions;
- limited LCA integration;
- limited explanation for non-specialist users;
- limited flexibility for future well repurposing and wider CCS infrastructure screening.

Our tool should therefore be built around transparency rather than only calculation speed.

## Role Of External Tools

| Tool or data source | Best role in this project | Core engine or benchmark? |
| --- | --- | --- |
| NSTA open data | Main public source for UK offshore pipeline attributes. | Core data source |
| NETL REPACT | Reference for pipeline reuse screening logic, capacity checks, and assumptions. | Benchmark |
| NETL CO2 Transport Cost Model / CO2_T_COM | Reference for new-build transport cost estimates. | Benchmark |
| CoolProp / REFPROP | CO2 density, viscosity, phase, and thermodynamic property validation. | Validation engine |
| openLCA / Brightway | LCA modelling workflow linked to ecoinvent. | LCA engine or bridge |
| ecoinvent | Licensed life-cycle inventory database. | External database |
| SimCCS / Sequestrix | Network planning references for future cluster-scale optimisation. | Future benchmark |
| Dissertation and poster | Goldeneye assumptions and benchmark outputs. | Case study benchmark |

Important rule:

Do not commit licensed ecoinvent databases to GitHub. Commit only our scripts, process names, assumptions, mappings, and shareable derived outputs.

## Competitive Position

The tool should compete by being clearer and more auditable, not by pretending to replace every specialist engineering package.

Target strengths:

- UKCS and NSTA focused from day one;
- built around pipeline repurposing, not generic pipeline design only;
- explicit data quality checks before modelling;
- visible assumptions and warnings for every result;
- modular calculations that can run without the web app;
- Goldeneye benchmark cases for validation;
- separate technical, economic, and environmental gates;
- LCA integration using ecoinvent through openLCA or Brightway;
- exportable reports for engineers, researchers, and decision makers;
- future expansion to well repurposing.

## Validation Philosophy

Each major module should have three layers of validation.

1. Internal consistency:
   - units are checked;
   - missing values are handled explicitly;
   - assumptions are recorded;
   - outputs are reproducible from scripts.

2. Benchmark comparison:
   - capacity checked against REPACT or published examples;
   - cost checked against NETL CO2_T_COM or published cost models;
   - CO2 properties checked against CoolProp or REFPROP;
   - Goldeneye checked against dissertation and poster outputs.

3. Sensitivity and uncertainty:
   - key assumptions are varied;
   - weak inputs are highlighted;
   - the final decision shows confidence, not only a pass/fail result.

## Recommended Implementation Approach

Build the tool as transparent Python modules first, then connect the modules to a professional web interface.

The app should call the calculation modules. The calculation modules should not depend on the app.

Recommended layers:

| Layer | Main job |
| --- | --- |
| Data layer | Load NSTA, project data, user overrides, and source labels. |
| Model layer | Run capacity, integrity, cost, LCA, and decision-gate modules. |
| Validation layer | Compare selected results against external tools or benchmark cases. |
| Traceability layer | Store inputs, outputs, assumptions, warnings, and model versions. |
| Interface layer | Let users explore, override, compare, and export results. |

## How To Use NETL REPACT And Cost Models

Use REPACT and NETL cost tools as references, not as hidden black boxes.

Suggested workflow:

1. Run our model for a selected pipeline.
2. Run the comparable case in REPACT or NETL CO2_T_COM where possible.
3. Store the external result as a benchmark record.
4. Report the difference and explain the main reason, such as pressure, diameter, friction, cost year, or reuse assumption.

This helps us prove whether our model is reasonable while keeping our workflow open and editable.

## LCA Strategy

LCA should be added after the pre-LCA technical and economic gate.

Reason:

There is no value in running a detailed LCA for a pipeline that clearly fails basic capacity or integrity screening. However, the LCA module should still receive traceable inputs from earlier modules.

Minimum first LCA version:

- compare reuse versus new-build pipeline;
- use pipeline length, diameter, wall thickness, steel mass, lifetime, and transport duty;
- include steel, construction/refurbishment, operation, and decommissioning assumptions;
- report net CO2e saving and uncertainty;
- keep ecoinvent links outside public GitHub data.

## Wells Repurposing Strategy

Wells should be added as a Phase 2 module, after the first pipeline workflow is working.

Reason:

Well repurposing is closely connected to CCS storage, but it needs different data and different engineering checks from pipelines.

Possible well module scope:

- well status and location;
- casing and cement information;
- pressure and temperature conditions;
- completion and abandonment history;
- leakage risk screening;
- conversion or re-entry cost;
- monitoring requirements;
- link to storage/reservoir suitability;
- LCA effect of reusing versus drilling a new CO2 injection well.

The well module should use the same traceability structure as the pipeline modules.

## Roadmap

| Phase | Focus | Main output |
| --- | --- | --- |
| Phase 1 | Pipeline data, Goldeneye benchmark, capacity, integrity, cost, and pre-LCA gate. | Pipeline screening engine |
| Phase 1B | Compare selected outputs with REPACT, NETL CO2_T_COM, and property tools. | Validation report |
| Phase 1C | Add first LCA screening workflow using transparent assumptions and ecoinvent mapping. | Environmental gate |
| Phase 2 | Add well repurposing screening. | Well reuse module |
| Phase 3 | Add facilities, networks, hubs, and cluster-level optimisation. | CCS infrastructure platform |

## Near-Term Decision

For now, build the professional tool around our own documented Python modules.

External tools should be used to check, calibrate, and explain our results. This makes the project more defensible and easier to publish, extend, and use in real case studies.
