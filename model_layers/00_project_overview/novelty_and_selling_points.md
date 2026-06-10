# Novelty And Selling Points

Date: 2026-06-09

## Short Answer

Some parts of this work have been done before.

That is not a problem. In fact, it helps us validate the model.

The novelty is not that we invent every equation. The novelty is that we build a transparent, UKCS-focused, repurposing-first decision tool that connects data quality, engineering screening, cost, LCA, and future well reuse in one auditable workflow.

## What Already Exists

Existing work already covers many pieces:

- CO2 property tools such as REFPROP and CoolProp;
- CO2 pipeline cost tools such as NETL CO2_T_COM;
- network planning tools such as SimCCS;
- corrosion and pipeline guidance such as NORSOK, ISO, DNV, API, or ASME;
- LCA tools such as Brightway and openLCA;
- LCA databases such as ecoinvent;
- academic case studies on CCS transport and storage.

So we should not claim that the whole technical field is new.

## What Is Missing

The gap is that these pieces are usually not joined together for our specific problem.

Common missing pieces are:

- direct use of UK offshore pipeline data;
- explicit checks for missing values such as wall thickness or pressure;
- clear separation between source data and assumptions;
- pipeline repurposing focus, rather than only new pipeline design;
- simple explanation for non-specialist users;
- model-by-model validation evidence;
- LCA connected to engineering outputs;
- future extension to well repurposing;
- reproducible code and reports that can be checked line by line.

This is where our project can be stronger.

## Strong Selling Points

### 1. UKCS And NSTA Focus

The tool starts from UK offshore pipeline data, not a generic example.

This makes it useful for real UK CCS screening questions.

### 2. Repurposing-First Logic

Many tools estimate the cost of building new CO2 pipelines.

Our tool asks a different question:

> Can an existing oil and gas asset be reused, and what evidence is missing before we can trust that answer?

### 3. Data Quality Before Modelling

The tool does not silently fill gaps.

It shows when key fields are missing, assumed, repeated, or suspicious. This is important because pipeline reuse decisions are often limited by data quality, not by the equation itself.

### 4. Traceability

Every result should be linked to:

- input value;
- data source;
- assumption;
- model version;
- warning;
- output.

This makes the model easier to audit and defend.

### 5. Independent Validation

The student work reproduced its own outputs, but that does not prove accuracy.

Our approach uses external tools, standards, literature, and hand calculations to validate each module separately.

### 6. Modular Gates

The model is not one large black box.

It has clear gates:

- data gate;
- technical gate;
- economic gate;
- pre-LCA gate;
- LCA gate;
- future well gate.

This means a user can stop early when a case is weak, or continue when the evidence is strong.

### 7. LCA Integration

The LCA is not treated as a separate afterthought.

It receives outputs from the engineering model, such as length, diameter, steel mass, lifetime, refurbishment need, energy use, and transport duty.

This lets us compare:

- reuse existing pipeline;
- build a new CO2 pipeline;
- possibly reuse wells instead of drilling new wells.

### 8. Well Repurposing Extension

Adding wells gives the project a wider CCS asset-reuse angle.

This can move the work from "pipeline calculator" to "offshore CCS infrastructure repurposing platform".

### 9. Clear Interface For Non-Specialists

A professional interface can make the tool useful for researchers, policy teams, project developers, and students.

The user should see:

- what data exists;
- what is assumed;
- what passed;
- what failed;
- what must be checked by engineers.

### 10. Open And Reproducible Workflow

The scripts, reports, assumptions, and tests are kept in GitHub.

This makes the work easier to review, publish, extend, and teach.

## What We Can Claim Now

Safe current claim:

> The project is more complete, traceable, modular, and validation-ready than the student prototype.

Do not claim yet:

> The model is more accurate.

Better claim after validation:

> Each module has been validated against independent sources within stated limits, and the tool clearly shows when data quality is not sufficient for a confident decision.

## Possible Project Positioning

Simple title:

> A traceable decision-support tool for reusing UK offshore pipelines and wells in CCS infrastructure.

More detailed version:

> This project develops an auditable Python-based screening framework for UK offshore CCS asset repurposing, combining public pipeline data, engineering checks, cost screening, LCA, and future well reuse into a modular workflow with independent validation evidence.

## Main Novel Contribution

The main contribution is integration with traceability.

The value is not one magic equation. The value is a defensible workflow that tells users:

- what the data says;
- what the model assumes;
- what the result means;
- how confident we should be;
- what evidence is still needed before a real project decision.

