# How To Run The Model

This guide is for a user with no programming background.

The model is run from PowerShell using simple commands. You copy one command, press Enter, then read the output file.

## Before You Start

Open PowerShell.

Go to the project folder:

```powershell
cd "C:\Users\aj52\Documents\Repurposing Pipelines"
```

You only need to do this once when you open a new PowerShell window.

## Option 0: Open The Visual Dashboard

Use this when you want to choose a pipeline visually and read the current model outputs without opening many CSV files.

### Step 1: Install The Dashboard Packages

Run this once:

```powershell
python -m pip install -r requirements.txt
```

### Step 2: Start The Dashboard

```powershell
python -m streamlit run app\streamlit_app.py
```

PowerShell should show a local web address, usually:

```text
http://localhost:8501
```

Open that address in your browser.

### Step 3: Choose A Pipeline

Use the dropdown to choose an NSTA pipeline number, for example:

```text
PL774
```

You can also switch to `Known CCS benchmark cases` and choose Goldeneye.

The dashboard shows:

- the selected route on a map;
- the main screening decision;
- pipeline data and missing-data warnings;
- the input data and equation notes for each model layer;
- gate-by-gate outcomes;
- quantified refurbishment work-scope;
- cost and LCA factor status;
- traceability files and references.

To run the model from the dashboard:

1. Choose a pipeline from the dropdown, or click a route on the map when available.
2. Keep `Cost/LCA factors` as `screening` for a complete early estimate.
3. Click a layer button, such as `Run / refresh capacity layer`, `Run cost layer`, or `Run LCA layer`.
4. Use `Run all layers` only when you want to refresh the full workflow.

Important: the dashboard reads and updates saved model outputs. The command-line scripts below remain the auditable way to run the same workflow.

If the NSTA geometry file is updated and the map needs to be rebuilt, run:

```powershell
python scripts\build_dashboard_assets.py
```

## Option 1: Run A Known Goldeneye Case

Use this when you want to run one of the Goldeneye benchmark cases from the dissertation/poster.

### Step 1: Show Available Goldeneye Cases

```powershell
python scripts\run_pipeline_screen.py --list-scenarios
```

You should see:

```text
- goldeneye_dissertation
- goldeneye_poster
```

### Step 2: Choose One Case

For example, choose:

```text
goldeneye_poster
```

### Step 3: Run The Model

```powershell
python scripts\run_pipeline_screen.py --scenario goldeneye_poster
```

### Step 4: Read The Result

Open this file:

```text
model_layers/06_screening_and_decision/pipeline_screen_goldeneye_poster.md
```

The most important lines are:

- `Decision`
- `Confidence`
- `Main Numbers`
- `Quantified work-scope summary`
- `Why This Decision?`
- `Next Data To Check`

## Option 2: Screen All NSTA Pipelines

Use this as the normal first step when you want to compare many pipeline candidates.

### Step 1: Run The Full Screening

```powershell
python scripts\run_pipeline_screen.py --screen-all-nsta
```

This screens all model-ready NSTA hydrocarbon pipeline candidates using:

- the public NSTA pipeline data;
- simple shared screening assumptions;
- uncertainty ranges for wall thickness and corrosion.

### Step 2: Read The Batch Report

Open this file:

```text
model_layers/06_screening_and_decision/pipeline_screen_nsta_all.md
```

Start with:

- `Candidate Count`
- `Pre-LCA Decisions`
- `Top 30 Strategic Screened Pipelines`

The report focuses on strategic pipelines at least 1 km long. Very short connecting segments are still kept in the CSV file, but they are not the main screening priority.

### Step 3: Choose One Pipeline Number

In the report table, copy the NSTA number, for example:

```text
PL774
```

Then run that pipeline using Option 3 below.

The full table is also saved here:

```text
model_layers/06_screening_and_decision/pipeline_screen_nsta_all.csv
```

The quantified refurbishment work-scope table is saved here:

```text
model_layers/06_screening_and_decision/refurbishment_work_scope_nsta_all.csv
```

## Option 3: Run One NSTA Pipeline

Use this when you want to choose one pipeline from the ranked NSTA candidate list.

### Step 1: Show Top NSTA Pipelines

```powershell
python scripts\run_pipeline_screen.py --list-nsta --top 20
```

This command reads the ranked NSTA file:

```text
model_layers/01_data_foundation/nsta_candidate_ranked.csv
```

This shows a list like:

```text
- rank 1: PL774 | CATS PIPELINE | GAS | ACTIVE | 405.0 km
- rank 2: PL1761 | 20in Gas Trunkline - Schiehallion PLEM to Sullom Voe terminal | GAS | ACTIVE | 188.0 km
- rank 3: PL762 | SAGE PIPELINE | GAS | ACTIVE | 323.7 km
```

How to read one line:

```text
rank 1: PL774 | CATS PIPELINE | GAS | ACTIVE | 405.0 km
```

This means:

| Part | Meaning |
| --- | --- |
| `rank 1` | Its position in our current ranked list. |
| `PL774` | The NSTA pipeline number. This is the best value to copy. |
| `CATS PIPELINE` | Pipeline name. |
| `GAS` | Fluid in the pipeline. |
| `ACTIVE` | Current NSTA status. |
| `405.0 km` | Pipeline length. |

### Step 2: Copy The NSTA Pipeline Number

Use the code after the rank number.

Example:

```text
PL774
```

This is safer than using the pipeline name because names can be long or duplicated.

You can also open the full ranked table here:

```text
model_layers/01_data_foundation/nsta_candidate_ranked.csv
```

In that file, look for these columns:

| Column | Meaning |
| --- | --- |
| `RANK` | Ranking number created by our script. |
| `NSTAPIPNO` | NSTA pipeline number, for example `PL774`. |
| `PIPE_NAME` | Pipeline name. |
| `FLUID` | Fluid type, for example gas. |
| `STATUS` | Whether it is active, not in use, etc. |
| `LENGTH_KM` | Length in km. |

### Step 3: Run The Model

```powershell
python scripts\run_pipeline_screen.py --nsta-id PL774
```

You can replace `PL774` with another NSTA pipeline number from the list.

After you press Enter, expect PowerShell to print something like:

```text
Scenario: nsta_pl774
Pipeline: CATS PIPELINE
NSTA number: PL774
Decision: fail
Report: C:\Users\aj52\Documents\Repurposing Pipelines\model_layers\06_screening_and_decision\pipeline_screen_nsta_pl774.md
CSV: C:\Users\aj52\Documents\Repurposing Pipelines\model_layers\06_screening_and_decision\pipeline_screen_nsta_pl774.csv
Trace: C:\Users\aj52\Documents\Repurposing Pipelines\model_layers\06_screening_and_decision\pipeline_screen_nsta_pl774_trace.json
Work scope: C:\Users\aj52\Documents\Repurposing Pipelines\model_layers\06_screening_and_decision\refurbishment_work_scope_nsta_pl774.csv
```

The key line is:

```text
Decision: fail
```

Your decision may be `pass`, `marginal`, `fail`, or `insufficient_data`.

### Step 4: Read The Result

For `PL774`, open:

```text
model_layers/06_screening_and_decision/pipeline_screen_nsta_pl774.md
```

The quantified work-scope table is:

```text
model_layers/06_screening_and_decision/refurbishment_work_scope_nsta_pl774.csv
```

For another pipeline, the file name will follow the same pattern:

```text
model_layers/06_screening_and_decision/pipeline_screen_nsta_PIPELINENUMBER.md
```

Example:

```text
model_layers/06_screening_and_decision/pipeline_screen_nsta_pl762.md
```

Start with the report file. It is written for humans.

The CSV and JSON files are mainly for checking, debugging, or later use in the web app.

## Wall Thickness Uncertainty

Wall thickness is uncertain for any pipeline, not only Goldeneye.

For early screening, the model therefore uses a range:

| Case | Plain meaning |
| --- | --- |
| `low` | Conservative case. Less usable wall is available. |
| `base` | Main estimate. |
| `high` | Optimistic case. More usable wall is available. |

Goldeneye has a wider uncertainty range because the available information is less clear. Other NSTA pipelines still have uncertainty, but the default range is narrower unless better evidence says otherwise.

## What The Decision Means

| Decision | Plain meaning |
| --- | --- |
| `pass` | Good enough to move to LCA screening. |
| `marginal` | Promising, but important assumptions need checking. |
| `fail` | Do not move forward until the failed issue is fixed. |
| `insufficient_data` | The model does not have enough information to decide. |

## Important Files

For each run, the model normally creates three files.

| File type | What it is for |
| --- | --- |
| `model_layers/.../*.md` | Human-readable report. Start here. |
| `model_layers/.../*.csv` | Table of calculated numbers. |
| `model_layers/.../*.json` | Full trace showing inputs, assumptions, warnings, and formulas. |

## Very Important Warning

This is a screening model only.

It is not engineering approval.

If the model says `pass` or `marginal`, it means the pipeline may be worth checking further. It does not mean the pipeline is safe or ready for CO2 transport.

## If Something Goes Wrong

If PowerShell says:

```text
python is not recognized
```

then Python is not available from PowerShell. Install Python or open a PowerShell where Python is available.

If the model says:

```text
Unknown scenario
```

run:

```powershell
python scripts\run_pipeline_screen.py --list-scenarios
```

If the model says the NSTA pipeline was not found, run:

```powershell
python scripts\run_pipeline_screen.py --list-nsta --top 20
```

Then copy the `PL...` number exactly.

## Option 4: Run The LCA Report

Use this after you have selected one pipeline.

### Step 1: Create The Private Factor Template

Run this once:

```powershell
python scripts\run_ecoinvent_lca.py --create-factor-template
```

This creates a private CSV file here:

```text
model_layers/05_lca/private/lca_impact_factors_private.csv
```

This file is not uploaded to GitHub because it will contain ecoinvent-derived values.

### Step 2: Run LCA For One NSTA Pipeline

Example using public screening factors:

```powershell
python scripts\run_ecoinvent_lca.py --nsta-id PL774 --factor-mode screening
```

You can replace `PL774` with another NSTA pipeline number.

After you press Enter, expect PowerShell to print something like:

```text
Scenario: nsta_pl774
LCA status: sensitivity_only
Report: C:\Users\aj52\Documents\Repurposing Pipelines\model_layers\05_lca\lca_report_nsta_pl774.md
```

The key line is:

```text
LCA status: sensitivity_only
```

This is not an error. For `PL774`, it means the LCA has calculated with screening factors, but the upstream technical gate failed, so the result is only a sensitivity result.

If you run with private factors and they are missing, you may see:

```text
LCA status: blocked_missing_impact_factors
```

That means the model has built the inventory, but final kg CO2e values need the private impact factors.

### Step 3: Read The LCA Report

For `PL774`, open:

```text
model_layers/05_lca/lca_report_nsta_pl774.md
```

Start with:

- `Status`
- `Required Inventory Rows`
- `Missing factor keys`

## Option 5: Run Refurbishment Unit-Cost Factors

Use this when you want to turn the quantified work-scope table into a cost table.

### Step 1: Create The Private Unit-Cost Template

Run this once:

```powershell
python scripts\run_refurbishment_cost.py --create-factor-template
```

This creates:

```text
model_layers/04_cost_economics/private/refurbishment_unit_costs_private.csv
```

Fill this private file with unit rates when you have them. Do not upload it to GitHub.

### Step 2: Run One Pipeline

```powershell
python scripts\run_refurbishment_cost.py --case nsta_pl774 --factor-mode screening
```

### Step 3: Read The Result

Open:

```text
model_layers/04_cost_economics/refurbishment_cost_report_nsta_pl774.md
```

If the status is `sensitivity_only`, the cost has calculated but the upstream technical gate failed.

If the status is `screening_result`, the cost has calculated using public screening defaults.

To use private project rates after filling the private CSV, run:

```powershell
python scripts\run_refurbishment_cost.py --case nsta_pl774 --factor-mode private
```

## Option 6: Run The Independent Validation Checks

Use this when you want to check whether the model is technically credible.

### Step 1: Run The Validation Command

```powershell
python scripts\run_independent_validation.py
```

If PowerShell says `CoolProp is required`, run this once:

```powershell
python -m pip install CoolProp
```

Then run the validation command again.

Optional: include local LCA evidence from ecoinvent and the supplied LCA workbook:

```powershell
python scripts\run_independent_validation.py --ecoinvent-dir "D:\Amir\Heriot-Watt University Team Dropbox\RES_EPS_RCCS_Susana_Garcia\RCCS_Capture_Amir Jahanbakhsh\3. USorb-DAC Work\Ecoinvent_data_exported\Ecoinvent_apos_38" --lca-workbook "C:\Users\aj52\OneDrive - Heriot-Watt University\USorb-DAC\1-s2.0-S1750583623002098-mmc2.xlsx"
```

This does not copy ecoinvent data into GitHub. It only checks which useful process names are available.

### Step 2: Read The Validation Report

Open this file:

```text
model_layers/07_independent_validation/independent_validation_report.md
```

Start with the `Plain Summary` section.

### Step 3: Understand The Main Outputs

The command also creates these detailed tables:

| File | What it checks |
| --- | --- |
| `model_layers/02_capacity_hydraulics/co2_property_validation.csv` | CO2 density, viscosity, and Z factor against CoolProp. |
| `model_layers/02_capacity_hydraulics/capacity_validation.csv` | Capacity equation arithmetic and sensitivity to CoolProp Z factor. |
| `model_layers/03_corrosion_integrity/integrity_barlow_sanity_check.csv` | Simple wall-thickness sanity check. |
| `model_layers/04_cost_economics/cost_arithmetic_validation.csv` | Cost component sum and contingency arithmetic. |

Important:

If the validation report says `review_required`, it does not automatically mean the model is wrong. It means we need to check that item carefully before trusting it.
