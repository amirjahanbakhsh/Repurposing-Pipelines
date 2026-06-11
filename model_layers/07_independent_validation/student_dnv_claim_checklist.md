# Student DNV Approach Claim Checklist

Date: 2026-06-11

## Why This Matters

The student reportedly claimed that the work followed a DNV approach.

This is useful information, but it is not validation by itself. We should treat it as a claim to audit.

In plain language:

> Mentioning DNV is not enough. We need to see which DNV-style steps were actually used in the data, code, assumptions and decisions.

## How We Should Check The Claim

Use this checklist when reviewing the dissertation, poster and student notebooks.

| DNV-style item | What we need to see | Current judgement |
| --- | --- | --- |
| Design basis defined | CO2 phase, pressure, temperature, flow, source/sink and battery limits are stated. | Partly visible, needs traceable input table. |
| CO2 composition specified | CO2 purity, water limit and key impurities are stated. | Mostly missing or unclear. |
| Pipeline condition assessed | Wall thickness, corrosion, inspection and operating history are used. | Partly visible, but assumptions need evidence. |
| Hydraulic/flow assurance checked | Capacity, pressure drop and phase behaviour are calculated with clear units. | Present in prototype, not independently validated. |
| Integrity reassessed for CO2 service | Original pipeline suitability is checked against new CO2 service. | Only screening-level evidence visible. |
| Internal corrosion risk addressed | Free water, dew point and impurities are checked. | Not yet enough for CO2 service. |
| Fracture/decompression addressed | Dense-phase running ductile fracture or gas-phase limits are considered. | Not clearly visible. |
| Material/component compatibility checked | Pipe, welds, valves, seals, coatings and equipment are considered. | Not clearly visible. |
| Safety and release consequences considered | CO2 release, isolation, leak detection and emergency response are discussed. | Not clearly connected to model. |
| Modifications/work scope itemised | Cleaning, drying, inspection, repair or replacement are listed as work items. | Not clearly itemised. |
| Cost linked to work scope | Cost is based on actual required modifications, not only generic factors. | Not yet. |
| Documentation and traceability | Sources, assumptions, equations and warnings are recorded. | Weak in student notebooks; stronger in our rebuild. |

## What This Means For Our Model

The student work may have been inspired by DNV guidance, but the available code does not yet prove a full DNV-style requalification workflow.

Our rebuild should therefore:

- keep the DNV-style workflow as the structure;
- keep the student assumptions as traceable benchmark inputs only;
- add a formal `repurposing_gate` module;
- show which DNV-style checks pass, fail or need more evidence;
- avoid claiming final engineering approval.

## Best Use Of The Student Claim

The claim helps us choose the right validation question:

> Did the student merely cite DNV, or did the model actually implement the DNV-style decision workflow?

That should become one part of the independent validation review.

