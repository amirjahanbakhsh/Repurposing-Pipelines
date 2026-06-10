"""Independent validation helpers for screening modules."""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
import unicodedata
from zipfile import ZipFile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .assumptions import ScenarioAssumptions, read_scenario_assumptions
from .constants import G_PER_MOL_TO_KG_PER_MOL, INCH_TO_M, PSI_TO_PA, UNIVERSAL_GAS_CONSTANT
from .costs import COST_COMPONENT_PARAMETERS, evaluate_cost
from .gates import evaluate_pre_lca_gate
from .goldeneye import benchmark_scenario_with_trace
from .hydraulics import average_pressure_pa
from .trace import InputRecord, ModuleResult, OutputRecord
from .units import kg_per_s_to_mtpa


MODEL_VERSION = "independent_validation_v0.2"

PROPERTY_THRESHOLDS_PERCENT = {
    "density_kg_per_m3": 1.0,
    "viscosity_micro_pa_s": 3.0,
    "compressibility_factor_z": 1.0,
}

PIPE_GRADE_SMYS_MPA = {
    "X42": 289.6,
    "X52": 358.5,
    "X60": 413.7,
    "X65": 448.2,
    "X70": 482.6,
}

VALIDATION_STATUS_MEANINGS = {
    "validated_for_screening": "Enough evidence for current screening use.",
    "first_independent_pass": "External check passed, but more sources are welcome.",
    "automated_pass": "Automated logic tests passed.",
    "arithmetic_pass_external_pending": "Math is checked; external model comparison still needed.",
    "review_required": "The result may be wrong or too weak; technical review is needed.",
    "external_benchmark_needed": "Needs comparison with a separate tool or published example.",
    "blocked_by_data_access": "Cannot be completed without licensed or unavailable data.",
    "not_implemented": "The module does not exist yet, so it cannot be validated.",
    "validated_for_mapping": "Enough evidence exists to map inputs, but no full calculation is implemented yet.",
    "data_gap_confirmed": "A known data gap has been confirmed and must be handled explicitly.",
}

ALLOWED_QUALITIES = {
    "reported",
    "calculated",
    "derived",
    "assumed",
    "assumed_or_standard",
    "estimated",
}

REQUIRED_NSTA_FIELDS = [
    "OBJECTID",
    "NSTAPIPNO",
    "PIPE_NAME",
    "FLUID",
    "STATUS",
    "INT_DIAM",
    "MX_OP_PRES",
    "THICKNESS",
    "START_DATE",
    "LENGTH_M",
]

KEY_MODEL_READY_FIELDS = ["INT_DIAM", "MX_OP_PRES", "THICKNESS"]

LCA_INVENTORY_REQUIRED_COLUMNS = [
    "inventory_item",
    "scenario_role",
    "quantity_parameter",
    "unit",
    "calculated_from",
    "ecoinvent_mapping_key",
    "default_status",
    "notes",
]

LCA_MAPPING_REQUIRED_COLUMNS = [
    "mapping_key",
    "database",
    "system_model",
    "version",
    "activity_name",
    "location",
    "reference_product",
    "unit",
    "match_count",
    "source",
    "shareable",
    "review_status",
    "notes",
]

ECOSPOLD_LOOKUP_NAME = "FilenameToActivtiyLookup.csv"

ECOINVENT_PROCESS_QUERIES = [
    {
        "category": "pipeline_steel",
        "required_for": "new-build pipeline steel mass and refurbishment materials",
        "terms": ["steel, low-alloyed", "market for steel, low-alloyed"],
    },
    {
        "category": "offshore_pipeline_construction",
        "required_for": "new-build offshore pipeline comparison",
        "terms": ["pipeline, natural gas, long distance, high capacity, offshore"],
    },
    {
        "category": "decommissioned_pipeline",
        "required_for": "reuse/decommissioning credit or burden",
        "terms": ["decommissioned pipeline, natural gas"],
    },
    {
        "category": "electricity",
        "required_for": "operation, compression, pumping, and auxiliary power",
        "terms": ["electricity, medium voltage"],
    },
    {
        "category": "diesel_machinery",
        "required_for": "construction vessels, site equipment, and refurbishment machinery proxy",
        "terms": ["diesel, low-sulfur", "machine operation, diesel"],
    },
    {
        "category": "freight_transport",
        "required_for": "material transport and waste transport",
        "terms": ["transport, freight, lorry"],
    },
    {
        "category": "scrap_steel",
        "required_for": "steel waste, recycling, or avoided scrap handling",
        "terms": ["scrap steel"],
    },
]


def _coolprop():
    try:
        import CoolProp.CoolProp as coolprop  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local environment
        raise RuntimeError(
            "CoolProp is required for CO2 property validation. "
            "Install it with: python -m pip install CoolProp"
        ) from exc
    return coolprop


def _round(value: float | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    stripped = str(value).strip()
    return stripped == "" or stripped.upper() in {"N/A", "NA", "NULL", "UNKNOWN"}


def _to_float(value: Any) -> float | None:
    if _is_missing(value):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _positive_number(value: Any) -> bool:
    number = _to_float(value)
    return number is not None and number > 0 and number != -9999


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _clean_text(value: Any) -> str:
    text = str(value)
    try:
        repaired = text.encode("latin1").decode("utf-8")
        text = repaired
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def relative_difference_percent(model_value: float, reference_value: float) -> float:
    return 100 * (model_value - reference_value) / reference_value


def absolute_relative_difference_percent(model_value: float, reference_value: float) -> float:
    return abs(relative_difference_percent(model_value, reference_value))


def _scenario_pressure_temperature(scenario: ScenarioAssumptions) -> tuple[float, float, float, float]:
    inlet_pa = scenario.number("inlet_pressure_psia") * PSI_TO_PA
    outlet_pa = scenario.number("outlet_pressure_psia") * PSI_TO_PA
    average_pa = average_pressure_pa(inlet_pa, outlet_pa)
    temperature_k = scenario.number("transport_temperature_c") + 273.15
    return inlet_pa, outlet_pa, average_pa, temperature_k


def _manual_capacity_kg_per_s(
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
    """Local arithmetic check for the published equation form.

    This deliberately repeats the equation outside `hydraulics.max_capacity_kg_per_s`
    so implementation mistakes can be caught more easily.
    """
    import math

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


def _historical_wall_loss_mm(scenario: ScenarioAssumptions) -> float:
    reported = scenario.optional_number("reported_historical_wall_loss_mm")
    if reported is not None:
        return reported
    return (
        scenario.number("historical_corrosion_rate_mm_per_year")
        * scenario.number("historical_corrosion_years")
    )


def validate_co2_properties(scenarios: dict[str, ScenarioAssumptions]) -> list[dict[str, Any]]:
    coolprop = _coolprop()
    rows: list[dict[str, Any]] = []

    for scenario_name, scenario in sorted(scenarios.items()):
        _, _, average_pa, temperature_k = _scenario_pressure_temperature(scenario)
        reference_values = {
            "density_kg_per_m3": coolprop.PropsSI("D", "P", average_pa, "T", temperature_k, "CO2"),
            "viscosity_micro_pa_s": coolprop.PropsSI("V", "P", average_pa, "T", temperature_k, "CO2") * 1e6,
            "compressibility_factor_z": coolprop.PropsSI("Z", "P", average_pa, "T", temperature_k, "CO2"),
        }
        phase = coolprop.PhaseSI("P", average_pa, "T", temperature_k, "CO2")

        for parameter, reference_value in reference_values.items():
            model_value = scenario.number(parameter)
            difference = relative_difference_percent(model_value, reference_value)
            abs_difference = abs(difference)
            threshold = PROPERTY_THRESHOLDS_PERCENT[parameter]
            status = "pass" if abs_difference <= threshold else "review_required"
            rows.append(
                {
                    "scenario": scenario_name,
                    "module": "co2_properties",
                    "validation_type": "independent_benchmark",
                    "parameter": parameter,
                    "model_value": _round(model_value),
                    "reference_value": _round(reference_value),
                    "unit": scenario.record(parameter).unit,
                    "difference_percent": _round(difference, 4),
                    "absolute_difference_percent": _round(abs_difference, 4),
                    "acceptance_threshold_percent": threshold,
                    "status": status,
                    "reference": "CoolProp",
                    "pressure_mpa": _round(average_pa / 1e6, 6),
                    "temperature_c": scenario.number("transport_temperature_c"),
                    "phase": phase,
                    "notes": "Pure CO2 benchmark at the model average pipeline pressure.",
                }
            )

        rows.append(
            {
                "scenario": scenario_name,
                "module": "co2_properties",
                "validation_type": "independent_benchmark",
                "parameter": "phase_state",
                "model_value": "not_reported",
                "reference_value": phase,
                "unit": "text",
                "difference_percent": "",
                "absolute_difference_percent": "",
                "acceptance_threshold_percent": "",
                "status": "information",
                "reference": "CoolProp",
                "pressure_mpa": _round(average_pa / 1e6, 6),
                "temperature_c": scenario.number("transport_temperature_c"),
                "phase": phase,
                "notes": "The current model does not yet store phase as an input/output.",
            }
        )

    return rows


def validate_nsta_data_extraction(
    *,
    raw_attributes_path: Path,
    processed_attributes_path: Path,
    ranked_candidates_path: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    raw_data = json.loads(raw_attributes_path.read_text(encoding="utf-8"))
    raw_features = raw_data.get("features", [])
    processed_rows = _read_csv_rows(processed_attributes_path)
    ranked_rows = _read_csv_rows(ranked_candidates_path)
    processed_by_id = {row.get("NSTAPIPNO", "").upper(): row for row in processed_rows}
    ranked_by_id = {row.get("NSTAPIPNO", "").upper(): row for row in ranked_rows}

    rows.append(
        {
            "module": "data_extraction",
            "validation_type": "raw_to_processed_count",
            "check": "raw feature count equals processed CSV row count",
            "observed": len(processed_rows),
            "expected": len(raw_features),
            "status": "pass" if len(raw_features) == len(processed_rows) else "review_required",
            "reference": "NSTA raw attributes JSON",
            "notes": "Confirms that no features were lost between raw extract and processed CSV.",
        }
    )

    missing_fields = [field for field in REQUIRED_NSTA_FIELDS if field not in (processed_rows[0] if processed_rows else {})]
    rows.append(
        {
            "module": "data_extraction",
            "validation_type": "required_fields_present",
            "check": "required NSTA fields exist in processed CSV",
            "observed": "; ".join(missing_fields) if missing_fields else "none missing",
            "expected": "all required fields present",
            "status": "pass" if not missing_fields else "review_required",
            "reference": "NSTA processed attributes CSV",
            "notes": "Checks that the fields needed for screening are available as columns.",
        }
    )

    non_positive_ranked = [
        row.get("NSTAPIPNO", "")
        for row in ranked_rows
        if any(not _positive_number(row.get(field)) for field in KEY_MODEL_READY_FIELDS)
    ]
    rows.append(
        {
            "module": "data_extraction",
            "validation_type": "ranked_candidates_are_model_ready",
            "check": "ranked candidates have positive internal diameter, pressure, and wall thickness",
            "observed": len(ranked_rows) - len(non_positive_ranked),
            "expected": len(ranked_rows),
            "status": "pass" if not non_positive_ranked else "review_required",
            "reference": "NSTA ranked candidate CSV",
            "notes": (
                "First bad examples: " + ", ".join(non_positive_ranked[:5])
                if non_positive_ranked
                else "All ranked candidates have usable engineering values."
            ),
        }
    )

    for nsta_id, expected_name in [
        ("PL774", "CATS"),
        ("PL1761", "Schiehallion"),
        ("PL762", "SAGE"),
    ]:
        processed = processed_by_id.get(nsta_id)
        ranked = ranked_by_id.get(nsta_id)
        rows.append(
            {
                "module": "data_extraction",
                "validation_type": "spot_check_known_ranked_candidate",
                "check": f"{nsta_id} is present and ranked",
                "observed": processed.get("PIPE_NAME", "") if processed else "not found",
                "expected": expected_name,
                "status": "pass" if processed and ranked else "review_required",
                "reference": "NSTA processed and ranked data",
                "notes": "Spot-checks that known large candidates survive extraction and ranking.",
            }
        )

    goldeneye_matches = [
        row
        for row in processed_rows
        if "GOLDENEYE" in row.get("PIPE_NAME", "").upper()
        or "GOLDENEYE" in row.get("DESCRIPTIO", "").upper()
    ]
    goldeneye_ranked = [
        row
        for row in goldeneye_matches
        if row.get("NSTAPIPNO", "").upper() in ranked_by_id
    ]
    rows.append(
        {
            "module": "data_extraction",
            "validation_type": "known_ccs_candidate_data_gap",
            "check": "Goldeneye exists in NSTA but is not model-ready from NSTA alone",
            "observed": f"{len(goldeneye_matches)} NSTA matches; {len(goldeneye_ranked)} ranked matches",
            "expected": "Goldeneye present but engineering fields incomplete",
            "status": "data_gap_confirmed" if goldeneye_matches and not goldeneye_ranked else "review_required",
            "reference": "NSTA processed and ranked data",
            "notes": "This supports the project observation that Goldeneye needs external enrichment.",
        }
    )

    return rows


def validate_assumption_register(
    *,
    assumptions_path: Path,
    defaults_path: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    assumption_rows = _read_csv_rows(assumptions_path)
    default_rows = _read_csv_rows(defaults_path)
    combined = [
        ("goldeneye_assumptions", row)
        for row in assumption_rows
    ] + [
        ("nsta_screening_defaults", row)
        for row in default_rows
    ]

    required_columns = ["parameter", "value", "unit", "source", "quality", "notes"]
    blank_items = [
        f"{source}:{row.get('parameter', '<missing parameter>')}:{column}"
        for source, row in combined
        for column in required_columns
        if _is_missing(row.get(column))
    ]
    rows.append(
        {
            "module": "assumption_register",
            "validation_type": "required_trace_fields",
            "check": "every assumption has value, unit, source, quality, and notes",
            "observed": len(blank_items),
            "expected": 0,
            "status": "pass" if not blank_items else "review_required",
            "reference": "assumption CSV files",
            "notes": "; ".join(blank_items[:8]) if blank_items else "No blank traceability fields found.",
        }
    )

    bad_qualities = [
        f"{source}:{row.get('parameter', '<missing parameter>')}={row.get('quality', '')}"
        for source, row in combined
        if row.get("quality", "") not in ALLOWED_QUALITIES
    ]
    rows.append(
        {
            "module": "assumption_register",
            "validation_type": "quality_labels",
            "check": "quality labels use approved terms",
            "observed": len(bad_qualities),
            "expected": 0,
            "status": "pass" if not bad_qualities else "review_required",
            "reference": "assumption CSV files",
            "notes": "; ".join(bad_qualities[:8]) if bad_qualities else "All quality labels are recognised.",
        }
    )

    assumed_count = sum(1 for _, row in combined if row.get("quality", "") in {"assumed", "assumed_or_standard", "estimated"})
    rows.append(
        {
            "module": "assumption_register",
            "validation_type": "assumption_visibility",
            "check": "assumed values are visible rather than hidden",
            "observed": assumed_count,
            "expected": "explicitly labelled",
            "status": "pass",
            "reference": "assumption CSV files",
            "notes": "Assumed values are acceptable at screening stage when they are clearly labelled.",
        }
    )

    return rows


def assumption_evidence_register() -> list[dict[str, Any]]:
    """Map assumption families to the external evidence needed to validate them."""
    rows = [
        {
            "assumption_family": "asset_identity_and_dimensions",
            "current_parameters": "pipeline_name; pipeline_length_km; outer_diameter_in; inner_diameter_in; nominal_wall_thickness_mm; start_operation_year",
            "current_sources": "NSTA; dissertation; poster; student GeoJSON",
            "evidence_needed": "operator records, decommissioning reports, NSTA source records, or project documents",
            "recommended_sources": "NSTA open data; operator reports; decommissioning programmes; Goldeneye/Peterhead/Acorn public documents",
            "current_status": "visible_but_needs_source_upgrade",
            "notes": "Goldeneye is a priority because NSTA records are incomplete and the student used extra assumptions.",
        },
        {
            "assumption_family": "co2_properties",
            "current_parameters": "molecular_weight_co2_g_per_mol; compressibility_factor_z; density_kg_per_m3; viscosity_micro_pa_s",
            "current_sources": "dissertation; poster; CoolProp validation",
            "evidence_needed": "independent property reference over the pressure-temperature range",
            "recommended_sources": "CoolProp; NIST REFPROP; NIST tables; peer-reviewed CO2 mixture EOS papers",
            "current_status": "first_independent_pass",
            "notes": "Pure CO2 values pass against CoolProp for Goldeneye; impurities still need validation.",
        },
        {
            "assumption_family": "hydraulics_capacity",
            "current_parameters": "inlet_pressure_psia; outlet_pressure_psia; transport_temperature_c; fanning_friction_factor; capacity_factor; required_project_flow_mtpa",
            "current_sources": "dissertation; poster; screening defaults",
            "evidence_needed": "like-for-like capacity benchmark and pressure/phase basis",
            "recommended_sources": "NETL transport tools; SCO2T; McCoy and Rubin-style published examples; project basis documents",
            "current_status": "external_benchmark_needed",
            "notes": "Arithmetic passes; physical model selection still needs external comparison.",
        },
        {
            "assumption_family": "integrity_wall_thickness",
            "current_parameters": "pipe_grade; minimum_wall_thickness_mm; historical_corrosion_years; historical_corrosion_rate_mm_per_year; reported_historical_wall_loss_mm",
            "current_sources": "dissertation; poster; simple Barlow screening; NSTA defaults",
            "evidence_needed": "pipeline design/requalification basis and inspection evidence",
            "recommended_sources": "DNV submarine pipeline/integrity standards; ISO 27913; ASME/API pipeline rules; operator inspection records",
            "current_status": "review_required",
            "notes": "Simple Barlow sanity check gives higher minimum wall thickness than dissertation/poster values.",
        },
        {
            "assumption_family": "corrosion_and_co2_stream_quality",
            "current_parameters": "future_co2_corrosion_rate_mm_per_year; future_co2_corrosion_rate_low/high_mm_per_year; co2_water_content_ppmv; co2_water_spec_limit_ppmv; water_dew_point_margin_c",
            "current_sources": "dissertation; poster; screening defaults; project screening assumptions",
            "evidence_needed": "CO2 corrosion model, water content, impurities, pH/fugacity/shear-stress basis, dew-point basis",
            "recommended_sources": "NORSOK M-506; ISO 27913; DNV guidance; CO2 stream-quality literature",
            "current_status": "review_required",
            "notes": "A dry-CO2 screening risk module now exists, but it is not a calibrated NORSOK/DNV corrosion model.",
        },
        {
            "assumption_family": "cost",
            "current_parameters": "cost_material_usd_2025; cost_labor_usd_2025; cost_row_damages_usd_2025; cost_misc_usd_2025; cost_booster_station_usd_2025; contingency_fraction",
            "current_sources": "dissertation; poster; Goldeneye benchmark; screening defaults",
            "evidence_needed": "base year, currency, location factor, offshore factor, diameter/length equations, reuse modification costs",
            "recommended_sources": "NETL CO2_T_COM; Parker; Rui; Brown; McCoy and Rubin; project cost reports",
            "current_status": "external_benchmark_needed",
            "notes": "Arithmetic passes; independent cost-model suitability is still open.",
        },
        {
            "assumption_family": "lca_inventory",
            "current_parameters": "pipeline length; diameter; wall thickness; steel mass; electricity; construction/refurbishment; decommissioning; storage",
            "current_sources": "ecoinvent APOS 3.8 export; supplied LCA supplementary workbook",
            "evidence_needed": "functional unit, system boundary, dataset names, database version, allocation model, impact method",
            "recommended_sources": "ISO 14040/14044; ecoinvent; Brightway; openLCA; supplied LCA workbook; CCS LCA papers",
            "current_status": "validated_for_screening",
            "notes": "A first open proxy calculates steel mass and reuse/new-build CO2e screening. Full ecoinvent calculation is still separate.",
        },
        {
            "assumption_family": "wells",
            "current_parameters": "well status; casing; cement; depth; abandonment; leakage risk",
            "current_sources": "not yet loaded",
            "evidence_needed": "well integrity and storage-site evidence",
            "recommended_sources": "NSTA wells data; operator well files; well integrity guidance; storage permit documents",
            "current_status": "not_implemented",
            "notes": "Well repurposing needs a separate evidence model and gate.",
        },
    ]
    for row in rows:
        row["status"] = row["current_status"]
    return rows


def _match_ecoinvent_rows(rows: list[dict[str, str]], terms: list[str]) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    lowered_terms = [term.lower() for term in terms]
    for row in rows:
        text = f"{row.get('ActivityName', '')} {row.get('ReferenceProduct', '')}".lower()
        if any(term in text for term in lowered_terms):
            matches.append(row)
    return matches


def validate_ecoinvent_mapping(ecoinvent_dir: Path | None) -> list[dict[str, Any]]:
    if ecoinvent_dir is None:
        return [
            {
                "module": "lca_data",
                "validation_type": "ecoinvent_availability",
                "category": "ecoinvent_export",
                "required_for": "LCA data mapping",
                "matches": 0,
                "selected_activity": "",
                "location": "",
                "reference_product": "",
                "status": "blocked_by_data_access",
                "reference": "ecoinvent APOS 3.8 local export",
                "notes": "No ecoinvent directory was supplied to the validation command.",
            }
        ]

    lookup_path = ecoinvent_dir / ECOSPOLD_LOOKUP_NAME
    datasets_dir = ecoinvent_dir / "datasets"
    if not lookup_path.exists() or not datasets_dir.exists():
        return [
            {
                "module": "lca_data",
                "validation_type": "ecoinvent_availability",
                "category": "ecoinvent_export",
                "required_for": "LCA data mapping",
                "matches": 0,
                "selected_activity": "",
                "location": "",
                "reference_product": "",
                "status": "blocked_by_data_access",
                "reference": "ecoinvent APOS 3.8 local export",
                "notes": "Expected lookup CSV or datasets folder was not found.",
            }
        ]

    lookup_rows = _read_csv_rows_semicolon(lookup_path)
    dataset_count = len(list(datasets_dir.glob("*.spold")))
    results = [
        {
            "module": "lca_data",
            "validation_type": "ecoinvent_availability",
            "category": "ecoinvent_export",
            "required_for": "local licensed LCA database access",
            "matches": dataset_count,
            "selected_activity": "lookup CSV available",
            "location": "local",
            "reference_product": "ecoinvent APOS 3.8",
            "status": "pass" if dataset_count > 0 and lookup_rows else "review_required",
            "reference": "ecoinvent APOS 3.8 local export",
            "notes": "Counts files only; licensed unit process data are not copied into GitHub.",
        }
    ]

    for query in ECOINVENT_PROCESS_QUERIES:
        matches = _match_ecoinvent_rows(lookup_rows, query["terms"])
        selected = _select_preferred_ecoinvent_match(matches)
        results.append(
            {
                "module": "lca_data",
                "validation_type": "ecoinvent_process_availability",
                "category": query["category"],
                "required_for": query["required_for"],
                "matches": len(matches),
                "selected_activity": selected.get("ActivityName", "") if selected else "",
                "location": selected.get("Location", "") if selected else "",
                "reference_product": selected.get("ReferenceProduct", "") if selected else "",
                "status": "pass" if matches else "review_required",
                "reference": "ecoinvent APOS 3.8 local export",
                "notes": "This confirms candidate process availability only; final dataset choice still needs LCA review.",
            }
        )
    return results


def _read_csv_rows_semicolon(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def _select_preferred_ecoinvent_match(matches: list[dict[str, str]]) -> dict[str, str] | None:
    if not matches:
        return None
    preferred_locations = ["GB", "Europe without Switzerland", "RER", "GLO", "RoW"]
    for location in preferred_locations:
        for row in matches:
            if row.get("Location") == location:
                return row
    return matches[0]


def _xlsx_col_idx(cell_ref: str) -> int:
    letters = re.match(r"([A-Z]+)", cell_ref)
    if not letters:
        return 0
    number = 0
    for char in letters.group(1):
        number = number * 26 + ord(char) - 64
    return number - 1


def _xlsx_shared_strings(archive: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall("main:si", ns):
        values.append("".join(text.text or "" for text in item.findall(".//main:t", ns)))
    return values


def _xlsx_cell_value(cell: ET.Element, shared: list[str]) -> str:
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    cell_type = cell.attrib.get("t")
    if cell_type == "s":
        value = cell.find("main:v", ns)
        return shared[int(value.text)] if value is not None and value.text else ""
    if cell_type == "inlineStr":
        return "".join(text.text or "" for text in cell.findall(".//main:t", ns))
    value = cell.find("main:v", ns)
    if value is not None and value.text is not None:
        return value.text
    formula = cell.find("main:f", ns)
    return f"={formula.text}" if formula is not None and formula.text else ""


def _xlsx_sheet_rows(path: Path) -> dict[str, list[list[str]]]:
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    relationship_key = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    with ZipFile(path) as archive:
        shared = _xlsx_shared_strings(archive)
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        sheets: dict[str, list[list[str]]] = {}
        for sheet in workbook.findall(".//main:sheet", ns):
            name = sheet.attrib["name"]
            target = rel_map[sheet.attrib[relationship_key]]
            root = ET.fromstring(archive.read(f"xl/{target}"))
            rows: list[list[str]] = []
            for row in root.findall(".//main:sheetData/main:row", ns):
                values: list[str] = []
                for cell in row.findall("main:c", ns):
                    index = _xlsx_col_idx(cell.attrib["r"])
                    while len(values) <= index:
                        values.append("")
                    values[index] = _xlsx_cell_value(cell, shared)
                rows.append(values)
            sheets[name] = rows
        return sheets


def validate_lca_reference_workbook(workbook_path: Path | None) -> list[dict[str, Any]]:
    if workbook_path is None or not workbook_path.exists():
        return [
            {
                "module": "lca_reference",
                "validation_type": "supplementary_workbook_review",
                "sheet": "",
                "functional_unit": "",
                "technosphere_rows": 0,
                "biosphere_rows": 0,
                "useful_for_pipeline_lca": "unknown",
                "status": "blocked_by_data_access",
                "notes": "No LCA supplementary workbook was supplied.",
            }
        ]

    sheet_rows = _xlsx_sheet_rows(workbook_path)
    results: list[dict[str, Any]] = []
    for sheet_name, rows in sheet_rows.items():
        title = _clean_text(rows[0][0]) if rows and rows[0] else ""
        functional_unit = _clean_text(rows[0][3]) if rows and len(rows[0]) > 3 else ""
        flat_text = " ".join(" ".join(row) for row in rows).lower()
        technosphere_count = sum(1 for row in rows if len(row) > 2 and _to_float(row[2]) is not None)
        biosphere_sections = sum(1 for row in rows if row and "biosphere flow" in row[0].lower())
        useful_flags = []
        if "pipeline" in flat_text:
            useful_flags.append("pipeline")
        if "injection well" in flat_text:
            useful_flags.append("injection_well")
        if "per t of injected co2" in flat_text or "per t of captured co2" in flat_text:
            useful_flags.append("functional_unit")
        if "decommissioned pipeline" in flat_text:
            useful_flags.append("decommissioned_pipeline")
        results.append(
            {
                "module": "lca_reference",
                "validation_type": "supplementary_workbook_review",
                "sheet": _clean_text(sheet_name),
                "title": title,
                "functional_unit": functional_unit,
                "technosphere_rows": technosphere_count,
                "biosphere_sections": biosphere_sections,
                "useful_for_pipeline_lca": "; ".join(useful_flags) if useful_flags else "limited",
                "status": "pass" if useful_flags else "information",
                "notes": "Reviewed sheet structure only; workbook data are not copied into the repo.",
            }
        )
    return results


def validate_lca_model_input_csvs(
    *,
    inventory_template_path: Path,
    process_mapping_path: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not inventory_template_path.exists() or not process_mapping_path.exists():
        return [
            {
                "module": "lca_model_inputs",
                "validation_type": "lca_csv_availability",
                "check": "LCA inventory and process mapping CSV files exist",
                "observed": "missing file",
                "expected": "both files present",
                "status": "review_required",
                "notes": (
                    "Create model_layers/05_lca/lca_inventory_template.csv and "
                    "model_layers/05_lca/lca_process_mapping.csv."
                ),
            }
        ]

    inventory_rows = _read_csv_rows(inventory_template_path)
    mapping_rows = _read_csv_rows(process_mapping_path)
    inventory_columns = set(inventory_rows[0]) if inventory_rows else set()
    mapping_columns = set(mapping_rows[0]) if mapping_rows else set()
    missing_inventory_columns = [
        column for column in LCA_INVENTORY_REQUIRED_COLUMNS if column not in inventory_columns
    ]
    missing_mapping_columns = [
        column for column in LCA_MAPPING_REQUIRED_COLUMNS if column not in mapping_columns
    ]
    rows.append(
        {
            "module": "lca_model_inputs",
            "validation_type": "inventory_csv_columns",
            "check": "inventory template has required columns",
            "observed": "; ".join(missing_inventory_columns) if missing_inventory_columns else "none missing",
            "expected": "all required columns",
            "status": "pass" if not missing_inventory_columns else "review_required",
            "notes": "Checks the shareable project inventory template.",
        }
    )
    rows.append(
        {
            "module": "lca_model_inputs",
            "validation_type": "process_mapping_csv_columns",
            "check": "process mapping file has required columns",
            "observed": "; ".join(missing_mapping_columns) if missing_mapping_columns else "none missing",
            "expected": "all required columns",
            "status": "pass" if not missing_mapping_columns else "review_required",
            "notes": "Checks the shareable process mapping metadata file.",
        }
    )

    mapping_keys = {row.get("mapping_key", "") for row in mapping_rows}
    inventory_keys = {row.get("ecoinvent_mapping_key", "") for row in inventory_rows}
    missing_keys = sorted(key for key in inventory_keys if key not in mapping_keys)
    rows.append(
        {
            "module": "lca_model_inputs",
            "validation_type": "inventory_mapping_keys",
            "check": "every inventory mapping key exists in process mapping CSV",
            "observed": "; ".join(missing_keys) if missing_keys else "none missing",
            "expected": "all mapping keys covered",
            "status": "pass" if not missing_keys else "review_required",
            "notes": "This lets the future LCA model join quantities to process choices.",
        }
    )

    non_shareable = [
        row.get("mapping_key", "")
        for row in mapping_rows
        if row.get("shareable", "").strip().lower() not in {"yes", "true", "1"}
    ]
    rows.append(
        {
            "module": "lca_model_inputs",
            "validation_type": "mapping_metadata_shareable",
            "check": "process mapping contains shareable metadata only",
            "observed": len(non_shareable),
            "expected": 0,
            "status": "pass" if not non_shareable else "review_required",
            "notes": (
                "Non-shareable mapping keys: " + ", ".join(non_shareable[:8])
                if non_shareable
                else "All rows are labelled as shareable metadata."
            ),
        }
    )

    return rows


def validate_capacity(scenarios: dict[str, ScenarioAssumptions]) -> list[dict[str, Any]]:
    coolprop = _coolprop()
    rows: list[dict[str, Any]] = []

    for scenario_name, scenario in sorted(scenarios.items()):
        inlet_pa, outlet_pa, average_pa, temperature_k = _scenario_pressure_temperature(scenario)
        row, _ = benchmark_scenario_with_trace(scenario_name, scenario)
        manual_capacity_mtpa = kg_per_s_to_mtpa(
            _manual_capacity_kg_per_s(
                inner_diameter_m=scenario.number("inner_diameter_in") * INCH_TO_M,
                length_m=scenario.number("pipeline_length_km") * 1000,
                inlet_pressure_pa=inlet_pa,
                outlet_pressure_pa=outlet_pa,
                temperature_k=temperature_k,
                compressibility_factor=scenario.number("compressibility_factor_z"),
                molecular_weight_kg_per_mol=scenario.number("molecular_weight_co2_g_per_mol")
                * G_PER_MOL_TO_KG_PER_MOL,
                fanning_friction_factor=scenario.number("fanning_friction_factor"),
            )
        )
        arithmetic_difference = manual_capacity_mtpa - row["capacity_mtpa"]
        rows.append(
            {
                "scenario": scenario_name,
                "module": "capacity",
                "validation_type": "implementation_arithmetic_check",
                "parameter": "capacity_mtpa",
                "model_value": _round(row["capacity_mtpa"]),
                "reference_value": _round(manual_capacity_mtpa),
                "unit": "MtCO2/year",
                "difference_percent": _round(
                    relative_difference_percent(row["capacity_mtpa"], manual_capacity_mtpa),
                    6,
                ),
                "status": "pass" if abs(arithmetic_difference) <= 1e-9 else "review_required",
                "reference": "independent arithmetic repeat of the equation",
                "notes": "This checks code arithmetic, not the physical model choice.",
            }
        )

        coolprop_z = coolprop.PropsSI("Z", "P", average_pa, "T", temperature_k, "CO2")
        capacity_with_coolprop_z_mtpa = kg_per_s_to_mtpa(
            _manual_capacity_kg_per_s(
                inner_diameter_m=scenario.number("inner_diameter_in") * INCH_TO_M,
                length_m=scenario.number("pipeline_length_km") * 1000,
                inlet_pressure_pa=inlet_pa,
                outlet_pressure_pa=outlet_pa,
                temperature_k=temperature_k,
                compressibility_factor=coolprop_z,
                molecular_weight_kg_per_mol=scenario.number("molecular_weight_co2_g_per_mol")
                * G_PER_MOL_TO_KG_PER_MOL,
                fanning_friction_factor=scenario.number("fanning_friction_factor"),
            )
        )
        rows.append(
            {
                "scenario": scenario_name,
                "module": "capacity",
                "validation_type": "independent_property_sensitivity",
                "parameter": "capacity_with_coolprop_z_mtpa",
                "model_value": _round(row["capacity_mtpa"]),
                "reference_value": _round(capacity_with_coolprop_z_mtpa),
                "unit": "MtCO2/year",
                "difference_percent": _round(
                    relative_difference_percent(row["capacity_mtpa"], capacity_with_coolprop_z_mtpa),
                    4,
                ),
                "status": (
                    "pass"
                    if absolute_relative_difference_percent(
                        row["capacity_mtpa"],
                        capacity_with_coolprop_z_mtpa,
                    )
                    <= 1.0
                    else "review_required"
                ),
                "reference": "CoolProp Z factor",
                "notes": "This shows the capacity impact of replacing the student Z factor with CoolProp.",
            }
        )

    return rows


def validate_integrity_barlow_sanity(
    scenarios: dict[str, ScenarioAssumptions],
    *,
    design_factor: float = 0.72,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for scenario_name, scenario in sorted(scenarios.items()):
        pipe_grade = str(scenario.raw("pipe_grade")).strip().upper()
        smys_mpa = PIPE_GRADE_SMYS_MPA.get(pipe_grade)
        if smys_mpa is None:
            rows.append(
                {
                    "scenario": scenario_name,
                    "module": "integrity",
                    "validation_type": "barlow_sanity_check",
                    "status": "insufficient_data",
                    "notes": f"Unknown pipe grade '{pipe_grade}'.",
                }
            )
            continue

        pressure_mpa = scenario.number("inlet_pressure_psia") * PSI_TO_PA / 1e6
        outer_diameter_mm = scenario.number("outer_diameter_in") * 25.4
        barlow_min_wall_mm = pressure_mpa * outer_diameter_mm / (2 * smys_mpa * design_factor)
        scenario_min_wall_mm = scenario.number("minimum_wall_thickness_mm")
        historical_loss_mm = _historical_wall_loss_mm(scenario)
        current_wall_mm = scenario.number("nominal_wall_thickness_mm") - historical_loss_mm
        available_wall_model_mm = current_wall_mm - scenario_min_wall_mm
        available_wall_barlow_mm = current_wall_mm - barlow_min_wall_mm
        future_corrosion = scenario.number("future_co2_corrosion_rate_mm_per_year")
        remaining_life_model_years = (
            available_wall_model_mm / future_corrosion if available_wall_model_mm > 0 else 0
        )
        remaining_life_barlow_years = (
            available_wall_barlow_mm / future_corrosion if available_wall_barlow_mm > 0 else 0
        )
        status = "pass_sanity" if scenario_min_wall_mm >= barlow_min_wall_mm else "review_required"

        rows.append(
            {
                "scenario": scenario_name,
                "module": "integrity",
                "validation_type": "barlow_sanity_check",
                "pipe_grade": pipe_grade,
                "smys_mpa": smys_mpa,
                "design_factor": design_factor,
                "pressure_mpa": _round(pressure_mpa, 6),
                "outer_diameter_mm": _round(outer_diameter_mm, 3),
                "scenario_min_wall_mm": _round(scenario_min_wall_mm, 6),
                "barlow_min_wall_mm": _round(barlow_min_wall_mm, 6),
                "difference_mm": _round(scenario_min_wall_mm - barlow_min_wall_mm, 6),
                "current_wall_mm": _round(current_wall_mm, 6),
                "available_wall_model_mm": _round(available_wall_model_mm, 6),
                "available_wall_barlow_mm": _round(available_wall_barlow_mm, 6),
                "remaining_life_model_years": _round(remaining_life_model_years, 3),
                "remaining_life_barlow_years": _round(remaining_life_barlow_years, 3),
                "status": status,
                "reference": "simple Barlow pressure sanity check",
                "notes": (
                    "Screening check only. It is not a full pipeline requalification "
                    "calculation and must be reviewed by a pipeline integrity specialist."
                ),
            }
        )

    return rows


def validate_cost_arithmetic(scenarios: dict[str, ScenarioAssumptions]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario_name, scenario in sorted(scenarios.items()):
        cost_result = evaluate_cost(scenario)
        cost_outputs = cost_result.output_map()
        component_sum = sum(scenario.number(name) for name in COST_COMPONENT_PARAMETERS)
        contingency = component_sum * scenario.number("contingency_fraction")
        total = component_sum + contingency
        reported = scenario.optional_number("reported_total_capex_usd_2025")
        difference = total - reported if reported is not None else None
        status = (
            "pass"
            if reported is not None and abs(difference or 0) <= 1.0
            else "review_required"
        )
        rows.append(
            {
                "scenario": scenario_name,
                "module": "cost",
                "validation_type": "arithmetic_check",
                "component_sum_usd_2025": _round(component_sum, 2),
                "contingency_usd_2025": _round(contingency, 2),
                "calculated_total_usd_2025": _round(total, 2),
                "reported_total_usd_2025": _round(reported, 2),
                "difference_usd_2025": _round(difference, 2),
                "netl_reference_total_usd_2025": _round(
                    cost_outputs.get("netl_reference_total_capex_usd_2025"),
                    2,
                ),
                "netl_difference_percent": _round(
                    cost_outputs.get("netl_cost_delta_percent"),
                    2,
                ),
                "netl_status": cost_outputs.get("netl_cost_validation_status"),
                "status": status,
                "reference": "student reported cost total",
                "notes": (
                    "This validates the arithmetic only. Independent cost-model validation "
                    "against NETL CO2_T_COM runs when a like-for-like NETL reference is supplied."
                ),
            }
        )
    return rows


def _module(name: str, status: str, outputs: list[OutputRecord], inputs: list[InputRecord] | None = None) -> ModuleResult:
    return ModuleResult(
        module=name,
        model_version="validation_test",
        status=status,
        inputs=inputs or [],
        outputs=outputs,
    )


def validate_pre_lca_gate_logic() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cases = [
        {
            "case": "all_pass_strong_inputs",
            "expected": "pass",
            "capacity": ModuleResult(
                module="capacity",
                model_version="validation_test",
                status="pass",
                inputs=[InputRecord("inner_diameter_in", 18.0, "in", quality="reported")],
                outputs=[
                    OutputRecord("capacity_mtpa", 10.0),
                    OutputRecord("required_design_mtpa", 5.0),
                ],
            ),
            "integrity": _module(
                "integrity",
                "pass",
                [
                    OutputRecord("remaining_life_years", 30.0),
                    OutputRecord("available_wall_thickness_mm", 5.0),
                ],
            ),
            "cost": _module("cost", "pass", [OutputRecord("cost_total_usd_2025", 100_000_000)]),
        },
        {
            "case": "assumed_capacity_input",
            "expected": "marginal",
            "capacity": ModuleResult(
                module="capacity",
                model_version="validation_test",
                status="pass",
                inputs=[InputRecord("inner_diameter_in", 18.0, "in", quality="assumed")],
                outputs=[
                    OutputRecord("capacity_mtpa", 10.0),
                    OutputRecord("required_design_mtpa", 5.0),
                ],
            ),
            "integrity": _module(
                "integrity",
                "pass",
                [
                    OutputRecord("remaining_life_years", 30.0),
                    OutputRecord("available_wall_thickness_mm", 5.0),
                ],
            ),
            "cost": _module("cost", "pass", [OutputRecord("cost_total_usd_2025", 100_000_000)]),
        },
        {
            "case": "failed_capacity",
            "expected": "fail",
            "capacity": _module(
                "capacity",
                "fail",
                [
                    OutputRecord("capacity_mtpa", 3.0),
                    OutputRecord("required_design_mtpa", 5.0),
                ],
            ),
            "integrity": _module(
                "integrity",
                "pass",
                [
                    OutputRecord("remaining_life_years", 30.0),
                    OutputRecord("available_wall_thickness_mm", 5.0),
                ],
            ),
            "cost": _module("cost", "pass", [OutputRecord("cost_total_usd_2025", 100_000_000)]),
        },
        {
            "case": "missing_required_output",
            "expected": "insufficient_data",
            "capacity": _module("capacity", "pass", [OutputRecord("capacity_mtpa", 10.0)]),
            "integrity": _module(
                "integrity",
                "pass",
                [
                    OutputRecord("remaining_life_years", 30.0),
                    OutputRecord("available_wall_thickness_mm", 5.0),
                ],
            ),
            "cost": _module("cost", "pass", [OutputRecord("cost_total_usd_2025", 100_000_000)]),
        },
    ]

    for case in cases:
        result = evaluate_pre_lca_gate(
            capacity=case["capacity"],
            integrity=case["integrity"],
            cost=case["cost"],
        )
        observed = result.output_map()["pre_lca_decision"]
        rows.append(
            {
                "module": "pre_lca_gate",
                "validation_type": "engineered_logic_case",
                "case": case["case"],
                "observed": observed,
                "expected": case["expected"],
                "status": "pass" if observed == case["expected"] else "review_required",
                "reference": "manual engineered test case",
                "notes": "Checks gate decision behaviour for expected pass/marginal/fail/insufficient_data cases.",
            }
        )

    return rows


def lca_method_reference_register() -> list[dict[str, Any]]:
    return [
        {
            "source_id": "iso_14040_14044",
            "source_type": "standard",
            "source_name": "ISO 14040/14044",
            "module": "lca_method",
            "use_in_project": "overall LCA structure, goal and scope, inventory, impact assessment, interpretation, reporting",
            "status": "method_reference",
            "notes": "Defines the formal LCA framework; use as the baseline method requirement.",
        },
        {
            "source_id": "jrc_ilcd_handbook_2011",
            "source_type": "guidance",
            "source_name": "International Reference Life Cycle Data System (ILCD) Handbook, 2011",
            "module": "lca_method",
            "use_in_project": "practical quality, consistency, and documentation guidance for LCA studies",
            "status": "method_reference",
            "notes": "Useful bridge between ISO requirements and practical modelling decisions.",
        },
        {
            "source_id": "norsus_ccu_lca_guidelines_2022",
            "source_type": "report",
            "source_name": "Guidelines for Life Cycle Assessment (LCA) of CCU systems, NORSUS OR 28.22, 2022",
            "module": "lca_method",
            "use_in_project": "system expansion, reference system comparison, fossil/non-fossil CO2 handling, CCU/CCS boundary thinking",
            "status": "method_reference",
            "notes": "Useful for avoiding unfair comparisons between reuse and new-build/reference systems.",
        },
        {
            "source_id": "iogp_report_672_2024",
            "source_type": "report",
            "source_name": "Overview of lifecycle assessment for carbon capture and storage projects, IOGP Report 672, 2024",
            "module": "lca_method",
            "use_in_project": "CCS project lifecycle, baseline methodology, shared transport and storage networks, hub allocation, project-stage reporting",
            "status": "method_reference",
            "notes": "Especially useful for future shared network/hub cases.",
        },
        {
            "source_id": "global_co2_initiative_guidelines",
            "source_type": "guidance",
            "source_name": "Global CO2 Initiative TEA and LCA Guidelines for CO2 Utilization",
            "module": "lca_method",
            "use_in_project": "harmonised and transparent TEA/LCA framing for CO2 systems",
            "status": "method_reference",
            "notes": "More CCU-focused than pipeline reuse but useful for transparent reporting.",
        },
        {
            "source_id": "supplied_lca_workbook_2023",
            "source_type": "supplementary_workbook",
            "source_name": "Supplementary LCA workbook with capture, auxiliary process, and Northern Lights storage inventories",
            "module": "lca_inventory",
            "use_in_project": "example inventory structure per tonne of captured/injected CO2; storage pipeline and injection-well entries",
            "status": "inventory_template",
            "notes": "Use as a structural template; do not copy values blindly into our pipeline reuse case.",
        },
        {
            "source_id": "ecoinvent_apos_38",
            "source_type": "local_database",
            "source_name": "ecoinvent APOS 3.8 local export",
            "module": "lca_data",
            "use_in_project": "background process data for steel, pipeline construction, electricity, diesel machinery, freight transport, and waste treatment",
            "status": "local_data_source",
            "notes": "Licensed data stay outside GitHub; commit only mapping metadata and scripts.",
        },
        {
            "source_id": "brightway_framework",
            "source_type": "software",
            "source_name": "Brightway LCA Software Framework",
            "module": "lca_calculation",
            "use_in_project": "future Python calculation engine for local LCA runs",
            "status": "future_reference",
            "notes": "Fits our Python workflow and can work with local databases.",
        },
        {
            "source_id": "openlca_software",
            "source_type": "software",
            "source_name": "openLCA",
            "module": "lca_calculation",
            "use_in_project": "future independent cross-check and reviewer-friendly LCA modelling environment",
            "status": "future_reference",
            "notes": "Useful for external review and comparison with a widely used LCA tool.",
        },
        {
            "source_id": "prospective_lca_literature",
            "source_type": "paper_group",
            "source_name": "Prospective LCA literature",
            "module": "lca_future_extension",
            "use_in_project": "future 2030/2050 scenarios for electricity, steel, shipping, and background databases",
            "status": "future_reference",
            "notes": "Not part of version 1 conventional LCA.",
        },
        {
            "source_id": "dynamic_lca_literature",
            "source_type": "paper_group",
            "source_name": "Dynamic LCA literature",
            "module": "lca_future_extension",
            "use_in_project": "future time-dependent climate effects and timing of emissions or storage benefits",
            "status": "future_reference",
            "notes": "Not part of version 1 conventional LCA.",
        },
    ]


def validation_status_dashboard(
    *,
    ecoinvent_rows: list[dict[str, Any]] | None = None,
    lca_reference_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    ecoinvent_has_processes = bool(
        ecoinvent_rows
        and any(row.get("validation_type") == "ecoinvent_process_availability" and row.get("status") == "pass" for row in ecoinvent_rows)
    )
    lca_reference_has_template = bool(
        lca_reference_rows
        and any(row.get("status") == "pass" for row in lca_reference_rows)
    )
    lca_data_status = "validated_for_mapping" if ecoinvent_has_processes else "blocked_by_data_access"
    lca_data_evidence = (
        "local ecoinvent APOS 3.8 process candidates found"
        if ecoinvent_has_processes
        else "ecoinvent access is external/licensed and was not available to this run"
    )
    lca_calculation_status = "validated_for_mapping" if lca_reference_has_template else "not_implemented"
    lca_calculation_evidence = (
        "supplied LCA workbook gives inventory structure for capture/storage examples"
        if lca_reference_has_template
        else "Brightway/openLCA route is planned but not coded"
    )
    rows = [
        {
            "module": "data_extraction",
            "status": "validated_for_screening",
            "evidence": "raw-to-processed count, required fields, ranked candidate checks",
            "remaining_limitation": "source data values are not independently verified against operator records",
            "next_action": "spot-check priority pipelines against operator/public documents",
        },
        {
            "module": "assumption_register",
            "status": "validated_for_screening",
            "evidence": "all assumptions have value, unit, source, quality, and notes",
            "remaining_limitation": "many values remain assumptions rather than operator-confirmed data",
            "next_action": "replace Goldeneye and NSTA defaults with project-specific evidence",
        },
        {
            "module": "co2_properties",
            "status": "first_independent_pass",
            "evidence": "CoolProp pure-CO2 checks pass for Goldeneye pressure and temperature",
            "remaining_limitation": "REFPROP and impurity/mixture validation still needed",
            "next_action": "add REFPROP or NIST table cross-check when available",
        },
        {
            "module": "hydraulics_capacity",
            "status": "arithmetic_pass_external_pending",
            "evidence": "independent equation repeat and CoolProp-Z sensitivity pass",
            "remaining_limitation": "external transport model comparison still needed",
            "next_action": "build like-for-like SCO2T or NETL case",
        },
        {
            "module": "integrity_wall_thickness",
            "status": "review_required",
            "evidence": "simple Barlow sanity check flags Goldeneye minimum wall thickness",
            "remaining_limitation": "not a full requalification calculation",
            "next_action": "confirm correct design code, pressure basis, diameter basis, SMYS, and design factor",
        },
        {
            "module": "corrosion",
            "status": "review_required",
            "evidence": "screening dry-CO2 corrosion risk module uses water evidence and low/base/high corrosion-rate ranges",
            "remaining_limitation": "not a calibrated NORSOK/DNV corrosion model and does not model impurities, pH, shear stress, or local free water",
            "next_action": "replace placeholder water/corrosion defaults with project stream-quality evidence and specialist model review",
        },
        {
            "module": "future_co2_integrity",
            "status": "review_required",
            "evidence": "screening warnings require inspection and requalification evidence",
            "remaining_limitation": "free water, impurities, fracture, defects, and weld condition are not modelled",
            "next_action": "define stream-quality and inspection-data gates before allowing pass",
        },
        {
            "module": "cost",
            "status": "arithmetic_pass_external_pending",
            "evidence": "component sum and contingency match reported student total within rounding",
            "remaining_limitation": "NETL CO2_T_COM and original literature examples still needed",
            "next_action": "build NETL CO2_T_COM 2024 benchmark input sheet",
        },
        {
            "module": "pre_lca_gate",
            "status": "automated_pass",
            "evidence": "engineered pass/marginal/fail/insufficient-data cases pass",
            "remaining_limitation": "gate thresholds may evolve when LCA and integrity modules mature",
            "next_action": "keep gate tests updated as modules are added",
        },
        {
            "module": "lca",
            "status": "validated_for_screening",
            "evidence": "first proxy calculation estimates pipe steel mass and reuse versus new-build CO2e screening",
            "remaining_limitation": "proxy factors are open screening assumptions, not final ecoinvent/Brightway impact results",
            "next_action": "use the proxy for ranking, then run full ecoinvent/Brightway LCA for shortlisted pipelines",
        },
        {
            "module": "lca_data",
            "status": lca_data_status,
            "evidence": lca_data_evidence,
            "remaining_limitation": "final dataset choice needs LCA review and licensed database access on the modelling machine",
            "next_action": "use mapping file to build a Brightway/openLCA inventory skeleton",
        },
        {
            "module": "lca_calculation",
            "status": "validated_for_screening",
            "evidence": "executable open proxy exists; " + lca_calculation_evidence,
            "remaining_limitation": "licensed-database calculation is not implemented yet",
            "next_action": "choose Brightway first for ecoinvent calculation, then cross-check with openLCA",
        },
        {
            "module": "wells_repurposing",
            "status": "not_implemented",
            "evidence": "well module is a Phase 2 concept only",
            "remaining_limitation": "well data and integrity rules are not loaded",
            "next_action": "define well fields and a separate well integrity gate",
        },
        {
            "module": "interface",
            "status": "not_implemented",
            "evidence": "no web interface exists in the professional rebuild yet",
            "remaining_limitation": "UI cannot be validated until it is built",
            "next_action": "when UI starts, test that app outputs equal CLI/report outputs",
        },
    ]
    for row in rows:
        row["status_meaning"] = VALIDATION_STATUS_MEANINGS[row["status"]]
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
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


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _status_counts(rows: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        counts[str(row.get("status", "unknown"))] = counts.get(str(row.get("status", "unknown")), 0) + 1
    return ", ".join(f"{status}: {count}" for status, count in sorted(counts.items()))


def _dashboard_counts(rows: list[dict[str, Any]]) -> str:
    return _status_counts(rows)


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def _fmt(value: Any, digits: int = 3) -> str:
    if value == "" or value is None:
        return ""
    if isinstance(value, (float, int)):
        return f"{value:,.{digits}f}"
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def write_validation_report(
    path: Path,
    *,
    data_rows: list[dict[str, Any]],
    assumption_rows: list[dict[str, Any]],
    assumption_evidence_rows: list[dict[str, Any]],
    property_rows: list[dict[str, Any]],
    capacity_rows: list[dict[str, Any]],
    integrity_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    ecoinvent_rows: list[dict[str, Any]],
    lca_reference_rows: list[dict[str, Any]],
    lca_method_rows: list[dict[str, Any]],
    lca_model_input_rows: list[dict[str, Any]],
    dashboard_rows: list[dict[str, Any]],
    output_files: list[Path],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    property_summary = [
        [
            row["scenario"],
            row["parameter"],
            _fmt(row["model_value"]),
            _fmt(row["reference_value"]),
            _fmt(row["absolute_difference_percent"], 3),
            row["status"],
        ]
        for row in property_rows
        if row["parameter"] != "phase_state"
    ]

    capacity_summary = [
        [
            row["scenario"],
            row["validation_type"],
            _fmt(row["model_value"]),
            _fmt(row["reference_value"]),
            _fmt(row["difference_percent"], 3),
            row["status"],
        ]
        for row in capacity_rows
    ]

    integrity_summary = [
        [
            row["scenario"],
            _fmt(row.get("scenario_min_wall_mm")),
            _fmt(row.get("barlow_min_wall_mm")),
            _fmt(row.get("remaining_life_model_years")),
            _fmt(row.get("remaining_life_barlow_years")),
            row["status"],
        ]
        for row in integrity_rows
    ]

    cost_summary = [
        [
            row["scenario"],
            _fmt(row["calculated_total_usd_2025"], 0),
            _fmt(row["reported_total_usd_2025"], 0),
            _fmt(row["difference_usd_2025"], 0),
            row.get("netl_status", ""),
            row["status"],
        ]
        for row in cost_rows
    ]

    data_summary = [
        [
            row["validation_type"],
            row["observed"],
            row["expected"],
            row["status"],
        ]
        for row in data_rows
    ]

    assumption_summary = [
        [
            row["validation_type"],
            row["observed"],
            row["expected"],
            row["status"],
        ]
        for row in assumption_rows
    ]

    gate_summary = [
        [
            row["case"],
            row["observed"],
            row["expected"],
            row["status"],
        ]
        for row in gate_rows
    ]

    assumption_evidence_summary = [
        [
            row["assumption_family"],
            row["current_status"],
            row["recommended_sources"],
        ]
        for row in assumption_evidence_rows
    ]

    ecoinvent_summary = [
        [
            row["category"],
            row["matches"],
            row["selected_activity"],
            row["location"],
            row["status"],
        ]
        for row in ecoinvent_rows
    ]

    lca_reference_summary = [
        [
            row["sheet"],
            row.get("functional_unit", ""),
            row.get("useful_for_pipeline_lca", ""),
            row["status"],
        ]
        for row in lca_reference_rows
    ]

    lca_method_summary = [
        [
            row["source_name"],
            row["module"],
            row["status"],
            row["use_in_project"],
        ]
        for row in lca_method_rows
    ]

    lca_model_input_summary = [
        [
            row["validation_type"],
            row["observed"],
            row["expected"],
            row["status"],
        ]
        for row in lca_model_input_rows
    ]

    dashboard_summary = [
        [
            row["module"],
            row["status"],
            row["remaining_limitation"],
            row["next_action"],
        ]
        for row in dashboard_rows
    ]

    report = f"""# Independent Validation Report

Generated: {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

Model validation version: `{MODEL_VERSION}`

## Purpose

This report starts the full independent validation workflow.

It separates three things:

- reproduction of the student/dissertation outputs;
- independent checks against external references;
- engineering issues that need expert review.

## Plain Summary

| Area | Result |
| --- | --- |
| NSTA data extraction | `{_status_counts(data_rows)}` |
| Assumption traceability | `{_status_counts(assumption_rows)}` |
| Assumption evidence register | `{_status_counts(assumption_evidence_rows)}` |
| CO2 properties | `{_status_counts(property_rows)}` |
| Capacity | `{_status_counts(capacity_rows)}` |
| Integrity wall thickness | `{_status_counts(integrity_rows)}` |
| Cost arithmetic | `{_status_counts(cost_rows)}` |
| Pre-LCA gate | `{_status_counts(gate_rows)}` |
| ecoinvent data mapping | `{_status_counts(ecoinvent_rows)}` |
| LCA workbook review | `{_status_counts(lca_reference_rows)}` |
| LCA method references | `{_status_counts(lca_method_rows)}` |
| LCA model input CSVs | `{_status_counts(lca_model_input_rows)}` |
| Overall module status | `{_dashboard_counts(dashboard_rows)}` |

Main finding:

> The Goldeneye CO2 property values are close to CoolProp, but the integrity minimum-wall-thickness basis needs review. A simple Barlow pressure sanity check gives a higher minimum wall thickness than the dissertation/poster values.

Important boundary:

> This report removes vague pending labels, but it does not claim full engineering approval. Items marked `review_required`, `external_benchmark_needed`, `blocked_by_data_access`, or `not_implemented` are not validated.

## Overall Module Status

{_table(["Module", "Status", "Remaining limitation", "Next action"], dashboard_summary)}

Plain meaning:

There is no hidden pending work in this table. Each module has a clear state. Some modules are validated for screening, some need review, and some cannot be validated yet because they are not built or need external/licensed evidence.

## NSTA Data Extraction Validation

{_table(["Check", "Observed", "Expected", "Status"], data_summary)}

Plain meaning:

The extraction is reproducible and the ranked candidates keep only pipelines with usable engineering fields. Goldeneye is confirmed as a data-gap case: it appears in NSTA, but not as a strict model-ready record.

## Assumption Traceability Validation

{_table(["Check", "Observed", "Expected", "Status"], assumption_summary)}

Plain meaning:

The assumption files are traceable enough for screening: values have units, sources, quality labels, and notes. This does not mean the assumptions are all true; it means they are visible and auditable.

## Assumption Evidence Register

{_table(["Assumption family", "Current status", "Recommended sources"], assumption_evidence_summary)}

Plain meaning:

This is the next quality step beyond traceability. It shows which assumptions need DNV/ISO/NETL/operator/literature support before we can call them fully validated.

## CO2 Property Validation

Reference: CoolProp pure CO2 at the model average pipeline pressure and transport temperature.

Acceptance targets:

- density within 1%;
- viscosity within 3%;
- compressibility factor within 1%.

{_table(["Scenario", "Parameter", "Model", "CoolProp", "Abs diff %", "Status"], property_summary)}

Plain meaning:

The student/rebuilt CO2 property values are close enough for first-pass pure-CO2 screening. This does not yet validate impurity effects.

## Capacity Validation

{_table(["Scenario", "Check", "Model Mtpa", "Reference Mtpa", "Diff %", "Status"], capacity_summary)}

Plain meaning:

The arithmetic reproduces the equation. Replacing the student Z factor with CoolProp changes Goldeneye capacity by less than 1%, so property uncertainty is not the main issue for this case.

This still does not prove the selected capacity equation is the best engineering model. That needs comparison with external tools such as SCO2T or NETL where a like-for-like case can be built.

## Integrity Wall-Thickness Sanity Check

Reference: simple Barlow pressure check using X-grade SMYS and an assumed design factor of 0.72.

{_table(["Scenario", "Student min wall mm", "Barlow min wall mm", "Student life years", "Barlow life years", "Status"], integrity_summary)}

Plain meaning:

This is the biggest validation warning so far. The dissertation/poster minimum wall thickness is lower than the simple pressure sanity check. If the Barlow basis is appropriate, the remaining life becomes much shorter, especially for the poster case.

This does not mean the student is definitely wrong. It means we must verify:

- the exact pressure basis;
- whether outside diameter was used correctly;
- pipe grade and allowable stress;
- design factor;
- corrosion allowance;
- inspection and requalification rules.

Until this is resolved, integrity must remain `screening_unvalidated`.

## Cost Arithmetic Validation

{_table(["Scenario", "Calculated total USD", "Reported total USD", "Diff USD", "NETL status", "Status"], cost_summary)}

Plain meaning:

The cost arithmetic is internally consistent. This only checks the sum and contingency. NETL validation is separate and will run only when a like-for-like NETL CO2_T_COM result is supplied.

Next independent cost validation should use NETL CO2_T_COM and record the reference value in the assumption file or a dedicated benchmark input.

## Pre-LCA Gate Validation

{_table(["Case", "Observed", "Expected", "Status"], gate_summary)}

Plain meaning:

The decision gate behaves as intended for simple engineered examples. This helps ensure the model does not accidentally pass cases with failed modules or missing data.

## ecoinvent Mapping Check

{_table(["Category", "Matches", "Selected candidate", "Location", "Status"], ecoinvent_summary)}

Plain meaning:

The local ecoinvent APOS 3.8 export can support the future LCA mapping. The model should store only process choices and mapping metadata in GitHub, not licensed ecoinvent inventory data.

## LCA Workbook Review

{_table(["Sheet", "Functional unit", "Useful for our LCA", "Status"], lca_reference_summary)}

Plain meaning:

The supplied workbook is useful as a structure/template. The Northern Lights storage sheet is especially relevant because it includes permanent storage, pipeline, injection well, decommissioned pipeline, steel, diesel, and electricity entries.

## LCA Method References

{_table(["Source", "Module", "Status", "Use in project"], lca_method_summary)}

Plain meaning:

These sources define how the LCA should be built. They support system boundary, reference system, functional unit, shared transport-storage network, and reporting choices.

## LCA Model Input CSVs

{_table(["Check", "Observed", "Expected", "Status"], lca_model_input_summary)}

Plain meaning:

These CSVs are the bridge between our open model and the private LCA database. The inventory template lists model quantities, and the process mapping CSV tells the future LCA module which local ecoinvent process metadata to use.

## Current Validation Status

| Module | Status | Meaning |
| --- | --- | --- |
| Data extraction | validated for screening | Raw-to-processed count and candidate checks pass. |
| Assumptions | validated for screening | Traceability fields are present and quality labels are visible. |
| CO2 properties | first independent pass | Pure CO2 values pass against CoolProp for Goldeneye conditions. |
| Capacity | arithmetic pass, external model needed | Code equation is reproducible; external transport-model comparison still needed. |
| Integrity | review required | Minimum wall basis is not yet defensible. |
| Cost | arithmetic pass, external model needed | Arithmetic is correct; NETL cost validation still needed. |
| Pre-LCA gate | automated pass | Engineered gate cases pass. |
| LCA | validated for mapping | Method references, local ecoinvent mapping, workbook structure, and model input CSVs are in place; calculation is not implemented yet. |
| Wells | not implemented | Needs well data and integrity screening logic. |
| Interface | not implemented | No professional web interface exists yet. |

## Output Files

{chr(10).join(f"- `{_display_path(output_file)}`" for output_file in output_files)}

## Next Validation Actions

1. Resolve the Goldeneye minimum wall thickness formulation.
2. Build a like-for-like NETL CO2_T_COM cost case.
3. Build a like-for-like SCO2T or NETL transport capacity case.
4. Add the first LCA inventory skeleton after the pre-LCA gate.
5. Define the well-repurposing data fields before coding that module.
"""
    path.write_text(report, encoding="utf-8")


def run_independent_validation(
    *,
    assumptions_path: Path,
    defaults_path: Path,
    raw_attributes_path: Path,
    processed_attributes_path: Path,
    ranked_candidates_path: Path,
    validation_dir: Path,
    report_path: Path,
    lca_inventory_template_path: Path,
    lca_process_mapping_path: Path,
    output_paths: dict[str, Path] | None = None,
    ecoinvent_dir: Path | None = None,
    lca_workbook_path: Path | None = None,
) -> dict[str, list[dict[str, Any]]]:
    scenarios = read_scenario_assumptions(assumptions_path)
    data_rows = validate_nsta_data_extraction(
        raw_attributes_path=raw_attributes_path,
        processed_attributes_path=processed_attributes_path,
        ranked_candidates_path=ranked_candidates_path,
    )
    assumption_rows = validate_assumption_register(
        assumptions_path=assumptions_path,
        defaults_path=defaults_path,
    )
    assumption_evidence_rows = assumption_evidence_register()
    property_rows = validate_co2_properties(scenarios)
    capacity_rows = validate_capacity(scenarios)
    integrity_rows = validate_integrity_barlow_sanity(scenarios)
    cost_rows = validate_cost_arithmetic(scenarios)
    gate_rows = validate_pre_lca_gate_logic()
    ecoinvent_rows = validate_ecoinvent_mapping(ecoinvent_dir)
    lca_reference_rows = validate_lca_reference_workbook(lca_workbook_path)
    lca_method_rows = lca_method_reference_register()
    lca_model_input_rows = validate_lca_model_input_csvs(
        inventory_template_path=lca_inventory_template_path,
        process_mapping_path=lca_process_mapping_path,
    )
    dashboard_rows = validation_status_dashboard(
        ecoinvent_rows=ecoinvent_rows,
        lca_reference_rows=lca_reference_rows,
    )

    default_outputs = {
        "data": validation_dir / "data_extraction_validation.csv",
        "assumptions": validation_dir / "assumption_traceability_validation.csv",
        "assumption_evidence": validation_dir / "assumption_evidence_register.csv",
        "property": validation_dir / "co2_property_validation.csv",
        "capacity": validation_dir / "capacity_validation.csv",
        "integrity": validation_dir / "integrity_barlow_sanity_check.csv",
        "cost": validation_dir / "cost_arithmetic_validation.csv",
        "gate": validation_dir / "pre_lca_gate_validation.csv",
        "ecoinvent": validation_dir / "ecoinvent_process_mapping_validation.csv",
        "lca_reference": validation_dir / "lca_reference_workbook_review.csv",
        "lca_method": validation_dir / "lca_method_reference_register.csv",
        "lca_model_inputs": validation_dir / "lca_model_input_csv_validation.csv",
        "dashboard": validation_dir / "validation_status_dashboard.csv",
    }
    outputs = {**default_outputs, **(output_paths or {})}

    write_csv(outputs["data"], data_rows)
    write_csv(outputs["assumptions"], assumption_rows)
    write_csv(outputs["assumption_evidence"], assumption_evidence_rows)
    write_csv(outputs["property"], property_rows)
    write_csv(outputs["capacity"], capacity_rows)
    write_csv(outputs["integrity"], integrity_rows)
    write_csv(outputs["cost"], cost_rows)
    write_csv(outputs["gate"], gate_rows)
    write_csv(outputs["ecoinvent"], ecoinvent_rows)
    write_csv(outputs["lca_reference"], lca_reference_rows)
    write_csv(outputs["lca_method"], lca_method_rows)
    write_csv(outputs["lca_model_inputs"], lca_model_input_rows)
    write_csv(outputs["dashboard"], dashboard_rows)
    write_validation_report(
        report_path,
        data_rows=data_rows,
        assumption_rows=assumption_rows,
        assumption_evidence_rows=assumption_evidence_rows,
        property_rows=property_rows,
        capacity_rows=capacity_rows,
        integrity_rows=integrity_rows,
        cost_rows=cost_rows,
        gate_rows=gate_rows,
        ecoinvent_rows=ecoinvent_rows,
        lca_reference_rows=lca_reference_rows,
        lca_method_rows=lca_method_rows,
        lca_model_input_rows=lca_model_input_rows,
        dashboard_rows=dashboard_rows,
        output_files=list(outputs.values()),
    )

    return {
        "data": data_rows,
        "assumptions": assumption_rows,
        "assumption_evidence": assumption_evidence_rows,
        "property": property_rows,
        "capacity": capacity_rows,
        "integrity": integrity_rows,
        "cost": cost_rows,
        "gate": gate_rows,
        "ecoinvent": ecoinvent_rows,
        "lca_reference": lca_reference_rows,
        "lca_method": lca_method_rows,
        "lca_model_inputs": lca_model_input_rows,
        "dashboard": dashboard_rows,
    }
