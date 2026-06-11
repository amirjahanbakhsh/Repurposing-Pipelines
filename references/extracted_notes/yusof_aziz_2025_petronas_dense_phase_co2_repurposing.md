# Yusof And Aziz 2025 - PETRONAS Dense-Phase CO2 Pipeline Repurposing Case

Source ID: `REF_YUSOF_AZIZ_2025_PETRONAS_DENSE_PHASE_CO2_REPURPOSING`

## Citation

Noor Aini Yusof and M Faisal Aziz, 2025. `Challenge in Enabling Pipeline Repurpose for CO2 Transportation`. Proceedings of the 2025 Pipeline Technology Conference Asia, Kuala Lumpur.

## Local File

The PDF is available locally but is not committed to GitHub:

`D:\Amir\Heriot-Watt University Team Dropbox\RES_EPS_RCCS_Susana_Garcia\RCCS_Capture_Amir Jahanbakhsh\4. Student_projects\RCCS_CCUS_Jean Carlos Campos Valverde\References\ptc Asia 2025 Noor Aini Binti Yusof.pdf`

## Why This Paper Matters

This is a practical dense-phase CO2 repurposing case.

It is useful because it shows exactly the type of uncertainty we face: missing mill certificates, uncertain fracture toughness, crack history, corrosion, blowdown and external impact risk.

## Case Data Reported

| Parameter | Value reported |
| --- | --- |
| Pipeline type | Offshore gas export pipeline |
| Diameter | `30 inch` |
| Length | `220 km` in abstract; `230 km` in figure/text |
| Commission year | `1996` |
| Current service | `Dry gas` |
| Material | `Carbon steel` |
| Grade | `X65 API Spec 5L` |
| SMYS | `448 MPa` |
| UTS | `530 MPa` |
| Manufacturing | `LSAW, cold expanded` |
| Wall thickness | `20.62 mm` and `28.58 mm` |
| Corrosion allowance | `None` |
| Water depth | `0-70 m` |

The length difference should be treated as a source inconsistency until checked.

## Model-Relevant Points

- Missing mill certificates can block direct fracture toughness assessment.
- The paper used a database of around 5,000 similar linepipe datapoints to infer toughness where certificates were unavailable.
- DNV-RP-F104 is used for minimum toughness needed to arrest running ductile fracture.
- A 5 km section around `KP4-KP9` or `KP4-KP10` is identified for replacement because of lower resistance under the studied conditions.
- OLGA simulations were used for corrosion and operating condition checks.
- The study reports no water dropout under normal or blowdown scenarios for the analysed case.
- A 6-7 day blowdown was found feasible without breaching the reported minimum design temperature of `0 C`.
- Dropped and dragged anchor risk was evaluated using DNV-RP-F107.

## How We Should Use It

Use this paper as a dense-phase CO2 benchmark for our gate.

It supports adding these fields:

- `material_certificates_available`;
- `fracture_toughness_basis`;
- `cvn_known_or_inferred`;
- `dense_phase_rdf_screen_required`;
- `section_replacement_required`;
- `water_dropout_risk`;
- `controlled_blowdown_duration_days`;
- `minimum_design_temperature_c`;
- `external_interference_screen_required`.

## Limitations

- It is one project case, not a general standard.
- Some values need confirmation because the paper uses both 220 km and 230 km.
- The method may not transfer directly to UK pipelines without matching material, wall thickness, pressure, temperature and CO2 composition.
