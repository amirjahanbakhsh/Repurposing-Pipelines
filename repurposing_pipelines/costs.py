"""Screening-level cost calculations."""

from __future__ import annotations

from .assumptions import ScenarioAssumptions
from .trace import ModuleResult, OutputRecord, TraceStep


MODEL_VERSION = "cost_screening_v0.1"

COST_COMPONENT_PARAMETERS = [
    "cost_material_usd_2025",
    "cost_labor_usd_2025",
    "cost_row_damages_usd_2025",
    "cost_misc_usd_2025",
    "cost_surge_tank_usd_2025",
    "cost_control_system_usd_2025",
    "cost_booster_station_usd_2025",
]


def evaluate_cost(scenario: ScenarioAssumptions) -> ModuleResult:
    subtotal = sum(scenario.number(name) for name in COST_COMPONENT_PARAMETERS)
    contingency = scenario.number("contingency_fraction") * subtotal
    total = subtotal + contingency
    reported_total = scenario.optional_number("reported_total_capex_usd_2025")
    cost_delta = total - reported_total if reported_total is not None else None

    return ModuleResult(
        module="cost",
        model_version=MODEL_VERSION,
        status="pass" if total > 0 else "fail",
        inputs=scenario.input_records(
            COST_COMPONENT_PARAMETERS
            + ["contingency_fraction"]
            + (
                ["reported_total_capex_usd_2025"]
                if "reported_total_capex_usd_2025" in scenario.records
                else []
            ),
            used_by=["cost"],
        ),
        assumptions=[
            scenario.assumption_record("contingency_fraction", sensitivity_required=True),
        ],
        outputs=[
            OutputRecord(
                "cost_subtotal_usd_2025",
                subtotal,
                "USD 2025",
                used_by=["cost", "pre_lca_gate"],
            ),
            OutputRecord(
                "cost_contingency_usd_2025",
                contingency,
                "USD 2025",
                used_by=["cost", "pre_lca_gate"],
            ),
            OutputRecord(
                "cost_total_usd_2025",
                total,
                "USD 2025",
                used_by=["pre_lca_gate", "final_gate"],
            ),
            OutputRecord(
                "reported_total_capex_usd_2025",
                reported_total,
                "USD 2025",
                quality="reported",
                used_by=["validation"],
            ),
            OutputRecord(
                "cost_delta_usd_2025",
                cost_delta,
                "USD 2025",
                used_by=["validation"],
            ),
        ],
        trace=[
            TraceStep(
                name="cost_subtotal",
                formula="sum(material, labor, ROW damages, misc, surge tank, control system, booster station)",
                inputs=COST_COMPONENT_PARAMETERS,
                result_name="cost_subtotal_usd_2025",
            ),
            TraceStep(
                name="contingency",
                formula="contingency_fraction * cost_subtotal_usd_2025",
                inputs=["contingency_fraction", "cost_subtotal_usd_2025"],
                result_name="cost_contingency_usd_2025",
            ),
            TraceStep(
                name="total_cost",
                formula="cost_subtotal_usd_2025 + cost_contingency_usd_2025",
                inputs=["cost_subtotal_usd_2025", "cost_contingency_usd_2025"],
                result_name="cost_total_usd_2025",
            ),
        ],
    )
