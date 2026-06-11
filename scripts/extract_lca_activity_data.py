"""Extract shareable LCA activity metadata from ecoinvent and other CSV files.

Examples:

    python scripts/extract_lca_activity_data.py --ecoinvent-dir "D:\\path\\Ecoinvent_apos_38"
    python scripts/extract_lca_activity_data.py --activity-csv my_activity_list.csv

The script writes metadata only. It must not export ecoinvent unit-process
inventories, exchanges, or private impact factors.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LCA_LAYER = ROOT / "model_layers" / "05_lca"

from repurposing_pipelines.lca_activity_extraction import (  # noqa: E402
    extract_lca_activity_data,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ecoinvent-dir",
        help="Local ecoinvent APOS export folder containing FilenameToActivtiyLookup.csv.",
    )
    parser.add_argument(
        "--activity-csv",
        action="append",
        default=[],
        help=(
            "Optional additional activity metadata CSV. Expected columns can include "
            "activity_name, location, reference_product, unit, database, system_model, version."
        ),
    )
    parser.add_argument(
        "--queries",
        default=str(LCA_LAYER / "lca_activity_query_terms.csv"),
        help="Optional activity query definition CSV.",
    )
    parser.add_argument(
        "--max-per-mapping",
        type=int,
        default=10,
        help="Maximum candidate activities to keep per mapping key.",
    )
    parser.add_argument(
        "--candidates-output",
        default=str(LCA_LAYER / "lca_activity_candidates.csv"),
        help="Output CSV for all candidate activities.",
    )
    parser.add_argument(
        "--preferred-output",
        default=str(LCA_LAYER / "lca_activity_preferred_mapping.csv"),
        help="Output CSV with rank-1 candidate per mapping key.",
    )
    parser.add_argument(
        "--report-output",
        default=str(LCA_LAYER / "lca_activity_extraction_report.md"),
        help="Output Markdown report.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    ecoinvent_dir = Path(args.ecoinvent_dir) if args.ecoinvent_dir else None
    activity_csvs = [Path(path) for path in args.activity_csv]
    query_path = Path(args.queries)
    if not query_path.exists():
        query_path = None

    if ecoinvent_dir is None and not activity_csvs:
        print("Please provide --ecoinvent-dir or at least one --activity-csv.")
        return 2

    summary = extract_lca_activity_data(
        ecoinvent_dir=ecoinvent_dir,
        activity_csvs=activity_csvs,
        query_path=query_path,
        candidates_path=Path(args.candidates_output),
        preferred_mapping_path=Path(args.preferred_output),
        report_path=Path(args.report_output),
        max_per_mapping=args.max_per_mapping,
    )
    print("LCA activity extraction completed.")
    print(f"Sources read: {summary['source_count']}")
    print(f"Source metadata rows: {summary['source_rows']}")
    print(f"Candidate rows: {summary['candidate_rows']}")
    print(f"Preferred mapping rows: {summary['preferred_rows']}")
    print(f"Candidates: {args.candidates_output}")
    print(f"Preferred: {args.preferred_output}")
    print(f"Report: {args.report_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

