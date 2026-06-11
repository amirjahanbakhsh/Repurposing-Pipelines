"""Quantified refurbishment work-scope table for pipeline repurposing.

The repurposing gate identifies what needs to be checked or done. This module
turns those named work items into simple quantity drivers for cost and LCA.
It does not claim contractor rates, vessel durations, or final impact factors.

Reference IDs are kept in the rows so the table remains traceable to the
repurposing literature register.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .assumptions import ScenarioAssumptions
from .lca import pipeline_steel_mass_from_wall_kg
from .trace import ModuleResult, OutputRecord, TraceStep, WarningRecord


MODEL_VERSION = "refurbishment_work_scope_v0.1"

REFERENCE_REQUALIFICATION = (
    "REF_OSTBY_TORBERGSEN_RONEID_LEINUM_2022_CO2_REQUALIFICATION; "
    "REF_MONSMA_MURRAY_2026_GAS_PHASE_CO2_REPURPOSING"
)
REFERENCE_IMR = (
    "REF_KUMAR_LOWERY_PASSUCCI_2025_ENI_LIVERPOOL_BAY_IMR; "
    "REF_DALONZO_BUSCO_ELVIRA_CHERUBINI_2025_CO2_IMR"
)
REFERENCE_DENSE_PHASE = "REF_YUSOF_AZIZ_2025_PETRONAS_DENSE_PHASE_CO2_REPURPOSING"
REFERENCE_DATA = "REF_BURKINSHAW_GALLON_CARVELL_HUSSAIN_2024_HYDROGEN_DATA_EVIDENCE"
REFERENCE_COMPATIBILITY = "REF_KASS_ET_AL_2023_MATERIAL_COMPATIBILITY"

WORK_ITEM_DEFINITIONS: dict[str, dict[str, str]] = {
    "confirm_co2_composition_and_impurities": {
        "name": "Confirm CO2 composition and impurities",
        "stage": "requalification_study",
        "quantity_method": "each",
        "unit": "study",
        "cost_driver": "engineering_study_each",
        "lca_mapping_key": "not_applicable",
        "cost_include": "yes",
        "lca_include": "no",
        "basis": "Required before corrosion, phase, material and operating checks can be finalised.",
        "reference_ids": REFERENCE_REQUALIFICATION,
    },
    "confirm_water_limit_and_dew_point": {
        "name": "Confirm water limit and dew-point basis",
        "stage": "requalification_study",
        "quantity_method": "each",
        "unit": "study",
        "cost_driver": "engineering_study_each",
        "lca_mapping_key": "not_applicable",
        "cost_include": "yes",
        "lca_include": "no",
        "basis": "Dry CO2 specification and water-dew-point margin control corrosion risk.",
        "reference_ids": REFERENCE_REQUALIFICATION,
    },
    "cleaning_drying_and_debris_assessment": {
        "name": "Cleaning, drying and debris assessment",
        "stage": "field_execution",
        "quantity_method": "length_km",
        "unit": "km",
        "cost_driver": "cleaning_drying_per_km",
        "lca_mapping_key": "refurbishment_activity",
        "cost_include": "yes",
        "lca_include": "included_in_refurbishment_package",
        "basis": "Pipeline preparation is needed where corrosion, debris or dry-CO2 readiness remains uncertain.",
        "reference_ids": REFERENCE_IMR,
    },
    "ili_mfl_or_equivalent_inspection": {
        "name": "ILI/MFL or equivalent inspection campaign",
        "stage": "inspection",
        "quantity_method": "length_km",
        "unit": "km",
        "cost_driver": "inspection_per_km",
        "lca_mapping_key": "refurbishment_activity",
        "cost_include": "yes",
        "lca_include": "included_in_refurbishment_package",
        "basis": "Inspection evidence is needed before reuse can be treated as a serious option.",
        "reference_ids": f"{REFERENCE_IMR}; {REFERENCE_DATA}",
    },
    "material_certificates_or_testing": {
        "name": "Material certificates or material testing",
        "stage": "requalification_study",
        "quantity_method": "each",
        "unit": "campaign",
        "cost_driver": "material_testing_campaign",
        "lca_mapping_key": "refurbishment_activity",
        "cost_include": "yes",
        "lca_include": "included_in_refurbishment_package",
        "basis": "Material evidence is needed for pipe, weld and fracture checks.",
        "reference_ids": f"{REFERENCE_REQUALIFICATION}; {REFERENCE_DENSE_PHASE}",
    },
    "component_compatibility_review": {
        "name": "Component compatibility review",
        "stage": "requalification_study",
        "quantity_method": "each",
        "unit": "review",
        "cost_driver": "compatibility_review_each",
        "lca_mapping_key": "not_applicable",
        "cost_include": "yes",
        "lca_include": "no",
        "basis": "Valves, seals, coatings and equipment exposed to CO2 service need compatibility review.",
        "reference_ids": REFERENCE_COMPATIBILITY,
    },
    "fracture_and_decompression_screen": {
        "name": "Fracture and decompression screen",
        "stage": "requalification_study",
        "quantity_method": "each",
        "unit": "study",
        "cost_driver": "fracture_decompression_study_each",
        "lca_mapping_key": "not_applicable",
        "cost_include": "yes",
        "lca_include": "no",
        "basis": "Dense-phase or high-pressure CO2 reuse needs fracture and decompression evidence.",
        "reference_ids": f"{REFERENCE_REQUALIFICATION}; {REFERENCE_DENSE_PHASE}",
    },
    "wall_thickness_verification": {
        "name": "Wall-thickness verification",
        "stage": "inspection",
        "quantity_method": "length_km",
        "unit": "km",
        "cost_driver": "wall_thickness_verification_per_km",
        "lca_mapping_key": "refurbishment_activity",
        "cost_include": "yes",
        "lca_include": "included_in_refurbishment_package",
        "basis": "Wall-thickness uncertainty must be reduced before detailed reuse decisions.",
        "reference_ids": f"{REFERENCE_DATA}; {REFERENCE_IMR}",
    },
    "co2_leak_detection_isolation_and_imr_plan": {
        "name": "CO2 leak detection, isolation and IMR plan",
        "stage": "operations_readiness",
        "quantity_method": "each",
        "unit": "plan",
        "cost_driver": "imr_plan_each",
        "lca_mapping_key": "not_applicable",
        "cost_include": "yes",
        "lca_include": "no",
        "basis": "Reuse needs an operating integrity, leak detection and repair plan before operation.",
        "reference_ids": REFERENCE_IMR,
    },
}


def _joined(items: list[str]) -> str:
    return "; ".join(dict.fromkeys(item for item in items if item))


def _split_items(value: Any) -> list[str]:
    return [item.strip() for item in str(value or "").split(";") if item.strip()]


def _optional_number(
    scenario: ScenarioAssumptions,
    parameter: str,
    default: float,
) -> float:
    value = scenario.optional_number(parameter)
    return default if value is None else float(value)


def _output(result: ModuleResult | None, name: str, default: Any = None) -> Any:
    if result is None:
        return default
    return result.output_map().get(name, default)


def _quantity_for_method(method: str, length_km: float) -> tuple[float, float, float]:
    if method == "length_km":
        return length_km, length_km, length_km
    return 1.0, 1.0, 1.0


def _base_row(
    *,
    scenario: ScenarioAssumptions,
    gate_outputs: dict[str, Any],
    work_item_id: str,
    definition: dict[str, str],
    quantity_low: float,
    quantity_base: float,
    quantity_high: float,
    unit: str,
    data_quality: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "scenario": scenario.name,
        "pipeline_name": scenario.raw("pipeline_name"),
        "gate_status": gate_outputs.get("repurposing_gate_status", ""),
        "gate_confidence": gate_outputs.get("repurposing_gate_confidence", ""),
        "work_item_id": work_item_id,
        "work_item_name": definition["name"],
        "work_stage": definition["stage"],
        "quantity_low": round(quantity_low, 6),
        "quantity_base": round(quantity_base, 6),
        "quantity_high": round(quantity_high, 6),
        "unit": unit,
        "cost_include": definition["cost_include"],
        "cost_driver": definition["cost_driver"],
        "lca_include": definition["lca_include"],
        "lca_mapping_key": definition["lca_mapping_key"],
        "data_quality": data_quality,
        "basis": definition["basis"],
        "reference_ids": definition["reference_ids"],
        "notes": notes,
    }


def _new_build_steel_mass_range(scenario: ScenarioAssumptions) -> tuple[float, float, float]:
    length_km = scenario.number("pipeline_length_km")
    inner_diameter_in = scenario.number("inner_diameter_in")
    wall_thickness_mm = scenario.number("nominal_wall_thickness_mm")
    steel_density = _optional_number(scenario, "steel_density_kg_per_m3", 7850.0)
    wall_uncertainty = _optional_number(
        scenario,
        "nominal_wall_thickness_uncertainty_fraction",
        0.0,
    )
    wall_low = max(0.0, wall_thickness_mm * (1 - wall_uncertainty))
    wall_high = wall_thickness_mm * (1 + wall_uncertainty)
    return (
        pipeline_steel_mass_from_wall_kg(
            length_km=length_km,
            inner_diameter_in=inner_diameter_in,
            wall_thickness_mm=wall_low,
            steel_density_kg_per_m3=steel_density,
        ),
        pipeline_steel_mass_from_wall_kg(
            length_km=length_km,
            inner_diameter_in=inner_diameter_in,
            wall_thickness_mm=wall_thickness_mm,
            steel_density_kg_per_m3=steel_density,
        ),
        pipeline_steel_mass_from_wall_kg(
            length_km=length_km,
            inner_diameter_in=inner_diameter_in,
            wall_thickness_mm=wall_high,
            steel_density_kg_per_m3=steel_density,
        ),
    )


def build_refurbishment_work_scope_rows(
    scenario: ScenarioAssumptions,
    *,
    repurposing_gate: ModuleResult,
    integrity: ModuleResult | None = None,
) -> list[dict[str, Any]]:
    """Build a quantified table from the repurposing gate work items."""
    gate_outputs = repurposing_gate.output_map()
    length_km = scenario.number("pipeline_length_km")
    rows: list[dict[str, Any]] = []

    for item in _split_items(gate_outputs.get("repurposing_work_scope_items")):
        definition = WORK_ITEM_DEFINITIONS.get(item)
        if definition is None:
            definition = {
                "name": item.replace("_", " "),
                "stage": "unmapped",
                "quantity_method": "each",
                "unit": "item",
                "cost_driver": "unmapped_work_item",
                "lca_mapping_key": "to_be_mapped",
                "cost_include": "yes",
                "lca_include": "review_required",
                "basis": "Gate item has not yet been mapped to a standard work-scope quantity.",
                "reference_ids": str(gate_outputs.get("repurposing_gate_cited_references", "")),
            }
        low, base, high = _quantity_for_method(definition["quantity_method"], length_km)
        rows.append(
            _base_row(
                scenario=scenario,
                gate_outputs=gate_outputs,
                work_item_id=item,
                definition=definition,
                quantity_low=low,
                quantity_base=base,
                quantity_high=high,
                unit=definition["unit"],
                data_quality="screening_driver",
                notes="Quantity is a work driver for cost/LCA scoping, not a contractor estimate.",
            )
        )

    refurbishment_fraction = float(
        gate_outputs.get("lca_refurbishment_steel_fraction_recommended")
        or _optional_number(scenario, "lca_refurbishment_steel_fraction", 0.05)
    )
    steel_low, steel_base, steel_high = _new_build_steel_mass_range(scenario)
    steel_definition = {
        "name": "Replacement or refurbishment steel allowance",
        "stage": "field_execution",
        "quantity_method": "calculated_steel_mass",
        "unit": "kg",
        "cost_driver": "replacement_steel_kg",
        "lca_mapping_key": "pipeline_steel",
        "cost_include": "yes",
        "lca_include": "yes",
        "basis": (
            "Calculated as new-build pipe steel mass multiplied by the gate-recommended "
            "refurbishment steel fraction."
        ),
        "reference_ids": f"{REFERENCE_REQUALIFICATION}; {REFERENCE_DENSE_PHASE}",
    }
    rows.append(
        _base_row(
            scenario=scenario,
            gate_outputs=gate_outputs,
            work_item_id="replacement_or_refurbishment_steel",
            definition=steel_definition,
            quantity_low=steel_low * refurbishment_fraction,
            quantity_base=steel_base * refurbishment_fraction,
            quantity_high=steel_high * refurbishment_fraction,
            unit="kg",
            data_quality="screening_calculation",
            notes=(
                f"Uses refurbishment fraction {refurbishment_fraction:.4f}; "
                "replace with inspection-based repair quantities when available."
            ),
        )
    )

    package_definition = {
        "name": "Refurbishment activity package",
        "stage": "aggregate_lca_package",
        "quantity_method": "length_km",
        "unit": "km",
        "cost_driver": "not_for_direct_cost_sum",
        "lca_mapping_key": "refurbishment_activity",
        "cost_include": "no",
        "lca_include": "yes",
        "basis": (
            "Aggregate LCA package for inspection, cleaning, drying, repair and "
            "recommissioning until detailed process factors are split."
        ),
        "reference_ids": f"{REFERENCE_REQUALIFICATION}; {REFERENCE_IMR}",
    }
    rows.append(
        _base_row(
            scenario=scenario,
            gate_outputs=gate_outputs,
            work_item_id="refurbishment_activity_package",
            definition=package_definition,
            quantity_low=length_km,
            quantity_base=length_km,
            quantity_high=length_km,
            unit="km",
            data_quality="aggregate_screening_package",
            notes=(
                "Use this as the current LCA package row. Individual work items "
                "show what the package should later be split into."
            ),
        )
    )

    remaining_life_low = _output(integrity, "remaining_life_low_years")
    if remaining_life_low is not None and float(remaining_life_low) <= 0:
        for row in rows:
            row["notes"] = f"{row['notes']} Conservative remaining life is non-positive; review before reuse."

    return rows


def evaluate_refurbishment_work_scope(
    scenario: ScenarioAssumptions,
    *,
    repurposing_gate: ModuleResult,
    integrity: ModuleResult | None = None,
) -> ModuleResult:
    rows = build_refurbishment_work_scope_rows(
        scenario,
        repurposing_gate=repurposing_gate,
        integrity=integrity,
    )
    cost_count = sum(1 for row in rows if row["cost_include"] == "yes")
    lca_count = sum(1 for row in rows if row["lca_include"] == "yes")
    replacement_steel = next(
        (
            float(row["quantity_base"])
            for row in rows
            if row["work_item_id"] == "replacement_or_refurbishment_steel"
        ),
        0.0,
    )
    package_km = next(
        (
            float(row["quantity_base"])
            for row in rows
            if row["work_item_id"] == "refurbishment_activity_package"
        ),
        0.0,
    )
    status = "ready_for_screening" if rows else "no_work_scope_items"
    warnings = [
        WarningRecord(
            level="medium",
            message=(
                "Refurbishment work-scope quantities are screening drivers. They are "
                "not contractor method statements, vendor quotes, or final LCA factors."
            ),
            affected_modules=["work_scope", "cost", "lca"],
        )
    ]
    if repurposing_gate.status == "fail":
        warnings.append(
            WarningRecord(
                level="high",
                message=(
                    "The repurposing gate failed. Work-scope rows describe what would "
                    "need resolution; they do not justify proceeding with reuse."
                ),
                affected_modules=["work_scope", "pre_lca_gate"],
            )
        )

    return ModuleResult(
        module="work_scope",
        model_version=MODEL_VERSION,
        status=status,
        outputs=[
            OutputRecord(
                "refurbishment_work_scope_status",
                status,
                "status",
                used_by=["cost", "lca", "report"],
            ),
            OutputRecord(
                "refurbishment_work_scope_item_count",
                len(rows),
                "count",
                used_by=["cost", "lca", "report"],
            ),
            OutputRecord(
                "refurbishment_cost_item_count",
                cost_count,
                "count",
                used_by=["cost", "report"],
            ),
            OutputRecord(
                "refurbishment_lca_item_count",
                lca_count,
                "count",
                used_by=["lca", "report"],
            ),
            OutputRecord(
                "refurbishment_replacement_steel_kg",
                replacement_steel,
                "kg",
                quality="screening_calculation",
                used_by=["cost", "lca"],
            ),
            OutputRecord(
                "refurbishment_activity_package_km",
                package_km,
                "km",
                quality="aggregate_screening_package",
                used_by=["lca"],
            ),
            OutputRecord(
                "refurbishment_work_scope_row_ids",
                _joined([str(row["work_item_id"]) for row in rows]),
                "text",
                used_by=["report"],
            ),
        ],
        warnings=warnings,
        trace=[
            TraceStep(
                name="gate_items_to_work_scope_rows",
                formula=(
                    "map repurposing_work_scope_items to quantity drivers; add replacement "
                    "steel and aggregate refurbishment activity package"
                ),
                inputs=[
                    "repurposing_work_scope_items",
                    "pipeline_length_km",
                    "nominal_wall_thickness_mm",
                    "inner_diameter_in",
                    "lca_refurbishment_steel_fraction_recommended",
                ],
                result_name="refurbishment_work_scope_item_count",
                notes=(
                    "Rows cite requalification, IMR, dense-phase, data quality and material "
                    "compatibility source IDs. They are designed to feed cost and LCA modules."
                ),
            )
        ],
    )


def write_refurbishment_work_scope_csv(path: Path, rows: list[dict[str, Any]]) -> None:
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


def collect_refurbishment_work_scope_rows(traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for trace in traces:
        rows.extend(trace.get("refurbishment_work_scope_rows", []))
    return rows
