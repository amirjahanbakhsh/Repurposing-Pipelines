# Telessy Barner Holz 2024 - Hydrogen Pipeline Repurposing Options

Source ID: `REF_TELESSY_BARNER_HOLZ_2024`

## Citation

Kornel Telessy, Lukas Barner and Franziska Holz, 2024. `Repurposing natural gas pipelines for hydrogen: Limits and options from a case study in Germany`. International Journal of Hydrogen Energy, 80, 821-831. DOI: `10.1016/j.ijhydene.2024.07.110`.

## Local File

The PDF is available locally but is not committed to GitHub:

`D:\Amir\Heriot-Watt University Team Dropbox\RES_EPS_RCCS_Susana_Garcia\RCCS_Capture_Amir Jahanbakhsh\4. Student_projects\RCCS_CCUS_Jean Carlos Campos Valverde\References\1-s2.0-S0360319924027812-main.pdf`

The PDF metadata states that the paper is open access under `CC BY 4.0`.

## Why This Paper Matters

This paper is mainly about hydrogen, not CO2. That means it should not be used as a direct CO2 corrosion or integrity standard.

It is still useful for our project because it shows how repurposing can be broken into clear technical options and then compared economically. That is close to our planned `repurposing_scope_class` idea.

## Model-Relevant Points

- The paper compares three pipeline repurposing options:
  - no pipeline modification, but enhanced maintenance;
  - use of gaseous inhibitors;
  - pipe-in-pipe.
- It shows that repurposing decisions are not only about cost. Other criteria such as sunk costs, public acceptance, and user requirements can shape the final decision.
- It highlights that the technical risk depends on the new fluid. For hydrogen, key risks include embrittlement, leakage, lower volumetric energy density, and compressor changes.
- It uses a real German high-pressure gas pipeline case study: the Norddeutsche Erdgasleitung, or `NEL`, pipeline.
- It calculates levelized cost of hydrogen transport for the repurposing options.
- It provides an example of structuring cost inputs by item, including pipeline CAPEX/OPEX, compressor CAPEX/OPEX, pipe-in-pipe CAPEX, inhibitor OPEX, economic lifetime, electricity price, WACC, and inflation.

## How We Should Use It

Use this paper as:

- a supporting reference for how to structure repurposing options;
- a reminder that physical refurbishment should be itemised, not assumed as a fixed percentage;
- a reference for cost-comparison logic between different repurposing scopes;
- a prompt to include non-cost criteria in our decision gate.

Do not use it as:

- a direct CO2 pipeline integrity standard;
- evidence that hydrogen risks and CO2 risks are the same;
- final proof that a specific pipeline can be reused.

## Possible Link To Our Model

This paper supports a future model design where each pipeline receives a scope class, for example:

| Model scope idea | Similar idea in the paper |
| --- | --- |
| `requalification_only` | no modification, but enhanced maintenance |
| `minor_modification` | added operational or safety measures |
| `major_refurbishment` | pipe-in-pipe or major physical intervention |

For our CO2 model, the actual work items will be different, but the decision structure is useful.

## Next Extraction Task

If we later develop a cost-comparison module for different repurposing scopes, extract:

- the cost equation for levelized cost of transport;
- cost categories used in the paper;
- lifetime, WACC, electricity price, and OPEX assumptions;
- how compressor requirements change under repurposing;
- which parts are hydrogen-specific and should not be transferred to CO2.
