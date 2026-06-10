# System Architecture

Date: 2026-06-10

## Purpose

This document defines the planned modular architecture for the pipeline repurposing decision-support tool.

The main design principle is:

> Each module should be able to run independently, but every module output must be traceable and reusable by later modules.

This avoids a black-box tool. A user should be able to see:

- what data went in;
- where each value came from;
- what assumptions were made;
- what model/equation was used;
- what result came out;
- which later module used that result.

## Coding Style In Plain Language

The code should stay understandable to non-specialist programmers.

We use two simple ideas:

- data objects hold information, sources, assumptions, warnings, and outputs;
- calculation functions do the engineering maths.

In plain terms:

- an object is like a labelled form;
- a function is like a small calculator;
- a module is a group of related calculators;
- a trace is the receipt that shows what numbers were used and how the answer was produced.

This is why the project uses objects such as `ModuleResult`, `InputRecord`, and `OutputRecord`, but keeps equations as simple functions. It makes the model easier to check, test, and explain.

## High-Level Workflow

```text
Pipeline data
  -> Data quality module
  -> Capacity module
  -> Corrosion screening module
  -> Integrity module with uncertainty ranges
  -> Cost module
  -> Pre-LCA gate
  -> LCA screening proxy
  -> Final decision gate
  -> Exportable report
```

## Two-Gate Decision Logic

### Gate 1: Pre-LCA Screening Gate

This gate answers:

> Is this pipeline technically and economically worth taking into LCA?

Inputs:

- data completeness;
- CO2 transport capacity;
- pressure/phase suitability;
- integrity/corrosion result;
- early cost saving.

Outputs:

- `pass`;
- `marginal`;
- `fail`;
- `insufficient_data`.

Reason:

LCA should not be run as if the pipeline is realistic if the pipeline clearly fails basic technical screening or has no usable integrity information.

### Gate 2: Final Decision Gate

This gate answers:

> After technical, economic, and environmental assessment, should this pipeline be prioritised?

Inputs:

- all pre-LCA gate outputs;
- LCA results;
- uncertainty and data confidence;
- user-defined decision weights.

Outputs:

- `high_priority`;
- `promising_needs_more_data`;
- `technically_possible_weak_case`;
- `not_suitable`;
- `do_not_decide_yet`.

Reason:

The final answer should combine technical feasibility, economic value, and environmental value, while still showing which part is strong or weak.

## Module Independence

Each module should:

- accept a clear input object;
- return a clear output object;
- store all assumptions used;
- store all warnings;
- not silently change input values;
- not depend on the user interface;
- be testable from a script or notebook.

The app should call the modules. The modules should not call the app.

## Standard Module Result Object

Each module should return a standard structure like this:

```python
{
    "module": "integrity",
    "model_version": "integrity_screening_v0.1",
    "status": "pass",
    "inputs": [],
    "outputs": [],
    "assumptions": [],
    "warnings": [],
    "trace": []
}
```

### Input Record

Each input value should carry provenance:

```python
{
    "name": "wall_thickness",
    "value": 14.28,
    "unit": "mm",
    "source": "poster",
    "quality": "reported",
    "required": True,
    "used_by": ["integrity", "lca"],
    "notes": "Goldeneye poster value"
}
```

### Output Record

Each output should say what it means and what can use it next:

```python
{
    "name": "remaining_life",
    "value": 24.55,
    "unit": "years",
    "quality": "screening_estimate",
    "used_by": ["pre_lca_gate", "lca"],
    "notes": "Based on available wall thickness divided by assumed future CO2 corrosion rate"
}
```

### Assumption Record

Every assumption should be explicit:

```python
{
    "name": "future_co2_corrosion_rate",
    "value": 0.20,
    "unit": "mm/year",
    "source": "poster",
    "quality": "assumed",
    "sensitivity_required": True
}
```

### Warning Record

Warnings should be visible in the app and report:

```python
{
    "level": "high",
    "message": "NSTA Goldeneye record has zero wall thickness, so poster/dissertation values were used.",
    "affected_modules": ["integrity", "cost", "lca"]
}
```

## Data Quality Levels

Use the same quality labels throughout the project.

| Label | Meaning |
| --- | --- |
| `measured` | Direct measured/inspection value. |
| `reported` | Reported by NSTA, operator document, dissertation, poster, or publication. |
| `derived` | Calculated from other values. |
| `assumed` | Chosen assumption, not directly verified. |
| `estimated` | Engineering estimate from standards or typical values. |
| `missing` | Value not available. |
| `not_applicable` | Value does not apply to this case. |

## Module Contracts

### 1. Data Module

Purpose:

Load pipeline data, standardise units, and attach source/quality labels.

Inputs:

- NSTA raw attributes;
- enriched project data;
- user overrides;
- benchmark assumptions.

Outputs:

- standard pipeline object;
- data completeness score;
- data confidence score;
- source register.

Key warnings:

- missing wall thickness;
- zero/placeholder pressure;
- missing start date;
- assumed material grade;
- mismatch between NSTA and enriched values.

### 2. Capacity Module

Purpose:

Estimate whether the pipeline can transport the required CO2 flow.

Inputs:

- length;
- internal diameter;
- inlet pressure;
- outlet pressure;
- temperature;
- CO2 composition or pure CO2 assumption;
- roughness/friction assumption;
- required annual CO2 flow.

Outputs:

- maximum transport capacity;
- required design flow;
- pressure/phase warnings;
- capacity status.

Used by:

- pre-LCA gate;
- cost module, if compression/booster assumptions are needed;
- LCA module, for operating-energy assumptions.

External validation:

- NETL REPACT;
- CoolProp/REFPROP for properties.

### 3. Integrity Module

Purpose:

Estimate whether the pipeline has enough wall/integrity margin for reuse screening.

Inputs:

- wall thickness;
- wall thickness uncertainty range;
- diameter;
- grade/SMYS;
- historical corrosion assumptions;
- historical corrosion uncertainty range;
- operating history;
- minimum wall thickness model;
- minimum wall uncertainty range;
- future CO2 corrosion rate;
- future CO2 corrosion uncertainty range;
- dry-CO2 water/dew-point screening result;
- inspection information, when available.

Outputs:

- historical wall loss;
- current wall thickness;
- minimum required wall thickness;
- available wall thickness;
- remaining life low/base/high;
- integrity status;
- data confidence.

Used by:

- pre-LCA gate;
- LCA module, because remaining life affects functional unit and allocation;
- final decision gate.

Important rule:

The integrity module is a screening tool until inspection data and requalification checks are available. Wall thickness uncertainty is applied to every screened pipeline, not only Goldeneye. Goldeneye uses a wider range because its source information is less clear.

### 3a. Corrosion Screening Module

Purpose:

Flag whether the assumed CO2 service is low, medium, or high corrosion risk at screening level.

Inputs:

- future CO2 corrosion rate low/base/high;
- CO2 water content, if known;
- dry-CO2 water specification;
- water dew-point margin.

Outputs:

- corrosion risk level;
- corrosion rate range;
- warnings for missing water/dew-point evidence;
- notes for specialist corrosion review.

Important rule:

This is not a detailed NORSOK/DNV corrosion model yet. It is a conservative screening layer so uncertain candidates are not treated as approved.

### 4. Cost Module

Purpose:

Compare new-build cost and reuse cost at screening level.

Inputs:

- length;
- diameter;
- cost model selection;
- project year;
- escalation;
- contingency;
- reuse-specific cost assumptions;
- booster/compression assumptions.

Outputs:

- new-build CAPEX;
- reuse CAPEX;
- avoided CAPEX;
- net saving;
- cost uncertainty;
- cost status.

Used by:

- pre-LCA gate;
- LCA module, if cost-linked activities are used;
- final decision gate.

External validation:

- NETL CO2 Transport Cost Model / CO2_T_COM.

### 5. Pre-LCA Gate

Purpose:

Decide whether the pipeline should move into LCA.

Inputs:

- data confidence;
- capacity status;
- integrity status;
- cost status.

Outputs:

- screening decision;
- reasons;
- modules blocking the decision;
- recommended next data to collect.

Example:

```python
{
    "decision": "marginal",
    "reasons": [
        "Capacity passes 5 MtCO2/year target",
        "Integrity result depends on assumed Goldeneye wall thickness",
        "Cost saving is positive but reuse cost is not yet modelled"
    ],
    "next_data": ["verified wall thickness", "inspection records", "reuse modification cost"]
}
```

### 6. LCA Module

Purpose:

Compare the environmental impact of reusing an existing pipeline versus building a new equivalent CO2 pipeline.

Inputs from earlier modules:

- length from data module;
- diameter/thickness/material from data/integrity module;
- remaining life from integrity module;
- required flow from capacity module;
- operating/compression assumptions from capacity/cost modules;
- new-build and reuse activity assumptions from cost module.

External inputs:

- ecoinvent process data;
- electricity mix;
- steel production process;
- offshore construction process;
- decommissioning/refurbishment assumptions.

Outputs:

- new-build CO2e;
- reuse CO2e;
- avoided CO2e;
- operational CO2e;
- net environmental saving;
- LCA uncertainty/data-quality score.

Important rule:

Do not commit the ecoinvent database to GitHub. Commit only scripts, process names, assumptions, and derived results allowed by the licence.

Current implementation:

The repo now includes a transparent LCA screening proxy. It estimates the steel and simple activity savings from reuse versus new-build. This is useful for ranking, but it is not yet the final ecoinvent/openLCA/Brightway LCA.

### 7. Final Decision Gate

Purpose:

Prioritise the pipeline using technical, economic, and environmental results.

Inputs:

- pre-LCA decision;
- LCA result;
- uncertainty;
- data confidence;
- user weights.

Outputs:

- final priority;
- short explanation;
- ranked weaknesses;
- recommended next action.

## Links Between Modules

| Output | Produced by | Used by |
| --- | --- | --- |
| `pipeline_length` | data | capacity, cost, LCA |
| `internal_diameter` | data | capacity, cost |
| `wall_thickness` | data | integrity, LCA |
| `max_capacity` | capacity | pre-LCA gate |
| `phase_warning` | capacity | pre-LCA gate, final gate |
| `corrosion_risk` | corrosion | integrity, pre-LCA gate |
| `remaining_life_low/base/high` | integrity | pre-LCA gate, LCA, final gate |
| `available_wall_thickness` | integrity | pre-LCA gate |
| `new_build_cost` | cost | pre-LCA gate, final gate |
| `reuse_cost` | cost | pre-LCA gate, LCA, final gate |
| `screening_decision` | pre-LCA gate | LCA, final gate |
| `net_co2e_saving` | LCA | final gate |

## Traceability In The User Interface

The future app should show three levels:

1. Simple result:
   - suitable/marginal/fail/insufficient data.

2. Evidence panel:
   - inputs, outputs, warnings, assumptions.

3. Audit view:
   - full trace from source data to calculation result.

Example user-facing trace:

```text
Remaining life = 24.55 years
  used wall thickness = 14.28 mm (poster, reported)
  used wall loss = 2.93 mm (poster, calculated)
  used minimum wall = 6.44 mm (poster, calculated)
  used future CO2 corrosion = 0.20 mm/year (poster, assumed)
  formula: available wall / future corrosion rate
```

## Reports

Every run should be exportable as:

- CSV outputs for calculations;
- Markdown/HTML report for humans;
- JSON trace file for audit/reuse by the app.

## Roadmap Beyond Pipelines

The first working tool should remain pipeline focused. This keeps the first model clear, testable, and publishable.

After the pipeline workflow is stable, the same modular structure can be extended to other CCS repurposing assets.

| Phase | Scope | Reason |
| --- | --- | --- |
| Phase 1 | Pipeline repurposing | This is the current core and already has NSTA data, Goldeneye benchmarks, and dissertation/poster assumptions. |
| Phase 2 | Well repurposing | Wells are important for CCS storage reuse, but they need different data and integrity checks. |
| Phase 3 | Facilities, hubs, and networks | These can connect pipelines and wells into a wider CCS infrastructure planning tool. |

### Future Well Repurposing Module

The well module should follow the same traceability rules as the pipeline modules.

Possible inputs:

- well location and status;
- casing and cement information;
- pressure and temperature;
- completion and abandonment history;
- reservoir or storage link;
- inspection or integrity evidence;
- conversion, re-entry, monitoring, and abandonment costs;
- LCA assumptions for reuse versus drilling a new injection well.

Possible outputs:

- well data completeness;
- reuse suitability screen;
- leakage/integrity warning level;
- conversion cost estimate;
- monitoring requirement;
- LCA input package;
- well reuse decision status.

The well module should not be built until the pipeline module structure is reusable. That way the same input/output, warning, assumption, and trace records can support both pipelines and wells.

For the external-tool strategy, see `docs/tooling_strategy.md`.

## Immediate Implementation Plan

Completed first:

- Goldeneye benchmark script converted into reusable capacity, integrity, cost, and traceability modules.
- Standard result objects added for inputs, outputs, assumptions, warnings, and formula trace.
- Regression tests added for the dissertation and poster Goldeneye cases.
- JSON trace output added for audit and future app evidence panels.
- Simple pre-LCA gate added for deciding whether a case is ready for LCA screening.
- Simple one-scenario runner added so a user can choose a scenario from an assumptions file.
- First NSTA candidate runner added using NSTA data plus a simple defaults file.
- Batch NSTA screening added for all model-ready hydrocarbon pipeline candidates.
- Corrosion screening module added.
- General wall-thickness uncertainty ranges added for all screened pipelines.
- Simple LCA screening proxy added.
- NETL cost-reference input template added.

Next implementation steps:

1. Add a clearer user override file so default NSTA assumptions can be edited per pipeline.
2. Add external benchmark comparisons with REPACT and NETL CO2_T_COM.
3. Later connect LCA to ecoinvent/openLCA/Brightway workflow.
4. Replace corrosion screening assumptions with literature-backed dry-CO2 corrosion checks where data are available.
