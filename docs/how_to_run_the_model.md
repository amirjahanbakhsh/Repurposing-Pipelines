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
reports/pipeline_screen_goldeneye_poster.md
```

The most important lines are:

- `Decision`
- `Confidence`
- `Main Numbers`
- `Why This Decision?`
- `Next Data To Check`

## Option 2: Run One NSTA Pipeline

Use this when you want to choose one pipeline from the ranked NSTA candidate list.

### Step 1: Show Top NSTA Pipelines

```powershell
python scripts\run_pipeline_screen.py --list-nsta --top 20
```

This command reads the ranked NSTA file:

```text
data/processed/nsta_candidate_ranked.csv
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
data/processed/nsta_candidate_ranked.csv
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
Report: C:\Users\aj52\Documents\Repurposing Pipelines\reports\pipeline_screen_nsta_pl774.md
CSV: C:\Users\aj52\Documents\Repurposing Pipelines\data\processed\pipeline_screen_nsta_pl774.csv
Trace: C:\Users\aj52\Documents\Repurposing Pipelines\data\processed\pipeline_screen_nsta_pl774_trace.json
```

The key line is:

```text
Decision: fail
```

Your decision may be `pass`, `marginal`, `fail`, or `insufficient_data`.

### Step 4: Read The Result

For `PL774`, open:

```text
reports/pipeline_screen_nsta_pl774.md
```

For another pipeline, the file name will follow the same pattern:

```text
reports/pipeline_screen_nsta_PIPELINENUMBER.md
```

Example:

```text
reports/pipeline_screen_nsta_pl762.md
```

Start with the report file. It is written for humans.

The CSV and JSON files are mainly for checking, debugging, or later use in the web app.

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
| `reports/...md` | Human-readable report. Start here. |
| `data/processed/...csv` | Table of calculated numbers. |
| `data/processed/...json` | Full trace showing inputs, assumptions, warnings, and formulas. |

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

## Option 3: Run The Independent Validation Checks

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
reports/independent_validation_report.md
```

Start with the `Plain Summary` section.

### Step 3: Understand The Main Outputs

The command also creates these detailed tables:

| File | What it checks |
| --- | --- |
| `data/validation/co2_property_validation.csv` | CO2 density, viscosity, and Z factor against CoolProp. |
| `data/validation/capacity_validation.csv` | Capacity equation arithmetic and sensitivity to CoolProp Z factor. |
| `data/validation/integrity_barlow_sanity_check.csv` | Simple wall-thickness sanity check. |
| `data/validation/cost_arithmetic_validation.csv` | Cost component sum and contingency arithmetic. |

Important:

If the validation report says `review_required`, it does not automatically mean the model is wrong. It means we need to check that item carefully before trusting it.
