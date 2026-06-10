"""Run independent validation checks for the current benchmark model."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DATA_LAYER = ROOT / "model_layers" / "01_data_foundation"
CAPACITY_LAYER = ROOT / "model_layers" / "02_capacity_hydraulics"
INTEGRITY_LAYER = ROOT / "model_layers" / "03_corrosion_integrity"
COST_LAYER = ROOT / "model_layers" / "04_cost_economics"
LCA_LAYER = ROOT / "model_layers" / "05_lca"
SCREENING_LAYER = ROOT / "model_layers" / "06_screening_and_decision"
VALIDATION_LAYER = ROOT / "model_layers" / "07_independent_validation"

from repurposing_pipelines.validation import run_independent_validation  # noqa: E402


def _existing_path_or_none(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.exists() else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ecoinvent-dir",
        help=(
            "Optional local ecoinvent export folder. "
            "Licensed data are read locally but not copied into this repository."
        ),
    )
    parser.add_argument(
        "--lca-workbook",
        help="Optional LCA supplementary Excel workbook to review as an inventory template.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = run_independent_validation(
        assumptions_path=SCREENING_LAYER / "goldeneye_assumptions.csv",
        defaults_path=SCREENING_LAYER / "nsta_screening_defaults.csv",
        raw_attributes_path=DATA_LAYER / "nsta_pipeline_attributes.json",
        processed_attributes_path=DATA_LAYER / "nsta_pipeline_attributes.csv",
        ranked_candidates_path=DATA_LAYER / "nsta_candidate_ranked.csv",
        validation_dir=VALIDATION_LAYER,
        report_path=VALIDATION_LAYER / "independent_validation_report.md",
        lca_inventory_template_path=LCA_LAYER / "lca_inventory_template.csv",
        lca_process_mapping_path=LCA_LAYER / "lca_process_mapping.csv",
        lca_impact_factor_template_path=LCA_LAYER / "lca_impact_factors_template.csv",
        output_paths={
            "data": DATA_LAYER / "data_extraction_validation.csv",
            "property": CAPACITY_LAYER / "co2_property_validation.csv",
            "capacity": CAPACITY_LAYER / "capacity_validation.csv",
            "integrity": INTEGRITY_LAYER / "integrity_barlow_sanity_check.csv",
            "cost": COST_LAYER / "cost_arithmetic_validation.csv",
            "gate": SCREENING_LAYER / "pre_lca_gate_validation.csv",
            "ecoinvent": LCA_LAYER / "ecoinvent_process_mapping_validation.csv",
            "lca_reference": LCA_LAYER / "lca_reference_workbook_review.csv",
            "lca_method": LCA_LAYER / "lca_method_reference_register.csv",
            "lca_model_inputs": LCA_LAYER / "lca_model_input_csv_validation.csv",
            "assumptions": VALIDATION_LAYER / "assumption_traceability_validation.csv",
            "assumption_evidence": VALIDATION_LAYER / "assumption_evidence_register.csv",
            "dashboard": VALIDATION_LAYER / "validation_status_dashboard.csv",
        },
        ecoinvent_dir=_existing_path_or_none(args.ecoinvent_dir),
        lca_workbook_path=_existing_path_or_none(args.lca_workbook),
    )
    print("Independent validation completed.")
    print(f"Data extraction checks: {len(results['data'])}")
    print(f"Assumption traceability checks: {len(results['assumptions'])}")
    print(f"Assumption evidence rows: {len(results['assumption_evidence'])}")
    print(f"CO2 property checks: {len(results['property'])}")
    print(f"Capacity checks: {len(results['capacity'])}")
    print(f"Integrity checks: {len(results['integrity'])}")
    print(f"Cost checks: {len(results['cost'])}")
    print(f"Pre-LCA gate checks: {len(results['gate'])}")
    print(f"ecoinvent mapping checks: {len(results['ecoinvent'])}")
    print(f"LCA workbook checks: {len(results['lca_reference'])}")
    print(f"LCA method references: {len(results['lca_method'])}")
    print(f"LCA model input CSV checks: {len(results['lca_model_inputs'])}")
    print(f"Report: {VALIDATION_LAYER / 'independent_validation_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
