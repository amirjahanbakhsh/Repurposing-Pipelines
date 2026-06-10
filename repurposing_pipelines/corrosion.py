"""Screening-level CO2 corrosion risk calculations."""

from __future__ import annotations

from .assumptions import ScenarioAssumptions
from .trace import ModuleResult, OutputRecord, TraceStep, WarningRecord


MODEL_VERSION = "corrosion_screening_v0.1"


def _optional_number(
    scenario: ScenarioAssumptions,
    parameter: str,
    default: float | None = None,
) -> float | None:
    value = scenario.optional_number(parameter)
    return default if value is None else value


def _risk_from_inputs(
    *,
    water_content_ppmv: float | None,
    water_limit_ppmv: float | None,
    dew_point_margin_c: float | None,
    rate_high_mm_per_year: float,
) -> tuple[str, str]:
    if water_content_ppmv is not None and water_limit_ppmv is not None:
        if water_content_ppmv > water_limit_ppmv:
            return "high", "CO2 water content is above the selected dry-CO2 screening limit."
    if dew_point_margin_c is not None and dew_point_margin_c < 0:
        return "high", "The stream may cross the water dew point, so free water risk is high."
    if water_content_ppmv is None and dew_point_margin_c is None:
        return "medium", "Water content and dew-point margin are missing, so corrosion risk is uncertain."
    if rate_high_mm_per_year >= 0.2:
        return "medium", "The high corrosion-rate case is material for remaining-life sensitivity."
    return "low", "Dry-CO2 screening inputs do not show an immediate free-water warning."


def evaluate_corrosion(scenario: ScenarioAssumptions) -> ModuleResult:
    """Evaluate a simple dry-CO2 corrosion screen.

    This is not a full NORSOK/DNV corrosion model. It is a transparent screening
    layer that records water-content evidence and supplies low/base/high
    corrosion rates to the integrity module.
    """
    base_rate = scenario.number("future_co2_corrosion_rate_mm_per_year")
    low_rate = _optional_number(
        scenario,
        "future_co2_corrosion_rate_low_mm_per_year",
        base_rate,
    )
    high_rate = _optional_number(
        scenario,
        "future_co2_corrosion_rate_high_mm_per_year",
        base_rate,
    )
    water_content = _optional_number(scenario, "co2_water_content_ppmv")
    water_limit = _optional_number(scenario, "co2_water_spec_limit_ppmv")
    dew_point_margin = _optional_number(scenario, "water_dew_point_margin_c")

    if low_rate is None or high_rate is None:
        raise ValueError("Corrosion-rate bounds could not be evaluated.")
    if low_rate <= 0 or base_rate <= 0 or high_rate <= 0:
        status = "fail"
        risk = "high"
        basis = "Corrosion rates must be positive."
    elif not (low_rate <= base_rate <= high_rate):
        status = "fail"
        risk = "high"
        basis = "Corrosion-rate bounds must follow low <= base <= high."
    else:
        risk, basis = _risk_from_inputs(
            water_content_ppmv=water_content,
            water_limit_ppmv=water_limit,
            dew_point_margin_c=dew_point_margin,
            rate_high_mm_per_year=high_rate,
        )
        status = "fail" if risk == "high" else "pass"

    warnings = [
        WarningRecord(
            level="medium",
            message=(
                "Corrosion model is a screening dry-CO2 risk check. A final model "
                "needs stream composition, water specification, operating envelope, "
                "inspection evidence, and specialist review."
            ),
            affected_modules=["corrosion", "integrity", "pre_lca_gate"],
        )
    ]
    if water_content is None and dew_point_margin is None:
        warnings.append(
            WarningRecord(
                level="medium",
                message="Water content and dew-point margin are missing.",
                affected_modules=["corrosion", "integrity"],
            )
        )
    if status == "fail":
        warnings.append(
            WarningRecord(
                level="high",
                message=basis,
                affected_modules=["corrosion", "integrity", "pre_lca_gate"],
            )
        )

    input_names = [
        "future_co2_corrosion_rate_mm_per_year",
    ]
    for optional_name in [
        "future_co2_corrosion_rate_low_mm_per_year",
        "future_co2_corrosion_rate_high_mm_per_year",
        "co2_water_content_ppmv",
        "co2_water_spec_limit_ppmv",
        "water_dew_point_margin_c",
    ]:
        if optional_name in scenario.records:
            input_names.append(optional_name)

    assumptions = [
        scenario.assumption_record(
            "future_co2_corrosion_rate_mm_per_year",
            sensitivity_required=True,
        )
    ]
    for optional_name in [
        "future_co2_corrosion_rate_low_mm_per_year",
        "future_co2_corrosion_rate_high_mm_per_year",
        "co2_water_content_ppmv",
        "co2_water_spec_limit_ppmv",
        "water_dew_point_margin_c",
    ]:
        if optional_name in scenario.records:
            assumptions.append(
                scenario.assumption_record(optional_name, sensitivity_required=True)
            )

    return ModuleResult(
        module="corrosion",
        model_version=MODEL_VERSION,
        status=status,
        inputs=scenario.input_records(input_names, used_by=["corrosion"]),
        assumptions=assumptions,
        outputs=[
            OutputRecord(
                "corrosion_rate_low_mm_per_year",
                low_rate,
                "mm/year",
                quality="assumed",
                used_by=["integrity"],
            ),
            OutputRecord(
                "corrosion_rate_base_mm_per_year",
                base_rate,
                "mm/year",
                quality="assumed",
                used_by=["integrity", "pre_lca_gate"],
            ),
            OutputRecord(
                "corrosion_rate_high_mm_per_year",
                high_rate,
                "mm/year",
                quality="assumed",
                used_by=["integrity"],
            ),
            OutputRecord(
                "co2_water_content_ppmv",
                water_content,
                "ppmv",
                quality="assumed",
                used_by=["corrosion", "validation"],
            ),
            OutputRecord(
                "co2_water_spec_limit_ppmv",
                water_limit,
                "ppmv",
                quality="assumed",
                used_by=["corrosion", "validation"],
            ),
            OutputRecord(
                "water_dew_point_margin_c",
                dew_point_margin,
                "degC",
                quality="assumed",
                used_by=["corrosion", "validation"],
            ),
            OutputRecord(
                "corrosion_risk_level",
                risk,
                "text",
                used_by=["integrity", "pre_lca_gate"],
            ),
            OutputRecord(
                "corrosion_basis",
                basis,
                "text",
                used_by=["report", "app"],
            ),
        ],
        warnings=warnings,
        trace=[
            TraceStep(
                name="corrosion_rate_range",
                formula="low/base/high corrosion rates are read from scenario assumptions",
                inputs=[
                    "future_co2_corrosion_rate_low_mm_per_year",
                    "future_co2_corrosion_rate_mm_per_year",
                    "future_co2_corrosion_rate_high_mm_per_year",
                ],
                result_name="corrosion_rate_low/base/high_mm_per_year",
                notes="Used for remaining-life uncertainty.",
            ),
            TraceStep(
                name="dry_co2_risk",
                formula=(
                    "high if water content exceeds limit or dew point margin is negative; "
                    "medium if water evidence is missing or high corrosion rate is material; "
                    "otherwise low"
                ),
                inputs=[
                    "co2_water_content_ppmv",
                    "co2_water_spec_limit_ppmv",
                    "water_dew_point_margin_c",
                    "corrosion_rate_high_mm_per_year",
                ],
                result_name="corrosion_risk_level",
                notes="Screening rule, not a detailed corrosion prediction model.",
            ),
        ],
    )
