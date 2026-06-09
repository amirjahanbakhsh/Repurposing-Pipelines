"""CO2 transport capacity screening calculations."""

from __future__ import annotations

import math

from .assumptions import ScenarioAssumptions
from .constants import (
    G_PER_MOL_TO_KG_PER_MOL,
    INCH_TO_M,
    PSI_TO_PA,
    UNIVERSAL_GAS_CONSTANT,
)
from .trace import ModuleResult, OutputRecord, TraceStep, WarningRecord
from .units import kg_per_s_to_mtpa


MODEL_VERSION = "capacity_screening_v0.1"


def average_pressure_pa(inlet_pa: float, outlet_pa: float) -> float:
    """Gas-pipeline average pressure used in McCoy/Rubin-style calculations."""
    return (2 / 3) * (inlet_pa + outlet_pa - (inlet_pa * outlet_pa / (inlet_pa + outlet_pa)))


def max_capacity_kg_per_s(
    *,
    inner_diameter_m: float,
    length_m: float,
    inlet_pressure_pa: float,
    outlet_pressure_pa: float,
    temperature_k: float,
    compressibility_factor: float,
    molecular_weight_kg_per_mol: float,
    fanning_friction_factor: float,
) -> float:
    """Steady-state dense-phase CO2 capacity using the dissertation equation form."""
    pressure_term = inlet_pressure_pa**2 - outlet_pressure_pa**2
    numerator = (
        math.pi**2
        * inner_diameter_m**5
        * molecular_weight_kg_per_mol
        * pressure_term
    )
    denominator = (
        64
        * fanning_friction_factor
        * compressibility_factor
        * UNIVERSAL_GAS_CONSTANT
        * temperature_k
        * length_m
    )
    return math.sqrt(numerator / denominator)


def reynolds_number(kg_per_s: float, viscosity_pa_s: float, inner_diameter_m: float) -> float:
    return 4 * kg_per_s / (math.pi * viscosity_pa_s * inner_diameter_m)


def evaluate_capacity(scenario: ScenarioAssumptions) -> ModuleResult:
    length_m = scenario.number("pipeline_length_km") * 1000
    inner_diameter_m = scenario.number("inner_diameter_in") * INCH_TO_M
    inlet_pa = scenario.number("inlet_pressure_psia") * PSI_TO_PA
    outlet_pa = scenario.number("outlet_pressure_psia") * PSI_TO_PA
    temperature_k = scenario.number("transport_temperature_c") + 273.15
    molecular_weight = scenario.number("molecular_weight_co2_g_per_mol") * G_PER_MOL_TO_KG_PER_MOL
    viscosity_pa_s = scenario.number("viscosity_micro_pa_s") * 1e-6

    capacity_kg_per_s = max_capacity_kg_per_s(
        inner_diameter_m=inner_diameter_m,
        length_m=length_m,
        inlet_pressure_pa=inlet_pa,
        outlet_pressure_pa=outlet_pa,
        temperature_k=temperature_k,
        compressibility_factor=scenario.number("compressibility_factor_z"),
        molecular_weight_kg_per_mol=molecular_weight,
        fanning_friction_factor=scenario.number("fanning_friction_factor"),
    )
    capacity_mtpa = kg_per_s_to_mtpa(capacity_kg_per_s)
    required_design_mtpa = scenario.number("required_project_flow_mtpa") / scenario.number(
        "capacity_factor"
    )
    average_pressure_mpa = average_pressure_pa(inlet_pa, outlet_pa) / 1e6
    reynolds = reynolds_number(capacity_kg_per_s, viscosity_pa_s, inner_diameter_m)
    reported_capacity = scenario.optional_number("reported_capacity_mtpa")
    capacity_delta = (
        capacity_mtpa - reported_capacity if reported_capacity is not None else None
    )
    capacity_suitable = "yes" if capacity_mtpa >= required_design_mtpa else "no"

    warnings = [
        WarningRecord(
            level="medium",
            message=(
                "CO2 properties are currently supplied by the benchmark assumptions; "
                "CoolProp/REFPROP validation is still required."
            ),
            affected_modules=["capacity"],
        )
    ]
    if capacity_delta is not None and abs(capacity_delta) > 0.1:
        warnings.append(
            WarningRecord(
                level="high",
                message="Calculated capacity differs from the reported benchmark by more than 0.1 MtCO2/year.",
                affected_modules=["capacity", "validation"],
            )
        )

    return ModuleResult(
        module="capacity",
        model_version=MODEL_VERSION,
        status="pass" if capacity_suitable == "yes" else "fail",
        inputs=scenario.input_records(
            [
                "pipeline_length_km",
                "inner_diameter_in",
                "inlet_pressure_psia",
                "outlet_pressure_psia",
                "transport_temperature_c",
                "molecular_weight_co2_g_per_mol",
                "compressibility_factor_z",
                "viscosity_micro_pa_s",
                "fanning_friction_factor",
                "required_project_flow_mtpa",
            ],
            used_by=["capacity"],
        ),
        assumptions=[
            scenario.assumption_record("capacity_factor", sensitivity_required=True),
        ],
        outputs=[
            OutputRecord("inner_diameter_m", inner_diameter_m, "m", used_by=["capacity"]),
            OutputRecord("average_pressure_mpa", average_pressure_mpa, "MPa", used_by=["capacity"]),
            OutputRecord("capacity_kg_per_s", capacity_kg_per_s, "kg/s", used_by=["pre_lca_gate"]),
            OutputRecord("capacity_mtpa", capacity_mtpa, "MtCO2/year", used_by=["pre_lca_gate"]),
            OutputRecord(
                "reported_capacity_mtpa",
                reported_capacity,
                "MtCO2/year",
                quality="reported",
                used_by=["validation"],
            ),
            OutputRecord("capacity_delta_mtpa", capacity_delta, "MtCO2/year", used_by=["validation"]),
            OutputRecord(
                "required_design_mtpa",
                required_design_mtpa,
                "MtCO2/year",
                used_by=["pre_lca_gate"],
            ),
            OutputRecord(
                "capacity_suitable",
                capacity_suitable,
                "yes/no",
                used_by=["pre_lca_gate"],
            ),
            OutputRecord("reynolds_number", reynolds, "dimensionless", used_by=["validation"]),
        ],
        warnings=warnings,
        trace=[
            TraceStep(
                name="average_pressure",
                formula="(2/3) * (P_in + P_out - P_in * P_out / (P_in + P_out))",
                inputs=["inlet_pressure_psia", "outlet_pressure_psia"],
                result_name="average_pressure_mpa",
            ),
            TraceStep(
                name="capacity",
                formula=(
                    "sqrt((pi^2 * D^5 * MW * (P_in^2 - P_out^2)) / "
                    "(64 * f * Z * R * T * L))"
                ),
                inputs=[
                    "inner_diameter_in",
                    "pipeline_length_km",
                    "inlet_pressure_psia",
                    "outlet_pressure_psia",
                    "transport_temperature_c",
                    "compressibility_factor_z",
                    "fanning_friction_factor",
                    "molecular_weight_co2_g_per_mol",
                ],
                result_name="capacity_mtpa",
                notes="This reproduces the dissertation/poster equation form.",
            ),
            TraceStep(
                name="required_design_flow",
                formula="required_project_flow_mtpa / capacity_factor",
                inputs=["required_project_flow_mtpa", "capacity_factor"],
                result_name="required_design_mtpa",
            ),
            TraceStep(
                name="reynolds_number",
                formula="4 * mass_flow / (pi * viscosity * inner_diameter)",
                inputs=["capacity_kg_per_s", "viscosity_micro_pa_s", "inner_diameter_m"],
                result_name="reynolds_number",
            ),
        ],
    )
