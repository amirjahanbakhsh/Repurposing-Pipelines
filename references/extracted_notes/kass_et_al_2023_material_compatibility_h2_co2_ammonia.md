# Kass Et Al. 2023 - Material Compatibility With Hydrogen, CO2 And Ammonia

Source ID: `REF_KASS_ET_AL_2023_MATERIAL_COMPATIBILITY`

## Citation

Michael D. Kass, James R. Keiser, Yan Liu, Amy Moore and Yarom Polsky, 2023. `Assessing Compatibility of Natural Gas Pipeline Materials with Hydrogen, CO2, and Ammonia`. Journal of Pipeline Systems Engineering and Practice, 14(2), 04023007. DOI: `10.1061/JPSEA2.PSENG-1431`.

## Local File

The PDF is available locally but is not committed to GitHub:

`C:\Users\aj52\AppData\Local\Temp\kass-et-al-2023-assessing-compatibility-of-natural-gas-pipeline-materials-with-hydrogen-co2-and-ammonia.pdf`

## Why This Paper Matters

This is one of the most useful papers so far for our repurposing foundation because it looks at existing natural gas pipeline materials and asks whether they are compatible with hydrogen blends, CO2 and ammonia.

For our project, the CO2 part is especially useful because it separates gaseous CO2 from supercritical CO2 and highlights component-level issues, not only the pipe wall.

## Model-Relevant Points

- Natural gas pipeline reuse should check the whole system, not only the steel pipe.
- Important components include pipe steel, polymers, coatings, seals, valves, meters, compressors, regulators and monitoring equipment.
- The paper indicates that pipeline materials are generally more promising for gaseous CO2 than for high hydrogen blends.
- Supercritical CO2 is more demanding than gaseous CO2, especially for compressor/regulator station materials and polymers.
- Existing compressor/regulator stations may not be suitable for supercritical CO2 without replacement or major checks.
- CO2 in the presence of water can form carbonic acid, so water control remains important.
- The paper identifies knowledge gaps around polymer performance and epoxy coatings in supercritical CO2 service.
- Hydrogen blend risks become more serious at higher hydrogen content; this is relevant if our project later expands to hydrogen.

## How We Should Use It

Use this paper to build a `material_compatibility` warning step in the repurposing gate.

Suggested warning fields:

| Field | Why it matters |
| --- | --- |
| `target_fluid_phase` | Gaseous CO2 and supercritical/dense CO2 should not be treated the same. |
| `water_control_required` | CO2 plus water can increase corrosion risk. |
| `compressor_regulator_reuse_confidence` | Existing natural gas stations may not transfer directly to supercritical CO2 service. |
| `polymer_seal_compatibility_unknown` | Public pipeline data rarely identify all elastomers and seal materials. |
| `coating_compatibility_unknown` | Coatings may need separate compatibility checks. |
| `component_level_review_required` | Valves, meters, seals and monitoring equipment need explicit review. |

## Direct Relevance To Our CO2 Model

This source supports our decision that repurposing should not be represented by a single generic refurbishment percentage.

Instead, the model should ask:

1. What CO2 phase is expected?
2. Is the CO2 dry?
3. Are compressor/regulator stations being reused?
4. Are polymers, seals and coatings known?
5. Are component replacements needed?

The answers should feed cost and LCA as itemised work, not as a hidden assumption.

## Limitations

- The paper is a compatibility review, not a complete requalification standard.
- It is based mainly on material compatibility knowledge, not project-specific inspection data.
- It does not approve any individual pipeline for reuse.

## Next Extraction Task

Create a compatibility matrix for our model:

- rows: steel pipe, welds, valves, compressors, regulators, seals, coatings, meters, sensors;
- columns: gaseous CO2, dense/supercritical CO2, wet CO2, hydrogen blend, ammonia;
- outputs: likely compatible, caution, not suitable, unknown, evidence needed.
