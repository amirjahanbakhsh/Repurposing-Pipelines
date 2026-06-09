"""Run the screening model for one selected pipeline scenario.

Examples:

    python scripts/run_pipeline_screen.py --list-scenarios
    python scripts/run_pipeline_screen.py --scenario goldeneye_poster

At this stage, scenarios come from:

    data/benchmarks/goldeneye_assumptions.csv

Later we will extend the same command to NSTA pipeline names plus an
assumption/override file for missing values.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.pipeline_screen import (  # noqa: E402
    available_scenarios,
    safe_filename,
    screen_one_pipeline,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one pipeline screening scenario and write a short report."
    )
    parser.add_argument(
        "--scenario",
        help="Scenario name to run, for example goldeneye_poster.",
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="Show available scenario names and stop.",
    )
    parser.add_argument(
        "--assumptions",
        default=str(ROOT / "data" / "benchmarks" / "goldeneye_assumptions.csv"),
        help="Path to the assumptions CSV file.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    assumptions_path = Path(args.assumptions)

    if args.list_scenarios:
        print("Available scenarios:")
        for name in available_scenarios(assumptions_path):
            print(f"- {name}")
        return 0

    if not args.scenario:
        parser.error("Please provide --scenario or use --list-scenarios.")

    safe_name = safe_filename(args.scenario)
    output_csv_path = ROOT / "data" / "processed" / f"pipeline_screen_{safe_name}.csv"
    trace_path = ROOT / "data" / "processed" / f"pipeline_screen_{safe_name}_trace.json"
    report_path = ROOT / "reports" / f"pipeline_screen_{safe_name}.md"

    try:
        row = screen_one_pipeline(
            assumptions_path=assumptions_path,
            scenario_name=args.scenario,
            output_csv_path=output_csv_path,
            trace_path=trace_path,
            report_path=report_path,
        )
    except ValueError as exc:
        print(exc)
        return 2

    print(f"Scenario: {row['scenario']}")
    print(f"Pipeline: {row['pipeline_name']}")
    print(f"Decision: {row['pre_lca_decision']}")
    print(f"Report: {report_path}")
    print(f"CSV: {output_csv_path}")
    print(f"Trace: {trace_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
