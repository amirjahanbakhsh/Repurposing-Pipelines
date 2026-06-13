"""Apply private unit-cost factors to refurbishment work-scope tables.

Examples:

    python scripts/run_refurbishment_cost.py --create-factor-template
    python scripts/run_refurbishment_cost.py --case nsta_pl774 --factor-mode screening
    python scripts/run_refurbishment_cost.py --case goldeneye_poster
    python scripts/run_refurbishment_cost.py --case nsta_all

Real unit-cost values belong in:

    model_layers/04_cost_economics/private/refurbishment_unit_costs_private.csv

Public screening defaults are stored in:

    model_layers/04_cost_economics/refurbishment_unit_cost_screening_defaults.csv
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

COST_LAYER = ROOT / "model_layers" / "04_cost_economics"
SCREENING_LAYER = ROOT / "model_layers" / "06_screening_and_decision"

from repurposing_pipelines.refurbishment_cost import (  # noqa: E402
    calculate_refurbishment_costs,
    read_csv_rows,
    read_unit_costs,
    screening_unit_cost_rows,
    unit_cost_template_rows,
    write_csv_rows,
    write_refurbishment_cost_report,
)


DEFAULT_PRIVATE_COST_PATH = (
    COST_LAYER / "private" / "refurbishment_unit_costs_private.csv"
)
PUBLIC_TEMPLATE_PATH = COST_LAYER / "refurbishment_unit_cost_template.csv"
SCREENING_COST_PATH = COST_LAYER / "refurbishment_unit_cost_screening_defaults.csv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        default="nsta_pl774",
        help=(
            "Known case name: nsta_pl774, goldeneye_poster, goldeneye_benchmark, "
            "or nsta_all. Ignored when --work-scope is supplied."
        ),
    )
    parser.add_argument(
        "--work-scope",
        help="Optional explicit refurbishment_work_scope_*.csv input path.",
    )
    parser.add_argument(
        "--unit-costs",
        help="Explicit unit-cost CSV path. Overrides --factor-mode.",
    )
    parser.add_argument(
        "--factor-mode",
        choices=["screening", "private"],
        default="screening",
        help="Use public screening defaults or the ignored private unit-cost file.",
    )
    parser.add_argument(
        "--create-factor-template",
        action="store_true",
        help="Create the private unit-cost CSV template if it does not exist.",
    )
    return parser


def _known_work_scope_path(case: str) -> Path:
    key = case.strip().lower()
    mapping = {
        "nsta_pl774": SCREENING_LAYER / "refurbishment_work_scope_nsta_pl774.csv",
        "pl774": SCREENING_LAYER / "refurbishment_work_scope_nsta_pl774.csv",
        "goldeneye_poster": SCREENING_LAYER / "refurbishment_work_scope_goldeneye_poster.csv",
        "goldeneye_benchmark": SCREENING_LAYER / "refurbishment_work_scope_goldeneye_benchmark.csv",
        "nsta_all": SCREENING_LAYER / "refurbishment_work_scope_nsta_all.csv",
    }
    if key not in mapping:
        known = ", ".join(sorted(mapping))
        raise ValueError(f"Unknown case '{case}'. Use one of: {known}, or pass --work-scope.")
    return mapping[key]


def _safe_case_name(work_scope_path: Path) -> str:
    stem = work_scope_path.stem
    prefix = "refurbishment_work_scope_"
    if stem.startswith(prefix):
        return stem[len(prefix):]
    return stem


def _create_private_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    if PUBLIC_TEMPLATE_PATH.exists():
        shutil.copyfile(PUBLIC_TEMPLATE_PATH, path)
    else:
        write_csv_rows(path, unit_cost_template_rows())


def _ensure_screening_defaults(path: Path) -> None:
    if not path.exists():
        write_csv_rows(path, screening_unit_cost_rows())


def main() -> int:
    args = build_parser().parse_args()
    if args.unit_costs:
        unit_cost_path = Path(args.unit_costs)
    elif args.create_factor_template:
        unit_cost_path = DEFAULT_PRIVATE_COST_PATH
    else:
        unit_cost_path = DEFAULT_PRIVATE_COST_PATH if args.factor_mode == "private" else SCREENING_COST_PATH
    if args.factor_mode == "screening" and not args.unit_costs:
        _ensure_screening_defaults(unit_cost_path)

    if args.create_factor_template:
        _create_private_template(unit_cost_path)
        print(f"Private unit-cost template: {unit_cost_path}")
        if not args.work_scope and args.case == "nsta_pl774":
            return 0

    work_scope_path = Path(args.work_scope) if args.work_scope else _known_work_scope_path(args.case)
    if not work_scope_path.exists():
        print(f"Work-scope file not found: {work_scope_path}")
        return 2

    case_name = _safe_case_name(work_scope_path)
    cost_rows_path = COST_LAYER / f"refurbishment_costs_{case_name}.csv"
    summary_path = COST_LAYER / f"refurbishment_cost_summary_{case_name}.csv"
    report_path = COST_LAYER / f"refurbishment_cost_report_{case_name}.md"

    work_scope_rows = read_csv_rows(work_scope_path)
    unit_costs = read_unit_costs(unit_cost_path)
    cost_rows, summary_rows = calculate_refurbishment_costs(work_scope_rows, unit_costs)

    write_csv_rows(cost_rows_path, cost_rows)
    write_csv_rows(summary_path, summary_rows)
    write_refurbishment_cost_report(
        report_path,
        work_scope_path=work_scope_path,
        unit_cost_path=unit_cost_path,
        cost_rows_path=cost_rows_path,
        summary_path=summary_path,
        summary_rows=summary_rows,
    )

    print(f"Case: {case_name}")
    print(f"Scenarios costed: {len(summary_rows)}")
    print(f"Report: {report_path}")
    print(f"Row costs: {cost_rows_path}")
    print(f"Summary: {summary_path}")
    missing = sorted(
        {
            row["refurbishment_cost_status"]
            for row in summary_rows
            if row["refurbishment_cost_status"] == "blocked_missing_unit_costs"
        }
    )
    if missing:
        print("Status: blocked_missing_unit_costs")
        print(f"Private unit-cost file: {unit_cost_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
