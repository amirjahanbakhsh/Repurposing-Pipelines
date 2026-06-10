# Pipeline Repurposing Practice Review

Date: 2026-06-10

## Short Conclusion

Pipeline repurposing for CO2 transport should be treated as a requalification and change-of-service problem first.

In simple words: we do not assume a pipeline is reusable, and we do not assume it needs a fixed amount of refurbishment steel. We first ask whether the existing pipeline can safely do the new CO2 job. Only after that do we decide whether it needs cleaning, drying, pigging, repair, tie-ins, valve changes, local replacement, or a new section.

## Why This Matters For Our Model

The model should not use one hidden "refurbishment percentage" as a default truth.

Instead, each pipeline should pass through a repurposing gate:

1. Is the data complete enough for screening?
2. Is the pipeline physically suitable for the proposed CO2 duty?
3. Is inspection or requalification evidence available?
4. What physical work is needed, if any?
5. Only then should cost and LCA calculate impacts from itemised work quantities.

This makes the tool more defendable because it follows engineering practice rather than guessing a refurbishment rate.

## Practical Repurposing Workflow

| Step | Plain-language question | Evidence needed | Model implication |
| --- | --- | --- | --- |
| 1. Define new CO2 duty | What job will the pipeline do now? | CO2 flow, pressure, temperature, phase, lifetime, start-stop cases, impurity and water limits. | Inputs must describe the target CO2 service, not only the old hydrocarbon service. |
| 2. Collect asset data | What exactly is the pipeline? | Diameter, wall thickness, material grade, design code, design pressure, MAOP, route, risers, valves, coatings, cathodic protection, start date, previous fluid. | Missing wall thickness, pressure, fluid, or date should reduce confidence. |
| 3. Regulatory and standards screen | Is this a major change of service? | HSE/PSR notification needs, ALARP basis, relevant codes, gap analysis to current good practice. | The model should report "screening only", not "approved for reuse". |
| 4. Integrity requalification | Is the pipe strong enough and in good condition? | Minimum wall calculation, inspection history, ILI/MFL/UT pigging, defect list, corrosion history, dents, gouges, spans, crossings, landfall and riser checks. | Integrity module should output pass, marginal, fail, or insufficient evidence. |
| 5. CO2-specific checks | Does CO2 introduce new risks? | Dryness/water control, impurities, corrosion risk, dense-phase operation, decompression temperature, running ductile fracture, dispersion and asphyxiation hazard. | CO2 is not just "natural gas with a different name"; the model needs warnings for CO2-specific risks. |
| 6. Cleaning, drying and pigging | Can the pipeline be prepared and inspected? | Piggability, launcher/receiver status, intelligent pigging method, drying plan, cleaning plan. | Add work items only when required by the requalification scenario. |
| 7. Define modification scope | What must be changed before reuse? | Tie-ins, pigging facilities, manifolds, spools, valves, repair clamps, section replacement, new infield line, monitoring equipment. | Cost and LCA should use itemised quantities from this step. |
| 8. Recommission and operate | How will safe operation be maintained? | Operating procedures, inspection interval, leak detection, maintenance plan, emergency response, repair philosophy. | Screening result should include operational conditions and future inspection needs. |
| 9. Reassess over life | Does the decision remain valid? | New inspections, changed CO2 specification, changed pressure, defect growth, changed regulations. | Outputs should be traceable and updateable when new evidence arrives. |

## What "Refurbishment" Should Mean

For this project, refurbishment should not mean a default percentage of total pipeline steel.

It should mean a list of actual actions, for example:

- clean and dry the line;
- run an intelligent pigging campaign;
- recondition or replace pig launcher/receiver facilities;
- add tie-ins, manifolds, spools, or valves;
- install monitoring or leak detection equipment;
- repair a local defect using a clamp or sleeve;
- replace a damaged section;
- construct a new short infield pipeline if the old pipeline cannot reach the injection point.

Some pipelines may need very little physical work. Some may be unsuitable. Some may need major changes. That is exactly why a screening tool needs a repurposing gate.

## Important Technical Risks To Track

| Risk | Why it matters | How our model should treat it |
| --- | --- | --- |
| Wall thickness uncertainty | Many public records do not give measured wall thickness. | Use uncertainty ranges and confidence levels. |
| Internal diameter uncertainty | Capacity depends strongly on diameter. | Store source and confidence for diameter. |
| Maximum operating pressure | Determines how much CO2 can be transported safely. | Use original design/MAOP carefully and flag missing pressure data. |
| Previous service | Hydrocarbon history affects corrosion and contamination risk. | Keep previous fluid and operating history as traceable inputs. |
| Dry CO2 requirement | Free water plus CO2 can cause corrosion. | LCA/cost should include drying/conditioning where required. |
| CO2 impurities | O2, H2S, SOx, NOx and water can change corrosion and phase behaviour. | Add impurity warnings before detailed design. |
| Dense-phase operation | Dense CO2 creates different decompression and fracture risks. | Do not rely only on natural-gas pipeline logic. |
| Running ductile fracture | CO2 decompression can make long fracture propagation a key risk. | Add a qualitative flag until fracture data are available. |
| Inspection evidence | Public data alone cannot prove fitness for reuse. | Require ILI/requalification evidence for high-confidence decisions. |

## Proposed Model Gate Before Cost And LCA

The next model layer should produce a `repurposing_scope_class`.

Suggested classes:

| Scope class | Meaning | Cost/LCA treatment |
| --- | --- | --- |
| `insufficient_data` | Public data are not enough for a defensible screen. | Do not calculate final cost/LCA; allow sensitivity only. |
| `requalification_only` | Existing pipeline appears suitable, but needs engineering requalification evidence. | Low physical work; include inspection and study effort. |
| `clean_dry_pig` | Pipeline may be reused after cleaning, drying and intelligent pigging. | Include pigging, cleaning/drying, temporary equipment and inspection. |
| `minor_modification` | Reuse possible with limited tie-ins, valves, pigging facility work, or local repairs. | Include itemised minor works. |
| `major_refurbishment` | Reuse possible only with major repairs, section replacement, or new connecting line. | Include major steel/construction quantities. |
| `not_suitable` | The pipeline fails key screening criteria. | Do not pass to cost/LCA as a reuse candidate. |

## Sources That Shape This Practice

The main open sources used are:

- HSE guidance says a change of conveyed fluid needs reassessment of the original pipeline design, and that CO2 projects may involve modifying existing pipeline infrastructure.
- HSE notification guidance treats changes in pressure limits, fluid type/composition, major modifications, and re-use after out-of-commissioning as events needing attention under PSR rules.
- HSE good-practice guidance expects current good practice and a gap analysis when using standards and guidance.
- DNV-RP-F104 explicitly covers design, construction, operation, and re-qualification of CO2 pipelines.
- DNV-ST-F101 covers submarine pipeline life phases, structural integrity, materials, corrosion control, operation and abandonment.
- DNV-RP-F116 is the public DNV route for submarine pipeline integrity management.
- DNV-RP-F101 is the key DNV route for assessing corrosion defects.
- Acorn's Goldeneye work used intelligent pigging to confirm fitness for purpose and discussed MFL/UT inspection options.
- Acorn's operations and maintenance philosophy discusses local repair clamps, running ductile fracture risk, component replacement, and refurbishment of recovered subsea items.
- UK CCS transport reports show that CO2 pipeline projects need integrated inspection, maintenance and repair regimes and intelligent pigging capability.

## Sources We Still Need To Obtain

These are important but not fully available from open web pages:

- Full DNV-RP-F104.
- Full DNV-ST-F101.
- Full DNV-RP-F116.
- Full DNV-RP-F101.
- BS PD 8010 Part 1 and Part 2.
- BS EN 14161.
- ISO 27913 current edition.
- API RP 579 and ASME B31G.
- Original Peterhead-Goldeneye Energy Procedia paper by Spence, Horan and Tucker, DOI: 10.1016/j.egypro.2014.11.657.

If we can access these through the university library, DNV Veracity, BSI, ISO, or ScienceDirect, the next validation step is to extract the exact clauses and turn them into model requirements.
