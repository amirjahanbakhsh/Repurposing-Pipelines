"""Pipeline integrity and remaining-life screening calculations."""

from __future__ import annotations

from .assumptions import ScenarioAssumptions
from .trace import ModuleResult, OutputRecord, TraceStep, WarningRecord


MODEL_VERSION = "integrity_screening_v0.1"


def evaluate_integrity(scenario: ScenarioAssumptions) -> ModuleResult:
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
    future_corrosion_rate = scenario.number("future_co2_corrosion_rate_mm_per_year")
    remaining_life_years = (
        available_wall_thickness / future_corrosion_rate if available_wall_thickness > 0 else 0
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

    return ModuleResult(
        module="integrity",
        model_version=MODEL_VERSION,
        status="pass" if available_wall_thickness > 0 else "fail",
        inputs=scenario.input_records(input_names, used_by=["integrity"]),
        assumptions=[
            scenario.assumption_record(
                "future_co2_corrosion_rate_mm_per_year",
                sensitivity_required=True,
            )
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
        ],
    )
