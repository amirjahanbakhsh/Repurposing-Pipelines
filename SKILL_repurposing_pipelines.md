# Skill: Repurposing Pipelines Project

Use this file at the start of every session to restore full context before touching any code.

---

## 1. What the Project Is

A professional screening tool for evaluating existing UK offshore oil and gas pipelines for CO₂ transport and CCS reuse. It is not an engineering approval tool — a `pass` or `marginal` means the pipeline is worth studying further.

**GitHub repo:** `https://github.com/amirjahanbakhsh/Repurposing-Pipelines.git`
**Clone to:** `/home/claude/repo`

---

## 2. Repo Structure (Key Paths)

| Path | Purpose |
|---|---|
| `app/streamlit_app.py` | Main Streamlit UI (~1043 lines). Single file for the full dashboard. |
| `repurposing_pipelines/` | All Python model modules (costs, hydraulics, corrosion, LCA, etc.) |
| `scripts/` | CLI runners: `run_pipeline_screen.py`, `run_refurbishment_cost.py`, `run_ecoinvent_lca.py` |
| `model_layers/01_data_foundation/` | NSTA pipeline data CSVs, completeness reports |
| `model_layers/02_capacity_hydraulics/` | Capacity/hydraulic validation CSVs |
| `model_layers/03_corrosion_integrity/` | Wall-thickness and corrosion CSVs |
| `model_layers/04_cost_economics/` | `refurbishment_cost_summary_*.csv` — cost outputs consumed by the UI |
| `model_layers/05_lca/` | LCA inventory, ecoinvent mapping, LCA report CSVs |
| `model_layers/06_screening_and_decision/` | Main screening output CSVs and markdown reports |
| `model_layers/07_independent_validation/` | Validation plan and reports |
| `tests/` | `python -m unittest discover -s tests` |

---

## 3. The Eight Gate Model

The dashboard walks a pipeline through 8 sequential assessment stages, each with its own `render_*` function in `streamlit_app.py`:

| # | Gate | `render_` function | Key CSV source |
|---|---|---|---|
| 1 | Data Completeness | `render_data_layer` | `01_data_foundation/` |
| 2 | Transport Capacity | `render_capacity_layer` | `06_screening_and_decision/pipeline_screen_*.csv` |
| 3 | Corrosion Screening | `render_corrosion_layer` | same screening CSV |
| 4 | Wall Thickness / Integrity | `render_integrity_layer` | same screening CSV |
| 5 | Repurposing Evidence Gate | `render_gate_layer` | same screening CSV |
| 6 | Quantified Work Scope | `render_work_scope_layer` | same screening CSV |
| 7 | Refurbishment Cost | `render_cost_layer` | `04_cost_economics/refurbishment_cost_summary_*.csv` |
| 8 | LCA Screening | `render_lca_layer` | `05_lca/lca_report_*.csv` |

---

## 4. Known Cases vs NSTA Pipelines

The selector at the top of the UI has two modes:

- **NSTA model-ready pipelines** — selected from the ranked candidate list; scenario name is `nsta_{pipeline_id_lower}` (e.g. `nsta_pl774`).
- **Known CCS benchmark cases** — hardcoded in `KNOWN_CASES` dict: `goldeneye_poster`, `goldeneye_dissertation`. These benchmark against the student dissertation and conference poster assumptions.

---

## 5. Cost Layer — Current State and Outstanding Problem

### What exists
- `repurposing_pipelines/refurbishment_cost.py` — applies unit-cost factors to work-scope rows, outputs `cost_low_usd_2025`, `cost_base_usd_2025`, `cost_high_usd_2025`.
- `repurposing_pipelines/costs.py` — currently only partially implements Parker; only pre-calculated component inputs, not full regression equations.
- `model_layers/04_cost_economics/refurbishment_cost_summary_*.csv` — has refurbishment low/base/high; loaded by `load_cost_row()` in `streamlit_app.py`.
- The UI currently shows only refurbishment cost (low/base/high) as three metrics.

### What needs to be built (agreed decisions)

**Step 1 — Rewrite `costs.py`** to implement all four regression models properly:
- Parker (2004) — full equations, base year 2000 USD
- Rui et al. (2011) — regional + AVG, base year 2008 USD
- McCoy & Rubin (2008) — regional + AVG, base year 2004 USD
- Brown et al. (2022) — regional + AVG, base year 2018 USD

**Step 2 — Proper escalation chain** (see `model_layers/04_cost_economics/cost_escalation_basis.md`):
- Normalise all models to 2011 USD using Handy-Whitman / GDP / PPI index ratios
- Escalate 2011 → project year using **RSMeans CCI** (not a flat % rate)
- RSMeans CCI table: 191.2 (2011 base) → 295.6 (2024) → 298.7 (2025) → ~306.5 (2026 est.)
- For years beyond last known data point: user-defined flat rate with a warning

**Step 3 — CO2 factor and offshore factor:**
- CO2 factor: **1.25** on MAT + LAB only (not ROW or MISC). Ref: McCoy & Rubin (2008); NETL (2024)
- Offshore factor: **1.6** (base), range 1.5–2.0 for sensitivity. Replaces student's 1.3 which was too low
- Basis: USAID (2002) reports offshore ≈1.96× onshore; 1.6 is conservative for shallow North Sea

**Step 4 — UI: three-column cost layer**
The `render_cost_layer()` function must show:
1. **New-build CAPEX** — computed from chosen model + escalation + CO2 + offshore factors
2. **Refurbishment CAPEX** — from work-scope unit costs (low/base/high)
3. **Net CAPEX saving** = new-build − refurbishment (low/base/high)

**Step 5 — Model selection in UI**
User selects which of the four models to use for new-build CAPEX, with a default of Parker (most cited in CCS literature). All four can be shown together as a range.

### Key references (full bibliography in cost_escalation_basis.md)
- Parker (2004): original regression, UCD-ITS-RR-04-35
- Rui et al. (2011): Oil and Gas Journal, 109(27), 120–127
- McCoy & Rubin (2008): Int. J. Greenhouse Gas Control, 2(2), 219–229
- Brown et al. (2022): Int. J. Hydrogen Energy, 47(50), 33813–33826
- NETL (2024): CO2 Transport Cost Model 2024, OSTI:2473642
- RSMeans (2026): Construction Cost Index, Gordian Group

---

## 6. Map / Dropdown Selection — Current State

- The map renders pipeline routes using `render_route_map()` with a pydeck/HTML component.
- Map clicks set `st.session_state["map_selected_pipeline_id"]` and trigger `st.rerun()`.
- The dropdown (`st.selectbox`) reads from the same session state and stays in sync.
- **Known issue from prior session:** map click was unreliable; a fallback dropdown was added. Current code appears stable but has not been re-tested after recent changes.

---

## 7. Transparent Calculation Cards — Outstanding Objective

All 8 gate layers should show **explicit formula blocks and step-by-step calculation cards** rather than opaque status pills. This means:

- Show the equation used.
- Show the input values plugged in.
- Show the computed result.
- Use `equation_box()` (already in the app) for formulae and `st.metric()` / `data_table()` for values.

Current state: some layers (capacity, corrosion, cost) have partial formula blocks. Integrity, gate, and work-scope layers are minimal.

---

## 8. Working Rules (User Preferences)

- **Work on the repo directly** — not on individual files pasted into chat.
- **Short answers** preferred. Confirm understanding before writing code.
- **Iterative, confirmation-first** — propose the change, wait for a yes, then implement.
- **No large rewrites without confirmation.** Change the minimum needed.
- Push strategy: user handles `git push` themselves; Claude edits files in the cloned repo at `/home/claude/repo`.
- Always re-read the relevant file immediately before editing it.

---

## 9. Session Start Checklist

1. Clone the repo: `git clone https://github.com/amirjahanbakhsh/Repurposing-Pipelines.git /home/claude/repo`
2. Read this skill file.
3. Read `PROJECT_STATUS.md` and `START_HERE.md` for any updates since last session.
4. Confirm the active objective with the user before touching code.

---

## 9b. Data Quality Hierarchy — Formal Methodology

This hierarchy applies to **every parameter** in every pipeline assessment. It is the formal response to missing or conflicting data and must be implemented in Gate 1 (Data Completeness) and documented in the journal paper.

### Literature basis
- Burkinshaw (2024, ROSEN/National Gas): *"existing integrity management systems are currently based on secondary data, often without direct reference to the supporting primary records... Where primary records are not available, care should be taken and additional justifications may be required."*
- Mahmoud & Dodds (2022): *"Contingencies account for missing data"* and *"The method accepts some levels of data censoring."*
- API TR 1178: Data Integration for Pipeline Integrity — defines source hierarchy and SME knowledge use when primary records are absent.
- API RP 1160 (3rd ed.): Managing System Integrity — defines data quality requirements for IMP.
- ASME B31.8S: Supplement to B31.8 — specifies data integration approach for integrity management.

### The hierarchy (7 tiers)

| Priority | Source | Label in code | Notes |
|---|---|---|---|
| 1 | Original design/construction documents, mill certificates, as-built drawings | `primary_record` | Gold standard. Lock as `reported`. |
| 2 | Regulator database (NSTA, PHMSA, etc.) | `regulatory_record` | Publicly verifiable. Treat as `reported`. |
| 3 | ILI/MFL inspection report (measured in-service) | `measured_inspection` | Most current wall condition. Supersedes design wall for integrity. |
| 4 | Pressure test records (hydrotest — confirms minimum wall by implication) | `pressure_test_derived` | Indirect but physically binding lower bound. |
| 5 | Engineering back-calculation from known P, grade, design factor (Barlow) | `engineering_derived` | Accepted in API 1160 / ASME B31.8S. Must state all inputs and DF used. |
| 6 | API/ASME standard nominal wall for OD and pressure class | `standard_nominal` | Valid only when OD, grade, and MAOP are all confirmed. |
| 7 | Conservative engineering assumption with explicit uncertainty range | `assumed_conservative` | Last resort. Must state the range and what it would take to improve it. |

### Two-dimensional assessment required

Source quality alone is insufficient. Every parameter must also carry a **criticality flag**:

- **Critical** — result changes materially if this parameter is wrong (wall thickness, pipe grade, operating pressure, OD). A tier-7 source for a critical parameter must trigger a warning in the UI and be flagged in the journal paper.
- **Significant** — affects result but within sensitivity range (corrosion rate, capacity factor).
- **Minor** — small effect on output (LCA proxy factors, contingency fraction).

### Implementation in Gate 1
Every parameter's `quality` field in the assumptions CSV must be mapped to one of the 7 tiers above. Gate 1 scores completeness as: (number of critical parameters at tier ≤ 4) / (total critical parameters). A score below 50% means the result is screening-only and must not be cited as an engineering assessment.

### Goldeneye wall thickness conflict
- Dissertation: 22.23 mm (= Sch 140, standard wall) — consistent with ~260 barg design pressure typical of North Sea high-pressure gas export pipelines.
- Poster: 14.28 mm (non-standard, implies ~167 barg design pressure — lower but still feasible).
- Barlow minimum at 120 barg, X60, DF 0.72: 10.23 mm — both values are physically feasible.
- **Resolution**: 22.23 mm is more likely correct (standard schedule, consistent with North Sea HPHT practice). 14.28 mm may be a data entry error or a different section of the pipeline. Both should be run as sensitivity cases until primary records are found.
- **Source to seek**: Shell/Repsol Goldeneye pipeline specification, NSTA pipeline records, or Pale Blue Dot/Acorn pre-FEED documents.

---

## 10. Reference Library — Evaluation and Gate Mapping

All references are in `/write_up/papers_reports_guidelines/`. Every model layer must answer: **IS THIS RIGHT? IS THERE A WAY TO CROSS-CHECK AND VALIDATE?**

### 10.1 Standards and Guidelines (Authoritative — use as mandatory references)

| Ref | Document | Year | Relevant Gates | Key content |
|---|---|---|---|---|
| ISO-27913 | ISO 27913: CO2 Pipeline Transportation Systems | 2024 (2nd ed.) | Gates 3,4,5,6 | Design, materials, operating limits, inspection, commissioning for CO2 pipelines. **Most current standard — use for all CO2-specific requirements** |
| DNV-RP-J202 | DNV: Design and Operation of CO2 Pipelines | 2010 | Gates 3,4,5,6 | Re-qualification process, material compatibility, pressure, fracture. Superseded in part by ISO 27913 but still widely cited — note its age |
| API-RP-1110 | API RP 1110: Pressure Testing of Steel Pipelines (7th ed.) | 2022 | Gate 4,5,6 | Pressure testing requirements for CO2 service. **2022 edition — current** |
| CO2PipeHaz | CO2PipeHaz Good Practice Guidelines (EU FP7) | 2013 | Gates 3,4,5 | Failure consequence hazard assessment, safety distances, good practice for CO2 pipelines |
| CCS_Policy | CCS Policy, Legal and Regulatory Review | 2024 | Context/Introduction | Global CCS regulatory landscape. Use for introduction and policy context |

### 10.2 Key Papers on Pipeline Repurposing (Core technical references)

| Ref | Authors / Title | Year | Relevant Gates | Key content and validation use |
|---|---|---|---|---|
| Mahmoud & Dodds | Technical evaluation for repurposing submarine pipelines for H2 and CCS using survival analysis | 2022 | Gates 1,4,5 | **Directly relevant** — survival analysis for offshore pipeline remaining life. Validates approach to data completeness and integrity gate. Cross-check our wall thickness and remaining life estimates against their method |
| OTC-31457 (Luna-Ortiz) | Reusing Existing Infrastructure for CO2 Transport: Risks and Opportunities | 2022 | Gates 3,4,5,6 | Risks checklist for CO2 reuse: corrosion, materials, inspection, cleaning. Validates our gate structure |
| DNV PTC2022 (Leinum et al.) | Safely repurposing existing pipeline infrastructure for CO2 transport | 2022 | Gates 3,4,5,6 | DNV re-qualification process per DNV-ST-F101. **Key reference for the evidence/repurposing gate (Gate 5)** |
| DNV PTC2025 (Torbergsen et al.) | Key considerations for re-qualification of pipelines for CO2 in gas phase | 2025 | Gates 3,4,5 | Gas-phase CO2 repurposing specifics. Dense phase not always viable for existing pipes. **2025 — most current DNV view** |
| Saipem PTC2025 (D'Alonzo et al.) | Transport and Fitness for Purpose: assessment, baseline benchmark and IMR plan | 2025 | Gates 4,5,6 | Step-by-step guidance for inspection, maintenance, repair plan for repurposing and new CO2 pipelines. **Validates work scope (Gate 6)** |
| Burkinshaw 2024 (ROSEN/National Gas) | Case Study: Efficient Route to Evidence Safe Repurposing | 2024 | Gates 1,4,5 | Importance of primary data records. Validates our data completeness gate and evidence gate approach |
| Monsma & Murray 2026 (DNV) | Strategic Repurposing of Existing Oil Pipeline for CO2 Gas-phase Transport | 2026 | Gates 3,4,5 | **Most recent (2026)** feasibility framework for gas-phase CO2. Structured decision gate approach mirrors ours |
| Kumar et al. 2025 (Eni UK) | Integrity Management, Monitoring and Maintenance of Eni UK CCS Pipelines | 2025 | Gates 4,5,6 | Real case: Liverpool Bay repurposing. Validates integrity management approach |
| Kass et al. 2023 | Assessing Compatibility of NG Pipeline Materials with H2, CO2, and Ammonia | 2023 | Gates 3,4,5 | Material compatibility for CO2 (gaseous and supercritical). Steel and polymer compatibility. **Validates corrosion and material gate** |
| Ayodele & Ali 2026 (RGU Aberdeen) | Assessing Feasibility of Repurposing NG Pipelines for Hydrogen — Comprehensive Review | 2026 | Gates 3,4,5 | Pressure, temperature, composition effects. From Robert Gordon University (Aberdeen) — directly relevant to UKCS |

### 10.3 Cost References

| Ref | Authors / Title | Year | Relevant Gates | Key content |
|---|---|---|---|---|
| NETL 2024 | FECM/NETL CO2 Transport Cost Model | 2024 | Gate 7 | **Primary reference for new-build CAPEX model.** Contains regression equations, CO2 factor (1.25 on mat+lab for D>20"), escalation indices. All four model equations, coefficients and validation cases in one document |
| Smith 2021 (MIT) | Cost of CO2 Transport and Storage in Global Integrated Assessment Modelling | 2021 | Gate 7 | Reviews all four regression models. Cross-comparison. Use to validate our multi-model implementation |
| ZEP 2011 | The Costs of CO2 Transport: Post-Demonstration CCS in the EU | 2011 | Gate 7 | **Best available European offshore CO2 benchmark.** Based on real in-house data from Gassco, AMEC, Shell, Vattenfall. North Sea route. CAPEX tables for 2.5–20 Mtpa, 180–1500 km offshore. Base year Q2 2009 EUR. **Use as cross-validation benchmark** |
| Knoope et al. 2014 | Improved cost models for optimizing CO2 pipeline configuration | 2014 | Gate 7 | Physics-based European model (Utrecht + Shell). Costs in €2010. Offshore factor implicitly 1.7–3.5× vs onshore. Explicitly cross-checks against ZEP. Confirms our offshore factor 1.6 is conservative lower bound |
| Baek et al. 2026 | CO2 pipeline network transportation cost model (Argonne) | 2026 | Gate 7 | **Most current peer-reviewed paper (April 2026).** From same team as Brown et al. Uses Brown coefficients + road-network routing. Confirms regional variation is 13–70% — averaging across regions distorts estimates |
| GlobalCCS 2024 (DNV) | Building Our Way to Net-Zero: CO2 Pipelines in the United States | 2024 | Gate 7 | US CO2 pipeline cost benchmark. Use to sense-check outputs |

**Critical limitation documented in references:** There is no published regression equation calibrated on measured offshore CO2 pipeline construction costs. All four regression models (Parker–Brown) are US onshore gas data with scalar adjustment factors. ZEP (2011) and Knoope et al. (2014) give the closest available European offshore benchmarks but as cost tables and physics models, not regressions. This limitation must be stated explicitly in the journal paper and the UI.

### 10.4 Hydraulics and Flow Assurance References

| Ref | Authors / Title | Year | Relevant Gates | Key content |
|---|---|---|---|---|
| FlowAssurance | Key Elements of Flow Assurance in CCS | 2025 | Gate 2 | Supercritical CO2 transport, pressure/temperature management, phase behaviour. **Cross-check our capacity/hydraulics model** |
| REPACT 2024 | REPACT Tool User Manual | 2024 | Gate 2 | Excel-based CO2 flow screening tool (gaseous and supercritical phases). **Direct cross-validation tool for Gate 2** — run same pipeline through REPACT and compare |
| HyNet CCUS Pre-FEED | WP6: Offshore Transport and Storage | ~2020 | Gate 2 | Real offshore CCS pre-FEED hydraulic design. Pressure, flow, pipeline sizing for UK offshore CO2. **Benchmark for capacity gate** |
| Goldeneye 2014 (Shell) | Peterhead-Goldeneye CCS Project | 2014 | Gates 2,5,7 | **Our primary benchmark case.** Goldeneye pipeline specifications, CO2 flow assumptions, project cost estimates. All Goldeneye results in our tool should match this paper |

### 10.5 Corrosion and Integrity References

| Ref | Authors / Title | Year | Relevant Gates | Key content |
|---|---|---|---|---|
| DNV-RP-J202 | (see above) | 2010 | Gates 3,4 | CO2 corrosion threshold: <500 ppm water content to avoid internal corrosion. Wall thickness assessment methodology |
| ISO-27913 | (see above) | 2024 | Gates 3,4 | Updated limits for water content, impurities, pressure cycles. **Supersedes DNV-RP-J202 on technical limits** |
| Kass 2023 | (see above) | 2023 | Gates 3,4 | Polymer seals and epoxy coating compatibility with supercritical CO2. Knowledge gap on compressor/regulator stations |

### 10.6 Context and Background References

| Ref | Authors / Title | Year | Use |
|---|---|---|---|
| ReStream 2021 (EU) | Reuse of O&G Infrastructure for H2 and CCS in Europe | 2021 | Introduction: European context for pipeline reuse. 23 TSOs participated. Covers feasibility criteria |
| H2Germany 2024 (DIW Berlin) | Repurposing NG Pipelines for Hydrogen: Limits and Options | 2024 | Introduction and Gate 5: comparison between H2 and CO2 repurposing challenges |
| CCS_Policy 2024 | CCS Policy, Legal and Regulatory Review | 2024 | Introduction: current global regulatory landscape |
| Noor Aini 2025 (PETRONAS) | Challenge in Enabling Pipeline Repurpose for CO2 Transportation | 2025 | Gate 5: Asian perspective on CO2 repurposing challenges |
| Ptc_2022_Leinum | (see above) | 2022 | Gate 5: DNV safety framework |

### 10.7 Cross-Validation Strategy (IS THIS RIGHT?)

For every gate, a specific cross-validation method is required:

| Gate | Cross-validation approach | Reference used |
|---|---|---|
| Gate 1: Data | Compare our completeness scoring against Burkinshaw (2024) primary data checklist | Burkinshaw 2024 |
| Gate 2: Capacity | Run same pipeline through REPACT tool and compare outlet pressure and max flow | REPACT 2024; FlowAssurance |
| Gate 3: Corrosion | Check our water content threshold (500 ppm) against ISO 27913:2024 Table values | ISO-27913; DNV-RP-J202 |
| Gate 4: Integrity | Compare wall thickness and remaining life calculation against Mahmoud & Dodds survival analysis outputs for same pipeline | Mahmoud & Dodds 2022 |
| Gate 5: Evidence | Map our evidence checklist against DNV re-qualification steps (DNV-ST-F101 / PTC2022 Leinum) | DNV PTC2022; Monsma 2026 |
| Gate 6: Work scope | Check our work scope items against Saipem IMR plan items (D'Alonzo 2025) | Saipem PTC2025 |
| Gate 7: Cost | (a) Compare Parker new-build to NETL model output for same OD/length. (b) Validate Goldeneye new-build estimate against Goldeneye 2014 paper project cost | NETL 2024; Smith 2021; Goldeneye 2014 |
| Gate 8: LCA | Compare our LCA results against Re-Stream report and HyNet pre-FEED carbon footprint figures | ReStream 2021; HyNet |

---

## 11. Priority Order for Outstanding Work

1. **Cost layer** — new-build vs refurbishment vs net saving (three-column layout, low/base/high).
2. **Data input page** — new Streamlit page for uploading and mapping external pipeline data.
3. **Map/dropdown reliability** — verify and fix if broken after testing.
4. **Transparent calculation cards** — expand formula blocks across all 8 gates.
5. **Two-level documentation** — layman and technical, both significantly improved.
6. **Factor assumptions review** — NETL comparison, wall-thickness validation basis.
7. **Wells** — Phase 2, do not start until pipeline screening is stable.

---

## 11. Data Input Page — Design Specification

### Purpose
Allow any user — regardless of data source or country — to use the tool with their own pipeline database. The tool must not be implicitly NSTA-specific.

### Supported Input Formats
- CSV
- Excel (.xlsx)
- JSON
- SQLite (file-based database, no server required)
- Future extension: PostgreSQL, SQL Server (not in scope now)

### Workflow (5 steps)

**Step 1 — Upload**
User uploads their raw database file (any supported format) or a pre-filled version of our standard input template.

**Step 2 — Auto-extraction**
If a raw file is uploaded, the tool attempts to map the user's column names to our standard template fields using name-similarity matching. Each match is shown with a confidence indicator (high / medium / low / no match).

**Step 3 — Review and confirm mapping**
User sees a table of: their column → our field → confidence. They can correct any mapping via dropdown (fallback to manual). Missing fields with no match are flagged clearly.

**Step 4 — Fill gaps manually**
Missing required fields are listed. User can enter values manually in the UI. Optional fields can be left blank with a warning.

**Step 5 — Save template**
Exports the completed data as our standard input CSV template, which feeds all 8 model gates. User can also save the column mapping for reuse with the same data source.

### Map behaviour
The pipeline map must use coordinates from the uploaded data, not hardcoded to the North Sea. Map centre and zoom adjust dynamically to the dataset's geographic extent.

### Field naming convention
All internal field names are based on the model's own terminology (e.g. `pipeline_id`, `outer_diameter_in`, `length_km`). No field name should be NSTA-specific. Names must be common, readable, and self-explanatory to a non-specialist.

### Column auto-matching approach
- Primary: string similarity between user column names and our field names (case-insensitive, ignore underscores/spaces)
- Secondary: match against a list of known aliases per field (e.g. `OD`, `outer_dia`, `pipe_diameter` all map to `outer_diameter_in`)
- Fallback: manual dropdown selection by user
- Confidence levels: High (>85% match), Medium (60–85%), Low (<60%), No match

---

## 12. Documentation — Design Specification

### Two levels required

**Layman / policymaker level**
- What the tool does and why it matters (plain English)
- What inputs are needed and where to get them
- How to read the results
- What a `pass`, `marginal`, or `fail` means in practice
- No Python, no equations

**Technical level**
- Full methodology for each of the 8 gates
- Equation derivations and references
- How to extend the tool (new data sources, new gates)
- How to run scripts from the command line
- How to interpret validation outputs

### Format
- Both levels should be accessible from the Streamlit UI (a Help or Documentation page)
- Also available as standalone markdown files in the repo
- Current `README.md`, `START_HERE.md`, and `methodology.md` are a starting point but need significant expansion and simplification
