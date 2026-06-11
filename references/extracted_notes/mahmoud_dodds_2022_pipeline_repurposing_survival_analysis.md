# Mahmoud And Dodds 2022 - Pipeline Repurposing Survival Analysis

Source ID: `REF_MAHMOUD_DODDS_2022`

## Citation

Ramy Magdy A. Mahmoud and Paul E. Dodds, 2022. `A technical evaluation to analyse of potential repurposing of submarine pipelines for hydrogen and CCS using survival analysis`. Ocean Engineering, 266, 112893. DOI: `10.1016/j.oceaneng.2022.112893`.

## Local File

The PDF is available locally but is not committed to GitHub:

`D:\Amir\Heriot-Watt University Team Dropbox\RES_EPS_RCCS_Susana_Garcia\RCCS_Capture_Amir Jahanbakhsh\4. Student_projects\RCCS_CCUS_Jean Carlos Campos Valverde\References\1-s2.0-S002980182202176X-main.pdf`

The PDF metadata states that the paper is open access under `CC BY 4.0`.

## Why This Paper Matters

This paper is directly relevant to our project because it is about repurposing submarine pipelines for low-carbon service, including CCS.

The useful idea is survival analysis: using historical pipeline failure records to estimate remaining life when full inspection data are incomplete. This does not replace engineering requalification, but it may be useful as an early screening or validation method.

## Model-Relevant Points

- The paper supports the idea that repurposing should be treated as technical screening first, not automatic reuse.
- It discusses several assessment routes: integrity evaluation, integrity management, Monte Carlo simulation, LCA, and survival analysis.
- It argues that survival analysis can work with some data gaps and can estimate likely remaining life from historical failure records.
- It uses PARLOC historical pipeline failure data as the basis for survival curves.
- It warns that better failure records would improve the method.
- It is useful for our remaining-life module, especially where measured inspection evidence is missing.

## Goldeneye Case Data Reported In The Paper

The paper includes Goldeneye as a CO2 repurposing case study.

| Parameter | Goldeneye value reported |
| --- | --- |
| Length | `101 km` |
| Diameter | `20 inch` |
| Previous service | `Gas` |
| Proposed service | `CO2` |
| Estimated remaining life at 2018 | `8-10 years` |
| Original design life | `20 years` |
| Commissioning year | `2004` |
| Cease of production | `2011` |
| Proposed date for new service | `2023` |

The paper's survival-analysis result suggests Goldeneye reaches the same survival probability as a 20-year design life around `2029`, which implies about `6 years` from a 2023 reuse start in that analysis.

Important: this is a statistical screening result, not proof that Goldeneye is approved for reuse. It should be compared against inspection, requalification, pressure, wall-thickness, corrosion, and CO2-specific checks.

## How We Should Use It

Use this paper as:

- a literature source supporting screening of many pipelines;
- a possible benchmark for a future remaining-life or survival-analysis module;
- an independent comparison source for Goldeneye assumptions;
- evidence that public data gaps are normal and should be handled explicitly.

Do not use it as final engineering approval for any pipeline.

## Next Extraction Task

Extract the paper's method in more detail:

- PARLOC data categories used;
- Kaplan-Meier calculation basis;
- how shutdown periods are treated;
- how diameter, length, content, and operating status affect survival curves;
- whether its Goldeneye assumptions match the NSTA data and Acorn/Goldeneye reports.
