"""Run the NSTA wall-thickness pressure sanity check."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DATA_LAYER = ROOT / "model_layers" / "01_data_foundation"
INTEGRITY_LAYER = ROOT / "model_layers" / "03_corrosion_integrity"
SCREENING_LAYER = ROOT / "model_layers" / "06_screening_and_decision"

from repurposing_pipelines.wall_thickness import (  # noqa: E402
    build_nsta_wall_thickness_check_rows,
    write_csv,
    write_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--nsta-candidates",
        default=str(DATA_LAYER / "nsta_candidate_ranked.csv"),
        help="Path to the ranked NSTA candidate CSV file.",
    )
    parser.add_argument(
        "--nsta-defaults",
        default=str(SCREENING_LAYER / "nsta_screening_defaults.csv"),
        help="Path to the NSTA screening defaults CSV file.",
    )
    parser.add_argument(
        "--output-csv",
        default=str(INTEGRITY_LAYER / "nsta_wall_thickness_pressure_check.csv"),
        help="CSV path for the wall-thickness pressure check.",
    )
    parser.add_argument(
        "--report",
        default=str(INTEGRITY_LAYER / "nsta_wall_thickness_pressure_check.md"),
        help="Markdown report path for the wall-thickness pressure check.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional number of NSTA rows to check for quick testing.",
    )
    return parser


def _status_counts(rows: list[dict[str, object]]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    return ", ".join(f"{status}: {count}" for status, count in sorted(counts.items()))


def main() -> int:
    args = build_parser().parse_args()
    candidates_path = Path(args.nsta_candidates)
    defaults_path = Path(args.nsta_defaults)
    output_csv_path = Path(args.output_csv)
    report_path = Path(args.report)

    rows = build_nsta_wall_thickness_check_rows(
        candidates_path=candidates_path,
        defaults_path=defaults_path,
        limit=args.limit,
    )
    write_csv(output_csv_path, rows)
    write_report(
        report_path,
        rows=rows,
        candidates_path=candidates_path,
        defaults_path=defaults_path,
        csv_path=output_csv_path,
    )

    print(f"Checked pipelines: {len(rows)}")
    print(f"Statuses: {_status_counts(rows)}")
    print(f"CSV: {output_csv_path}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
