# Student Code Critical Review

Review date: 2026-06-09

Reviewed files:

- `pipe_ev2.ipynb`
- `corrosion_norsok2.ipynb`
- `cost_model.ipynb`
- `data_pipelines_uk (1).geojson`

Supporting repo files:

- `scripts/audit_student_submission.py`
- `reports/student_submission_audit.md`

## Short Conclusion

The student code is useful as a prototype and as evidence of the modelling ideas used in the dissertation. It should not be used as the production code for this project.

The main reason is not that the work is worthless. The issue is that the notebooks are not traceable, tested, or reproducible enough for a professional CCS repurposing tool. Some assumptions are hidden inside the code, some data values appear manually filled, and several calculations need formal validation before we trust the outputs.

## What The Student Code Contains

| Area | What is present | Main comment |
| --- | --- | --- |
| Pipeline capacity | Streamlit prototype using pure CO2 properties, Duan EOS, viscosity, friction factor, and McCoy and Rubin style capacity equation | Good starting idea, but not validated and not connected to the pipeline dataset |
| Corrosion | NORSOK M-506 style hydrocarbon corrosion calculation plus remaining wall thickness calculation | Useful reference, but not enough for CO2 repurposing integrity decisions |
| Cost | Parker, Rui, McCoy and Rubin, and Brown cost models | Several models are present, but the implementation mixes years, currencies, regions, and assumptions |
| Data | Small GeoJSON table with 27 pipelines | Not the full NSTA dataset; many values look manually assumed |
| Interface | Basic Streamlit and notebook widgets | Prototype only; not yet a professional web app |

## Critical Findings

### 1. The pipeline data is not reliable enough yet

The supplied GeoJSON has only 27 pipeline records. Our NSTA extraction found thousands of pipeline records and 155 usable hydrocarbon candidates after filtering.

Key completeness check on the student GeoJSON:

| Field | Result |
| --- | --- |
| Total records | 27 |
| Maximum operating pressure | Missing or zero in 26 of 27 records |
| Wall thickness | Same value, 22.225 mm, for all 27 records |
| Goldeneye | Included as `PL1978`, but maximum operating pressure is zero |
| Fluids | Includes gas, oil, and water pipelines |
| Match with full NSTA attributes | All 27 records are present in the full NSTA extraction |
| Match with our 155 model-ready NSTA candidates | Only 1 record overlaps: `PL1761` Schiehallion |

This strongly suggests that some values, especially wall thickness, grade, and start date, were manually assumed. These values may still be useful, but only if we record their source and confidence level.

There are also direct data differences. For example, the student table gives Schiehallion `PL1761` a wall thickness of `22.225 mm`, while the NSTA attribute extraction gives `17.5 mm`. The student table also sets some maximum operating pressures to zero where the full NSTA extraction has a non-zero value, for example `PL1762` and `PL10`.

### 2. Goldeneye is included, but not with complete data

Goldeneye appears as:

- NSTA number: `PL1978`
- Name: `20" GAS GOLDENEYE - ST. FERGUS`
- Length: `101676.7 m`
- Diameter: `20 in`
- Internal diameter: `18.25 in`
- Grade: `X60`
- Start date: `2003`
- Status: `NOT IN USE`
- Maximum operating pressure: `0.0`
- Wall thickness: `22.225 mm`

This supports the earlier concern: the Goldeneye record exists, but important engineering fields are not complete. We should treat Goldeneye as a benchmark scenario with documented assumptions, not as a clean NSTA-derived record.

### 3. The capacity model is promising but not validated

The notebook uses a serious technical route: CO2 property routines, Duan equation of state, viscosity, friction factor, and a McCoy and Rubin style flow equation.

Main risks:

- It assumes pure CO2.
- It uses average pressure and constant temperature.
- It uses a standard nominal internal diameter rather than always using the actual pipeline internal diameter.
- It does not check against trusted property packages such as REFPROP, CoolProp, NIST data, or NETL tools.
- It has weak input protection. For example, reversed inlet/outlet pressure could produce invalid results.

This model is useful as a reference, but we need benchmark tests before accepting the results.

### 4. The corrosion model is not enough for CO2 service decisions

The corrosion notebook is mostly a NORSOK M-506 style hydrocarbon corrosion calculator. That is not the same as a full dense-phase CO2 pipeline corrosion assessment.

Main risks:

- The code asks for the future CO2 corrosion rate as an input instead of predicting it from CO2 quality, water, impurities, pressure, and temperature.
- The calculation uses the current computer year, so the result changes as time passes unless the assessment year is fixed.
- The notebook asks for internal diameter, then uses that value in the minimum wall thickness calculation where outside diameter is normally required.
- The pressure guidance says to use absolute or gauge pressure "just be consistent"; this is not strong enough for design review.
- If the available wall thickness is negative, the code can still calculate a negative remaining CO2 service life.

This part should become a screening-level integrity module only, with clear warnings and validation against NORSOK examples and pipeline requalification guidance.

### 5. The cost notebook has several models, but weak cost discipline

The student used several economic models: Parker, Rui, McCoy and Rubin, and Brown. This is useful because it lets us compare cost estimates instead of relying on one formula.

Main risks:

- The same function name `costbooster` is defined twice. The second definition overwrites the first.
- `total_cost()` passes a length in kilometres into a booster function that expects miles.
- A Euro to US dollar conversion factor is set to `1`, which is a hidden assumption.
- A CO2 cost factor of `1.25`, offshore factor of `1.3`, escalation rate, and contingency are hard-coded in places.
- The models are mostly US cost correlations, so they need calibration before being used for UK offshore CCS pipelines.
- Base years are mixed: 2000, 2004, 2008, 2011, and 2018.

The cost models are worth keeping as options, but each result must report its source, base year, currency, region, escalation, and uncertainty.

### 6. The visual interface is a prototype, not a professional app

The Streamlit code is generated from inside the notebook using `%%writefile` or string-writing. This is fine for a student demonstration, but not for a maintainable web app.

Interface gaps:

- No pipeline picker connected to the GeoJSON.
- No map view.
- No clear input validation.
- No scenario save/load.
- No traceable result report.
- No modular result pages for capacity, integrity, cost, LCA, and final decision.

For our tool, the interface should sit on top of tested model modules. The app should not contain the scientific equations directly.

## What We Should Reuse

We should reuse these parts as references:

- The list of models the student selected.
- The Goldeneye assumptions, but only as a traceable benchmark scenario.
- The 27-pipeline GeoJSON as a clue to manually enriched data, not as the master dataset.
- The Streamlit prototype as a rough picture of what the student tried to show.

We should not copy the notebooks directly into the production model.

## Model Validation Plan

Before trusting any output, we should validate each module separately:

| Module | Validation check |
| --- | --- |
| CO2 properties | Compare density, viscosity, and compressibility against REFPROP, CoolProp, NIST, or published tables |
| Hydraulics | Compare Goldeneye and selected pipelines against dissertation results and NETL or similar CO2 transport tools |
| Corrosion | Compare NORSOK calculations against official examples; separately define CO2-service corrosion assumptions |
| Wall thickness | Check against proper pipeline design/requalification equations and clarify inside vs outside diameter |
| Cost | Reproduce published model examples, then compare with NETL REPACT or other CCS cost tools |
| Data | Compare every filled value against NSTA, operator documents, decommissioning reports, or stated assumptions |
| Interface | Test that the app result matches the command-line model for the same inputs |

## Recommended Way Forward

1. Keep the student notebooks as historical reference only.
2. Continue with our modular Python structure.
3. Create a traceable input table for Goldeneye and the 27 student-selected pipelines.
4. Compare those 27 records against our 155 usable NSTA candidates.
5. Add validation tests for CO2 properties, hydraulics, corrosion, wall thickness, and cost.
6. Only after validation, build the professional interface around the tested modules.
7. Add LCA after the pre-LCA screening gate, so LCA is applied only to technically plausible candidates.

## Decision

The student code confirms the project direction, but it also confirms why we need a professional rebuild.

The safest approach is:

- use the student work to understand assumptions,
- keep every assumption traceable,
- rebuild the models as tested modules,
- validate each module before using it for ranking or decision-making.
