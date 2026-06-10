"""Run the screening model for one selected pipeline scenario.

Examples:

    python scripts/run_pipeline_screen.py --list-scenarios
    python scripts/run_pipeline_screen.py --scenario goldeneye_poster
    python scripts/run_pipeline_screen.py --list-nsta --top 10
    python scripts/run_pipeline_screen.py --screen-all-nsta
    python scripts/run_pipeline_screen.py --nsta-id PL774

At this stage, scenarios come from:

    model_layers/06_screening_and_decision/goldeneye_assumptions.csv

NSTA runs combine:

    model_layers/01_data_foundation/nsta_candidate_ranked.csv
    model_layers/06_screening_and_decision/nsta_screening_defaults.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DATA_LAYER = ROOT / "model_layers" / "01_data_foundation"
SCREENING_LAYER = ROOT / "model_layers" / "06_screening_and_decision"

from repurposing_pipelines.pipeline_screen import (  # noqa: E402
    available_nsta_candidates,
    available_scenarios,
    safe_filename,
    screen_all_nsta_pipelines,
    screen_nsta_pipeline,
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
        "--list-nsta",
        action="store_true",
        help="Show top ranked NSTA candidate pipelines and stop.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="How many NSTA candidates to show with --list-nsta.",
    )
    parser.add_argument(
        "--nsta-id",
        help="Run one NSTA candidate by NSTA pipeline number, for example PL774.",
    )
    parser.add_argument(
        "--nsta-rank",
        type=int,
        help="Run one NSTA candidate by ranking number, for example 1.",
    )
    parser.add_argument(
        "--nsta-name",
        help="Run one NSTA candidate by unique name search text.",
    )
    parser.add_argument(
        "--screen-all-nsta",
        action="store_true",
        help="Run the screening model for all ranked NSTA candidate pipelines.",
    )
    parser.add_argument(
        "--screen-limit",
        type=int,
        help="Optional limit for --screen-all-nsta, useful for a quick test run.",
    )
    parser.add_argument(
        "--assumptions",
        default=str(SCREENING_LAYER / "goldeneye_assumptions.csv"),
        help="Path to the assumptions CSV file.",
    )
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

    candidates_path = Path(args.nsta_candidates)
    defaults_path = Path(args.nsta_defaults)

    if args.list_nsta:
        print("Top NSTA candidates:")
        for row in available_nsta_candidates(candidates_path, limit=args.top):
            print(
                f"- rank {row.get('RANK')}: {row.get('NSTAPIPNO')} | "
                f"{row.get('PIPE_NAME')} | {row.get('FLUID')} | "
                f"{row.get('STATUS')} | {float(row.get('LENGTH_KM') or 0):.1f} km"
            )
        return 0

    if args.screen_all_nsta:
        output_csv_path = SCREENING_LAYER / "pipeline_screen_nsta_all.csv"
        trace_path = SCREENING_LAYER / "pipeline_screen_nsta_all_trace.json"
        report_path = SCREENING_LAYER / "pipeline_screen_nsta_all.md"
        rows = screen_all_nsta_pipelines(
            candidates_path=candidates_path,
            defaults_path=defaults_path,
            output_csv_path=output_csv_path,
            trace_path=trace_path,
            report_path=report_path,
            limit=args.screen_limit,
        )
        print(f"Screened pipelines: {len(rows)}")
        print(f"Report: {report_path}")
        print(f"CSV: {output_csv_path}")
        print(f"Trace: {trace_path}")
        return 0

    if args.nsta_id or args.nsta_rank or args.nsta_name:
        if args.nsta_id:
            selector = args.nsta_id
        elif args.nsta_rank:
            selector = f"rank_{args.nsta_rank}"
        else:
            selector = args.nsta_name or "nsta"
        safe_name = f"nsta_{safe_filename(str(selector))}"
        output_csv_path = SCREENING_LAYER / f"pipeline_screen_{safe_name}.csv"
        trace_path = SCREENING_LAYER / f"pipeline_screen_{safe_name}_trace.json"
        report_path = SCREENING_LAYER / f"pipeline_screen_{safe_name}.md"
        try:
            row = screen_nsta_pipeline(
                candidates_path=candidates_path,
                defaults_path=defaults_path,
                nsta_id=args.nsta_id,
                rank=args.nsta_rank,
                name=args.nsta_name,
                output_csv_path=output_csv_path,
                trace_path=trace_path,
                report_path=report_path,
            )
        except ValueError as exc:
            print(exc)
            return 2

        print(f"Scenario: {row['scenario']}")
        print(f"Pipeline: {row['pipeline_name']}")
        print(f"NSTA number: {row['nsta_pipeline_number']}")
        print(f"Decision: {row['pre_lca_decision']}")
        print(f"Report: {report_path}")
        print(f"CSV: {output_csv_path}")
        print(f"Trace: {trace_path}")
        return 0

    if not args.scenario:
        parser.error(
            "Please provide --scenario, --nsta-id, --nsta-rank, --nsta-name, "
            "--screen-all-nsta, or use --list-scenarios / --list-nsta."
        )

    safe_name = safe_filename(args.scenario)
    output_csv_path = SCREENING_LAYER / f"pipeline_screen_{safe_name}.csv"
    trace_path = SCREENING_LAYER / f"pipeline_screen_{safe_name}_trace.json"
    report_path = SCREENING_LAYER / f"pipeline_screen_{safe_name}.md"

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
