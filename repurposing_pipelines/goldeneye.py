"""Goldeneye benchmark orchestration and reporting."""

from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

from .assumptions import ScenarioAssumptions, read_scenario_assumptions
from .corrosion import evaluate_corrosion
from .costs import evaluate_cost
from .gates import evaluate_pre_lca_gate
from .hydraulics import evaluate_capacity
from .integrity import evaluate_integrity
from .lca import evaluate_lca_screening
from .repurposing_gate import evaluate_repurposing_gate
from .trace import ModuleResult, module_results_to_dicts


MODEL_VERSION = "goldeneye_benchmark_v0.5"

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
    "available_wall_low_mm",
    "available_wall_high_mm",
    "corrosion_risk_level",
    "future_co2_corrosion_rate_mm_per_year",
    "corrosion_rate_low_mm_per_year",
    "corrosion_rate_high_mm_per_year",
    "remaining_life_years",
    "remaining_life_low_years",
    "remaining_life_high_years",
    "remaining_life_range_width_years",
    "reported_remaining_life_years",
    "remaining_life_delta_years",
    "cost_subtotal_usd_2025",
    "cost_contingency_usd_2025",
    "cost_total_usd_2025",
    "reported_total_capex_usd_2025",
    "cost_delta_usd_2025",
    "netl_reference_total_capex_usd_2025",
    "netl_cost_delta_usd_2025",
    "netl_cost_delta_percent",
    "netl_cost_validation_status",
    "repurposing_gate_status",
    "repurposing_gate_confidence",
    "repurposing_gate_reason_summary",
    "repurposing_gate_reasons",
    "repurposing_gate_next_data",
    "repurposing_phase_status",
    "repurposing_evidence_score",
    "repurposing_evidence_gaps",
    "repurposing_showstoppers",
    "repurposing_work_scope_items",
    "repurposing_lca_work_scope_items",
    "lca_refurbishment_steel_fraction_recommended",
    "repurposing_gate_cited_references",
    "pre_lca_decision",
    "pre_lca_confidence",
    "pre_lca_reason_summary",
    "pre_lca_reasons",
    "pre_lca_next_data",
    "lca_steel_mass_new_build_kg",
    "lca_refurbishment_steel_kg",
    "lca_refurbishment_steel_fraction_used",
    "lca_gate_work_scope_items",
    "lca_avoided_steel_kg",
    "lca_new_build_proxy_kgco2e",
    "lca_reuse_proxy_kgco2e",
    "lca_proxy_saving_kgco2e",
    "lca_proxy_saving_percent",
    "lca_screening_decision",
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
    corrosion = evaluate_corrosion(scenario)
    integrity = evaluate_integrity(scenario, corrosion=corrosion)
    cost = evaluate_cost(scenario)
    repurposing_gate = evaluate_repurposing_gate(
        scenario,
        capacity=capacity,
        corrosion=corrosion,
        integrity=integrity,
    )
    pre_lca_gate = evaluate_pre_lca_gate(
        capacity=capacity,
        integrity=integrity,
        cost=cost,
        repurposing=repurposing_gate,
    )
    lca = evaluate_lca_screening(
        scenario,
        pre_lca_decision=pre_lca_gate.output_map()["pre_lca_decision"],
        repurposing_gate=repurposing_gate,
    )
    outputs = _outputs(capacity, corrosion, integrity, cost, repurposing_gate, pre_lca_gate, lca)

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
        "available_wall_low_mm": outputs["available_wall_low_mm"],
        "available_wall_high_mm": outputs["available_wall_high_mm"],
        "corrosion_risk_level": outputs["corrosion_risk_level"],
        "future_co2_corrosion_rate_mm_per_year": outputs[
            "future_co2_corrosion_rate_mm_per_year"
        ],
        "corrosion_rate_low_mm_per_year": outputs["corrosion_rate_low_mm_per_year"],
        "corrosion_rate_high_mm_per_year": outputs["corrosion_rate_high_mm_per_year"],
        "remaining_life_years": outputs["remaining_life_years"],
        "remaining_life_low_years": outputs["remaining_life_low_years"],
        "remaining_life_high_years": outputs["remaining_life_high_years"],
        "remaining_life_range_width_years": outputs["remaining_life_range_width_years"],
        "reported_remaining_life_years": outputs["reported_remaining_life_years"],
        "remaining_life_delta_years": outputs["remaining_life_delta_years"],
        "cost_subtotal_usd_2025": outputs["cost_subtotal_usd_2025"],
        "cost_contingency_usd_2025": outputs["cost_contingency_usd_2025"],
        "cost_total_usd_2025": outputs["cost_total_usd_2025"],
        "reported_total_capex_usd_2025": outputs["reported_total_capex_usd_2025"],
        "cost_delta_usd_2025": outputs["cost_delta_usd_2025"],
        "netl_reference_total_capex_usd_2025": outputs[
            "netl_reference_total_capex_usd_2025"
        ],
        "netl_cost_delta_usd_2025": outputs["netl_cost_delta_usd_2025"],
        "netl_cost_delta_percent": outputs["netl_cost_delta_percent"],
        "netl_cost_validation_status": outputs["netl_cost_validation_status"],
        "repurposing_gate_status": outputs["repurposing_gate_status"],
        "repurposing_gate_confidence": outputs["repurposing_gate_confidence"],
        "repurposing_gate_reason_summary": outputs["repurposing_gate_reason_summary"],
        "repurposing_gate_reasons": outputs["repurposing_gate_reasons"],
        "repurposing_gate_next_data": outputs["repurposing_gate_next_data"],
        "repurposing_phase_status": outputs["repurposing_phase_status"],
        "repurposing_evidence_score": outputs["repurposing_evidence_score"],
        "repurposing_evidence_gaps": outputs["repurposing_evidence_gaps"],
        "repurposing_showstoppers": outputs["repurposing_showstoppers"],
        "repurposing_work_scope_items": outputs["repurposing_work_scope_items"],
        "repurposing_lca_work_scope_items": outputs["repurposing_lca_work_scope_items"],
        "lca_refurbishment_steel_fraction_recommended": outputs[
            "lca_refurbishment_steel_fraction_recommended"
        ],
        "repurposing_gate_cited_references": outputs["repurposing_gate_cited_references"],
        "pre_lca_decision": outputs["pre_lca_decision"],
        "pre_lca_confidence": outputs["pre_lca_confidence"],
        "pre_lca_reason_summary": outputs["pre_lca_reason_summary"],
        "pre_lca_reasons": outputs["pre_lca_reasons"],
        "pre_lca_next_data": outputs["pre_lca_next_data"],
        "lca_steel_mass_new_build_kg": outputs["lca_steel_mass_new_build_kg"],
        "lca_refurbishment_steel_kg": outputs["lca_refurbishment_steel_kg"],
        "lca_refurbishment_steel_fraction_used": outputs[
            "lca_refurbishment_steel_fraction_used"
        ],
        "lca_gate_work_scope_items": outputs["lca_gate_work_scope_items"],
        "lca_avoided_steel_kg": outputs["lca_avoided_steel_kg"],
        "lca_new_build_proxy_kgco2e": outputs["lca_new_build_proxy_kgco2e"],
        "lca_reuse_proxy_kgco2e": outputs["lca_reuse_proxy_kgco2e"],
        "lca_proxy_saving_kgco2e": outputs["lca_proxy_saving_kgco2e"],
        "lca_proxy_saving_percent": outputs["lca_proxy_saving_percent"],
        "lca_screening_decision": outputs["lca_screening_decision"],
    }

    module_results = [capacity, corrosion, integrity, cost, repurposing_gate, pre_lca_gate, lca]
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
    repurposing_rows = []
    lca_rows = []
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
                row["corrosion_risk_level"],
                fmt(row["corrosion_rate_low_mm_per_year"], 3),
                fmt(row["future_co2_corrosion_rate_mm_per_year"], 3),
                fmt(row["corrosion_rate_high_mm_per_year"], 3),
                fmt(row["remaining_life_low_years"], 2),
                fmt(row["remaining_life_years"], 2),
                fmt(row["remaining_life_high_years"], 2),
            ]
        )
        cost_rows.append(
            [
                row["scenario"],
                usd(row["cost_subtotal_usd_2025"]),
                usd(row["cost_contingency_usd_2025"]),
                usd(row["cost_total_usd_2025"]),
                usd(row["reported_total_capex_usd_2025"]),
                row["netl_cost_validation_status"],
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
        repurposing_rows.append(
            [
                row["scenario"],
                row["repurposing_gate_status"],
                row["repurposing_gate_confidence"],
                fmt(row["repurposing_evidence_score"], 1),
                row["repurposing_phase_status"],
                row["repurposing_gate_reason_summary"],
            ]
        )
        lca_rows.append(
            [
                row["scenario"],
                fmt(row["lca_steel_mass_new_build_kg"] / 1000, 0),
                fmt(row["lca_refurbishment_steel_kg"] / 1000, 0),
                fmt(row["lca_refurbishment_steel_fraction_used"] * 100, 1),
                fmt(row["lca_new_build_proxy_kgco2e"] / 1000, 0),
                fmt(row["lca_reuse_proxy_kgco2e"] / 1000, 0),
                fmt(row["lca_proxy_saving_percent"], 1),
                row["lca_screening_decision"],
            ]
        )

    report = f"""# Goldeneye Benchmark

Generated: {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

Assumptions: `model_layers/06_screening_and_decision/goldeneye_assumptions.csv`

Runner script: `scripts/run_goldeneye_benchmark.py`

Core modules: `repurposing_pipelines/`

Outputs:

- `model_layers/06_screening_and_decision/goldeneye_benchmark_outputs.csv`
- `model_layers/06_screening_and_decision/goldeneye_benchmark_trace.json`

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

{markdown_table(["Scenario", "Nominal wall mm", "Wall loss mm", "Available wall mm", "Corrosion risk", "Low corr.", "Base corr.", "High corr.", "Conservative life", "Base life", "Optimistic life"], integrity_rows)}

## Cost Benchmark

{markdown_table(["Scenario", "Subtotal", "Contingency", "Calculated total", "Reported total", "NETL status"], cost_rows)}

## Repurposing Gate

{markdown_table(["Scenario", "Gate", "Confidence", "Evidence score", "CO2 phase screen", "Meaning"], repurposing_rows)}

Plain meaning:

This gate checks whether the case has enough evidence for repurposing, not only whether the capacity and lifetime calculations run. It follows the DNV-style requalification themes recorded in the project literature register.

## LCA Screening Proxy

{markdown_table(["Scenario", "New steel t", "Refurb steel t", "Refurb steel % used", "New-build proxy tCO2e", "Reuse proxy tCO2e", "Saving %", "LCA screen"], lca_rows)}

Plain meaning:

This is the first calculated LCA-style screening result. It is useful for ranking and sensitivity, but it is not yet a final ecoinvent/Brightway result.

## Pre-LCA Gate

{markdown_table(["Scenario", "Decision", "Confidence", "Meaning"], gate_rows)}

Plain meaning:

- `pass`: good enough to move into LCA screening.
- `marginal`: technically promising, but important assumptions still need checking.
- `fail`: do not move into LCA until the failed screen is fixed.
- `insufficient_data`: do not move into LCA because key data are missing.

## Interpretation

- The dissertation and poster use different Goldeneye wall-thickness assumptions.
- The dissertation case uses a thicker nominal wall (`22.23 mm`) and lower future CO2 corrosion rate (`0.10 mm/year`), which gives a much longer base remaining life.
- The poster case uses a lower nominal wall (`14.28 mm`) and higher future CO2 corrosion rate (`0.20 mm/year`), which gives about `24.5 years` in the base case.
- The uncertainty range is now reported separately because the Goldeneye wall basis is not cleanly resolved.
- The capacity difference is mainly caused by the internal diameter/friction assumptions: `18.25 in` in the dissertation case versus about `18.876 in` in the poster case.
- Cost is consistent between the two versions because both use the same Parker-style new-build cost breakdown.
- Both Goldeneye cases are currently `marginal`, because the calculations pass but key assumptions still need independent validation before detailed LCA.

## Traceability

Each scenario now has traceable module results for:

- capacity;
- corrosion;
- integrity;
- cost;
- pre-LCA gate.
- LCA screening proxy.

The JSON trace records the inputs, outputs, assumptions, warnings, and formula notes used by each module. This is the first building block for the future web app evidence panel.

## NETL Benchmark Plan

We should use NETL tools as external checks:

- REPACT: compare our Goldeneye transport capacity, pressure, and phase-screening behaviour.
- NETL CO2 Transport Cost Model / CO2_T_COM: compare our cost estimate and sensitivity to diameter, length, escalation, contingency, and booster stations.

The project should not depend on Excel workbooks as the core engine. The professional app should use transparent Python modules, with NETL outputs used as validation evidence.

## Next Technical Step

Run the batch screening command for all model-ready NSTA pipelines, then prioritise the top candidates for data enrichment.
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
