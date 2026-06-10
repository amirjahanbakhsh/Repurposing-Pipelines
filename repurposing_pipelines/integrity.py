"""Pipeline integrity and remaining-life screening calculations."""

from __future__ import annotations

from .assumptions import ScenarioAssumptions
from .trace import ModuleResult, OutputRecord, TraceStep, WarningRecord


MODEL_VERSION = "integrity_screening_v0.2"


def _optional_number(
    scenario: ScenarioAssumptions,
    parameter: str,
    default: float,
) -> float:
    value = scenario.optional_number(parameter)
    return default if value is None else value


def _output_value(result: ModuleResult | None, name: str, default: float | str | None = None):
    if result is None:
        return default
    return result.output_map().get(name, default)


def _life(available_wall_mm: float, corrosion_rate_mm_per_year: float) -> float:
    if available_wall_mm <= 0 or corrosion_rate_mm_per_year <= 0:
        return 0
    return available_wall_mm / corrosion_rate_mm_per_year


def evaluate_integrity(
    scenario: ScenarioAssumptions,
    *,
    corrosion: ModuleResult | None = None,
) -> ModuleResult:
    reported_historical_wall_loss = scenario.optional_number("reported_historical_wall_loss_mm")
    if reported_historical_wall_loss is None:
        historical_wall_loss = (
            scenario.number("historical_corrosion_rate_mm_per_year")
            * scenario.number("historical_corrosion_years")
        )
        loss_notes = "Calculated from historical corrosion rate and historical years."
    else:
        historical_wall_loss = reported_historical_wall_loss
        loss_notes = "Used reported historical wall loss."

    current_wall_thickness = scenario.number("nominal_wall_thickness_mm") - historical_wall_loss
    minimum_wall_thickness = scenario.number("minimum_wall_thickness_mm")
    available_wall_thickness = current_wall_thickness - minimum_wall_thickness
    future_corrosion_rate = float(
        _output_value(
            corrosion,
            "corrosion_rate_base_mm_per_year",
            scenario.number("future_co2_corrosion_rate_mm_per_year"),
        )
    )
    corrosion_low = float(
        _output_value(
            corrosion,
            "corrosion_rate_low_mm_per_year",
            _optional_number(
                scenario,
                "future_co2_corrosion_rate_low_mm_per_year",
                future_corrosion_rate,
            ),
        )
    )
    corrosion_high = float(
        _output_value(
            corrosion,
            "corrosion_rate_high_mm_per_year",
            _optional_number(
                scenario,
                "future_co2_corrosion_rate_high_mm_per_year",
                future_corrosion_rate,
            ),
        )
    )
    corrosion_risk = str(_output_value(corrosion, "corrosion_risk_level", "not_assessed"))
    nominal_uncertainty = _optional_number(
        scenario,
        "nominal_wall_thickness_uncertainty_fraction",
        0.0,
    )
    minimum_wall_uncertainty = _optional_number(
        scenario,
        "minimum_wall_thickness_uncertainty_fraction",
        0.0,
    )
    historical_loss_uncertainty = _optional_number(
        scenario,
        "historical_wall_loss_uncertainty_fraction",
        0.0,
    )

    nominal_wall = scenario.number("nominal_wall_thickness_mm")
    current_wall_low = (
        nominal_wall * (1 - nominal_uncertainty)
        - historical_wall_loss * (1 + historical_loss_uncertainty)
    )
    current_wall_high = (
        nominal_wall * (1 + nominal_uncertainty)
        - max(0.0, historical_wall_loss * (1 - historical_loss_uncertainty))
    )
    minimum_wall_low = minimum_wall_thickness * (1 - minimum_wall_uncertainty)
    minimum_wall_high = minimum_wall_thickness * (1 + minimum_wall_uncertainty)
    available_wall_low = current_wall_low - minimum_wall_high
    available_wall_high = current_wall_high - minimum_wall_low

    remaining_life_years = _life(available_wall_thickness, future_corrosion_rate)
    remaining_life_low_years = _life(available_wall_low, corrosion_high)
    remaining_life_high_years = _life(available_wall_high, corrosion_low)
    remaining_life_range_width_years = (
        remaining_life_high_years - remaining_life_low_years
    )
    reported_life = scenario.optional_number("reported_remaining_life_years")
    remaining_life_delta = (
        remaining_life_years - reported_life if reported_life is not None else None
    )

    warnings = [
        WarningRecord(
            level="medium",
            message=(
                "Integrity result is a screening estimate only; inspection records, "
                "material grade checks, defects, and requalification are still needed."
            ),
            affected_modules=["integrity", "pre_lca_gate"],
        )
    ]
    if available_wall_thickness <= 0:
        warnings.append(
            WarningRecord(
                level="high",
                message="Available wall thickness is zero or negative.",
                affected_modules=["integrity", "pre_lca_gate"],
            )
        )
    if corrosion is None:
        warnings.append(
            WarningRecord(
                level="medium",
                message="No separate corrosion module result was supplied.",
                affected_modules=["integrity", "corrosion"],
            )
        )
    if corrosion_risk == "high":
        warnings.append(
            WarningRecord(
                level="high",
                message="Corrosion screen reports high risk.",
                affected_modules=["integrity", "corrosion", "pre_lca_gate"],
            )
        )
    if remaining_life_low_years == 0 and remaining_life_years > 0:
        warnings.append(
            WarningRecord(
                level="medium",
                message=(
                    "Conservative uncertainty case gives zero remaining life; "
                    "wall-thickness basis needs targeted evidence."
                ),
                affected_modules=["integrity", "validation"],
            )
        )

    input_names = [
        "nominal_wall_thickness_mm",
        "minimum_wall_thickness_mm",
        "future_co2_corrosion_rate_mm_per_year",
    ]
    if "reported_remaining_life_years" in scenario.records:
        input_names.append("reported_remaining_life_years")
    if reported_historical_wall_loss is None:
        input_names.extend(["historical_corrosion_rate_mm_per_year", "historical_corrosion_years"])
    else:
        input_names.append("reported_historical_wall_loss_mm")
    for optional_name in [
        "nominal_wall_thickness_uncertainty_fraction",
        "minimum_wall_thickness_uncertainty_fraction",
        "historical_wall_loss_uncertainty_fraction",
        "future_co2_corrosion_rate_low_mm_per_year",
        "future_co2_corrosion_rate_high_mm_per_year",
    ]:
        if optional_name in scenario.records:
            input_names.append(optional_name)

    status = "pass" if available_wall_thickness > 0 and corrosion_risk != "high" else "fail"

    return ModuleResult(
        module="integrity",
        model_version=MODEL_VERSION,
        status=status,
        inputs=scenario.input_records(input_names, used_by=["integrity"]),
        assumptions=[
            scenario.assumption_record(
                "future_co2_corrosion_rate_mm_per_year",
                sensitivity_required=True,
            ),
            *(
                [
                    scenario.assumption_record(
                        "nominal_wall_thickness_uncertainty_fraction",
                        sensitivity_required=True,
                    )
                ]
                if "nominal_wall_thickness_uncertainty_fraction" in scenario.records
                else []
            ),
            *(
                [
                    scenario.assumption_record(
                        "minimum_wall_thickness_uncertainty_fraction",
                        sensitivity_required=True,
                    )
                ]
                if "minimum_wall_thickness_uncertainty_fraction" in scenario.records
                else []
            ),
            *(
                [
                    scenario.assumption_record(
                        "historical_wall_loss_uncertainty_fraction",
                        sensitivity_required=True,
                    )
                ]
                if "historical_wall_loss_uncertainty_fraction" in scenario.records
                else []
            ),
        ],
        outputs=[
            OutputRecord(
                "historical_wall_loss_mm",
                historical_wall_loss,
                "mm",
                used_by=["integrity", "pre_lca_gate"],
                notes=loss_notes,
            ),
            OutputRecord(
                "current_wall_thickness_mm",
                current_wall_thickness,
                "mm",
                used_by=["integrity"],
            ),
            OutputRecord(
                "minimum_wall_thickness_mm",
                minimum_wall_thickness,
                "mm",
                used_by=["integrity", "pre_lca_gate"],
            ),
            OutputRecord(
                "available_wall_thickness_mm",
                available_wall_thickness,
                "mm",
                used_by=["integrity", "pre_lca_gate"],
            ),
            OutputRecord(
                "future_co2_corrosion_rate_mm_per_year",
                future_corrosion_rate,
                "mm/year",
                quality="assumed",
                used_by=["integrity"],
            ),
            OutputRecord(
                "remaining_life_years",
                remaining_life_years,
                "years",
                used_by=["pre_lca_gate", "lca"],
            ),
            OutputRecord(
                "remaining_life_low_years",
                remaining_life_low_years,
                "years",
                quality="screening_estimate",
                used_by=["pre_lca_gate", "lca", "validation"],
                notes="Conservative wall-thickness and high-corrosion case.",
            ),
            OutputRecord(
                "remaining_life_base_years",
                remaining_life_years,
                "years",
                quality="screening_estimate",
                used_by=["pre_lca_gate", "lca", "validation"],
            ),
            OutputRecord(
                "remaining_life_high_years",
                remaining_life_high_years,
                "years",
                quality="screening_estimate",
                used_by=["pre_lca_gate", "lca", "validation"],
                notes="Optimistic wall-thickness and low-corrosion case.",
            ),
            OutputRecord(
                "remaining_life_range_width_years",
                remaining_life_range_width_years,
                "years",
                quality="screening_estimate",
                used_by=["validation", "app"],
            ),
            OutputRecord(
                "available_wall_low_mm",
                available_wall_low,
                "mm",
                quality="screening_estimate",
                used_by=["integrity", "validation"],
            ),
            OutputRecord(
                "available_wall_high_mm",
                available_wall_high,
                "mm",
                quality="screening_estimate",
                used_by=["integrity", "validation"],
            ),
            OutputRecord(
                "corrosion_risk_level",
                corrosion_risk,
                "text",
                used_by=["pre_lca_gate", "validation"],
            ),
            OutputRecord(
                "reported_remaining_life_years",
                reported_life,
                "years",
                quality="reported",
                used_by=["validation"],
            ),
            OutputRecord(
                "remaining_life_delta_years",
                remaining_life_delta,
                "years",
                used_by=["validation"],
            ),
        ],
        warnings=warnings,
        trace=[
            TraceStep(
                name="historical_wall_loss",
                formula=(
                    "reported_historical_wall_loss_mm, if available; otherwise "
                    "historical_corrosion_rate_mm_per_year * historical_corrosion_years"
                ),
                inputs=[
                    "reported_historical_wall_loss_mm",
                    "historical_corrosion_rate_mm_per_year",
                    "historical_corrosion_years",
                ],
                result_name="historical_wall_loss_mm",
            ),
            TraceStep(
                name="current_wall_thickness",
                formula="nominal_wall_thickness_mm - historical_wall_loss_mm",
                inputs=["nominal_wall_thickness_mm", "historical_wall_loss_mm"],
                result_name="current_wall_thickness_mm",
            ),
            TraceStep(
                name="available_wall_thickness",
                formula="current_wall_thickness_mm - minimum_wall_thickness_mm",
                inputs=["current_wall_thickness_mm", "minimum_wall_thickness_mm"],
                result_name="available_wall_thickness_mm",
            ),
            TraceStep(
                name="remaining_life",
                formula="available_wall_thickness_mm / future_co2_corrosion_rate_mm_per_year",
                inputs=[
                    "available_wall_thickness_mm",
                    "future_co2_corrosion_rate_mm_per_year",
                ],
                result_name="remaining_life_years",
            ),
            TraceStep(
                name="remaining_life_uncertainty",
                formula=(
                    "conservative life = low wall / high corrosion; "
                    "optimistic life = high wall / low corrosion"
                ),
                inputs=[
                    "nominal_wall_thickness_uncertainty_fraction",
                    "minimum_wall_thickness_uncertainty_fraction",
                    "historical_wall_loss_uncertainty_fraction",
                    "corrosion_rate_low_mm_per_year",
                    "corrosion_rate_high_mm_per_year",
                ],
                result_name="remaining_life_low_years; remaining_life_high_years",
                notes="Screening uncertainty band for limited or conflicting wall evidence.",
            ),
        ],
    )
