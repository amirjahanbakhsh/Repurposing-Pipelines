"""Independent validation helpers for screening modules."""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
from typing import Any

from .assumptions import ScenarioAssumptions, read_scenario_assumptions
from .constants import G_PER_MOL_TO_KG_PER_MOL, INCH_TO_M, PSI_TO_PA, UNIVERSAL_GAS_CONSTANT
from .costs import COST_COMPONENT_PARAMETERS
from .goldeneye import benchmark_scenario_with_trace
from .hydraulics import average_pressure_pa
from .units import kg_per_s_to_mtpa


MODEL_VERSION = "independent_validation_v0.1"

PROPERTY_THRESHOLDS_PERCENT = {
    "density_kg_per_m3": 1.0,
    "viscosity_micro_pa_s": 3.0,
    "compressibility_factor_z": 1.0,
}

PIPE_GRADE_SMYS_MPA = {
    "X42": 289.6,
    "X52": 358.5,
    "X60": 413.7,
    "X65": 448.2,
    "X70": 482.6,
}


def _coolprop():
    try:
        import CoolProp.CoolProp as coolprop  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local environment
        raise RuntimeError(
            "CoolProp is required for CO2 property validation. "
            "Install it with: python -m pip install CoolProp"
        ) from exc
    return coolprop


def _round(value: float | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def relative_difference_percent(model_value: float, reference_value: float) -> float:
    return 100 * (model_value - reference_value) / reference_value


def absolute_relative_difference_percent(model_value: float, reference_value: float) -> float:
    return abs(relative_difference_percent(model_value, reference_value))


def _scenario_pressure_temperature(scenario: ScenarioAssumptions) -> tuple[float, float, float, float]:
    inlet_pa = scenario.number("inlet_pressure_psia") * PSI_TO_PA
    outlet_pa = scenario.number("outlet_pressure_psia") * PSI_TO_PA
    average_pa = average_pressure_pa(inlet_pa, outlet_pa)
    temperature_k = scenario.number("transport_temperature_c") + 273.15
    return inlet_pa, outlet_pa, average_pa, temperature_k


def _manual_capacity_kg_per_s(
    *,
    inner_diameter_m: float,
    length_m: float,
    inlet_pressure_pa: float,
    outlet_pressure_pa: float,
    temperature_k: float,
    compressibility_factor: float,
    molecular_weight_kg_per_mol: float,
    fanning_friction_factor: float,
) -> float:
    """Local arithmetic check for the published equation form.

    This deliberately repeats the equation outside `hydraulics.max_capacity_kg_per_s`
    so implementation mistakes can be caught more easily.
    """
    import math

    pressure_term = inlet_pressure_pa**2 - outlet_pressure_pa**2
    numerator = (
        math.pi**2
        * inner_diameter_m**5
        * molecular_weight_kg_per_mol
        * pressure_term
    )
    denominator = (
        64
        * fanning_friction_factor
        * compressibility_factor
        * UNIVERSAL_GAS_CONSTANT
        * temperature_k
        * length_m
    )
    return math.sqrt(numerator / denominator)


def _historical_wall_loss_mm(scenario: ScenarioAssumptions) -> float:
    reported = scenario.optional_number("reported_historical_wall_loss_mm")
    if reported is not None:
        return reported
    return (
        scenario.number("historical_corrosion_rate_mm_per_year")
        * scenario.number("historical_corrosion_years")
    )


def validate_co2_properties(scenarios: dict[str, ScenarioAssumptions]) -> list[dict[str, Any]]:
    coolprop = _coolprop()
    rows: list[dict[str, Any]] = []

    for scenario_name, scenario in sorted(scenarios.items()):
        _, _, average_pa, temperature_k = _scenario_pressure_temperature(scenario)
        reference_values = {
            "density_kg_per_m3": coolprop.PropsSI("D", "P", average_pa, "T", temperature_k, "CO2"),
            "viscosity_micro_pa_s": coolprop.PropsSI("V", "P", average_pa, "T", temperature_k, "CO2") * 1e6,
            "compressibility_factor_z": coolprop.PropsSI("Z", "P", average_pa, "T", temperature_k, "CO2"),
        }
        phase = coolprop.PhaseSI("P", average_pa, "T", temperature_k, "CO2")

        for parameter, reference_value in reference_values.items():
            model_value = scenario.number(parameter)
            difference = relative_difference_percent(model_value, reference_value)
            abs_difference = abs(difference)
            threshold = PROPERTY_THRESHOLDS_PERCENT[parameter]
            status = "pass" if abs_difference <= threshold else "review_required"
            rows.append(
                {
                    "scenario": scenario_name,
                    "module": "co2_properties",
                    "validation_type": "independent_benchmark",
                    "parameter": parameter,
                    "model_value": _round(model_value),
                    "reference_value": _round(reference_value),
                    "unit": scenario.record(parameter).unit,
                    "difference_percent": _round(difference, 4),
                    "absolute_difference_percent": _round(abs_difference, 4),
                    "acceptance_threshold_percent": threshold,
                    "status": status,
                    "reference": "CoolProp",
                    "pressure_mpa": _round(average_pa / 1e6, 6),
                    "temperature_c": scenario.number("transport_temperature_c"),
                    "phase": phase,
                    "notes": "Pure CO2 benchmark at the model average pipeline pressure.",
                }
            )

        rows.append(
            {
                "scenario": scenario_name,
                "module": "co2_properties",
                "validation_type": "independent_benchmark",
                "parameter": "phase_state",
                "model_value": "not_reported",
                "reference_value": phase,
                "unit": "text",
                "difference_percent": "",
                "absolute_difference_percent": "",
                "acceptance_threshold_percent": "",
                "status": "information",
                "reference": "CoolProp",
                "pressure_mpa": _round(average_pa / 1e6, 6),
                "temperature_c": scenario.number("transport_temperature_c"),
                "phase": phase,
                "notes": "The current model does not yet store phase as an input/output.",
            }
        )

    return rows


def validate_capacity(scenarios: dict[str, ScenarioAssumptions]) -> list[dict[str, Any]]:
    coolprop = _coolprop()
    rows: list[dict[str, Any]] = []

    for scenario_name, scenario in sorted(scenarios.items()):
        inlet_pa, outlet_pa, average_pa, temperature_k = _scenario_pressure_temperature(scenario)
        row, _ = benchmark_scenario_with_trace(scenario_name, scenario)
        manual_capacity_mtpa = kg_per_s_to_mtpa(
            _manual_capacity_kg_per_s(
                inner_diameter_m=scenario.number("inner_diameter_in") * INCH_TO_M,
                length_m=scenario.number("pipeline_length_km") * 1000,
                inlet_pressure_pa=inlet_pa,
                outlet_pressure_pa=outlet_pa,
                temperature_k=temperature_k,
                compressibility_factor=scenario.number("compressibility_factor_z"),
                molecular_weight_kg_per_mol=scenario.number("molecular_weight_co2_g_per_mol")
                * G_PER_MOL_TO_KG_PER_MOL,
                fanning_friction_factor=scenario.number("fanning_friction_factor"),
            )
        )
        arithmetic_difference = manual_capacity_mtpa - row["capacity_mtpa"]
        rows.append(
            {
                "scenario": scenario_name,
                "module": "capacity",
                "validation_type": "implementation_arithmetic_check",
                "parameter": "capacity_mtpa",
                "model_value": _round(row["capacity_mtpa"]),
                "reference_value": _round(manual_capacity_mtpa),
                "unit": "MtCO2/year",
                "difference_percent": _round(
                    relative_difference_percent(row["capacity_mtpa"], manual_capacity_mtpa),
                    6,
                ),
                "status": "pass" if abs(arithmetic_difference) <= 1e-9 else "review_required",
                "reference": "independent arithmetic repeat of the equation",
                "notes": "This checks code arithmetic, not the physical model choice.",
            }
        )

        coolprop_z = coolprop.PropsSI("Z", "P", average_pa, "T", temperature_k, "CO2")
        capacity_with_coolprop_z_mtpa = kg_per_s_to_mtpa(
            _manual_capacity_kg_per_s(
                inner_diameter_m=scenario.number("inner_diameter_in") * INCH_TO_M,
                length_m=scenario.number("pipeline_length_km") * 1000,
                inlet_pressure_pa=inlet_pa,
                outlet_pressure_pa=outlet_pa,
                temperature_k=temperature_k,
                compressibility_factor=coolprop_z,
                molecular_weight_kg_per_mol=scenario.number("molecular_weight_co2_g_per_mol")
                * G_PER_MOL_TO_KG_PER_MOL,
                fanning_friction_factor=scenario.number("fanning_friction_factor"),
            )
        )
        rows.append(
            {
                "scenario": scenario_name,
                "module": "capacity",
                "validation_type": "independent_property_sensitivity",
                "parameter": "capacity_with_coolprop_z_mtpa",
                "model_value": _round(row["capacity_mtpa"]),
                "reference_value": _round(capacity_with_coolprop_z_mtpa),
                "unit": "MtCO2/year",
                "difference_percent": _round(
                    relative_difference_percent(row["capacity_mtpa"], capacity_with_coolprop_z_mtpa),
                    4,
                ),
                "status": (
                    "pass"
                    if absolute_relative_difference_percent(
                        row["capacity_mtpa"],
                        capacity_with_coolprop_z_mtpa,
                    )
                    <= 1.0
                    else "review_required"
                ),
                "reference": "CoolProp Z factor",
                "notes": "This shows the capacity impact of replacing the student Z factor with CoolProp.",
            }
        )

    return rows


def validate_integrity_barlow_sanity(
    scenarios: dict[str, ScenarioAssumptions],
    *,
    design_factor: float = 0.72,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for scenario_name, scenario in sorted(scenarios.items()):
        pipe_grade = str(scenario.raw("pipe_grade")).strip().upper()
        smys_mpa = PIPE_GRADE_SMYS_MPA.get(pipe_grade)
        if smys_mpa is None:
            rows.append(
                {
                    "scenario": scenario_name,
                    "module": "integrity",
                    "validation_type": "barlow_sanity_check",
                    "status": "insufficient_data",
                    "notes": f"Unknown pipe grade '{pipe_grade}'.",
                }
            )
            continue

        pressure_mpa = scenario.number("inlet_pressure_psia") * PSI_TO_PA / 1e6
        outer_diameter_mm = scenario.number("outer_diameter_in") * 25.4
        barlow_min_wall_mm = pressure_mpa * outer_diameter_mm / (2 * smys_mpa * design_factor)
        scenario_min_wall_mm = scenario.number("minimum_wall_thickness_mm")
        historical_loss_mm = _historical_wall_loss_mm(scenario)
        current_wall_mm = scenario.number("nominal_wall_thickness_mm") - historical_loss_mm
        available_wall_model_mm = current_wall_mm - scenario_min_wall_mm
        available_wall_barlow_mm = current_wall_mm - barlow_min_wall_mm
        future_corrosion = scenario.number("future_co2_corrosion_rate_mm_per_year")
        remaining_life_model_years = (
            available_wall_model_mm / future_corrosion if available_wall_model_mm > 0 else 0
        )
        remaining_life_barlow_years = (
            available_wall_barlow_mm / future_corrosion if available_wall_barlow_mm > 0 else 0
        )
        status = "pass_sanity" if scenario_min_wall_mm >= barlow_min_wall_mm else "review_required"

        rows.append(
            {
                "scenario": scenario_name,
                "module": "integrity",
                "validation_type": "barlow_sanity_check",
                "pipe_grade": pipe_grade,
                "smys_mpa": smys_mpa,
                "design_factor": design_factor,
                "pressure_mpa": _round(pressure_mpa, 6),
                "outer_diameter_mm": _round(outer_diameter_mm, 3),
                "scenario_min_wall_mm": _round(scenario_min_wall_mm, 6),
                "barlow_min_wall_mm": _round(barlow_min_wall_mm, 6),
                "difference_mm": _round(scenario_min_wall_mm - barlow_min_wall_mm, 6),
                "current_wall_mm": _round(current_wall_mm, 6),
                "available_wall_model_mm": _round(available_wall_model_mm, 6),
                "available_wall_barlow_mm": _round(available_wall_barlow_mm, 6),
                "remaining_life_model_years": _round(remaining_life_model_years, 3),
                "remaining_life_barlow_years": _round(remaining_life_barlow_years, 3),
                "status": status,
                "reference": "simple Barlow pressure sanity check",
                "notes": (
                    "Screening check only. It is not a full pipeline requalification "
                    "calculation and must be reviewed by a pipeline integrity specialist."
                ),
            }
        )

    return rows


def validate_cost_arithmetic(scenarios: dict[str, ScenarioAssumptions]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario_name, scenario in sorted(scenarios.items()):
        component_sum = sum(scenario.number(name) for name in COST_COMPONENT_PARAMETERS)
        contingency = component_sum * scenario.number("contingency_fraction")
        total = component_sum + contingency
        reported = scenario.optional_number("reported_total_capex_usd_2025")
        difference = total - reported if reported is not None else None
        status = (
            "pass"
            if reported is not None and abs(difference or 0) <= 1.0
            else "review_required"
        )
        rows.append(
            {
                "scenario": scenario_name,
                "module": "cost",
                "validation_type": "arithmetic_check",
                "component_sum_usd_2025": _round(component_sum, 2),
                "contingency_usd_2025": _round(contingency, 2),
                "calculated_total_usd_2025": _round(total, 2),
                "reported_total_usd_2025": _round(reported, 2),
                "difference_usd_2025": _round(difference, 2),
                "status": status,
                "reference": "student reported cost total",
                "notes": (
                    "This validates the arithmetic only. Independent cost-model validation "
                    "against NETL CO2_T_COM is still pending."
                ),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _status_counts(rows: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        counts[str(row.get("status", "unknown"))] = counts.get(str(row.get("status", "unknown")), 0) + 1
    return ", ".join(f"{status}: {count}" for status, count in sorted(counts.items()))


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def _fmt(value: Any, digits: int = 3) -> str:
    if value == "" or value is None:
        return ""
    if isinstance(value, (float, int)):
        return f"{value:,.{digits}f}"
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def write_validation_report(
    path: Path,
    *,
    property_rows: list[dict[str, Any]],
    capacity_rows: list[dict[str, Any]],
    integrity_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    property_summary = [
        [
            row["scenario"],
            row["parameter"],
            _fmt(row["model_value"]),
            _fmt(row["reference_value"]),
            _fmt(row["absolute_difference_percent"], 3),
            row["status"],
        ]
        for row in property_rows
        if row["parameter"] != "phase_state"
    ]

    capacity_summary = [
        [
            row["scenario"],
            row["validation_type"],
            _fmt(row["model_value"]),
            _fmt(row["reference_value"]),
            _fmt(row["difference_percent"], 3),
            row["status"],
        ]
        for row in capacity_rows
    ]

    integrity_summary = [
        [
            row["scenario"],
            _fmt(row.get("scenario_min_wall_mm")),
            _fmt(row.get("barlow_min_wall_mm")),
            _fmt(row.get("remaining_life_model_years")),
            _fmt(row.get("remaining_life_barlow_years")),
            row["status"],
        ]
        for row in integrity_rows
    ]

    cost_summary = [
        [
            row["scenario"],
            _fmt(row["calculated_total_usd_2025"], 0),
            _fmt(row["reported_total_usd_2025"], 0),
            _fmt(row["difference_usd_2025"], 0),
            row["status"],
        ]
        for row in cost_rows
    ]

    report = f"""# Independent Validation Report

Generated: {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

Model validation version: `{MODEL_VERSION}`

## Purpose

This report starts the full independent validation workflow.

It separates three things:

- reproduction of the student/dissertation outputs;
- independent checks against external references;
- engineering issues that need expert review.

## Plain Summary

| Area | Result |
| --- | --- |
| CO2 properties | `{_status_counts(property_rows)}` |
| Capacity | `{_status_counts(capacity_rows)}` |
| Integrity wall thickness | `{_status_counts(integrity_rows)}` |
| Cost arithmetic | `{_status_counts(cost_rows)}` |

Main finding:

> The Goldeneye CO2 property values are close to CoolProp, but the integrity minimum-wall-thickness basis needs review. A simple Barlow pressure sanity check gives a higher minimum wall thickness than the dissertation/poster values.

## CO2 Property Validation

Reference: CoolProp pure CO2 at the model average pipeline pressure and transport temperature.

Acceptance targets:

- density within 1%;
- viscosity within 3%;
- compressibility factor within 1%.

{_table(["Scenario", "Parameter", "Model", "CoolProp", "Abs diff %", "Status"], property_summary)}

Plain meaning:

The student/rebuilt CO2 property values are close enough for first-pass pure-CO2 screening. This does not yet validate impurity effects.

## Capacity Validation

{_table(["Scenario", "Check", "Model Mtpa", "Reference Mtpa", "Diff %", "Status"], capacity_summary)}

Plain meaning:

The arithmetic reproduces the equation. Replacing the student Z factor with CoolProp changes Goldeneye capacity by less than 1%, so property uncertainty is not the main issue for this case.

This still does not prove the selected capacity equation is the best engineering model. That needs comparison with external tools such as SCO2T or NETL where a like-for-like case can be built.

## Integrity Wall-Thickness Sanity Check

Reference: simple Barlow pressure check using X-grade SMYS and an assumed design factor of 0.72.

{_table(["Scenario", "Student min wall mm", "Barlow min wall mm", "Student life years", "Barlow life years", "Status"], integrity_summary)}

Plain meaning:

This is the biggest validation warning so far. The dissertation/poster minimum wall thickness is lower than the simple pressure sanity check. If the Barlow basis is appropriate, the remaining life becomes much shorter, especially for the poster case.

This does not mean the student is definitely wrong. It means we must verify:

- the exact pressure basis;
- whether outside diameter was used correctly;
- pipe grade and allowable stress;
- design factor;
- corrosion allowance;
- inspection and requalification rules.

Until this is resolved, integrity must remain `screening_unvalidated`.

## Cost Arithmetic Validation

{_table(["Scenario", "Calculated total USD", "Reported total USD", "Diff USD", "Status"], cost_summary)}

Plain meaning:

The cost arithmetic is internally consistent. This only checks the sum and contingency. It does not yet validate whether the cost model itself is appropriate.

Next independent cost validation should use NETL CO2_T_COM.

## Current Validation Status

| Module | Status | Meaning |
| --- | --- | --- |
| CO2 properties | first independent pass | Pure CO2 values pass against CoolProp for Goldeneye conditions. |
| Capacity | arithmetic pass, external model pending | Code equation is reproducible; external transport-model comparison still needed. |
| Integrity | review required | Minimum wall basis is not yet defensible. |
| Cost | arithmetic pass, external model pending | Arithmetic is correct; NETL cost validation still needed. |
| LCA | not started | Needs functional unit and ecoinvent mapping. |
| Wells | not started | Needs well data and integrity screening logic. |

## Output Files

- `data/validation/co2_property_validation.csv`
- `data/validation/capacity_validation.csv`
- `data/validation/integrity_barlow_sanity_check.csv`
- `data/validation/cost_arithmetic_validation.csv`

## Next Validation Actions

1. Resolve the Goldeneye minimum wall thickness formulation.
2. Build a like-for-like NETL CO2_T_COM cost case.
3. Build a like-for-like SCO2T or NETL transport capacity case.
4. Add the first LCA inventory skeleton after the pre-LCA gate.
"""
    path.write_text(report, encoding="utf-8")


def run_independent_validation(
    *,
    assumptions_path: Path,
    validation_dir: Path,
    report_path: Path,
) -> dict[str, list[dict[str, Any]]]:
    scenarios = read_scenario_assumptions(assumptions_path)
    property_rows = validate_co2_properties(scenarios)
    capacity_rows = validate_capacity(scenarios)
    integrity_rows = validate_integrity_barlow_sanity(scenarios)
    cost_rows = validate_cost_arithmetic(scenarios)

    write_csv(validation_dir / "co2_property_validation.csv", property_rows)
    write_csv(validation_dir / "capacity_validation.csv", capacity_rows)
    write_csv(validation_dir / "integrity_barlow_sanity_check.csv", integrity_rows)
    write_csv(validation_dir / "cost_arithmetic_validation.csv", cost_rows)
    write_validation_report(
        report_path,
        property_rows=property_rows,
        capacity_rows=capacity_rows,
        integrity_rows=integrity_rows,
        cost_rows=cost_rows,
    )

    return {
        "property": property_rows,
        "capacity": capacity_rows,
        "integrity": integrity_rows,
        "cost": cost_rows,
    }
