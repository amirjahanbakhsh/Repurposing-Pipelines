"""Run one pipeline screening scenario from a traceable assumptions file."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Any

from .assumptions import read_scenario_assumptions
from .goldeneye import benchmark_scenario_with_trace, write_outputs, write_trace


def safe_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    safe = safe.strip("_").lower()
    return safe or "pipeline_screen"


def available_scenarios(assumptions_path: Path) -> list[str]:
    return sorted(read_scenario_assumptions(assumptions_path).keys())


def _bullet_lines(text: str) -> str:
    items = [item.strip() for item in text.split(";") if item.strip()]
    if not items:
        return "- none recorded"
    return "\n".join(f"- {item}" for item in items)


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _path_text(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(path)


def write_single_pipeline_report(
    path: Path,
    *,
    row: dict[str, Any],
    assumptions_path: Path,
    output_csv_path: Path,
    trace_path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    report = f"""# Pipeline Screen: {row["scenario"]}

Generated: {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

Input assumptions: `{_path_text(assumptions_path)}`

Outputs:

- `{_path_text(output_csv_path)}`
- `{_path_text(trace_path)}`

## Plain Result

Pipeline: `{row["pipeline_name"]}`

Decision: `{row["pre_lca_decision"]}`

Confidence: `{row["pre_lca_confidence"]}`

Meaning: {row["pre_lca_reason_summary"]}

## Main Numbers

| Item | Value |
| --- | --- |
| CO2 capacity | {row["capacity_mtpa"]:.2f} MtCO2/year |
| Required design flow | {row["required_design_mtpa"]:.2f} MtCO2/year |
| Remaining life | {row["remaining_life_years"]:.2f} years |
| Available wall thickness | {row["available_wall_thickness_mm"]:.2f} mm |
| Benchmark avoided new-build CAPEX | {_money(row["cost_total_usd_2025"])} |

## Why This Decision?

{_bullet_lines(row["pre_lca_reasons"])}

## Next Data To Check

{_bullet_lines(row["pre_lca_next_data"])}

## Important Caveat

This is a screening result, not engineering approval. The decision is only as strong as the input assumptions.
"""
    path.write_text(report, encoding="utf-8")


def screen_one_pipeline(
    *,
    assumptions_path: Path,
    scenario_name: str,
    output_csv_path: Path,
    trace_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    scenarios = read_scenario_assumptions(assumptions_path)
    if scenario_name not in scenarios:
        available = ", ".join(sorted(scenarios))
        raise ValueError(f"Unknown scenario '{scenario_name}'. Available scenarios: {available}")

    row, trace = benchmark_scenario_with_trace(scenario_name, scenarios[scenario_name])
    write_outputs(output_csv_path, [row])
    write_trace(trace_path, [trace])
    write_single_pipeline_report(
        report_path,
        row=row,
        assumptions_path=assumptions_path,
        output_csv_path=output_csv_path,
        trace_path=trace_path,
    )
    return row
