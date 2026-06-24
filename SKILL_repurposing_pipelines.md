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
- `repurposing_pipelines/costs.py` — separate module that calculates **new-build CAPEX** using component parameters (Parker 2004-style: material, labour, ROW damages, misc, surge tank, control, booster + contingency).
- `model_layers/04_cost_economics/refurbishment_cost_summary_*.csv` — has refurbishment low/base/high; loaded by `load_cost_row()` in `streamlit_app.py`.
- The UI currently shows only refurbishment cost (low/base/high) as three metrics.

### What is missing (the key outstanding objective)
The cost layer in `render_cost_layer()` must show **three things side by side**:
1. **New-build CAPEX** — Parker (2004) regression applied to the pipeline's OD and length (from `costs.py`)
2. **Refurbishment CAPEX** — itemised work-scope unit costs (from `refurbishment_cost.py`)
3. **Net CAPEX saving** = new-build − refurbishment, with low/base/high range

This is the core economic claim of the tool: reusing the pipeline saves money vs building new. It must be visible in the UI, not buried in CSVs.

### How to achieve it
- The new-build cost is already computed in `costs.py`; its output `cost_total_usd_2025` needs to be surfaced in the cost summary CSV or computed on the fly in the UI.
- The cost layer needs a three-column layout: new-build | refurbishment | net saving.
- Low/base/high ranges should be shown for each column.
- A formula block should explain the arithmetic explicitly.

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

## 10. Priority Order for Outstanding Work

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
