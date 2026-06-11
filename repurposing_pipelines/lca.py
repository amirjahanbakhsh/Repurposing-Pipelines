"""Screening-level LCA inventory and proxy impact calculations."""

from __future__ import annotations

import csv
import datetime as dt
import json
import math
from pathlib import Path
from typing import Any

from .assumptions import ScenarioAssumptions
from .constants import INCH_TO_M
from .trace import ModuleResult, OutputRecord, TraceStep, WarningRecord


MODEL_VERSION = "lca_screening_proxy_v0.1"
ECOINVENT_MODEL_VERSION = "ecoinvent_factor_lca_v0.1"


def _optional_number(
    scenario: ScenarioAssumptions,
    parameter: str,
    default: float,
) -> float:
    value = scenario.optional_number(parameter)
    return default if value is None else value


def pipeline_steel_mass_kg(
    *,
    length_km: float,
    outer_diameter_in: float,
    inner_diameter_in: float,
    steel_density_kg_per_m3: float,
) -> float:
    outer_diameter_m = outer_diameter_in * INCH_TO_M
    inner_diameter_m = inner_diameter_in * INCH_TO_M
    steel_area_m2 = math.pi * (outer_diameter_m**2 - inner_diameter_m**2) / 4
    return steel_area_m2 * length_km * 1000 * steel_density_kg_per_m3


def pipeline_steel_mass_from_wall_kg(
    *,
    length_km: float,
    inner_diameter_in: float,
    wall_thickness_mm: float,
    steel_density_kg_per_m3: float,
) -> float:
    wall_thickness_m = wall_thickness_mm / 1000
    inner_diameter_m = inner_diameter_in * INCH_TO_M
    outer_diameter_m = inner_diameter_m + 2 * wall_thickness_m
    steel_area_m2 = math.pi * (outer_diameter_m**2 - inner_diameter_m**2) / 4
    return steel_area_m2 * length_km * 1000 * steel_density_kg_per_m3


def read_process_mapping(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["mapping_key"]: row for row in csv.DictReader(handle)}


def read_impact_factors(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    factors: dict[str, dict[str, Any]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            raw_factor = row.get("impact_factor_kgco2e_per_unit", "").strip()
            if not raw_factor:
                continue
            key = row["mapping_key"]
            factors[key] = {
                **row,
                "impact_factor_kgco2e_per_unit": float(raw_factor),
            }
    return factors


def _mapping_value(
    process_mapping: dict[str, dict[str, str]],
    mapping_key: str,
    column: str,
) -> str:
    return process_mapping.get(mapping_key, {}).get(column, "")


def _inventory_row(
    *,
    scenario: str,
    alternative: str,
    inventory_item: str,
    mapping_key: str,
    quantity_low: float,
    quantity_base: float,
    quantity_high: float,
    unit: str,
    include_in_total: bool,
    data_quality: str,
    process_mapping: dict[str, dict[str, str]],
    notes: str,
) -> dict[str, Any]:
    return {
        "scenario": scenario,
        "alternative": alternative,
        "inventory_item": inventory_item,
        "mapping_key": mapping_key,
        "quantity_low": quantity_low,
        "quantity_base": quantity_base,
        "quantity_high": quantity_high,
        "unit": unit,
        "include_in_total": "yes" if include_in_total else "no",
        "data_quality": data_quality,
        "ecoinvent_activity_name": _mapping_value(process_mapping, mapping_key, "activity_name"),
        "ecoinvent_location": _mapping_value(process_mapping, mapping_key, "location"),
        "ecoinvent_reference_product": _mapping_value(
            process_mapping,
            mapping_key,
            "reference_product",
        ),
        "notes": notes,
    }


def build_pipeline_lca_inventory(
    scenario: ScenarioAssumptions,
    *,
    process_mapping: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    length_km = scenario.number("pipeline_length_km")
    inner_diameter_in = scenario.number("inner_diameter_in")
    wall_thickness_mm = scenario.number("nominal_wall_thickness_mm")
    steel_density = _optional_number(scenario, "steel_density_kg_per_m3", 7850.0)
    wall_uncertainty = _optional_number(
        scenario,
        "nominal_wall_thickness_uncertainty_fraction",
        0.0,
    )
    refurbishment_fraction = _optional_number(
        scenario,
        "lca_refurbishment_steel_fraction",
        0.05,
    )

    wall_low = max(0.0, wall_thickness_mm * (1 - wall_uncertainty))
    wall_high = wall_thickness_mm * (1 + wall_uncertainty)
    new_steel_low = pipeline_steel_mass_from_wall_kg(
        length_km=length_km,
        inner_diameter_in=inner_diameter_in,
        wall_thickness_mm=wall_low,
        steel_density_kg_per_m3=steel_density,
    )
    new_steel_base = pipeline_steel_mass_from_wall_kg(
        length_km=length_km,
        inner_diameter_in=inner_diameter_in,
        wall_thickness_mm=wall_thickness_mm,
        steel_density_kg_per_m3=steel_density,
    )
    new_steel_high = pipeline_steel_mass_from_wall_kg(
        length_km=length_km,
        inner_diameter_in=inner_diameter_in,
        wall_thickness_mm=wall_high,
        steel_density_kg_per_m3=steel_density,
    )
    refurb_steel_low = new_steel_low * refurbishment_fraction
    refurb_steel_base = new_steel_base * refurbishment_fraction
    refurb_steel_high = new_steel_high * refurbishment_fraction

    return [
        _inventory_row(
            scenario=scenario.name,
            alternative="new_build",
            inventory_item="pipeline_steel_mass",
            mapping_key="pipeline_steel",
            quantity_low=new_steel_low,
            quantity_base=new_steel_base,
            quantity_high=new_steel_high,
            unit="kg",
            include_in_total=True,
            data_quality="conditional_wall_thickness",
            process_mapping=process_mapping,
            notes="Steel mass for a new equivalent pipeline; wall-thickness uncertainty is included.",
        ),
        _inventory_row(
            scenario=scenario.name,
            alternative="new_build",
            inventory_item="offshore_pipeline_construction",
            mapping_key="offshore_pipeline_construction",
            quantity_low=length_km,
            quantity_base=length_km,
            quantity_high=length_km,
            unit="km",
            include_in_total=True,
            data_quality="screening_estimate",
            process_mapping=process_mapping,
            notes="New offshore pipeline construction activity.",
        ),
        _inventory_row(
            scenario=scenario.name,
            alternative="reuse",
            inventory_item="refurbishment_steel",
            mapping_key="pipeline_steel",
            quantity_low=refurb_steel_low,
            quantity_base=refurb_steel_base,
            quantity_high=refurb_steel_high,
            unit="kg",
            include_in_total=True,
            data_quality="assumed_fraction",
            process_mapping=process_mapping,
            notes="Assumed replacement/refurbishment steel before reuse.",
        ),
        _inventory_row(
            scenario=scenario.name,
            alternative="reuse",
            inventory_item="pipeline_refurbishment_activity",
            mapping_key="refurbishment_activity",
            quantity_low=length_km,
            quantity_base=length_km,
            quantity_high=length_km,
            unit="km",
            include_in_total=True,
            data_quality="needs_private_lca_factor",
            process_mapping=process_mapping,
            notes="Inspection, cleaning, repair, and recommissioning package per km.",
        ),
        _inventory_row(
            scenario=scenario.name,
            alternative="reuse",
            inventory_item="decommissioned_pipeline",
            mapping_key="decommissioned_pipeline",
            quantity_low=0,
            quantity_base=0,
            quantity_high=0,
            unit="kg",
            include_in_total=False,
            data_quality="scenario_choice",
            process_mapping=process_mapping,
            notes="Not included by default; use for decommissioning or end-of-life sensitivity.",
        ),
        _inventory_row(
            scenario=scenario.name,
            alternative="operation",
            inventory_item="electricity_operation",
            mapping_key="electricity",
            quantity_low=0,
            quantity_base=0,
            quantity_high=0,
            unit="kWh",
            include_in_total=False,
            data_quality="not_implemented",
            process_mapping=process_mapping,
            notes="Operational electricity is not yet linked to compression or pumping calculations.",
        ),
    ]


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1"}


def calculate_ecoinvent_impacts(
    inventory_rows: list[dict[str, Any]],
    impact_factors: dict[str, dict[str, Any]],
    *,
    pre_lca_decision: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    detailed_rows: list[dict[str, Any]] = []
    totals = {
        "new_build": {"low": 0.0, "base": 0.0, "high": 0.0},
        "reuse": {"low": 0.0, "base": 0.0, "high": 0.0},
    }
    missing_keys: list[str] = []
    included_count = 0

    for row in inventory_rows:
        include = _as_bool(row["include_in_total"]) and float(row["quantity_base"]) != 0
        factor_row = impact_factors.get(row["mapping_key"])
        factor = (
            factor_row.get("impact_factor_kgco2e_per_unit")
            if factor_row is not None
            else None
        )
        factor_status = "not_required"
        impacts = {"low": 0.0, "base": 0.0, "high": 0.0}
        if include:
            if factor is None:
                factor_status = "missing"
                if row["mapping_key"] not in missing_keys:
                    missing_keys.append(row["mapping_key"])
            else:
                factor_status = "available"
                included_count += 1
                impacts = {
                    "low": float(row["quantity_low"]) * float(factor),
                    "base": float(row["quantity_base"]) * float(factor),
                    "high": float(row["quantity_high"]) * float(factor),
                }
                alternative = row["alternative"]
                if alternative in totals:
                    for key in ["low", "base", "high"]:
                        totals[alternative][key] += impacts[key]

        detailed_rows.append(
            {
                **row,
                "impact_method": (
                    factor_row.get("impact_method", "") if factor_row is not None else ""
                ),
                "impact_category": (
                    factor_row.get("impact_category", "") if factor_row is not None else ""
                ),
                "impact_factor_kgco2e_per_unit": "" if factor is None else factor,
                "impact_factor_status": factor_status,
                "impact_low_kgco2e": impacts["low"],
                "impact_base_kgco2e": impacts["base"],
                "impact_high_kgco2e": impacts["high"],
            }
        )

    saving_base = totals["new_build"]["base"] - totals["reuse"]["base"]
    saving_low = totals["new_build"]["low"] - totals["reuse"]["high"]
    saving_high = totals["new_build"]["high"] - totals["reuse"]["low"]
    saving_percent = (
        100 * saving_base / totals["new_build"]["base"]
        if totals["new_build"]["base"] > 0
        else 0
    )
    if missing_keys:
        status = "blocked_missing_impact_factors"
    elif pre_lca_decision in {"fail", "insufficient_data"}:
        status = "sensitivity_only"
    else:
        status = "conditional_result"

    summary = {
        "lca_model_version": ECOINVENT_MODEL_VERSION,
        "lca_status": status,
        "pre_lca_decision": pre_lca_decision,
        "new_build_kgco2e_low": totals["new_build"]["low"],
        "new_build_kgco2e_base": totals["new_build"]["base"],
        "new_build_kgco2e_high": totals["new_build"]["high"],
        "reuse_kgco2e_low": totals["reuse"]["low"],
        "reuse_kgco2e_base": totals["reuse"]["base"],
        "reuse_kgco2e_high": totals["reuse"]["high"],
        "saving_kgco2e_low": saving_low,
        "saving_kgco2e_base": saving_base,
        "saving_kgco2e_high": saving_high,
        "saving_percent_base": saving_percent,
        "included_factor_count": included_count,
        "missing_factor_count": len(missing_keys),
        "missing_mapping_keys": "; ".join(missing_keys),
    }
    return detailed_rows, summary


def impact_factor_template_rows(
    process_mapping: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    rows = []
    for key, mapping in process_mapping.items():
        if key in {"not_applicable", "to_be_mapped"}:
            continue
        rows.append(
            {
                "mapping_key": key,
                "impact_method": "IPCC 2021 GWP100",
                "impact_category": "climate change",
                "activity_name": mapping.get("activity_name", ""),
                "location": mapping.get("location", ""),
                "reference_product": mapping.get("reference_product", ""),
                "unit": mapping.get("unit", ""),
                "impact_factor_kgco2e_per_unit": "",
                "source": "private ecoinvent/openLCA/Brightway result",
                "quality": "to_be_filled",
                "notes": "Do not commit private licensed impact factors to GitHub.",
            }
        )
    return rows


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
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


def write_lca_trace(
    path: Path,
    *,
    scenario_name: str,
    inventory_rows: list[dict[str, Any]],
    impact_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "scenario": scenario_name,
        "model_version": ECOINVENT_MODEL_VERSION,
        "summary": summary,
        "inventory_rows": inventory_rows,
        "impact_rows": impact_rows,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _path_text(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(path)


def _fmt(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item).replace("|", "/") for item in row) + " |")
    return "\n".join(lines)


def write_ecoinvent_lca_report(
    path: Path,
    *,
    scenario_name: str,
    inventory_path: Path,
    impact_path: Path,
    results_path: Path,
    trace_path: Path,
    factor_path: Path,
    summary: dict[str, Any],
    impact_rows: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    required_rows = [
        [
            row["alternative"],
            row["inventory_item"],
            row["mapping_key"],
            _fmt(row["quantity_base"], 2),
            row["unit"],
            row["impact_factor_status"],
        ]
        for row in impact_rows
        if _as_bool(row["include_in_total"]) and float(row["quantity_base"]) != 0
    ]
    report = f"""# Ecoinvent-Based Conditional LCA: {scenario_name}

Generated: {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

## Plain Result

Status: `{summary["lca_status"]}`

This is an ecoinvent-linked conditional LCA workflow. It needs private ecoinvent-derived impact factors before final kg CO2e results can be trusted.

## Main Numbers

| Item | Value |
| --- | --- |
| Pre-LCA decision | {summary["pre_lca_decision"]} |
| New-build base impact | {_fmt(summary["new_build_kgco2e_base"] / 1000, 2)} tCO2e |
| Reuse base impact | {_fmt(summary["reuse_kgco2e_base"] / 1000, 2)} tCO2e |
| Base saving | {_fmt(summary["saving_kgco2e_base"] / 1000, 2)} tCO2e |
| Base saving percent | {_fmt(summary["saving_percent_base"], 1)}% |
| Missing factor keys | {summary["missing_mapping_keys"] or "none"} |

## Required Inventory Rows

{_markdown_table(["Alternative", "Inventory item", "Mapping key", "Base quantity", "Unit", "Factor status"], required_rows)}

## Output Files

- `{_path_text(inventory_path)}`
- `{_path_text(impact_path)}`
- `{_path_text(results_path)}`
- `{_path_text(trace_path)}`

## Private Factor File

Expected private factor file:

```text
{_path_text(factor_path)}
```

This file should contain ecoinvent/openLCA/Brightway-derived impact factors and should not be committed to GitHub.

## Important Caveat

The result is conditional until wall thickness is validated and all required private impact factors are supplied.
"""
    path.write_text(report, encoding="utf-8")


def evaluate_lca_screening(
    scenario: ScenarioAssumptions,
    *,
    pre_lca_decision: str,
    repurposing_gate: ModuleResult | None = None,
) -> ModuleResult:
    """Calculate a first open LCA screening proxy.

    This deliberately does not claim to be a full ecoinvent result. It gives a
    reproducible first environmental indicator while the licensed LCA workflow
    is being prepared.
    """
    length_km = scenario.number("pipeline_length_km")
    steel_density = _optional_number(scenario, "steel_density_kg_per_m3", 7850.0)
    refurbishment_fraction = _optional_number(
        scenario,
        "lca_refurbishment_steel_fraction",
        0.05,
    )
    gate_refurbishment_fraction = None
    gate_work_scope = ""
    if repurposing_gate is not None:
        gate_outputs = repurposing_gate.output_map()
        gate_refurbishment_fraction = gate_outputs.get(
            "lca_refurbishment_steel_fraction_recommended"
        )
        gate_work_scope = str(gate_outputs.get("repurposing_lca_work_scope_items") or "")
        if gate_refurbishment_fraction is not None:
            refurbishment_fraction = max(
                refurbishment_fraction,
                float(gate_refurbishment_fraction),
            )
    steel_factor = _optional_number(
        scenario,
        "lca_pipeline_steel_factor_kgco2e_per_kg",
        2.0,
    )
    new_build_construction_factor = _optional_number(
        scenario,
        "lca_new_build_construction_factor_kgco2e_per_km",
        100000.0,
    )
    refurbishment_activity_factor = _optional_number(
        scenario,
        "lca_refurbishment_activity_factor_kgco2e_per_km",
        20000.0,
    )

    new_build_steel = pipeline_steel_mass_kg(
        length_km=length_km,
        outer_diameter_in=scenario.number("outer_diameter_in"),
        inner_diameter_in=scenario.number("inner_diameter_in"),
        steel_density_kg_per_m3=steel_density,
    )
    refurbishment_steel = new_build_steel * refurbishment_fraction
    avoided_steel = new_build_steel - refurbishment_steel
    new_build_proxy = (
        new_build_steel * steel_factor
        + length_km * new_build_construction_factor
    )
    reuse_proxy = (
        refurbishment_steel * steel_factor
        + length_km * refurbishment_activity_factor
    )
    saving = new_build_proxy - reuse_proxy
    saving_percent = 100 * saving / new_build_proxy if new_build_proxy > 0 else 0

    if pre_lca_decision in {"fail", "insufficient_data"}:
        status = "sensitivity_only"
        decision = "needs_data"
    elif saving > 0:
        status = "pass"
        decision = "favour_reuse"
    else:
        status = "review_required"
        decision = "inconclusive"

    input_names = [
        "pipeline_length_km",
        "outer_diameter_in",
        "inner_diameter_in",
    ]
    for optional_name in [
        "steel_density_kg_per_m3",
        "lca_refurbishment_steel_fraction",
        "lca_pipeline_steel_factor_kgco2e_per_kg",
        "lca_new_build_construction_factor_kgco2e_per_km",
        "lca_refurbishment_activity_factor_kgco2e_per_km",
    ]:
        if optional_name in scenario.records:
            input_names.append(optional_name)

    assumptions = [
        scenario.assumption_record(name, sensitivity_required=True)
        for name in [
            "lca_refurbishment_steel_fraction",
            "lca_pipeline_steel_factor_kgco2e_per_kg",
            "lca_new_build_construction_factor_kgco2e_per_km",
            "lca_refurbishment_activity_factor_kgco2e_per_km",
        ]
        if name in scenario.records
    ]

    warnings = [
        WarningRecord(
            level="medium",
            message=(
                "LCA result is a screening proxy only. It uses open factors from "
                "the assumption file, not final ecoinvent impact results."
            ),
            affected_modules=["lca", "final_gate"],
        )
    ]
    if status == "sensitivity_only":
        warnings.append(
            WarningRecord(
                level="high",
                message="Pre-LCA gate did not pass, so LCA must be read as sensitivity only.",
                affected_modules=["lca", "pre_lca_gate"],
            )
        )

    return ModuleResult(
        module="lca",
        model_version=MODEL_VERSION,
        status=status,
        inputs=scenario.input_records(input_names, used_by=["lca"]),
        assumptions=assumptions,
        outputs=[
            OutputRecord("lca_steel_mass_new_build_kg", new_build_steel, "kg", used_by=["lca"]),
            OutputRecord("lca_refurbishment_steel_kg", refurbishment_steel, "kg", used_by=["lca"]),
            OutputRecord(
                "lca_refurbishment_steel_fraction_used",
                refurbishment_fraction,
                "fraction",
                quality="screening_placeholder",
                used_by=["lca", "report"],
                notes="Uses the larger of the scenario value and repurposing-gate recommendation.",
            ),
            OutputRecord(
                "lca_gate_work_scope_items",
                gate_work_scope,
                "text",
                used_by=["lca", "report"],
            ),
            OutputRecord("lca_avoided_steel_kg", avoided_steel, "kg", used_by=["lca"]),
            OutputRecord(
                "lca_new_build_proxy_kgco2e",
                new_build_proxy,
                "kg CO2e",
                quality="screening_proxy",
                used_by=["final_gate"],
            ),
            OutputRecord(
                "lca_reuse_proxy_kgco2e",
                reuse_proxy,
                "kg CO2e",
                quality="screening_proxy",
                used_by=["final_gate"],
            ),
            OutputRecord(
                "lca_proxy_saving_kgco2e",
                saving,
                "kg CO2e",
                quality="screening_proxy",
                used_by=["final_gate"],
            ),
            OutputRecord(
                "lca_proxy_saving_percent",
                saving_percent,
                "%",
                quality="screening_proxy",
                used_by=["final_gate", "report", "app"],
            ),
            OutputRecord(
                "lca_screening_decision",
                decision,
                "decision",
                used_by=["final_gate", "report", "app"],
            ),
        ],
        warnings=warnings,
        trace=[
            TraceStep(
                name="pipeline_steel_mass",
                formula="pi * (OD^2 - ID^2) / 4 * length * steel_density",
                inputs=[
                    "outer_diameter_in",
                    "inner_diameter_in",
                    "pipeline_length_km",
                    "steel_density_kg_per_m3",
                ],
                result_name="lca_steel_mass_new_build_kg",
            ),
            TraceStep(
                name="lca_proxy",
                formula=(
                    "new-build proxy = steel mass * steel factor + length * construction factor; "
                    "reuse proxy = refurbishment steel * steel factor + length * refurbishment factor"
                ),
                inputs=[
                    "lca_refurbishment_steel_fraction",
                    "lca_refurbishment_steel_fraction_recommended",
                    "lca_pipeline_steel_factor_kgco2e_per_kg",
                    "lca_new_build_construction_factor_kgco2e_per_km",
                    "lca_refurbishment_activity_factor_kgco2e_per_km",
                ],
                result_name="lca_proxy_saving_kgco2e",
                notes=(
                    "Screening proxy to be replaced by Brightway/openLCA ecoinvent calculation. "
                    "The refurbishment fraction may be increased by the repurposing gate when "
                    "evidence gaps suggest additional validation or replacement work."
                ),
            ),
        ],
    )
