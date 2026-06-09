"""Run Goldeneye benchmark calculations for dissertation and poster scenarios.

Inputs:

- data/benchmarks/goldeneye_assumptions.csv

Outputs:

- data/benchmarks/goldeneye_benchmark_outputs.csv
- reports/goldeneye_benchmark.md

The goal is not to provide final engineering approval. The goal is to make the
Goldeneye assumptions explicit and reproduce the headline capacity, integrity,
and cost results before generalising the model to other pipelines.
"""

from __future__ import annotations

import csv
import datetime as dt
import math
from pathlib import Path
from typing import Any


SECONDS_PER_YEAR = 31_557_600
PSI_TO_PA = 6_894.757293168
INCH_TO_M = 0.0254
G_PER_MOL_TO_KG_PER_MOL = 0.001
UNIVERSAL_GAS_CONSTANT = 8.314462618


def read_assumptions(path: Path) -> dict[str, dict[str, dict[str, str]]]:
    scenarios: dict[str, dict[str, dict[str, str]]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            scenarios.setdefault(row["scenario"], {})[row["parameter"]] = row
    return scenarios


def value(scenario: dict[str, dict[str, str]], parameter: str) -> str:
    return scenario[parameter]["value"]


def number(scenario: dict[str, dict[str, str]], parameter: str) -> float:
    return float(value(scenario, parameter))


def optional_number(scenario: dict[str, dict[str, str]], parameter: str) -> float | None:
    if parameter not in scenario:
        return None
    raw = value(scenario, parameter).strip()
    if not raw:
        return None
    return float(raw)


def mtpa_to_kg_per_s(mtpa: float) -> float:
    return mtpa * 1e9 / SECONDS_PER_YEAR


def kg_per_s_to_mtpa(kg_per_s: float) -> float:
    return kg_per_s * SECONDS_PER_YEAR / 1e9


def average_pressure_pa(inlet_pa: float, outlet_pa: float) -> float:
    """Gas-pipeline average pressure used in McCoy/Rubin-style calculations."""
    return (2 / 3) * (inlet_pa + outlet_pa - (inlet_pa * outlet_pa / (inlet_pa + outlet_pa)))


def max_capacity_kg_per_s(
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
    """Steady-state dense-phase CO2 capacity using the dissertation equation form.

    This rearranged form reproduces the dissertation/poster Goldeneye outputs
    when using their reported Z, friction factor, pressure, temperature, length,
    and internal diameter assumptions.
    """
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


def reynolds_number(kg_per_s: float, viscosity_pa_s: float, inner_diameter_m: float) -> float:
    return 4 * kg_per_s / (math.pi * viscosity_pa_s * inner_diameter_m)


def cost_total(scenario: dict[str, dict[str, str]]) -> dict[str, float]:
    component_names = [
        "cost_material_usd_2025",
        "cost_labor_usd_2025",
        "cost_row_damages_usd_2025",
        "cost_misc_usd_2025",
        "cost_surge_tank_usd_2025",
        "cost_control_system_usd_2025",
        "cost_booster_station_usd_2025",
    ]
    subtotal = sum(number(scenario, name) for name in component_names)
    contingency = number(scenario, "contingency_fraction") * subtotal
    total = subtotal + contingency
    return {"subtotal": subtotal, "contingency": contingency, "total": total}


def benchmark_scenario(name: str, scenario: dict[str, dict[str, str]]) -> dict[str, Any]:
    length_m = number(scenario, "pipeline_length_km") * 1000
    inner_diameter_m = number(scenario, "inner_diameter_in") * INCH_TO_M
    inlet_pa = number(scenario, "inlet_pressure_psia") * PSI_TO_PA
    outlet_pa = number(scenario, "outlet_pressure_psia") * PSI_TO_PA
    temperature_k = number(scenario, "transport_temperature_c") + 273.15
    molecular_weight = number(scenario, "molecular_weight_co2_g_per_mol") * G_PER_MOL_TO_KG_PER_MOL
    viscosity_pa_s = number(scenario, "viscosity_micro_pa_s") * 1e-6

    capacity_kg_per_s = max_capacity_kg_per_s(
        inner_diameter_m=inner_diameter_m,
        length_m=length_m,
        inlet_pressure_pa=inlet_pa,
        outlet_pressure_pa=outlet_pa,
        temperature_k=temperature_k,
        compressibility_factor=number(scenario, "compressibility_factor_z"),
        molecular_weight_kg_per_mol=molecular_weight,
        fanning_friction_factor=number(scenario, "fanning_friction_factor"),
    )
    capacity_mtpa = kg_per_s_to_mtpa(capacity_kg_per_s)
    required_design_mtpa = number(scenario, "required_project_flow_mtpa") / number(scenario, "capacity_factor")
    average_pressure_mpa = average_pressure_pa(inlet_pa, outlet_pa) / 1e6

    historical_wall_loss = optional_number(scenario, "reported_historical_wall_loss_mm")
    if historical_wall_loss is None:
        historical_wall_loss = (
            number(scenario, "historical_corrosion_rate_mm_per_year")
            * number(scenario, "historical_corrosion_years")
        )

    current_wall_thickness = number(scenario, "nominal_wall_thickness_mm") - historical_wall_loss
    available_wall_thickness = current_wall_thickness - number(scenario, "minimum_wall_thickness_mm")
    remaining_life_years = (
        available_wall_thickness / number(scenario, "future_co2_corrosion_rate_mm_per_year")
        if available_wall_thickness > 0
        else 0
    )

    costs = cost_total(scenario)
    reported_capacity = number(scenario, "reported_capacity_mtpa")
    reported_life = number(scenario, "reported_remaining_life_years")
    reported_cost = number(scenario, "reported_total_capex_usd_2025")

    return {
        "scenario": name,
        "pipeline_name": value(scenario, "pipeline_name"),
        "length_km": number(scenario, "pipeline_length_km"),
        "inner_diameter_in": number(scenario, "inner_diameter_in"),
        "inner_diameter_m": inner_diameter_m,
        "nominal_wall_thickness_mm": number(scenario, "nominal_wall_thickness_mm"),
        "average_pressure_mpa": average_pressure_mpa,
        "capacity_kg_per_s": capacity_kg_per_s,
        "capacity_mtpa": capacity_mtpa,
        "reported_capacity_mtpa": reported_capacity,
        "capacity_delta_mtpa": capacity_mtpa - reported_capacity,
        "required_design_mtpa": required_design_mtpa,
        "capacity_suitable": "yes" if capacity_mtpa >= required_design_mtpa else "no",
        "reynolds_number": reynolds_number(capacity_kg_per_s, viscosity_pa_s, inner_diameter_m),
        "historical_wall_loss_mm": historical_wall_loss,
        "current_wall_thickness_mm": current_wall_thickness,
        "minimum_wall_thickness_mm": number(scenario, "minimum_wall_thickness_mm"),
        "available_wall_thickness_mm": available_wall_thickness,
        "future_co2_corrosion_rate_mm_per_year": number(
            scenario, "future_co2_corrosion_rate_mm_per_year"
        ),
        "remaining_life_years": remaining_life_years,
        "reported_remaining_life_years": reported_life,
        "remaining_life_delta_years": remaining_life_years - reported_life,
        "cost_subtotal_usd_2025": costs["subtotal"],
        "cost_contingency_usd_2025": costs["contingency"],
        "cost_total_usd_2025": costs["total"],
        "reported_total_capex_usd_2025": reported_cost,
        "cost_delta_usd_2025": costs["total"] - reported_cost,
    }


def write_outputs(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "scenario",
        "pipeline_name",
        "length_km",
        "inner_diameter_in",
        "inner_diameter_m",
        "nominal_wall_thickness_mm",
        "average_pressure_mpa",
        "capacity_kg_per_s",
        "capacity_mtpa",
        "reported_capacity_mtpa",
        "capacity_delta_mtpa",
        "required_design_mtpa",
        "capacity_suitable",
        "reynolds_number",
        "historical_wall_loss_mm",
        "current_wall_thickness_mm",
        "minimum_wall_thickness_mm",
        "available_wall_thickness_mm",
        "future_co2_corrosion_rate_mm_per_year",
        "remaining_life_years",
        "reported_remaining_life_years",
        "remaining_life_delta_years",
        "cost_subtotal_usd_2025",
        "cost_contingency_usd_2025",
        "cost_total_usd_2025",
        "reported_total_capex_usd_2025",
        "cost_delta_usd_2025",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def fmt(value: float, digits: int = 2) -> str:
    return f"{value:,.{digits}f}"


def usd(value: float) -> str:
    return f"${value:,.0f}"


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    summary_rows = []
    integrity_rows = []
    cost_rows = []
    for row in rows:
        summary_rows.append(
            [
                row["scenario"],
                fmt(row["inner_diameter_in"], 3),
                fmt(row["average_pressure_mpa"], 3),
                fmt(row["capacity_mtpa"], 3),
                fmt(row["reported_capacity_mtpa"], 3),
                row["capacity_suitable"],
            ]
        )
        integrity_rows.append(
            [
                row["scenario"],
                fmt(row["nominal_wall_thickness_mm"], 2),
                fmt(row["historical_wall_loss_mm"], 2),
                fmt(row["available_wall_thickness_mm"], 2),
                fmt(row["future_co2_corrosion_rate_mm_per_year"], 2),
                fmt(row["remaining_life_years"], 2),
                fmt(row["reported_remaining_life_years"], 2),
            ]
        )
        cost_rows.append(
            [
                row["scenario"],
                usd(row["cost_subtotal_usd_2025"]),
                usd(row["cost_contingency_usd_2025"]),
                usd(row["cost_total_usd_2025"]),
                usd(row["reported_total_capex_usd_2025"]),
            ]
        )

    report = f"""# Goldeneye Benchmark

Generated: {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

Assumptions: `data/benchmarks/goldeneye_assumptions.csv`

Script: `scripts/run_goldeneye_benchmark.py`

Outputs: `data/benchmarks/goldeneye_benchmark_outputs.csv`

## Purpose

This benchmark makes the Goldeneye assumptions explicit and reproducible before we generalise the model to other NSTA pipelines.

It compares two available versions:

- `goldeneye_dissertation`
- `goldeneye_poster`

The benchmark currently reproduces the headline capacity, remaining-life, and cost results using the values reported in the dissertation/poster. It is still a screening model, not an engineering approval model.

## Capacity Benchmark

{markdown_table(["Scenario", "ID in", "Average pressure MPa", "Calculated capacity Mtpa", "Reported capacity Mtpa", "Meets 5 Mtpa target?"], summary_rows)}

## Integrity / Lifetime Benchmark

{markdown_table(["Scenario", "Nominal wall mm", "Wall loss mm", "Available wall mm", "Future corrosion mm/yr", "Calculated life years", "Reported life years"], integrity_rows)}

## Cost Benchmark

{markdown_table(["Scenario", "Subtotal", "Contingency", "Calculated total", "Reported total"], cost_rows)}

## Interpretation

- The dissertation and poster use different Goldeneye wall-thickness assumptions.
- The dissertation case uses a thicker nominal wall (`22.23 mm`) and lower future CO2 corrosion rate (`0.10 mm/year`), which gives a much longer remaining life.
- The poster case uses a lower nominal wall (`14.28 mm`) and higher future CO2 corrosion rate (`0.20 mm/year`), which gives about `24.5 years`.
- The capacity difference is mainly caused by the internal diameter/friction assumptions: `18.25 in` in the dissertation case versus about `18.876 in` in the poster case.
- Cost is consistent between the two versions because both use the same Parker-style new-build cost breakdown.

## NETL Benchmark Plan

We should use NETL tools as external checks:

- REPACT: compare our Goldeneye transport capacity, pressure, and phase-screening behaviour.
- NETL CO2 Transport Cost Model / CO2_T_COM: compare our cost estimate and sensitivity to diameter, length, escalation, contingency, and booster stations.

The project should not depend on Excel workbooks as the core engine. The professional app should use transparent Python modules, with NETL outputs used as validation evidence.

## Next Technical Step

Turn this benchmark into tested Python modules:

- `properties`
- `hydraulics`
- `integrity`
- `cost`

Then add one validation test that checks the Goldeneye dissertation and poster cases stay reproducible.
"""
    path.write_text(report, encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    assumptions_path = root / "data" / "benchmarks" / "goldeneye_assumptions.csv"
    output_path = root / "data" / "benchmarks" / "goldeneye_benchmark_outputs.csv"
    report_path = root / "reports" / "goldeneye_benchmark.md"

    scenarios = read_assumptions(assumptions_path)
    outputs = [benchmark_scenario(name, scenario) for name, scenario in sorted(scenarios.items())]

    write_outputs(output_path, outputs)
    write_report(report_path, outputs)

    print(f"Read {len(scenarios)} Goldeneye scenarios")
    print(output_path)
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
