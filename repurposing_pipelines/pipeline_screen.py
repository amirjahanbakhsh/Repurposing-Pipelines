"""Run one pipeline screening scenario from a traceable assumptions file."""

from __future__ import annotations

import csv
import datetime as dt
import re
from pathlib import Path
from typing import Any

from .assumptions import AssumptionValue, ScenarioAssumptions, read_scenario_assumptions
from .constants import BAR_TO_PSI
from .goldeneye import benchmark_scenario_with_trace, write_trace


def safe_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    safe = safe.strip("_").lower()
    return safe or "pipeline_screen"


def available_scenarios(assumptions_path: Path) -> list[str]:
    return sorted(read_scenario_assumptions(assumptions_path).keys())


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_defaults(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["parameter"]: row for row in csv.DictReader(handle)}


def available_nsta_candidates(candidates_path: Path, limit: int = 10) -> list[dict[str, str]]:
    return read_csv_rows(candidates_path)[:limit]


def write_pipeline_outputs(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)


def _bullet_lines(text: str) -> str:
    items = [item.strip() for item in text.split(";") if item.strip()]
    if not items:
        return "- none recorded"
    return "\n".join(f"- {item}" for item in items)


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _markdown_cell(value: Any) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").replace("|", "/")
    return " ".join(text.split())


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_markdown_cell(item) for item in row) + " |")
    return "\n".join(lines)


def _to_float(value: Any) -> float:
    return float(str(value).strip())


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return _to_float(value)
    except (TypeError, ValueError):
        return default


def _year_from_date(value: str) -> int | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        return int(cleaned[:4])
    except ValueError:
        return None


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

Input mode: `{row.get("input_mode", "scenario")}`

NSTA pipeline number: `{row.get("nsta_pipeline_number", "not applicable")}`

Decision: `{row["pre_lca_decision"]}`

Confidence: `{row["pre_lca_confidence"]}`

Meaning: {row["pre_lca_reason_summary"]}

## Main Numbers

| Item | Value |
| --- | --- |
| CO2 capacity | {row["capacity_mtpa"]:.2f} MtCO2/year |
| Required design flow | {row["required_design_mtpa"]:.2f} MtCO2/year |
| Remaining life | {row["remaining_life_years"]:.2f} years |
| Remaining life range | {row["remaining_life_low_years"]:.2f} to {row["remaining_life_high_years"]:.2f} years |
| Available wall thickness | {row["available_wall_thickness_mm"]:.2f} mm |
| Corrosion risk | {row["corrosion_risk_level"]} |
| Benchmark avoided new-build CAPEX | {_money(row["cost_total_usd_2025"])} |
| NETL cost check | {row["netl_cost_validation_status"]} |
| LCA proxy saving | {row["lca_proxy_saving_percent"]:.1f}% |
| LCA screen | {row["lca_screening_decision"]} |

## Why This Decision?

{_bullet_lines(row["pre_lca_reasons"])}

## Next Data To Check

{_bullet_lines(row["pre_lca_next_data"])}

## Important Caveat

This is a screening result, not engineering approval. The decision is only as strong as the input assumptions.
"""
    path.write_text(report, encoding="utf-8")


def _record(
    *,
    scenario: str,
    parameter: str,
    value: Any,
    unit: str,
    source: str,
    quality: str,
    notes: str,
) -> AssumptionValue:
    return AssumptionValue(
        scenario=scenario,
        parameter=parameter,
        value=str(value),
        unit=unit,
        source=source,
        quality=quality,
        notes=notes,
    )


def _default_record(scenario_name: str, defaults: dict[str, dict[str, str]], parameter: str) -> AssumptionValue:
    row = defaults[parameter]
    return _record(
        scenario=scenario_name,
        parameter=parameter,
        value=row["value"],
        unit=row["unit"],
        source=row["source"],
        quality=row["quality"],
        notes=row["notes"],
    )


def _default_number(defaults: dict[str, dict[str, str]], parameter: str) -> float:
    return float(defaults[parameter]["value"])


def _cost_record(
    *,
    scenario_name: str,
    defaults: dict[str, dict[str, str]],
    parameter: str,
    scale_factor: float,
) -> AssumptionValue:
    row = defaults[parameter]
    return _record(
        scenario=scenario_name,
        parameter=parameter,
        value=float(row["value"]) * scale_factor,
        unit=row["unit"],
        source="scaled_from_goldeneye_benchmark",
        quality="estimated",
        notes=(
            f"{row['notes']}; scaled by NSTA length/reference length only "
            f"(scale factor {scale_factor:.3f})"
        ),
    )


def find_nsta_candidate(
    candidates: list[dict[str, str]],
    *,
    nsta_id: str | None = None,
    rank: int | None = None,
    name: str | None = None,
) -> dict[str, str]:
    if nsta_id:
        wanted = nsta_id.strip().upper()
        for row in candidates:
            if row.get("NSTAPIPNO", "").strip().upper() == wanted:
                return row
        raise ValueError(f"NSTA pipeline number '{nsta_id}' was not found in the ranked candidates.")

    if rank is not None:
        for row in candidates:
            if int(float(row.get("RANK", "0") or 0)) == rank:
                return row
        raise ValueError(f"NSTA rank '{rank}' was not found in the ranked candidates.")

    if name:
        wanted = name.strip().upper()
        matches = [row for row in candidates if wanted in row.get("PIPE_NAME", "").upper()]
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise ValueError(f"No NSTA candidate name contains '{name}'.")
        examples = ", ".join(f"{row.get('NSTAPIPNO')}: {row.get('PIPE_NAME')}" for row in matches[:5])
        raise ValueError(f"More than one NSTA candidate matched '{name}'. Please use --nsta-id. Examples: {examples}")

    raise ValueError("Choose an NSTA pipeline using --nsta-id, --nsta-rank, or --nsta-name.")


def build_nsta_scenario(
    *,
    nsta_row: dict[str, str],
    defaults: dict[str, dict[str, str]],
) -> ScenarioAssumptions:
    nsta_id = nsta_row["NSTAPIPNO"].strip()
    scenario_name = f"nsta_{safe_filename(nsta_id)}"
    records: dict[str, AssumptionValue] = {}

    length_km = _to_float(nsta_row["LENGTH_KM"])
    inner_diameter_mm = _to_float(nsta_row["INT_DIAM"])
    wall_thickness_mm = _to_float(nsta_row["THICKNESS"])
    pressure_barg = _to_float(nsta_row["MX_OP_PRES"])
    if length_km <= 0:
        raise ValueError(
            f"NSTA pipeline {nsta_id} cannot be screened because length is zero or missing."
        )
    outer_diameter_mm = inner_diameter_mm + 2 * wall_thickness_mm
    inlet_pressure_psia = (pressure_barg + 1.01325) * BAR_TO_PSI
    default_outlet_psia = _default_number(defaults, "outlet_pressure_psia")
    outlet_pressure_psia = min(default_outlet_psia, inlet_pressure_psia * 0.8)

    start_year = _year_from_date(nsta_row.get("START_DATE", ""))
    assessment_year = int(_default_number(defaults, "assessment_year"))
    historical_years = (
        max(0, assessment_year - start_year)
        if start_year is not None
        else _default_number(defaults, "fallback_historical_corrosion_years")
    )

    smys_mpa = _default_number(defaults, "smys_mpa")
    design_factor = _default_number(defaults, "design_factor")
    pressure_mpa = (pressure_barg + 1.01325) * 0.1
    minimum_wall_mm = pressure_mpa * outer_diameter_mm / (2 * smys_mpa * design_factor)

    reference_length_km = _default_number(defaults, "reference_cost_length_km")
    scale_factor = length_km / reference_length_km

    nsta_source = "NSTA ranked candidate dataset"
    records["pipeline_name"] = _record(
        scenario=scenario_name,
        parameter="pipeline_name",
        value=nsta_row["PIPE_NAME"],
        unit="text",
        source=nsta_source,
        quality="reported",
        notes=f"NSTA pipeline number {nsta_id}; rank {nsta_row.get('RANK', '')}",
    )
    records["pipeline_length_km"] = _record(
        scenario=scenario_name,
        parameter="pipeline_length_km",
        value=length_km,
        unit="km",
        source=nsta_source,
        quality="reported",
        notes="NSTA LENGTH_M converted to km in the ranked candidate file",
    )
    records["outer_diameter_in"] = _record(
        scenario=scenario_name,
        parameter="outer_diameter_in",
        value=outer_diameter_mm / 25.4,
        unit="in",
        source=nsta_source,
        quality="derived",
        notes="Estimated as internal diameter plus two times wall thickness",
    )
    records["inner_diameter_in"] = _record(
        scenario=scenario_name,
        parameter="inner_diameter_in",
        value=inner_diameter_mm / 25.4,
        unit="in",
        source=nsta_source,
        quality="derived",
        notes="NSTA internal diameter converted from mm to inches",
    )
    records["nominal_wall_thickness_mm"] = _record(
        scenario=scenario_name,
        parameter="nominal_wall_thickness_mm",
        value=wall_thickness_mm,
        unit="mm",
        source=nsta_source,
        quality="reported",
        notes="NSTA wall thickness",
    )
    records["inlet_pressure_psia"] = _record(
        scenario=scenario_name,
        parameter="inlet_pressure_psia",
        value=inlet_pressure_psia,
        unit="psia",
        source=nsta_source,
        quality="derived",
        notes="NSTA max operating pressure in barg converted to approximate psia",
    )
    records["outlet_pressure_psia"] = _record(
        scenario=scenario_name,
        parameter="outlet_pressure_psia",
        value=outlet_pressure_psia,
        unit="psia",
        source="screening_default",
        quality="assumed",
        notes="Default outlet pressure; clipped to 80 percent of inlet if needed",
    )
    records["historical_corrosion_years"] = _record(
        scenario=scenario_name,
        parameter="historical_corrosion_years",
        value=historical_years,
        unit="years",
        source=nsta_source if start_year is not None else "screening_default",
        quality="derived" if start_year is not None else "assumed",
        notes="Assessment year minus NSTA start year, or fallback if start date is missing",
    )
    records["minimum_wall_thickness_mm"] = _record(
        scenario=scenario_name,
        parameter="minimum_wall_thickness_mm",
        value=minimum_wall_mm,
        unit="mm",
        source="simple_barlow_screening",
        quality="derived",
        notes="Approximate t = P * OD / (2 * SMYS * design factor); screening only",
    )

    if start_year is not None:
        records["start_operation_year"] = _record(
            scenario=scenario_name,
            parameter="start_operation_year",
            value=start_year,
            unit="year",
            source=nsta_source,
            quality="reported",
            notes="Year parsed from NSTA start date",
        )

    for parameter in [
        "transport_temperature_c",
        "capacity_factor",
        "required_project_flow_mtpa",
        "molecular_weight_co2_g_per_mol",
        "compressibility_factor_z",
        "density_kg_per_m3",
        "viscosity_micro_pa_s",
        "fanning_friction_factor",
        "pipe_grade",
        "historical_corrosion_rate_mm_per_year",
        "future_co2_corrosion_rate_mm_per_year",
        "future_co2_corrosion_rate_low_mm_per_year",
        "future_co2_corrosion_rate_high_mm_per_year",
        "nominal_wall_thickness_uncertainty_fraction",
        "minimum_wall_thickness_uncertainty_fraction",
        "historical_wall_loss_uncertainty_fraction",
        "co2_water_content_ppmv",
        "co2_water_spec_limit_ppmv",
        "water_dew_point_margin_c",
        "steel_density_kg_per_m3",
        "lca_refurbishment_steel_fraction",
        "lca_pipeline_steel_factor_kgco2e_per_kg",
        "lca_new_build_construction_factor_kgco2e_per_km",
        "lca_refurbishment_activity_factor_kgco2e_per_km",
        "contingency_fraction",
    ]:
        records[parameter] = _default_record(scenario_name, defaults, parameter)

    for parameter in [
        "cost_material_usd_2025",
        "cost_labor_usd_2025",
        "cost_row_damages_usd_2025",
        "cost_misc_usd_2025",
        "cost_surge_tank_usd_2025",
        "cost_control_system_usd_2025",
        "cost_booster_station_usd_2025",
    ]:
        records[parameter] = _cost_record(
            scenario_name=scenario_name,
            defaults=defaults,
            parameter=parameter,
            scale_factor=scale_factor,
        )

    return ScenarioAssumptions(name=scenario_name, records=records)


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
    row["input_mode"] = "scenario_assumptions"
    row["nsta_pipeline_number"] = "not applicable"
    write_pipeline_outputs(output_csv_path, row)
    write_trace(trace_path, [trace])
    write_single_pipeline_report(
        report_path,
        row=row,
        assumptions_path=assumptions_path,
        output_csv_path=output_csv_path,
        trace_path=trace_path,
    )
    return row


def _status_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, "unknown"))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _counts_table(counts: dict[str, int]) -> str:
    if not counts:
        return "| Value | Count |\n| --- | --- |\n"
    lines = ["| Value | Count |", "| --- | --- |"]
    for key, value in sorted(counts.items()):
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def _screening_sort_key(row: dict[str, Any]) -> tuple[int, float, float, float]:
    decision_rank = {"pass": 3, "marginal": 2, "fail": 1, "insufficient_data": 0}
    return (
        decision_rank.get(str(row.get("pre_lca_decision")), 0),
        float(row.get("capacity_mtpa") or 0),
        float(row.get("remaining_life_low_years") or 0),
        float(row.get("lca_proxy_saving_percent") or 0),
    )


def _row_length_km(row: dict[str, Any]) -> float:
    return _safe_float(row.get("length_km", 0))


def _row_rank(row: dict[str, Any]) -> float:
    return _safe_float(row.get("nsta_rank", 999999), 999999)


def _dedupe_longest_by_nsta_id(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("nsta_pipeline_number") or row.get("scenario") or "")
        existing = selected.get(key)
        if existing is None or _row_length_km(row) > _row_length_km(existing):
            selected[key] = row
    return list(selected.values())


def write_batch_screening_report(
    path: Path,
    *,
    rows: list[dict[str, Any]],
    candidates_path: Path,
    defaults_path: Path,
    output_csv_path: Path,
    trace_path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    strategic_rows = [row for row in rows if _row_length_km(row) >= 1]
    strategic_unique_rows = _dedupe_longest_by_nsta_id(strategic_rows)
    sorted_rows = sorted(strategic_unique_rows, key=_row_rank)
    top_rows = []
    for row in sorted_rows[:30]:
        top_rows.append(
            [
                row.get("nsta_rank", ""),
                row.get("nsta_pipeline_number", ""),
                row.get("pipeline_name", ""),
                row.get("nsta_fluid", ""),
                row.get("nsta_status", ""),
                f"{float(row.get('length_km') or 0):.1f}",
                row.get("pre_lca_decision", ""),
                f"{float(row.get('capacity_mtpa') or 0):.2f}",
                f"{float(row.get('remaining_life_low_years') or 0):.1f}",
                f"{float(row.get('remaining_life_years') or 0):.1f}",
                f"{float(row.get('remaining_life_high_years') or 0):.1f}",
                row.get("corrosion_risk_level", ""),
                f"{float(row.get('lca_proxy_saving_percent') or 0):.1f}",
            ]
        )

    report = f"""# NSTA Pipeline Batch Screening

Generated: {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

Candidate file: `{_path_text(candidates_path)}`

Default assumptions: `{_path_text(defaults_path)}`

Outputs:

- `{_path_text(output_csv_path)}`
- `{_path_text(trace_path)}`

## Plain Result

This report screens all model-ready NSTA hydrocarbon pipeline candidates in one run.

This is the right first use of the tool: screen many pipelines, rank them, then inspect one pipeline in detail.

The full CSV keeps all screened records, including short connecting segments. The table below focuses on strategic pipelines at least 1 km long and keeps the longest record for each NSTA pipeline number.

Wall thickness is treated as uncertain for every pipeline, not only Goldeneye. Goldeneye simply uses a wider uncertainty band because its source data are less clear.

## Candidate Count

Screened pipelines: `{len(rows)}`

Strategic screened records at least 1 km long: `{len(strategic_rows)}`

Unique strategic NSTA pipeline numbers after keeping the longest record per number: `{len(strategic_unique_rows)}`

## Pre-LCA Decisions

{_counts_table(_status_counts(rows, "pre_lca_decision"))}

## Pre-LCA Decisions For Unique Strategic Pipelines

{_counts_table(_status_counts(strategic_unique_rows, "pre_lca_decision"))}

## Corrosion Risk

{_counts_table(_status_counts(rows, "corrosion_risk_level"))}

## Top 30 Strategic Screened Pipelines

{markdown_table(["NSTA rank", "NSTA no.", "Pipeline", "Fluid", "Status", "Length km", "Decision", "Capacity Mtpa", "Life low", "Life base", "Life high", "Corr. risk", "LCA saving %"], top_rows)}

## How To Use This

1. Start with the top table.
2. Pick a pipeline number such as `PL774`.
3. Run the single-pipeline command for a detailed report:

```powershell
python scripts\\run_pipeline_screen.py --nsta-id PL774
```

## Important Caveat

This is still screening. The strongest candidates are not approved pipelines. They are candidates for data enrichment, technical validation, NETL cost comparison, and proper LCA.
"""
    path.write_text(report, encoding="utf-8")


def screen_all_nsta_pipelines(
    *,
    candidates_path: Path,
    defaults_path: Path,
    output_csv_path: Path,
    trace_path: Path,
    report_path: Path,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    candidates = read_csv_rows(candidates_path)
    if limit is not None:
        candidates = candidates[:limit]
    defaults = read_defaults(defaults_path)
    rows: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    for nsta_row in candidates:
        scenario_name = f"nsta_{safe_filename(nsta_row.get('NSTAPIPNO', 'unknown'))}"
        try:
            scenario = build_nsta_scenario(nsta_row=nsta_row, defaults=defaults)
            row, trace = benchmark_scenario_with_trace(scenario.name, scenario)
            row["screening_error"] = ""
        except ValueError as exc:
            row = {
                "scenario": scenario_name,
                "pipeline_name": nsta_row.get("PIPE_NAME", ""),
                "length_km": _safe_float(nsta_row.get("LENGTH_KM", 0) or 0),
                "input_mode": "nsta_batch_candidate_plus_defaults",
                "nsta_pipeline_number": nsta_row.get("NSTAPIPNO", ""),
                "nsta_rank": nsta_row.get("RANK", ""),
                "nsta_fluid": nsta_row.get("FLUID", ""),
                "nsta_status": nsta_row.get("STATUS", ""),
                "capacity_mtpa": 0,
                "remaining_life_low_years": 0,
                "remaining_life_years": 0,
                "remaining_life_high_years": 0,
                "corrosion_risk_level": "not_assessed",
                "lca_proxy_saving_percent": 0,
                "pre_lca_decision": "insufficient_data",
                "pre_lca_confidence": "low",
                "pre_lca_reason_summary": str(exc),
                "screening_error": str(exc),
            }
            trace = {
                "scenario": scenario_name,
                "pipeline_name": nsta_row.get("PIPE_NAME", ""),
                "model_version": "pipeline_screen_nsta_batch_v0.1",
                "nsta_candidate": nsta_row,
                "defaults_path": _path_text(defaults_path),
                "screening_error": str(exc),
            }
        row["input_mode"] = "nsta_batch_candidate_plus_defaults"
        row["nsta_pipeline_number"] = nsta_row.get("NSTAPIPNO", "")
        row["nsta_rank"] = nsta_row.get("RANK", "")
        row["nsta_fluid"] = nsta_row.get("FLUID", "")
        row["nsta_status"] = nsta_row.get("STATUS", "")
        trace["model_version"] = "pipeline_screen_nsta_batch_v0.1"
        trace["nsta_candidate"] = nsta_row
        trace["defaults_path"] = _path_text(defaults_path)
        rows.append(row)
        traces.append(trace)

    if rows:
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames: list[str] = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        with output_csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    write_trace(trace_path, traces)
    write_batch_screening_report(
        report_path,
        rows=rows,
        candidates_path=candidates_path,
        defaults_path=defaults_path,
        output_csv_path=output_csv_path,
        trace_path=trace_path,
    )
    return rows


def screen_nsta_pipeline(
    *,
    candidates_path: Path,
    defaults_path: Path,
    output_csv_path: Path,
    trace_path: Path,
    report_path: Path,
    nsta_id: str | None = None,
    rank: int | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    candidates = read_csv_rows(candidates_path)
    nsta_row = find_nsta_candidate(candidates, nsta_id=nsta_id, rank=rank, name=name)
    defaults = read_defaults(defaults_path)
    scenario = build_nsta_scenario(nsta_row=nsta_row, defaults=defaults)
    row, trace = benchmark_scenario_with_trace(scenario.name, scenario)

    row["input_mode"] = "nsta_candidate_plus_defaults"
    row["nsta_pipeline_number"] = nsta_row.get("NSTAPIPNO", "")
    row["nsta_rank"] = nsta_row.get("RANK", "")
    row["nsta_fluid"] = nsta_row.get("FLUID", "")
    row["nsta_status"] = nsta_row.get("STATUS", "")
    trace["model_version"] = "pipeline_screen_nsta_v0.1"
    trace["nsta_candidate"] = nsta_row
    trace["defaults_path"] = _path_text(defaults_path)

    write_pipeline_outputs(output_csv_path, row)
    write_trace(trace_path, [trace])
    write_single_pipeline_report(
        report_path,
        row=row,
        assumptions_path=defaults_path,
        output_csv_path=output_csv_path,
        trace_path=trace_path,
    )
    return row
