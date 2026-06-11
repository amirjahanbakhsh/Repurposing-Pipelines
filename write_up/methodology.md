# Methodology Draft

Date: 2026-06-11

## 1. Aim And Scope

This study develops a transparent screening method for assessing whether existing UK offshore hydrocarbon pipelines could be repurposed for carbon dioxide transport as part of carbon capture and storage projects.

The method is designed for early-stage decision support. It does not replace detailed engineering design, regulatory approval, operator requalification, or specialist integrity review. Its purpose is to screen many candidate pipelines, identify promising cases, show where evidence is missing, and support more detailed follow-up work.

The first model scope is pipeline repurposing. Wells, platforms, compression facilities, hubs, and storage-site integration are planned as later extensions once the pipeline workflow is stable.

## 2. Method Philosophy

The model follows a modular screening philosophy. In simple terms, this means the overall decision is split into smaller layers:

```text
pipeline data
  -> data quality and assumptions
  -> CO2 capacity screening
  -> corrosion screening
  -> wall-thickness and remaining-life screening
  -> repurposing evidence gate
  -> cost screening
  -> pre-LCA decision gate
  -> LCA screening
  -> validation and reporting
```

Each module can run separately, but each output is also saved so it can be used by later modules. This avoids a black-box model. Every important input, assumption, warning, equation note, and output is written to a trace file.

The method is deliberately conservative. A pipeline can have good capacity but still be marked `marginal` if important evidence is missing. This is important because repurposing is not only a flow calculation. It is also a requalification problem.

## 3. Data Foundation

The main public dataset is the NSTA offshore pipeline dataset. The extracted records are processed into a candidate ranking table, and the screening workflow currently runs over 155 model-ready hydrocarbon pipeline records.

For each pipeline, the model uses key fields where available:

- pipeline number;
- pipeline name;
- fluid;
- status;
- length;
- internal diameter;
- wall thickness;
- maximum operating pressure;
- start date.

The model also uses Goldeneye as a benchmark case because Goldeneye is a known UK CCS repurposing candidate. However, Goldeneye is not treated as a perfect public-data record. The NSTA data and student/dissertation data contain gaps and conflicting assumptions, so Goldeneye is treated as a benchmark scenario with traceable assumptions.

All values are labelled by source and data quality. Typical quality labels are:

| Label | Meaning |
| --- | --- |
| `reported` | Reported in a dataset, paper, poster, dissertation, or operator source. |
| `derived` | Calculated from other values. |
| `calculated` | Produced by a model or previous calculation. |
| `assumed` | Temporarily assumed because direct evidence is missing. |
| `missing` | Not available. |

This is important because a value from a certificate or inspection record is not the same as a value assumed for screening.

## 4. Benchmark And Reference Cases

The methodology uses three types of reference case.

First, Goldeneye dissertation and poster cases are used for reproduction. Reproduction means our model can reproduce the student/dissertation outputs. This is useful, but it is not independent validation because those outputs came from the student code.

Second, the broader literature is used to shape the model structure. The DNV/PTC requalification papers support treating CO2 pipeline reuse as a staged requalification process rather than a simple reuse calculation. These sources support the repurposing gate, phase screening, CO2 specification checks, corrosion warnings, fracture evidence needs, and work-scope outputs.

Third, independent tools and external references are planned for validation. These include REFPROP or CoolProp for CO2 properties, NETL CO2 transport cost tools for cost comparison, and ecoinvent/openLCA/Brightway for LCA.

## 5. Capacity Screening

The capacity module estimates whether a selected pipeline can transport the target annual CO2 flow.

Inputs include:

- pipeline length;
- internal diameter;
- inlet pressure;
- outlet pressure;
- transport temperature;
- CO2 molecular weight;
- compressibility factor;
- viscosity;
- friction factor;
- required annual CO2 flow.

The current capacity model reproduces the equation form used in the student dissertation/poster workflow. It calculates an average pressure, estimates maximum mass flow rate, converts the flow to MtCO2/year, and compares it with the required design flow.

The average pressure is calculated as:

```text
P_average = (2 / 3) * (P_in + P_out - (P_in * P_out) / (P_in + P_out))
```

The design flow is calculated as:

```text
required_design_flow = required_project_flow / capacity_factor
```

The current model uses supplied CO2 property values rather than a fully validated property package. Therefore, capacity results are suitable for screening and reproduction, but they still need independent validation against REFPROP, CoolProp, or another trusted CO2 property source.

## 6. Corrosion Screening

The corrosion module is a screening-level dry-CO2 risk check. It is not a full corrosion prediction model.

The module checks:

- assumed future CO2 corrosion-rate range;
- CO2 water content, if available;
- water specification limit, if available;
- water dew-point margin, if available.

The logic is conservative:

- if water content is above the selected limit, the corrosion risk is `high`;
- if the dew-point margin is negative, the corrosion risk is `high`;
- if water and dew-point evidence are missing, the corrosion risk is at least `medium`;
- if the conservative corrosion-rate case is material, the risk is at least `medium`.

This reflects the literature position that free water and impurities can create serious corrosion risk in carbon-steel CO2 pipelines. The corrosion result is passed to the integrity module and the repurposing gate.

## 7. Integrity And Wall-Thickness Screening

The integrity module estimates remaining life using a simple wall-thickness balance.

The main calculation is:

```text
historical_wall_loss = historical_corrosion_rate * historical_years
current_wall_thickness = nominal_wall_thickness - historical_wall_loss
available_wall = current_wall_thickness - minimum_wall_thickness
remaining_life = available_wall / future_CO2_corrosion_rate
```

The model also calculates low, base, and high remaining-life cases. This is done because wall thickness, historical wall loss, minimum wall basis, and future CO2 corrosion rate are often uncertain during screening.

Wall-thickness uncertainty is applied to all screened pipelines, not only Goldeneye. Goldeneye receives special attention because different sources report or imply different wall-thickness assumptions.

The output is not a final fitness-for-service decision. It is a screening result that shows whether a pipeline is worth deeper investigation.

## 8. Repurposing Gate

The repurposing gate is the main new feature added to make the model more aligned with current requalification practice.

The gate asks:

> Is this pipeline only mathematically possible, or is there enough real evidence to treat reuse as a serious option?

The gate checks:

- CO2 phase: gas phase, dense phase, or unknown;
- CO2 composition, water and impurity evidence;
- wall-thickness and remaining-life evidence;
- inspection evidence, such as ILI/MFL;
- material certificates or testing basis;
- fracture/decompression evidence, especially for dense phase;
- component compatibility for valves, seals, coatings, and equipment;
- cleaning, drying, debris, leak detection, isolation, and IMR work-scope needs.

The gate outputs:

- `repurposing_gate_status`;
- `repurposing_evidence_score`;
- `repurposing_phase_status`;
- `repurposing_evidence_gaps`;
- `repurposing_work_scope_items`;
- `repurposing_gate_cited_references`.

The gate is based on requalification themes from DNV/PTC and related practical case studies. The current implementation cites the relevant source IDs directly in the code and in the output trace.

The gate does not approve reuse. It identifies what must be checked next. This is a key methodological point: the model turns uncertainty into an explicit output instead of hiding uncertainty inside a final score.

## 9. Cost Screening

The cost module currently estimates a screening-level new-build benchmark and avoided capital cost. The first implementation uses cost components inherited from the Goldeneye/student benchmark and scales default NSTA cases by length.

Current outputs include:

- material cost;
- labour cost;
- right-of-way or damages cost;
- miscellaneous cost;
- surge tank cost;
- control system cost;
- booster station cost;
- contingency;
- total cost.

At this stage, cost is useful for relative screening but is not yet externally validated. The next cost-method step is to compare selected cases with NETL CO2 transport cost tools and to convert repurposing-gate work-scope items into itemised reuse costs.

## 10. LCA Method

The LCA method is currently designed as a conventional process-based LCA. Conventional means it uses current process data, current background datasets, and clearly stated assumptions. Prospective and dynamic LCA are planned as later extensions.

The first LCA question is:

> What environmental burden is avoided, added, or shifted by reusing an existing pipeline instead of building a new equivalent CO2 pipeline?

The first comparison is:

- reuse an existing offshore pipeline for CO2 transport;
- build a new equivalent offshore CO2 pipeline.

The first functional unit should be:

```text
transport 1 tonne of CO2 through the selected pipeline route
```

The current repository includes two LCA routes:

1. A screening proxy that estimates steel and simple construction/refurbishment impacts.
2. An ecoinvent-linked conditional workflow that creates inventory and mapping files, but requires private ecoinvent-derived impact factors before final kg CO2e values can be claimed.

Licensed ecoinvent database files and private impact factors are not committed to GitHub. Only shareable mappings, templates, scripts, and conditional reports are stored.

The repurposing gate feeds LCA by listing work-scope items such as cleaning, drying, inspection, material testing, fracture study, and monitoring. The next LCA improvement is to turn those items into itemised quantities.

## 11. Decision Gates

The method uses decision gates to prevent weak cases from looking stronger than they are.

The repurposing gate checks whether reuse evidence is strong enough.

The pre-LCA gate checks whether a pipeline should move into LCA:

- `pass`: technically credible enough for LCA screening;
- `marginal`: promising, but key assumptions still need checking;
- `fail`: do not move forward until technical issues are resolved;
- `insufficient_data`: not enough information to decide.

LCA should not be used to rescue a technically weak pipeline. If the technical or evidence gate fails, the LCA result is marked as sensitivity-only or blocked.

## 12. Validation Strategy

The validation strategy separates reproduction from independent validation.

| Level | Meaning |
| --- | --- |
| Level 0 | The code runs and unit tests pass. |
| Level 1 | The model reproduces the dissertation/poster outputs. |
| Level 2 | The model agrees with external references, tools, or published examples. |
| Level 3 | A domain expert reviews the assumptions, limits, and interpretation. |

This distinction is essential. Matching the student's dissertation result does not prove the model is correct, because the dissertation result came from student code. Independent validation is needed before making strong accuracy claims.

Current validation status:

- unit tests are implemented for the main modules;
- Goldeneye dissertation/poster reproduction is implemented;
- NSTA batch screening runs for 155 candidate records;
- independent validation against REFPROP/CoolProp, NETL, and final ecoinvent/openLCA/Brightway results is still pending.

## 13. Outputs And Traceability

Each run produces three output types:

- CSV files for tables and calculations;
- Markdown reports for human reading;
- JSON trace files for audit and future web-app evidence panels.

The trace file records:

- source parameters;
- module inputs;
- assumptions;
- outputs;
- warnings;
- formula notes;
- model version;
- cited references where relevant.

This traceability is part of the methodology, not just a coding convenience. It allows another person to see how each result was produced.

## 14. Current Limitations

The current methodology has important limits:

- CO2 properties are not yet fully validated against REFPROP or CoolProp.
- Corrosion is a screening check, not a full CO2 corrosion model.
- Integrity is a wall-thickness screening calculation, not full requalification.
- Fracture/decompression is flagged by the repurposing gate but not yet calculated.
- Cost is not yet fully validated against NETL.
- LCA has an ecoinvent-linked workflow, but final kg CO2e needs private impact factors.
- Work-scope items are listed, but detailed cost and LCA quantities are not yet calculated.
- Wells and storage integration are not yet implemented.

These limitations are visible by design. The model is intended to show what is known, what is assumed, and what must be checked next.

## 15. Key Sources Used

The methodology currently uses the following project source IDs. Full reference details are stored in `references/literature_index.csv`.

| Source ID | How it supports the method |
| --- | --- |
| `REF_PETERHEAD_GOLDENEYE_2014` | Goldeneye CCS project context. |
| `REF_MAHMOUD_DODDS_2022` | Submarine pipeline repurposing and remaining-life screening context. |
| `REF_OSTBY_TORBERGSEN_RONEID_LEINUM_2022_CO2_REQUALIFICATION` | CO2 requalification logic and key risks. |
| `REF_TORBERGSEN_LEINUM_RONEID_2025_GAS_PHASE_CO2_REQUALIFICATION` | Gas-phase versus dense-phase reuse logic. |
| `REF_MONSMA_MURRAY_2026_GAS_PHASE_CO2_REPURPOSING` | Feasibility-gate structure and work-scope thinking. |
| `REF_KUMAR_LOWERY_PASSUCCI_2025_ENI_LIVERPOOL_BAY_IMR` | Cleaning, drying, residual debris, inspection and IMR practice. |
| `REF_YUSOF_AZIZ_2025_PETRONAS_DENSE_PHASE_CO2_REPURPOSING` | Dense-phase CO2 fracture, material certificate and section-replacement issues. |
| `REF_DALONZO_BUSCO_ELVIRA_CHERUBINI_2025_CO2_IMR` | Fitness-for-purpose and IMR planning. |
| `REF_BURKINSHAW_GALLON_CARVELL_HUSSAIN_2024_HYDROGEN_DATA_EVIDENCE` | Evidence confidence, data completeness and traceability approach. |
| `REF_KASS_ET_AL_2023_MATERIAL_COMPATIBILITY` | Material and component compatibility screening. |
| `REF_BOGS_ABDELSHAFY_WALTHER_2025_MINIMUM_REGRET_CO2_NETWORKS` | Future extension to network planning under uncertainty. |
| `REF_ANVARI_ET_AL_2026_CO2_NETWORK_SIMULATION` | Future extension to source-sink and physical network simulation. |
| `REF_KUMAR_ROSEN_ESQUIVEL_2025_CO2_RICH_MIXTURE_TRANSPORT` | Future extension to advanced CO2-rich mixture modelling. |

## 16. Next Methodology Work

The next writing tasks are:

1. Add a short mathematical appendix for all implemented equations.
2. Add a data-processing subsection for the NSTA extraction and completeness check.
3. Add a validation-results subsection once REFPROP/CoolProp, NETL, and LCA checks are completed.
4. Convert source IDs into the final reference style required by the target report or paper.

