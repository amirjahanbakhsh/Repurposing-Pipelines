# Similar Tools And Data Sources

Date: 2026-06-09

## Short conclusion

There are existing tools close to this project, but none appear to cover the full vision we want:

- pipeline reuse screening;
- CO2 capacity and phase checks;
- integrity/corrosion confidence;
- economic comparison;
- LCA/environmental comparison;
- UKCS/NSTA data workflow;
- professional web interface.

This means the project is still worthwhile, but we should learn from existing tools instead of rebuilding in isolation.

## Similar tools found

### 1. NETL REPACT

Reuse of Existing Pipelines for Adapted Carbon Transport (REPACT) is the closest match.

What it does:

- Excel-based first-pass screening tool.
- Checks whether an existing natural gas pipeline could be reused for CO2 transport.
- Covers gaseous and supercritical CO2.
- Estimates flow rate and outlet pressure.
- Includes phase-change checks.
- Allows booster station sensitivity.

Important limitation:

- NETL explicitly says it is only a high-level screening tool and should not be used for engineering, financial, or regulatory decisions.

Why it matters for us:

- We should study its input/output structure.
- We can use it as a benchmark for our hydraulics and screening logic.
- We can improve on it by adding UKCS data, corrosion/integrity confidence, cost, LCA, and a better web interface.

Source:

- https://www.osti.gov/biblio/2473254
- https://www.osti.gov/servlets/purl/2473254

### 2. NETL CO2 Transport Cost Model / CO2_T_COM

What it does:

- Excel-based model for CO2 pipeline transport cost.
- Estimates capital, operating, financing, and revenue/cost of liquid-phase CO2 transport by pipeline.
- Can optimise pipeline diameter and number of booster pumps for lowest cost.

Why it matters for us:

- Strong benchmark for the economic module.
- Better than relying only on Parker/Rui/McCoy/Brown regression equations.

Source:

- https://www.netl.doe.gov/node/12859
- https://www.netl.doe.gov/projects/files/FECMNETLCO2TransportCostModel2024DescriptionandUsersManual_082324.pdf

### 3. SimCCS

What it does:

- Open-source tool for designing carbon capture, transport, and storage infrastructure.
- Supports source-sink network design, GIS, optimisation, and regional CCUS planning.

Why it matters for us:

- Useful for network planning and routing ideas.
- Less focused on detailed reuse/integrity of a named existing pipeline.

Source:

- https://simccs.org/

### 4. Sequestrix

What it does:

- Open-source CO2 transport network optimisation tool.
- Builds on SimCCS.
- Can embed existing pipelines into network optimisation.
- Uses Streamlit, Plotly, Mapbox, and MILP optimisation.

Why it matters for us:

- Very relevant for future expansion from "single pipeline evaluation" to "network planning".
- Useful interface and architecture reference.
- It appears more network/economics focused than integrity/LCA focused.

Source:

- https://www.sequestrix.com/

### 5. Clean Air Task Force Europe CCS Cost Tool

What it does:

- Interactive European CO2 transport and storage cost tool.
- Compares pipeline, ship, barge, and rail under deployment scenarios.

Why it matters for us:

- Useful for European cost context and user-facing map design.
- It is not a pipeline reuse integrity tool.

Source:

- https://www.catf.us/ccs-cost-tool/

### 6. Commercial pipeline tools

Examples include DNV Synergi Pipeline Simulator and commercial CCUS intelligence platforms.

Why they matter:

- They show what professional users expect: scenario management, map-based workflows, reporting, and operational simulation.
- They may not be open enough for our research/codebase, but they inform our design.

Source:

- https://www.dnv.com/software/services/pipeline/mastering-co2-pipeline-operations/

## NSTA data situation

The student's clean 27-pipeline table is missing, but this may not be fatal.

The public NSTA pipeline linear data includes many of the exact fields we need:

- NSTA pipeline number;
- pipeline name;
- fluid;
- pipeline system;
- status;
- diameter;
- length;
- insulation/coating type;
- internal diameter;
- max operating pressure;
- wall thickness;
- start date;
- end date;
- untrenched/exposed flags.

This is better than expected. However, values may be missing or inconsistent, so we still need a data quality process.

Source:

- https://services-eu1.arcgis.com/OZMfUznmLTnWccBc/arcgis/rest/services/UKCS%20offshore%20infrastructure%20pipeline%20linear%20ED50/FeatureServer/layers
- https://www.data.gov.uk/dataset/b5016ca1-5371-4ee5-8e5a-b7e806de6c0e/nsta-offshore-infrastructure-etrs895

## Suggested data recovery strategy

1. Extract the NSTA pipeline linear dataset directly.
2. Build a raw table with all fields preserved.
3. Filter candidate CO2 reuse pipelines by:
   - gas/condensate/mixed hydrocarbon service;
   - status;
   - diameter;
   - length;
   - max operating pressure;
   - wall thickness availability;
   - distance to CCS clusters/storage.
4. Add a data quality flag to every field:
   - reported by NSTA;
   - derived from geometry;
   - found in report;
   - estimated from standard;
   - missing.
5. Search pipeline-by-pipeline for missing high-value fields, especially:
   - wall thickness;
   - grade/material;
   - design pressure;
   - commissioning year;
   - historical operating conditions;
   - inspection/decommissioning status.
6. Do not silently assume wall thickness or grade. If we estimate, the UI must clearly say "assumed".

## Design opportunity

The gap in existing tools is a UKCS-focused, transparent, professional screening tool that combines:

- NSTA pipeline data;
- CO2 hydraulic capacity;
- phase risk;
- corrosion/integrity screening;
- cost saving;
- LCA comparison;
- assumption tracking;
- exportable decision report.

That is the direction we should take.
