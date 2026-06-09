"""Goldeneye benchmark orchestration and reporting."""

from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

from .assumptions import ScenarioAssumptions, read_scenario_assumptions
from .costs import evaluate_cost
from .gates import evaluate_pre_lca_gate
from .hydraulics import evaluate_capacity
from .integrity import evaluate_integrity
from .trace import ModuleResult, module_results_to_dicts


MODEL_VERSION = "goldeneye_benchmark_v0.3"

FIELDNAMES = [
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
    "pre_lca_decision",
    "pre_lca_confidence",
    "pre_lca_reason_summary",
    "pre_lca_reasons",
    "pre_lca_next_data",
]


def _outputs(*results: ModuleResult) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for result in results:
        merged.update(result.output_map())
    return merged


def benchmark_scenario_with_trace(
    name: str,
    scenario: ScenarioAssumptions,
) -> tuple[dict[str, Any], dict[str, Any]]:
    capacity = evaluate_capacity(scenario)
    integrity = evaluate_integrity(scenario)
    cost = evaluate_cost(scenario)
    pre_lca_gate = evaluate_pre_lca_gate(capacity=capacity, integrity=integrity, cost=cost)
    outputs = _outputs(capacity, integrity, cost, pre_lca_gate)

    row = {
        "scenario": name,
        "pipeline_name": scenario.raw("pipeline_name"),
        "length_km": scenario.number("pipeline_length_km"),
        "inner_diameter_in": scenario.number("inner_diameter_in"),
        "inner_diameter_m": outputs["inner_diameter_m"],
        "nominal_wall_thickness_mm": scenario.number("nominal_wall_thickness_mm"),
        "average_pressure_mpa": outputs["average_pressure_mpa"],
        "capacity_kg_per_s": outputs["capacity_kg_per_s"],
        "capacity_mtpa": outputs["capacity_mtpa"],
        "reported_capacity_mtpa": outputs["reported_capacity_mtpa"],
        "capacity_delta_mtpa": outputs["capacity_delta_mtpa"],
        "required_design_mtpa": outputs["required_design_mtpa"],
        "capacity_suitable": outputs["capacity_suitable"],
        "reynolds_number": outputs["reynolds_number"],
        "historical_wall_loss_mm": outputs["historical_wall_loss_mm"],
        "current_wall_thickness_mm": outputs["current_wall_thickness_mm"],
        "minimum_wall_thickness_mm": outputs["minimum_wall_thickness_mm"],
        "available_wall_thickness_mm": outputs["available_wall_thickness_mm"],
        "future_co2_corrosion_rate_mm_per_year": outputs[
            "future_co2_corrosion_rate_mm_per_year"
        ],
        "remaining_life_years": outputs["remaining_life_years"],
        "reported_remaining_life_years": outputs["reported_remaining_life_years"],
        "remaining_life_delta_years": outputs["remaining_life_delta_years"],
        "cost_subtotal_usd_2025": outputs["cost_subtotal_usd_2025"],
        "cost_contingency_usd_2025": outputs["cost_contingency_usd_2025"],
        "cost_total_usd_2025": outputs["cost_total_usd_2025"],
        "reported_total_capex_usd_2025": outputs["reported_total_capex_usd_2025"],
        "cost_delta_usd_2025": outputs["cost_delta_usd_2025"],
        "pre_lca_decision": outputs["pre_lca_decision"],
        "pre_lca_confidence": outputs["pre_lca_confidence"],
        "pre_lca_reason_summary": outputs["pre_lca_reason_summary"],
        "pre_lca_reasons": outputs["pre_lca_reasons"],
        "pre_lca_next_data": outputs["pre_lca_next_data"],
    }

    module_results = [capacity, integrity, cost, pre_lca_gate]
    trace = {
        "scenario": name,
        "pipeline_name": scenario.raw("pipeline_name"),
        "model_version": MODEL_VERSION,
        "source_parameters": scenario.to_dicts(),
        "module_results": module_results_to_dicts(module_results),
    }
    return row, trace


def benchmark_scenario(name: str, scenario: ScenarioAssumptions) -> dict[str, Any]:
    row, _ = benchmark_scenario_with_trace(name, scenario)
    return row


def run_benchmarks(assumptions_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scenarios = read_scenario_assumptions(assumptions_path)
    rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    for name, scenario in sorted(scenarios.items()):
        row, trace = benchmark_scenario_with_trace(name, scenario)
        rows.append(row)
        traces.append(trace)
    return rows, traces


def write_outputs(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def write_trace(path: Path, traces: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(traces, indent=2), encoding="utf-8")


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
    path.parent.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    integrity_rows = []
    cost_rows = []
    gate_rows = []
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
        gate_rows.append(
            [
                row["scenario"],
                row["pre_lca_decision"],
                row["pre_lca_confidence"],
                row["pre_lca_reason_summary"],
            ]
        )

    report = f"""# Goldeneye Benchmark

Generated: {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

Assumptions: `data/benchmarks/goldeneye_assumptions.csv`

Runner script: `scripts/run_goldeneye_benchmark.py`

Core modules: `repurposing_pipelines/`

Outputs:

- `data/benchmarks/goldeneye_benchmark_outputs.csv`
- `data/benchmarks/goldeneye_benchmark_trace.json`

## Purpose

This benchmark makes the Goldeneye assumptions explicit and reproducible before we generalise the model to other NSTA pipelines.

It compares two available versions:

- `goldeneye_dissertation`
- `goldeneye_poster`

The benchmark currently reproduces the headline capacity, remaining-life, and cost results using the values reported in the dissertation/poster. It is still a screening model, not an engineering approval model.

## How To Read This Report

- Capacity means how much CO2 the pipeline could carry each year.
- Integrity/lifetime means whether enough wall thickness remains for screening.
- Cost means the estimated avoided cost of building a new equivalent pipeline.
- Pre-LCA gate means the simple decision on whether the case is ready for LCA.
- Reported values are the values from the dissertation or poster.
- Calculated values are produced by our Python code.
- Small differences are expected because of rounding.

## Capacity Benchmark

{markdown_table(["Scenario", "ID in", "Average pressure MPa", "Calculated capacity Mtpa", "Reported capacity Mtpa", "Meets 5 Mtpa target?"], summary_rows)}

## Integrity / Lifetime Benchmark

{markdown_table(["Scenario", "Nominal wall mm", "Wall loss mm", "Available wall mm", "Future corrosion mm/yr", "Calculated life years", "Reported life years"], integrity_rows)}

## Cost Benchmark

{markdown_table(["Scenario", "Subtotal", "Contingency", "Calculated total", "Reported total"], cost_rows)}

## Pre-LCA Gate

{markdown_table(["Scenario", "Decision", "Confidence", "Meaning"], gate_rows)}

Plain meaning:

- `pass`: good enough to move into LCA screening.
- `marginal`: technically promising, but important assumptions still need checking.
- `fail`: do not move into LCA until the failed screen is fixed.
- `insufficient_data`: do not move into LCA because key data are missing.

## Interpretation

- The dissertation and poster use different Goldeneye wall-thickness assumptions.
- The dissertation case uses a thicker nominal wall (`22.23 mm`) and lower future CO2 corrosion rate (`0.10 mm/year`), which gives a much longer remaining life.
- The poster case uses a lower nominal wall (`14.28 mm`) and higher future CO2 corrosion rate (`0.20 mm/year`), which gives about `24.5 years`.
- The capacity difference is mainly caused by the internal diameter/friction assumptions: `18.25 in` in the dissertation case versus about `18.876 in` in the poster case.
- Cost is consistent between the two versions because both use the same Parker-style new-build cost breakdown.
- Both Goldeneye cases are currently `marginal`, because the calculations pass but key assumptions still need independent validation before detailed LCA.

## Traceability

Each scenario now has traceable module results for:

- capacity;
- integrity;
- cost;
- pre-LCA gate.

The JSON trace records the inputs, outputs, assumptions, warnings, and formula notes used by each module. This is the first building block for the future web app evidence panel.

## NETL Benchmark Plan

We should use NETL tools as external checks:

- REPACT: compare our Goldeneye transport capacity, pressure, and phase-screening behaviour.
- NETL CO2 Transport Cost Model / CO2_T_COM: compare our cost estimate and sensitivity to diameter, length, escalation, contingency, and booster stations.

The project should not depend on Excel workbooks as the core engine. The professional app should use transparent Python modules, with NETL outputs used as validation evidence.

## Next Technical Step

Add the first simple LCA screening module for reuse versus new-build pipeline emissions.
"""
    path.write_text(report, encoding="utf-8")


def run_from_paths(
    *,
    assumptions_path: Path,
    output_path: Path,
    trace_path: Path,
    report_path: Path,
) -> int:
    rows, traces = run_benchmarks(assumptions_path)
    write_outputs(output_path, rows)
    write_trace(trace_path, traces)
    write_report(report_path, rows)
    return len(rows)
