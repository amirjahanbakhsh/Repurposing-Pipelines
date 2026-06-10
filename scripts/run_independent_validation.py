"""Run independent validation checks for the current benchmark model."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

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
        assumptions_path=ROOT / "data" / "benchmarks" / "goldeneye_assumptions.csv",
        defaults_path=ROOT / "data" / "inputs" / "nsta_screening_defaults.csv",
        raw_attributes_path=ROOT / "data" / "raw" / "nsta_pipeline_attributes.json",
        processed_attributes_path=ROOT / "data" / "processed" / "nsta_pipeline_attributes.csv",
        ranked_candidates_path=ROOT / "data" / "processed" / "nsta_candidate_ranked.csv",
        validation_dir=ROOT / "data" / "validation",
        report_path=ROOT / "reports" / "independent_validation_report.md",
        lca_inventory_template_path=ROOT / "data" / "inputs" / "lca_inventory_template.csv",
        lca_process_mapping_path=ROOT / "data" / "inputs" / "lca_process_mapping.csv",
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
    print(f"Report: {ROOT / 'reports' / 'independent_validation_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
