"""Screening-level LCA inventory and proxy impact calculations."""

from __future__ import annotations

import math

from .assumptions import ScenarioAssumptions
from .constants import INCH_TO_M
from .trace import ModuleResult, OutputRecord, TraceStep, WarningRecord


MODEL_VERSION = "lca_screening_proxy_v0.1"


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


def evaluate_lca_screening(
    scenario: ScenarioAssumptions,
    *,
    pre_lca_decision: str,
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
                    "lca_pipeline_steel_factor_kgco2e_per_kg",
                    "lca_new_build_construction_factor_kgco2e_per_km",
                    "lca_refurbishment_activity_factor_kgco2e_per_km",
                ],
                result_name="lca_proxy_saving_kgco2e",
                notes="Screening proxy to be replaced by Brightway/openLCA ecoinvent calculation.",
            ),
        ],
    )
