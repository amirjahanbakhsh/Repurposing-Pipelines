# Model Validation Review

Date: 2026-06-09

Source reviewed: MSc dissertation by Jean Carlos Campos Valverde on repurposing UK oil and gas pipelines for CO2 transport.

## Short conclusion

The dissertation is a good research prototype, but it is not enough by itself to rebuild a professional tool. It names useful models and shows some equations, but the original code is missing, some formula notation in the dissertation appears unclear, and several engineering checks needed for real pipeline re-use are not included.

Our rebuild should treat the dissertation as a starting point, not as a source of truth.

## What the student appears to have used

| Area | Dissertation model choice | Initial verdict |
| --- | --- | --- |
| Pipeline data | NSTA data, cross-checked with BEIS candidate pipelines | Good idea, but every field needs source/confidence labels. |
| CO2 density | Duan EOS for pure CO2 | Acceptable as a research model, but should be benchmarked against REFPROP/CoolProp. |
| CO2 viscosity | Fenghour/Wakeham/Vesovic correlation | Good historical choice, but newer reference correlations exist. |
| Hydraulic capacity | McCoy and Rubin style steady-state capacity calculation | Useful for screening, but not enough for full design/requalification. |
| Corrosion | NORSOK M-506 | Useful for CO2 corrosion in hydrocarbon production/process systems, but not a complete dense-phase CO2 reuse model. |
| Minimum wall thickness | ASME B31.8-style pressure formula | Needs careful unit checking and proper requalification context. |
| Cost | Parker, Rui et al., McCoy and Rubin, Brown et al. | Useful early CAPEX models, but mostly based on US natural gas pipeline data. |
| LCA | Not implemented | Should become a fourth evaluation module. |

## Key validation findings

### 1. CO2 properties and hydraulics

The student effectively used one pure-CO2 property pathway:

- density from Duan EOS;
- viscosity from Fenghour et al.;
- hydraulic capacity from a steady-state mass-flow relationship.

This is acceptable for a first screening tool. It is not enough for a professional CO2 pipeline tool because real CCS streams may contain impurities such as N2, O2, Ar, CH4, H2S, SOx, NOx, and water. These can change phase behaviour, density, corrosion risk, and operating envelope.

Important issue found in the dissertation: the reduced-variable notation on the Duan EOS page appears to use critical volume where critical temperature and pressure should be used. This may be only a writing error, but it means we must verify the equations from the original references before coding.

Recommended implementation:

- Use CoolProp as the open-source reference property engine for pure CO2 first.
- Allow REFPROP comparison where available.
- Keep a local implementation of Duan/Fenghour only if needed for transparency and comparison.
- Later add mixture capability for realistic CO2 streams.
- Add phase-envelope checks: the tool should warn if pressure/temperature are near gas/liquid/two-phase boundaries.

Validation tests:

- Compare density, viscosity, compressibility factor, and phase state against CoolProp at several points: low pressure gas, near critical, dense phase, and high-pressure liquid-like conditions.
- Reproduce the Goldeneye case: about 9.1 MtCO2/year reported in the dissertation.
- Check unit conversions: psia/bar/Pa, inch/m, kg/s/Mt/year.
- Test bad inputs: outlet pressure higher than inlet pressure, temperature near critical point, impossible diameter, missing wall thickness.

### 2. Corrosion and integrity

The student used one main corrosion model: NORSOK M-506.

This is not wrong, but it is only one part of the problem. NORSOK M-506 is for CO2 corrosion rate calculation in hydrocarbon production and process systems. Reusing a pipeline for dense-phase CO2 transport also needs requalification thinking: material condition, dents, cracks, welds, fatigue, fracture propagation, water content, impurities, inspection history, and operating envelope.

Recommended implementation:

- Split corrosion into two submodules:
  - historical service damage: oil/gas operating history and previous corrosion;
  - future CO2 service: water/impurity control, remaining wall margin, and operating risk.
- Use NORSOK M-506 only inside its valid purpose and clearly label it as a screening calculation.
- Add a requalification checklist aligned with DNV-SE-0657, DNV-RP-F104, and ISO 27913.
- Show "insufficient data" when inspection data is missing; do not force a false yes/no answer.

Validation tests:

- Compare NORSOK calculations against official NORSOK example cases if we can access the standard and spreadsheet.
- Check pH, fugacity, wall shear stress, and corrosion rate separately before combining them.
- Test whether results change logically: more water, higher CO2 fugacity, higher temperature, or higher shear should not reduce risk without a clear physical reason.
- Compare minimum wall thickness with consistent units and add safety/design factors explicitly.

### 3. Economic model

The dissertation correctly says several economic models were used:

- Parker;
- Rui et al.;
- McCoy and Rubin;
- Brown et al.

However, these are mostly regression-based pipeline CAPEX models. They are useful for early screening, but they do not automatically represent UK offshore reuse costs.

Missing or weak cost items:

- inspection and intelligent pigging;
- cleaning, drying, and dewatering;
- valve and control modifications;
- compression/pumping and metering;
- offshore tie-ins and landfall work;
- permitting and regulatory work;
- monitoring systems;
- uncertainty range;
- OPEX;
- decommissioning deferral or avoidance.

Recommended implementation:

- Keep the four literature models as selectable early-cost models.
- Add NETL CO2 Transport Cost Model as a benchmark, not necessarily as the only method.
- Add a reuse-cost model, because "avoided new-build CAPEX" is not the same as "reuse project cost".
- Always report costs as ranges, not single numbers.

Validation tests:

- Reproduce the dissertation Goldeneye result: about USD 228.5 million new-build CAPEX using Parker assumptions.
- Compare the same case with NETL CO2_T_COM where possible.
- Test escalation year, currency, contingency, diameter, and length sensitivity.
- Separate new-build cost, reuse cost, avoided cost, and net saving.

### 4. LCA module to add

The professional version should include LCA as a fourth module. The key question is:

"What environmental impact is avoided by reusing an existing pipeline instead of building a new one?"

Recommended first LCA scope:

- Functional unit: transport 1 MtCO2/year over a defined lifetime, or reuse one named pipeline for a defined CCS service.
- Compare two scenarios:
  - reuse existing pipeline;
  - build a new equivalent CO2 pipeline.
- Include:
  - steel production avoided;
  - pipe manufacture avoided;
  - offshore construction avoided;
  - refurbishment emissions;
  - cleaning/drying emissions;
  - compression/pumping electricity;
  - monitoring and operation;
  - avoided or delayed decommissioning;
  - end-of-life treatment.

Recommended tools:

- Brightway if we want a Python-native LCA engine.
- openLCA if we want a recognised LCA desktop workflow with API linkage.
- ecoinvent if we have or can obtain a licence for high-quality background data.
- ISO 14040/14044 for structure and reporting.
- IEAGHG CCUS GHG accounting guidance for CCUS-specific logic.

Validation tests:

- Start with a simplified carbon-only LCA using transparent emission factors.
- Then connect to a proper LCI database.
- Always show assumptions and data quality.
- Report environmental results as ranges.

## Recommended model stack for our rebuild

1. Data layer
   - Pipeline database with units, source, confidence level, and assumptions.
   - Separate measured values from inferred values.

2. Property layer
   - CoolProp baseline for pure CO2.
   - Optional REFPROP comparison.
   - Later: impurities and phase-envelope modelling.

3. Hydraulic screening layer
   - Steady-state pressure drop and capacity.
   - Clear warning if close to phase boundary or outside model assumptions.

4. Integrity layer
   - Historical corrosion estimate.
   - Remaining wall check.
   - Requalification checklist.
   - Inspection-data status.

5. Economic layer
   - Literature CAPEX models.
   - NETL benchmark.
   - Reuse-specific cost model.
   - Uncertainty/sensitivity.

6. LCA layer
   - Reuse vs new-build environmental comparison.
   - ISO-style goal/scope, inventory, impact, interpretation.
   - Exportable assumptions and results.

7. Decision layer
   - Technical score.
   - Integrity confidence score.
   - Economic score.
   - LCA score.
   - Overall status: suitable, marginal, unsuitable, or insufficient data.

## Practical way forward

Phase 1: Build a validation notebook

- Recreate Goldeneye inputs.
- Run property checks against CoolProp.
- Reproduce the dissertation outputs.
- Record every assumption.

Phase 2: Build tested calculation modules

- `properties`
- `hydraulics`
- `corrosion`
- `integrity`
- `cost`
- `lca`

Phase 3: Build a professional UI

- Map first.
- Pipeline summary second.
- Suitability result third.
- Detailed modules below.
- Exportable report.

Phase 4: Add quality controls

- Unit tests.
- Benchmark tests.
- Assumption register.
- Data confidence labels.
- Versioned model references.

## Sources to use

- DNV-RP-F104, "Design and operation of carbon dioxide pipelines": https://www.dnv.com/energy/standards-guidelines/dnv-rp-f104-design-and-operation-of-carbon-dioxide-pipelines/
- DNV-SE-0657, "Re-qualification of pipeline systems for transport of hydrogen and carbon dioxide": https://www.dnv.com/energy/standards-guidelines/dnv-se-0657-re-qualification-of-pipeline-systems-for-transport-of-hydrogen-and-carbon-dioxide/
- ISO 27913:2024, "Carbon dioxide capture, transportation and geological storage - Pipeline transportation systems": https://www.iso.org/cms/%20render/live/en/sites/isoorg/contents/data/standard/08/48/84840.html
- NIST REFPROP: https://www.nist.gov/srd/refprop
- CoolProp CO2 documentation: https://coolprop.org/fluid_properties/fluids/CarbonDioxide.html
- NIST 2026 alternative fundamental EOS for CO2: https://www.nist.gov/publications/alternative-fundamental-equation-state-fluid-carbon-dioxide
- FECM/NETL CO2 Transport Cost Model 2024: https://www.osti.gov/biblio/2473642
- Standards Norway note on NORSOK M-506:2017 review: https://standard.no/en/news/norsok-m-5062017-co2-corrosion-rate-calculation-model-is-on-systematic-review/
- ISO 14044 LCA requirements and guidelines: https://www.iso.org/standard/38498.html
- IEAGHG Integrated GHG accounting guidelines for CCUS: https://ieaghg.org/publications/integrated-ghg-accounting-guidelines-for-ccus/
- Brightway LCA framework: https://docs.brightway.dev/en/latest/
- openLCA: https://www.openlca.org/
- ecoinvent database: https://ecoinvent.org/database/
