"""Decision gates that combine module results into clear screening outcomes."""

from __future__ import annotations

from .trace import ModuleResult, OutputRecord, TraceStep, WarningRecord


MODEL_VERSION = "pre_lca_gate_v0.1"

WEAK_QUALITIES = {
    "assumed",
    "assumed_or_standard",
    "estimated",
}


def _joined(items: list[str]) -> str:
    return "; ".join(dict.fromkeys(item for item in items if item))


def _weak_input_names(results: list[ModuleResult]) -> list[str]:
    weak_names: list[str] = []
    for result in results:
        for item in result.inputs:
            if item.quality in WEAK_QUALITIES:
                weak_names.append(item.name)
        for item in result.assumptions:
            if item.sensitivity_required or item.quality in WEAK_QUALITIES:
                weak_names.append(item.name)
    return sorted(set(weak_names))


def _warning_levels(results: list[ModuleResult]) -> list[str]:
    return [warning.level for result in results for warning in result.warnings]


def evaluate_pre_lca_gate(
    *,
    capacity: ModuleResult,
    integrity: ModuleResult,
    cost: ModuleResult,
) -> ModuleResult:
    """Decide whether a pipeline should move into LCA screening.

    The gate is deliberately conservative. A pipeline can pass the maths but
    still be labelled `marginal` when key inputs are assumptions or when the
    technical modules warn that validation is still needed.
    """
    module_results = [capacity, integrity, cost]
    outputs = {}
    for result in module_results:
        outputs.update(result.output_map())

    required_outputs = [
        "capacity_mtpa",
        "required_design_mtpa",
        "remaining_life_years",
        "available_wall_thickness_mm",
        "cost_total_usd_2025",
    ]
    missing_outputs = [name for name in required_outputs if name not in outputs]

    reasons: list[str] = []
    next_data: list[str] = []
    warnings: list[WarningRecord] = []

    if missing_outputs:
        decision = "insufficient_data"
        confidence = "low"
        reasons.append("The gate cannot run because key outputs are missing.")
        next_data.append("rerun the upstream capacity, integrity, and cost modules")
        warnings.append(
            WarningRecord(
                level="high",
                message=f"Missing outputs for pre-LCA gate: {_joined(missing_outputs)}.",
                affected_modules=["pre_lca_gate"],
            )
        )
    else:
        failing_modules = [result.module for result in module_results if result.status == "fail"]
        if failing_modules:
            decision = "fail"
            confidence = "medium"
            reasons.append(f"One or more upstream modules failed: {_joined(failing_modules)}.")
        else:
            capacity_mtpa = float(outputs["capacity_mtpa"])
            required_design_mtpa = float(outputs["required_design_mtpa"])
            remaining_life_years = float(outputs["remaining_life_years"])
            available_wall_thickness = float(outputs["available_wall_thickness_mm"])
            cost_total = float(outputs["cost_total_usd_2025"])

            reasons.append(
                f"Capacity passes: {capacity_mtpa:.2f} MtCO2/year versus "
                f"{required_design_mtpa:.2f} MtCO2/year required."
            )
            reasons.append(
                f"Integrity passes at screening level: {remaining_life_years:.2f} years "
                f"remaining life and {available_wall_thickness:.2f} mm available wall."
            )
            reasons.append(
                f"Cost screen is positive: benchmark avoided new-build CAPEX is ${cost_total:,.0f}."
            )

            weak_inputs = _weak_input_names(module_results)
            warning_levels = _warning_levels(module_results)
            has_module_warnings = bool(warning_levels)

            if weak_inputs:
                reasons.append(
                    "Some important values are assumed or sensitivity inputs: "
                    f"{_joined(weak_inputs)}."
                )
            if has_module_warnings:
                reasons.append("Upstream modules still contain validation warnings.")

            if weak_inputs or has_module_warnings:
                decision = "marginal"
                confidence = "medium"
                warnings.append(
                    WarningRecord(
                        level="medium",
                        message=(
                            "Pipeline is technically promising, but should not move to detailed LCA "
                            "without checking key assumptions."
                        ),
                        affected_modules=["pre_lca_gate", "lca"],
                    )
                )
            else:
                decision = "pass"
                confidence = "high"

            next_data.extend(
                [
                    "verify wall thickness and inspection records",
                    "validate CO2 density, viscosity, compressibility, and phase behaviour",
                    "compare cost with NETL CO2_T_COM or another external benchmark",
                    "define reuse modification cost before detailed LCA",
                ]
            )

    reason_summary = {
        "pass": "Move to LCA screening.",
        "marginal": "Move to LCA only as a sensitivity case until assumptions are checked.",
        "fail": "Do not move to LCA until failed technical or cost checks are resolved.",
        "insufficient_data": "Do not move to LCA because there is not enough information.",
    }[decision]

    return ModuleResult(
        module="pre_lca_gate",
        model_version=MODEL_VERSION,
        status=decision,
        outputs=[
            OutputRecord(
                "pre_lca_decision",
                decision,
                "decision",
                used_by=["lca", "final_gate"],
            ),
            OutputRecord(
                "pre_lca_confidence",
                confidence,
                "quality",
                used_by=["lca", "final_gate"],
            ),
            OutputRecord(
                "pre_lca_reason_summary",
                reason_summary,
                "text",
                used_by=["report", "app"],
            ),
            OutputRecord(
                "pre_lca_reasons",
                _joined(reasons),
                "text",
                used_by=["report", "app"],
            ),
            OutputRecord(
                "pre_lca_next_data",
                _joined(next_data),
                "text",
                used_by=["report", "app"],
            ),
        ],
        warnings=warnings,
        trace=[
            TraceStep(
                name="pre_lca_gate",
                formula=(
                    "fail if any upstream module fails; insufficient_data if key outputs are missing; "
                    "marginal if outputs pass but key assumptions or validation warnings remain; "
                    "otherwise pass"
                ),
                inputs=required_outputs,
                result_name="pre_lca_decision",
                notes="This is a screening gate, not an engineering approval decision.",
            )
        ],
    )
