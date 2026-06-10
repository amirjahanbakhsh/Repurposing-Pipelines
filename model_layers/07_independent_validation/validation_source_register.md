# Validation Source Register

Date: 2026-06-09

## Purpose

This register lists the external sources we can use to validate the model.

It answers a simple question:

> If someone asks "how do you know this calculation is right?", what independent source do we compare against?

The register is stored as a table in `model_layers/07_independent_validation/validation_source_register.csv`.

## Validation Rule

External tools and papers should not become hidden black boxes inside our model.

Use them for three jobs:

- check our numbers;
- check our assumptions;
- explain why our result is different when it is different.

Our own model should remain transparent, traceable, and editable.

## Source Types

| Type | Meaning | Example |
| --- | --- | --- |
| Hard benchmark | Gives numbers we can compare directly | CO2 density from REFPROP or CoolProp |
| Logic check | Gives rules, limits, or engineering requirements | ISO 27913:2024 |
| Case-study source | Gives real project assumptions or public context | Goldeneye/Peterhead reports |
| Cross-check tool | Gives another model output for the same case | NETL CO2_T_COM or SCO2T |
| LCA database/tool | Gives life-cycle inventory or LCA calculation route | ecoinvent, Brightway, openLCA |

## Highest-Priority Sources

| Source | Main use | Why it matters |
| --- | --- | --- |
| NIST REFPROP | CO2 properties | Strong reference for density, viscosity, Z factor, and phase behaviour. |
| CoolProp | CO2 properties | Open-source route that can be automated in Python. |
| ISO 27913:2024 | CO2 pipeline conversion logic | Covers CO2 pipeline transport, including existing pipeline conversion. |
| NETL CO2_T_COM | Cost comparison | Independent transport cost model for liquid-phase CO2 pipelines. |
| SCO2T | CO2 transport comparison | Public spreadsheet from the SimCCS group for transport screening. |
| NORSOK M-506 | Corrosion | Useful benchmark if we use NORSOK-style CO2 corrosion equations. |
| ISO 14040/14044 | LCA method | Defines how a defensible LCA should be structured. |
| ecoinvent | LCA inventory | Provides the background data for steel, power, construction, transport, and waste. |
| Brightway/openLCA | LCA calculation | Lets us calculate and cross-check LCA results. |

## Module-By-Module Validation

### Data Extraction

Validate against the public NSTA source data and metadata.

Checks:

- pipeline ID;
- pipeline name;
- length;
- internal diameter;
- wall thickness;
- maximum operating pressure;
- fluid;
- status;
- start date;
- missing values.

This is the first validation step because a correct equation is still poor if the input data is wrong.

### CO2 Properties

Validate pure CO2 properties against REFPROP and CoolProp first.

Checks:

- density;
- viscosity;
- compressibility factor;
- phase state;
- pressure and temperature units.

Later, add mixtures with impurities, because real captured CO2 is not always pure.

### Hydraulics And Capacity

Validate the flow equation separately from the rest of the model.

Checks:

- pressure basis;
- internal diameter basis;
- length units;
- temperature;
- friction factor;
- mass flow.

Useful references:

- published McCoy and Rubin-style examples;
- independent hand calculations;
- SCO2T;
- NETL tools where comparable.

### Integrity And Corrosion

Keep this conservative.

Checks:

- minimum wall thickness;
- outside diameter versus inside diameter;
- material grade;
- design factor;
- historic corrosion;
- future CO2 corrosion risk;
- free water and impurity warnings.

Important note:

> Screening can reject or flag a pipeline, but it cannot approve reuse without inspection and requalification evidence.

### Cost

Validate each cost model separately before combining them.

Checks:

- base year;
- currency;
- offshore/onshore factor;
- diameter and length basis;
- booster or pump cost;
- contingency;
- reuse cost versus new-build cost.

Main cross-check:

- NETL CO2_T_COM 2024.

### LCA

Add LCA after the pre-LCA gate.

Checks:

- functional unit;
- system boundary;
- reuse versus new-build comparison;
- ecoinvent database version;
- dataset names;
- electricity assumptions;
- steel mass;
- construction/refurbishment assumptions;
- lifetime.

Main route:

1. Build first inventory in our Python data structure.
2. Calculate in Brightway or openLCA.
3. Cross-check a simple case in the other tool.

### Wells

Well repurposing should be a Phase 2 module.

Checks:

- well status;
- location;
- age;
- completion;
- casing and cement data;
- abandonment status;
- leakage risk;
- link to storage site and injection duty.

This module needs its own gate. A well should not pass unless integrity evidence is available.

## First Practical Sprint

Recommended next steps:

1. Build a Goldeneye CO2 property benchmark table using CoolProp.
2. Compare our Goldeneye capacity calculation against a hand calculation.
3. Add NETL CO2_T_COM as the first cost benchmark source.
4. Create a Goldeneye assumption register with source and confidence for each value.
5. Keep integrity as "screening only" until inspection/requalification data is available.

This gives us validation evidence without over-building the web app too early.
