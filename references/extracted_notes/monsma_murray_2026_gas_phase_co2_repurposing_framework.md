# Monsma And Murray 2026 - Gas-Phase CO2 Pipeline Repurposing Framework

Source ID: `REF_MONSMA_MURRAY_2026_GAS_PHASE_CO2_REPURPOSING`

## Citation

Victoria Monsma and S. Murray, 2026. `Strategic Repurposing of Existing Oil Pipeline for CO2 gas-phase Transport: A Feasibility Framework`. Proceedings of the 2026 Pipeline Technology Conference, Berlin. ISSN `2510-6716`.

## Local File

The PDF is available locally but is not committed to GitHub:

`D:\Amir\Heriot-Watt University Team Dropbox\RES_EPS_RCCS_Susana_Garcia\RCCS_Capture_Amir Jahanbakhsh\4. Student_projects\RCCS_CCUS_Jean Carlos Campos Valverde\References\PaperSubmission_10009_0423062542.pdf`

## Why This Paper Matters

This is highly relevant to our model because it focuses directly on repurposing existing oil and gas pipelines for gas-phase CO2 transport.

The paper supports exactly the direction we have been discussing: repurposing should be handled through an early feasibility gate, followed by more detailed validation and execution only if the concept remains viable.

## Model-Relevant Points

- Gas-phase CO2 can be a practical repurposing option where dense-phase operation is limited by pressure, material or infrastructure constraints.
- The feasibility phase should define the CO2 purpose, source/sink value chain, expected volumes, operating pressure envelope, CO2 phase, and CO2 specification.
- These premises define the basis for hydraulics, safety, integrity, modification scope and cost screening.
- The paper treats feasibility as an early decision gate to avoid detailed engineering on weak assumptions.
- Screening should identify safety, integrity and cost-related showstoppers before detailed design.
- CO2 service can introduce changed risks compared with oil or gas service, including internal corrosion, fracture/decompression behaviour, release consequences and material compatibility.
- The paper supports itemising required repairs and modifications before estimating cost.
- Levelized Cost of Transport, or `LCOT`, is described as an early economic indicator once volume profile, pressure regime, and modification scope are known.

## DNV Repurposing Process Reported

The paper describes a structured DNV repurposing process with four phases:

| Phase | Meaning for our model |
| --- | --- |
| Initiation | Identify candidate pipeline and collect boundary conditions, data and premises. |
| Screening | High-level feasibility check to decide whether the pipeline is suitable in principle. |
| Validation | Detailed technical basis, testing, inspection, repair and modification scope. |
| Execution | Implement modifications and complete documentation for the agreed basis. |

This maps well onto our model plan:

| Our model layer | Link to paper |
| --- | --- |
| Data completeness | Initiation |
| Pre-LCA decision gate | Screening |
| Integrity/corrosion/material compatibility | Validation |
| Cost and LCA quantities | Repairs, modifications and operational requirements identified during validation |

## Specific Checks To Add To Our Gate

The paper supports adding these checks:

- target CO2 phase: gas phase versus dense/supercritical phase;
- operating pressure envelope;
- CO2 specification, including water and impurity limits;
- source and sink boundary conditions;
- volume profile over time;
- hydraulic feasibility and capacity;
- safety consequences of CO2 release;
- routing, permitting and regulatory constraints;
- internal corrosion under adverse water/impurity conditions;
- fracture and decompression screening;
- material compatibility of exposed components;
- isolation valves or line-break valves;
- monitoring, detection and leak-response strategy;
- repair and modification scope;
- preliminary LCOT after modification scope is known.

## Important Modelling Implication

This paper strongly supports our decision not to use a fixed default refurbishment percentage.

Instead:

1. identify risks;
2. convert risks into repairs, modifications, monitoring or operational controls;
3. pass those itemised quantities into cost and LCA;
4. then calculate screening economics such as LCOT.

That is more defendable than saying every pipeline needs an arbitrary percentage of replacement steel.

## Limitations

- It is a conference paper, not a full standard.
- It presents a feasibility framework rather than a complete design code.
- It supports screening and decision-gate logic, but final pipeline reuse still needs formal requalification and project-specific engineering evidence.

## Next Extraction Task

Use this paper to create a first `repurposing_gate` data structure:

- inputs: pipeline data, CO2 duty, phase, pressure, water/impurity limits, source/sink and volume profile;
- outputs: showstopper flags, required evidence, modification items, and gate status;
- downstream links: cost, LCA and final decision dashboard.
