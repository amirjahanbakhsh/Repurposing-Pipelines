"""Apply private unit-cost factors to refurbishment work-scope rows.

The work-scope table provides quantities. This module multiplies those
quantities by unit-cost factors when they are available. Public repository
files keep the template and blocked reports; private/commercial rates belong
in the ignored private CSV.
"""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
from typing import Any


MODEL_VERSION = "refurbishment_unit_cost_v0.2"

UNIT_COST_TEMPLATE_ROWS = [
    {
        "cost_driver": "engineering_study_each",
        "unit": "study",
        "unit_cost_low_usd_2025": "",
        "unit_cost_base_usd_2025": "",
        "unit_cost_high_usd_2025": "",
        "source": "private project estimate or literature benchmark",
        "quality": "to_be_filled",
        "notes": "Used for CO2 composition, impurity and water/dew-point studies.",
    },
    {
        "cost_driver": "cleaning_drying_per_km",
        "unit": "km",
        "unit_cost_low_usd_2025": "",
        "unit_cost_base_usd_2025": "",
        "unit_cost_high_usd_2025": "",
        "source": "private project estimate or contractor benchmark",
        "quality": "to_be_filled",
        "notes": "Pipeline cleaning, drying and debris assessment per km.",
    },
    {
        "cost_driver": "inspection_per_km",
        "unit": "km",
        "unit_cost_low_usd_2025": "",
        "unit_cost_base_usd_2025": "",
        "unit_cost_high_usd_2025": "",
        "source": "private project estimate or ILI benchmark",
        "quality": "to_be_filled",
        "notes": "ILI/MFL or equivalent inspection campaign per km.",
    },
    {
        "cost_driver": "material_testing_campaign",
        "unit": "campaign",
        "unit_cost_low_usd_2025": "",
        "unit_cost_base_usd_2025": "",
        "unit_cost_high_usd_2025": "",
        "source": "private project estimate or testing benchmark",
        "quality": "to_be_filled",
        "notes": "Material certificates, sampling, testing and verification campaign.",
    },
    {
        "cost_driver": "compatibility_review_each",
        "unit": "review",
        "unit_cost_low_usd_2025": "",
        "unit_cost_base_usd_2025": "",
        "unit_cost_high_usd_2025": "",
        "source": "private project estimate or engineering benchmark",
        "quality": "to_be_filled",
        "notes": "Valve, seal, coating and equipment compatibility review.",
    },
    {
        "cost_driver": "fracture_decompression_study_each",
        "unit": "study",
        "unit_cost_low_usd_2025": "",
        "unit_cost_base_usd_2025": "",
        "unit_cost_high_usd_2025": "",
        "source": "private project estimate or engineering benchmark",
        "quality": "to_be_filled",
        "notes": "Dense-phase fracture, decompression and blowdown study.",
    },
    {
        "cost_driver": "wall_thickness_verification_per_km",
        "unit": "km",
        "unit_cost_low_usd_2025": "",
        "unit_cost_base_usd_2025": "",
        "unit_cost_high_usd_2025": "",
        "source": "private project estimate or inspection benchmark",
        "quality": "to_be_filled",
        "notes": "Targeted wall-thickness validation per km.",
    },
    {
        "cost_driver": "imr_plan_each",
        "unit": "plan",
        "unit_cost_low_usd_2025": "",
        "unit_cost_base_usd_2025": "",
        "unit_cost_high_usd_2025": "",
        "source": "private project estimate or operations benchmark",
        "quality": "to_be_filled",
        "notes": "CO2 leak detection, isolation and IMR plan.",
    },
    {
        "cost_driver": "replacement_steel_kg",
        "unit": "kg",
        "unit_cost_low_usd_2025": "",
        "unit_cost_base_usd_2025": "",
        "unit_cost_high_usd_2025": "",
        "source": "private project estimate, supplier quote, or cost index",
        "quality": "to_be_filled",
        "notes": "Replacement or refurbishment steel allowance per kg.",
    },
    {
        "cost_driver": "unmapped_work_item",
        "unit": "item",
        "unit_cost_low_usd_2025": "",
        "unit_cost_base_usd_2025": "",
        "unit_cost_high_usd_2025": "",
        "source": "private project estimate",
        "quality": "to_be_filled",
        "notes": "Fallback for future work-scope items not yet mapped to a specific cost driver.",
    },
]

SCREENING_UNIT_COST_ROWS = [
    {
        "cost_driver": "engineering_study_each",
        "unit": "study",
        "unit_cost_low_usd_2025": "100000",
        "unit_cost_base_usd_2025": "250000",
        "unit_cost_high_usd_2025": "500000",
        "source": "screening estimate from engineering work-package judgement; replace with project quote",
        "quality": "screening_default_unvalidated",
        "notes": "Used for early CO2 composition, impurity and water/dew-point studies.",
    },
    {
        "cost_driver": "cleaning_drying_per_km",
        "unit": "km",
        "unit_cost_low_usd_2025": "25000",
        "unit_cost_base_usd_2025": "75000",
        "unit_cost_high_usd_2025": "150000",
        "source": "screening estimate for offshore cleaning/drying activity; replace with contractor estimate",
        "quality": "screening_default_unvalidated",
        "notes": "Pipeline cleaning, drying and debris assessment per km.",
    },
    {
        "cost_driver": "inspection_per_km",
        "unit": "km",
        "unit_cost_low_usd_2025": "10000",
        "unit_cost_base_usd_2025": "25000",
        "unit_cost_high_usd_2025": "60000",
        "source": "screening estimate for ILI/MFL or equivalent inspection; replace with ILI quote",
        "quality": "screening_default_unvalidated",
        "notes": "Inspection campaign per km.",
    },
    {
        "cost_driver": "material_testing_campaign",
        "unit": "campaign",
        "unit_cost_low_usd_2025": "100000",
        "unit_cost_base_usd_2025": "300000",
        "unit_cost_high_usd_2025": "750000",
        "source": "screening estimate for material verification campaign; replace with laboratory/project estimate",
        "quality": "screening_default_unvalidated",
        "notes": "Material certificates, sampling, testing and verification campaign.",
    },
    {
        "cost_driver": "compatibility_review_each",
        "unit": "review",
        "unit_cost_low_usd_2025": "50000",
        "unit_cost_base_usd_2025": "150000",
        "unit_cost_high_usd_2025": "300000",
        "source": "screening estimate for component compatibility engineering review",
        "quality": "screening_default_unvalidated",
        "notes": "Valve, seal, coating and equipment compatibility review.",
    },
    {
        "cost_driver": "fracture_decompression_study_each",
        "unit": "study",
        "unit_cost_low_usd_2025": "150000",
        "unit_cost_base_usd_2025": "350000",
        "unit_cost_high_usd_2025": "800000",
        "source": "screening estimate for dense-phase fracture/decompression engineering study",
        "quality": "screening_default_unvalidated",
        "notes": "Dense-phase fracture, decompression and blowdown study.",
    },
    {
        "cost_driver": "wall_thickness_verification_per_km",
        "unit": "km",
        "unit_cost_low_usd_2025": "5000",
        "unit_cost_base_usd_2025": "15000",
        "unit_cost_high_usd_2025": "35000",
        "source": "screening estimate for targeted wall-thickness validation",
        "quality": "screening_default_unvalidated",
        "notes": "Targeted wall-thickness verification per km.",
    },
    {
        "cost_driver": "imr_plan_each",
        "unit": "plan",
        "unit_cost_low_usd_2025": "100000",
        "unit_cost_base_usd_2025": "250000",
        "unit_cost_high_usd_2025": "500000",
        "source": "screening estimate for CO2 monitoring, isolation and response plan",
        "quality": "screening_default_unvalidated",
        "notes": "CO2 leak detection, isolation and IMR plan.",
    },
    {
        "cost_driver": "replacement_steel_kg",
        "unit": "kg",
        "unit_cost_low_usd_2025": "1.25",
        "unit_cost_base_usd_2025": "2.50",
        "unit_cost_high_usd_2025": "5.00",
        "source": "screening estimate for supplied/fabricated replacement steel; replace with supplier quote",
        "quality": "screening_default_unvalidated",
        "notes": "Replacement or refurbishment steel allowance per kg.",
    },
    {
        "cost_driver": "unmapped_work_item",
        "unit": "item",
        "unit_cost_low_usd_2025": "0",
        "unit_cost_base_usd_2025": "0",
        "unit_cost_high_usd_2025": "0",
        "source": "screening fallback",
        "quality": "screening_default_unvalidated",
        "notes": "Fallback is zero so future unmapped rows are visible but not silently costed.",
    },
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


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


def unit_cost_template_rows() -> list[dict[str, str]]:
    return [dict(row) for row in UNIT_COST_TEMPLATE_ROWS]


def screening_unit_cost_rows() -> list[dict[str, str]]:
    return [dict(row) for row in SCREENING_UNIT_COST_ROWS]


def read_unit_costs(path: Path | None) -> dict[str, dict[str, str]]:
    if path is None or not path.exists():
        return {}
    rows = read_csv_rows(path)
    return {
        row["cost_driver"]: row
        for row in rows
        if row.get("cost_driver")
    }


def _number(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    return float(text)


def _quantity(row: dict[str, Any], key: str) -> float:
    return float(str(row.get(key, 0) or 0))


def _as_yes(value: Any) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1"}


def calculate_refurbishment_costs(
    work_scope_rows: list[dict[str, Any]],
    unit_costs: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Calculate row-level and scenario-level refurbishment costs."""
    cost_rows: list[dict[str, Any]] = []
    totals: dict[str, dict[str, Any]] = {}
    missing: dict[str, set[str]] = {}
    included: dict[str, int] = {}
    quality_flags: dict[str, set[str]] = {}

    for row in work_scope_rows:
        scenario = str(row.get("scenario", "unknown"))
        totals.setdefault(
            scenario,
            {
                "scenario": scenario,
                "pipeline_name": row.get("pipeline_name", ""),
                "gate_status": row.get("gate_status", ""),
                "cost_low_usd_2025": 0.0,
                "cost_base_usd_2025": 0.0,
                "cost_high_usd_2025": 0.0,
            },
        )
        missing.setdefault(scenario, set())
        included.setdefault(scenario, 0)
        quality_flags.setdefault(scenario, set())

        include = _as_yes(row.get("cost_include"))
        driver = str(row.get("cost_driver", ""))
        factor_row = unit_costs.get(driver)
        low_factor = _number(factor_row.get("unit_cost_low_usd_2025")) if factor_row else None
        base_factor = _number(factor_row.get("unit_cost_base_usd_2025")) if factor_row else None
        high_factor = _number(factor_row.get("unit_cost_high_usd_2025")) if factor_row else None
        factor_available = (
            low_factor is not None
            and base_factor is not None
            and high_factor is not None
        )

        low_cost = base_cost = high_cost = 0.0
        factor_status = "not_required"
        if include:
            if not factor_available:
                factor_status = "missing_unit_cost"
                missing[scenario].add(driver)
            else:
                factor_status = "available"
                included[scenario] += 1
                quality_flags[scenario].add(str(factor_row.get("quality") or "unknown"))
                low_cost = _quantity(row, "quantity_low") * float(low_factor)
                base_cost = _quantity(row, "quantity_base") * float(base_factor)
                high_cost = _quantity(row, "quantity_high") * float(high_factor)
                totals[scenario]["cost_low_usd_2025"] += low_cost
                totals[scenario]["cost_base_usd_2025"] += base_cost
                totals[scenario]["cost_high_usd_2025"] += high_cost

        cost_rows.append(
            {
                **row,
                "unit_cost_low_usd_2025": "" if low_factor is None else low_factor,
                "unit_cost_base_usd_2025": "" if base_factor is None else base_factor,
                "unit_cost_high_usd_2025": "" if high_factor is None else high_factor,
                "factor_status": factor_status,
                "cost_low_usd_2025": low_cost,
                "cost_base_usd_2025": base_cost,
                "cost_high_usd_2025": high_cost,
                "factor_source": "" if factor_row is None else factor_row.get("source", ""),
                "factor_quality": "" if factor_row is None else factor_row.get("quality", ""),
            }
        )

    summary_rows: list[dict[str, Any]] = []
    for scenario, total in totals.items():
        missing_drivers = sorted(driver for driver in missing[scenario] if driver)
        if missing_drivers:
            status = "blocked_missing_unit_costs"
        elif str(total.get("gate_status")) == "fail":
            status = "sensitivity_only"
        elif quality_flags[scenario] and all(
            "screening_default" in quality for quality in quality_flags[scenario]
        ):
            status = "screening_result"
        else:
            status = "conditional_result"
        summary_rows.append(
            {
                "scenario": scenario,
                "pipeline_name": total["pipeline_name"],
                "refurbishment_cost_status": status,
                "gate_status": total.get("gate_status", ""),
                "cost_low_usd_2025": round(total["cost_low_usd_2025"], 2),
                "cost_base_usd_2025": round(total["cost_base_usd_2025"], 2),
                "cost_high_usd_2025": round(total["cost_high_usd_2025"], 2),
                "included_factor_count": included[scenario],
                "missing_factor_count": len(missing_drivers),
                "missing_cost_drivers": "; ".join(missing_drivers),
                "factor_quality_summary": "; ".join(sorted(quality_flags[scenario])),
                "model_version": MODEL_VERSION,
            }
        )
    return cost_rows, summary_rows


def _fmt_money(value: Any) -> str:
    return f"${float(value):,.0f}"


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item).replace("|", "/") for item in row) + " |")
    return "\n".join(lines)


def write_refurbishment_cost_report(
    path: Path,
    *,
    work_scope_path: Path,
    unit_cost_path: Path,
    cost_rows_path: Path,
    summary_path: Path,
    summary_rows: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table_rows = [
        [
            row["scenario"],
            row["refurbishment_cost_status"],
            _fmt_money(row["cost_base_usd_2025"]),
            row["included_factor_count"],
            row["missing_factor_count"],
            row["missing_cost_drivers"] or "none",
        ]
        for row in summary_rows
    ]
    report = f"""# Refurbishment Unit-Cost Report

Generated: {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

Model version: `{MODEL_VERSION}`

## Plain Result

This report applies unit-cost factors to the quantified refurbishment work-scope table.

If the status is `screening_result`, public screening defaults were used. This is useful for comparing cases, but it is not a contractor estimate.

If the status is `blocked_missing_unit_costs`, the model has quantities but the chosen unit-cost CSV still needs rates.

## Summary

{_table(["Scenario", "Status", "Base cost", "Factors used", "Missing", "Missing drivers"], table_rows)}

## Input Files

- Work scope: `{work_scope_path.as_posix()}`
- Unit costs: `{unit_cost_path.as_posix()}`

## Output Files

- Row costs: `{cost_rows_path.as_posix()}`
- Summary: `{summary_path.as_posix()}`

## Important Caveat

Public GitHub files must not contain confidential contractor rates, commercial estimates, or restricted cost data. Use public screening defaults for early ranking, then replace them with private project estimates before making publishable cost claims.
"""
    path.write_text(report, encoding="utf-8")
