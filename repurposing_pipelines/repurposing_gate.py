"""Evidence-based repurposing gate for CO2 pipeline reuse screening.

This module turns the state-of-art review into executable screening logic.
It is deliberately conservative: it does not approve a pipeline for reuse.
It identifies whether the case is promising, what evidence is missing, and
what work-scope items should feed cost and LCA.

References used by this code are listed in ``CITED_REFERENCES`` and are also
emitted as model outputs. The short source IDs match ``references/literature_index.csv``.
"""

from __future__ import annotations

from .assumptions import ScenarioAssumptions
from .trace import AssumptionRecord, ModuleResult, OutputRecord, TraceStep, WarningRecord


MODEL_VERSION = "repurposing_gate_v0.1"

CO2_CRITICAL_PRESSURE_MPA = 7.3773
CO2_CRITICAL_TEMPERATURE_C = 31.1

CITED_REFERENCES = {
    "REF_OSTBY_TORBERGSEN_RONEID_LEINUM_2022_CO2_REQUALIFICATION": (
        "CO2 pipeline requalification needs design basis, integrity, hydraulics, "
        "safety, CO2 composition, reassessment, modifications and documentation."
    ),
    "REF_TORBERGSEN_LEINUM_RONEID_2025_GAS_PHASE_CO2_REQUALIFICATION": (
        "Gas-phase CO2 may be the realistic reuse route where dense-phase service "
        "is limited by pressure, fracture or documentation gaps."
    ),
    "REF_MONSMA_MURRAY_2026_GAS_PHASE_CO2_REPURPOSING": (
        "Repurposing should pass through initiation, screening, validation and "
        "execution gates before detailed cost or LCOT claims."
    ),
    "REF_KUMAR_LOWERY_PASSUCCI_2025_ENI_LIVERPOOL_BAY_IMR": (
        "Cleaning, drying, residual debris, ILI/MFL inspection and IMR planning "
        "are practical work-scope items for UK CCS pipeline reuse."
    ),
    "REF_YUSOF_AZIZ_2025_PETRONAS_DENSE_PHASE_CO2_REPURPOSING": (
        "Dense-phase CO2 reuse needs fracture-toughness evidence, blowdown checks, "
        "water-dropout checks and possible section replacement."
    ),
    "REF_DALONZO_BUSCO_ELVIRA_CHERUBINI_2025_CO2_IMR": (
        "Post-screening outputs should include baseline benchmark, fitness for "
        "purpose, inspection, maintenance and repair planning."
    ),
    "REF_BURKINSHAW_GALLON_CARVELL_HUSSAIN_2024_HYDROGEN_DATA_EVIDENCE": (
        "Repurposing evidence should distinguish primary records, secondary records, "
        "inspection evidence, assumptions and data gaps."
    ),
    "REF_KASS_ET_AL_2023_MATERIAL_COMPATIBILITY": (
        "Material and component compatibility should consider pipe steel, welds, "
        "valves, seals, coatings and equipment exposed to CO2 service."
    ),
}

WEAK_QUALITIES = {"assumed", "assumed_or_standard", "estimated", "missing"}
STRONG_QUALITIES = {"measured", "reported", "calculated", "derived"}
YES_VALUES = {"yes", "true", "1", "available", "screened", "verified"}
NO_VALUES = {"no", "false", "0", "missing", "not_available", "none"}
UNKNOWN_VALUES = {"", "unknown", "not_known", "unclear", "to_be_checked"}

CORE_EVIDENCE_WEIGHTS = {
    "pipeline_length_km": 6,
    "inner_diameter_in": 6,
    "nominal_wall_thickness_mm": 10,
    "minimum_wall_thickness_mm": 10,
    "pipe_grade": 6,
    "inlet_pressure_psia": 8,
    "outlet_pressure_psia": 8,
    "target_co2_phase": 6,
    "co2_water_content_ppmv": 8,
    "co2_water_spec_limit_ppmv": 8,
    "water_dew_point_margin_c": 8,
    "co2_composition_known": 8,
    "material_certificates_available": 10,
    "fracture_toughness_basis": 10,
    "ili_mfl_available": 10,
    "component_compatibility_screened": 8,
}

STATUS_EVIDENCE = {
    "co2_composition_known",
    "material_certificates_available",
    "ili_mfl_available",
    "component_compatibility_screened",
}


def _joined(items: list[str]) -> str:
    return "; ".join(dict.fromkeys(item for item in items if item))


def _output(result: ModuleResult | None, name: str, default=None):
    if result is None:
        return default
    return result.output_map().get(name, default)


def _normalise_text(value: object) -> str:
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def _status_value(scenario: ScenarioAssumptions, parameter: str) -> str:
    if parameter not in scenario.records:
        return "missing"
    value = _normalise_text(scenario.raw(parameter))
    if value in YES_VALUES:
        return "yes"
    if value in NO_VALUES:
        return "no"
    if value in UNKNOWN_VALUES:
        return "unknown"
    return value


def _optional_number(
    scenario: ScenarioAssumptions,
    parameter: str,
    default: float | None = None,
) -> float | None:
    value = scenario.optional_number(parameter)
    return default if value is None else value


def _phase_status(scenario: ScenarioAssumptions, capacity: ModuleResult | None) -> tuple[str, str]:
    target_phase = _normalise_text(scenario.raw("target_co2_phase")) if "target_co2_phase" in scenario.records else ""
    pressure_mpa = _output(capacity, "average_pressure_mpa")
    temperature_c = _optional_number(scenario, "transport_temperature_c")

    if target_phase in {"gas", "gas_phase", "gaseous"}:
        return "gas_phase_selected", "Target CO2 phase is stated as gas phase."
    if target_phase in {"dense", "dense_phase", "liquid", "supercritical"}:
        return "dense_phase_selected", "Target CO2 phase is stated as dense/liquid/supercritical."
    if pressure_mpa is None:
        return "unknown", "Target CO2 phase is not stated and average pressure is missing."

    if float(pressure_mpa) >= CO2_CRITICAL_PRESSURE_MPA:
        if temperature_c is not None and temperature_c > CO2_CRITICAL_TEMPERATURE_C:
            return (
                "supercritical_or_dense_screening",
                "Average pressure is above CO2 critical pressure and temperature is above critical temperature.",
            )
        return (
            "dense_or_liquid_screening",
            "Average pressure is above CO2 critical pressure, so dense-phase checks are required.",
        )
    return (
        "gas_phase_screening",
        "Average pressure is below CO2 critical pressure, so gas-phase screening is assumed.",
    )


def _evidence_score(scenario: ScenarioAssumptions) -> tuple[float, list[str]]:
    score = 100.0
    gaps: list[str] = []

    for parameter, weight in CORE_EVIDENCE_WEIGHTS.items():
        if parameter not in scenario.records:
            score -= weight
            gaps.append(f"{parameter} is missing")
            continue

        record = scenario.record(parameter)
        quality = _normalise_text(record.quality)
        if parameter in STATUS_EVIDENCE:
            status = _status_value(scenario, parameter)
            if status != "yes":
                score -= weight
                gaps.append(f"{parameter} is {status}")
            elif quality in WEAK_QUALITIES:
                score -= weight * 0.5
                gaps.append(f"{parameter} is yes but source quality is {record.quality}")
        elif quality in WEAK_QUALITIES:
            score -= weight * 0.75
            gaps.append(f"{parameter} quality is {record.quality}")
        elif quality not in STRONG_QUALITIES:
            score -= weight * 0.25
            gaps.append(f"{parameter} quality is {record.quality}")

    return max(0.0, round(score, 1)), gaps


def _work_scope(
    *,
    scenario: ScenarioAssumptions,
    phase_status: str,
    corrosion_risk: str,
    remaining_life_low: float | None,
) -> tuple[list[str], list[str], list[str]]:
    items: list[str] = []
    next_data: list[str] = []
    lca_items: list[str] = []

    def add(item: str, data: str, lca_item: str | None = None) -> None:
        items.append(item)
        next_data.append(data)
        if lca_item:
            lca_items.append(lca_item)

    if _status_value(scenario, "co2_composition_known") != "yes":
        add(
            "confirm_co2_composition_and_impurities",
            "CO2 composition and impurity specification",
            "CO2 specification review",
        )
    if (
        "co2_water_content_ppmv" not in scenario.records
        or "co2_water_spec_limit_ppmv" not in scenario.records
        or scenario.record("co2_water_content_ppmv").quality in WEAK_QUALITIES
        or scenario.record("co2_water_spec_limit_ppmv").quality in WEAK_QUALITIES
    ):
        add(
            "confirm_water_limit_and_dew_point",
            "water content, water limit and dew-point basis",
            "dew-point and water-specification study",
        )
    if corrosion_risk in {"medium", "high"}:
        add(
            "cleaning_drying_and_debris_assessment",
            "cleaning, drying and residual debris evidence",
            "cleaning and drying activity",
        )
    if _status_value(scenario, "ili_mfl_available") != "yes":
        add(
            "ili_mfl_or_equivalent_inspection",
            "latest ILI/MFL or equivalent inspection report",
            "inspection campaign",
        )
    if _status_value(scenario, "material_certificates_available") != "yes":
        add(
            "material_certificates_or_testing",
            "mill certificates or material testing plan",
            "material verification/testing",
        )
    if _status_value(scenario, "component_compatibility_screened") != "yes":
        add(
            "component_compatibility_review",
            "valve, seal, coating and equipment compatibility review",
            "component compatibility review",
        )
    if "dense" in phase_status or "supercritical" in phase_status:
        add(
            "fracture_and_decompression_screen",
            "fracture toughness, decompression and blowdown evidence",
            "fracture/decompression study",
        )
    if remaining_life_low is not None and remaining_life_low <= 0:
        add(
            "wall_thickness_verification",
            "verified wall thickness and minimum-wall basis",
            "targeted wall-thickness validation",
        )

    add(
        "co2_leak_detection_isolation_and_imr_plan",
        "CO2 leak detection, isolation philosophy and IMR plan",
        "IMR and monitoring plan",
    )
    return items, next_data, lca_items


def _recommended_refurbishment_fraction(
    *,
    scenario: ScenarioAssumptions,
    remaining_life_low: float | None,
    phase_status: str,
) -> float:
    """Return a screening placeholder for LCA until itemised quantities exist.

    This is not a DNV value and not a literature-derived universal factor. It is
    a transparent bridge so LCA can react to evidence gaps while detailed work
    quantities are still unknown.
    """
    base = _optional_number(scenario, "lca_refurbishment_steel_fraction", 0.05) or 0.05
    section_replacement = _optional_number(scenario, "section_replacement_fraction", 0.0) or 0.0
    uplift = 0.0
    if remaining_life_low is not None and remaining_life_low <= 0:
        uplift += 0.03
    if _status_value(scenario, "material_certificates_available") != "yes":
        uplift += 0.01
    if "dense" in phase_status or "supercritical" in phase_status:
        if _status_value(scenario, "fracture_toughness_basis") != "yes":
            uplift += 0.01
    return round(min(0.20, max(base, section_replacement + uplift)), 4)


def _reference_summary() -> str:
    return _joined(list(CITED_REFERENCES))


def evaluate_repurposing_gate(
    scenario: ScenarioAssumptions,
    *,
    capacity: ModuleResult | None = None,
    corrosion: ModuleResult | None = None,
    integrity: ModuleResult | None = None,
) -> ModuleResult:
    """Evaluate whether the pipeline is ready for reuse screening decisions.

    The gate follows the requalification themes cited in ``CITED_REFERENCES``:
    define the design basis, check CO2 phase/specification, assess current
    condition, identify missing evidence, and turn the gaps into work-scope
    items for cost and LCA.
    """
    evidence_score, evidence_gaps = _evidence_score(scenario)
    phase_status, phase_basis = _phase_status(scenario, capacity)
    corrosion_risk = str(_output(corrosion, "corrosion_risk_level", "not_assessed"))
    remaining_life_low = _output(integrity, "remaining_life_low_years")
    available_wall = _output(integrity, "available_wall_thickness_mm")
    capacity_status = capacity.status if capacity is not None else "missing"
    corrosion_status = corrosion.status if corrosion is not None else "missing"
    integrity_status = integrity.status if integrity is not None else "missing"

    showstoppers: list[str] = []
    if capacity_status == "missing":
        showstoppers.append("capacity result is missing")
    elif capacity_status == "fail":
        showstoppers.append("capacity module failed")
    if corrosion_status == "missing":
        showstoppers.append("corrosion result is missing")
    elif corrosion_status == "fail" or corrosion_risk == "high":
        showstoppers.append("corrosion screen is high risk")
    if integrity_status == "missing":
        showstoppers.append("integrity result is missing")
    elif integrity_status == "fail":
        showstoppers.append("integrity module failed")
    if available_wall is not None and float(available_wall) <= 0:
        showstoppers.append("available wall thickness is zero or negative")

    work_items, next_data, lca_items = _work_scope(
        scenario=scenario,
        phase_status=phase_status,
        corrosion_risk=corrosion_risk,
        remaining_life_low=None if remaining_life_low is None else float(remaining_life_low),
    )
    refurbishment_fraction = _recommended_refurbishment_fraction(
        scenario=scenario,
        remaining_life_low=None if remaining_life_low is None else float(remaining_life_low),
        phase_status=phase_status,
    )

    reasons = [phase_basis]
    if evidence_gaps:
        reasons.append(f"Evidence gaps remain: {_joined(evidence_gaps)}.")
    if work_items:
        reasons.append(f"Required work scope: {_joined(work_items)}.")
    if showstoppers:
        reasons.append(f"Showstoppers: {_joined(showstoppers)}.")

    if showstoppers:
        status = "fail"
        confidence = "medium" if evidence_score >= 50 else "low"
        summary = "Do not proceed until the showstoppers are resolved."
    elif evidence_score < 50:
        status = "marginal"
        confidence = "low"
        summary = "Promising only as a screening case, but important evidence is missing."
    elif work_items:
        status = "marginal"
        confidence = "medium"
        summary = "Technically promising, but validation work is needed before detailed LCA/cost."
    else:
        status = "pass"
        confidence = "high"
        summary = "Ready to move to detailed cost and LCA screening."

    warnings: list[WarningRecord] = [
        WarningRecord(
            level="medium",
            message=(
                "Repurposing gate is a screening/requalification checklist. It is not final "
                "engineering approval."
            ),
            affected_modules=["repurposing_gate", "cost", "lca", "final_gate"],
        )
    ]
    if evidence_gaps:
        warnings.append(
            WarningRecord(
                level="medium",
                message=f"Repurposing evidence gaps: {_joined(evidence_gaps)}.",
                affected_modules=["repurposing_gate", "validation"],
            )
        )
    if showstoppers:
        warnings.append(
            WarningRecord(
                level="high",
                message=f"Repurposing showstoppers: {_joined(showstoppers)}.",
                affected_modules=["repurposing_gate", "pre_lca_gate"],
            )
        )

    input_names = [name for name in CORE_EVIDENCE_WEIGHTS if name in scenario.records]
    assumptions: list[AssumptionRecord] = []
    for name in [
        "target_co2_phase",
        "co2_composition_known",
        "material_certificates_available",
        "fracture_toughness_basis",
        "ili_mfl_available",
        "component_compatibility_screened",
        "section_replacement_fraction",
    ]:
        if name in scenario.records:
            assumptions.append(scenario.assumption_record(name, sensitivity_required=True))

    return ModuleResult(
        module="repurposing_gate",
        model_version=MODEL_VERSION,
        status=status,
        inputs=scenario.input_records(input_names, used_by=["repurposing_gate"]),
        assumptions=assumptions,
        outputs=[
            OutputRecord(
                "repurposing_gate_status",
                status,
                "decision",
                used_by=["pre_lca_gate", "lca", "final_gate"],
            ),
            OutputRecord(
                "repurposing_gate_confidence",
                confidence,
                "quality",
                used_by=["pre_lca_gate", "final_gate"],
            ),
            OutputRecord(
                "repurposing_gate_reason_summary",
                summary,
                "text",
                used_by=["report", "app"],
            ),
            OutputRecord(
                "repurposing_gate_reasons",
                _joined(reasons),
                "text",
                used_by=["report", "app"],
            ),
            OutputRecord(
                "repurposing_gate_next_data",
                _joined(next_data),
                "text",
                used_by=["report", "app"],
            ),
            OutputRecord(
                "repurposing_phase_status",
                phase_status,
                "text",
                used_by=["capacity", "integrity", "cost", "lca"],
            ),
            OutputRecord(
                "repurposing_evidence_score",
                evidence_score,
                "0-100 score",
                used_by=["validation", "final_gate"],
            ),
            OutputRecord(
                "repurposing_evidence_gaps",
                _joined(evidence_gaps),
                "text",
                used_by=["validation", "report", "app"],
            ),
            OutputRecord(
                "repurposing_showstoppers",
                _joined(showstoppers),
                "text",
                used_by=["pre_lca_gate", "report", "app"],
            ),
            OutputRecord(
                "repurposing_work_scope_items",
                _joined(work_items),
                "text",
                used_by=["cost", "lca", "report", "app"],
            ),
            OutputRecord(
                "repurposing_cost_work_scope_items",
                _joined(work_items),
                "text",
                used_by=["cost"],
            ),
            OutputRecord(
                "repurposing_lca_work_scope_items",
                _joined(lca_items),
                "text",
                used_by=["lca"],
            ),
            OutputRecord(
                "lca_refurbishment_steel_fraction_recommended",
                refurbishment_fraction,
                "fraction",
                quality="screening_placeholder",
                used_by=["lca"],
                notes="Not a standard value; a transparent screening bridge until itemised quantities exist.",
            ),
            OutputRecord(
                "repurposing_gate_cited_references",
                _reference_summary(),
                "source_id_list",
                used_by=["report", "validation"],
            ),
        ],
        warnings=warnings,
        trace=[
            TraceStep(
                name="repurposing_phase_screen",
                formula=(
                    "use target_co2_phase when stated; otherwise compare average pressure "
                    "with CO2 critical pressure as a screening flag"
                ),
                inputs=["target_co2_phase", "average_pressure_mpa", "transport_temperature_c"],
                result_name="repurposing_phase_status",
                notes=(
                    "Screening logic only; detailed phase behaviour needs validated EOS/mixture modelling. "
                    "Cites REF_OSTBY_TORBERGSEN_RONEID_LEINUM_2022_CO2_REQUALIFICATION and "
                    "REF_TORBERGSEN_LEINUM_RONEID_2025_GAS_PHASE_CO2_REQUALIFICATION."
                ),
            ),
            TraceStep(
                name="repurposing_evidence_score",
                formula=(
                    "start at 100; subtract weighted penalties for missing, assumed, unknown "
                    "or weak requalification evidence"
                ),
                inputs=list(CORE_EVIDENCE_WEIGHTS),
                result_name="repurposing_evidence_score",
                notes=(
                    "Cites REF_BURKINSHAW_GALLON_CARVELL_HUSSAIN_2024_HYDROGEN_DATA_EVIDENCE "
                    "for data confidence discipline."
                ),
            ),
            TraceStep(
                name="repurposing_work_scope",
                formula=(
                    "convert evidence gaps and CO2-service risks into named work items "
                    "for cost and LCA"
                ),
                inputs=[
                    "co2_composition_known",
                    "co2_water_content_ppmv",
                    "co2_water_spec_limit_ppmv",
                    "ili_mfl_available",
                    "material_certificates_available",
                    "component_compatibility_screened",
                    "repurposing_phase_status",
                ],
                result_name="repurposing_work_scope_items",
                notes=(
                    "Cites REF_KUMAR_LOWERY_PASSUCCI_2025_ENI_LIVERPOOL_BAY_IMR, "
                    "REF_DALONZO_BUSCO_ELVIRA_CHERUBINI_2025_CO2_IMR, "
                    "REF_YUSOF_AZIZ_2025_PETRONAS_DENSE_PHASE_CO2_REPURPOSING and "
                    "REF_KASS_ET_AL_2023_MATERIAL_COMPATIBILITY."
                ),
            ),
        ],
    )
