"""Screening-level cost calculations."""

from __future__ import annotations

from .assumptions import ScenarioAssumptions
from .trace import ModuleResult, OutputRecord, TraceStep, WarningRecord


MODEL_VERSION = "cost_screening_v0.2"

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
    netl_reference_total = scenario.optional_number("netl_reference_total_capex_usd_2025")
    netl_delta = total - netl_reference_total if netl_reference_total is not None else None
    netl_delta_percent = (
        100 * netl_delta / netl_reference_total
        if netl_reference_total not in {None, 0}
        else None
    )
    netl_status = "not_supplied"
    if netl_reference_total is not None and netl_delta_percent is not None:
        netl_status = "pass" if abs(netl_delta_percent) <= 20 else "review_required"

    warnings = []
    if netl_reference_total is None:
        warnings.append(
            WarningRecord(
                level="medium",
                message=(
                    "No NETL CO2_T_COM reference total is supplied for this scenario, "
                    "so cost is internally checked but not externally validated."
                ),
                affected_modules=["cost", "validation"],
            )
        )

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
            )
            + (
                ["netl_reference_total_capex_usd_2025"]
                if "netl_reference_total_capex_usd_2025" in scenario.records
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
            OutputRecord(
                "netl_reference_total_capex_usd_2025",
                netl_reference_total,
                "USD 2025",
                quality="reported",
                used_by=["validation"],
            ),
            OutputRecord(
                "netl_cost_delta_usd_2025",
                netl_delta,
                "USD 2025",
                used_by=["validation"],
            ),
            OutputRecord(
                "netl_cost_delta_percent",
                netl_delta_percent,
                "%",
                used_by=["validation"],
            ),
            OutputRecord(
                "netl_cost_validation_status",
                netl_status,
                "status",
                used_by=["validation", "report"],
            ),
        ],
        warnings=warnings,
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
            TraceStep(
                name="netl_cost_comparison",
                formula="cost_total_usd_2025 - netl_reference_total_capex_usd_2025",
                inputs=["cost_total_usd_2025", "netl_reference_total_capex_usd_2025"],
                result_name="netl_cost_delta_usd_2025",
                notes="Runs only when a like-for-like NETL CO2_T_COM reference is supplied.",
            ),
        ],
    )
