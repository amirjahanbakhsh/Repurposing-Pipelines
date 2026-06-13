"""Run the ecoinvent-linked conditional LCA workflow.

This command builds a pipeline LCA inventory from the screening model and
applies private ecoinvent-derived impact factors when they are available.

Examples:

    python scripts/run_ecoinvent_lca.py --nsta-id PL774 --factor-mode screening
    python scripts/run_ecoinvent_lca.py --scenario goldeneye_poster
    python scripts/run_ecoinvent_lca.py --create-factor-template

The private factor CSV is intentionally ignored by Git.

The public screening-factor CSV is committed for early screening runs.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATA_LAYER = ROOT / "model_layers" / "01_data_foundation"
LCA_LAYER = ROOT / "model_layers" / "05_lca"
SCREENING_LAYER = ROOT / "model_layers" / "06_screening_and_decision"

from repurposing_pipelines.assumptions import read_scenario_assumptions  # noqa: E402
from repurposing_pipelines.lca import (  # noqa: E402
    build_pipeline_lca_inventory,
    calculate_ecoinvent_impacts,
    impact_factor_template_rows,
    read_impact_factors,
    read_process_mapping,
    screening_impact_factor_rows,
    write_csv_rows,
    write_ecoinvent_lca_report,
    write_lca_trace,
)
from repurposing_pipelines.pipeline_screen import (  # noqa: E402
    build_nsta_scenario,
    find_nsta_candidate,
    read_csv_rows,
    read_defaults,
    safe_filename,
)
from repurposing_pipelines.goldeneye import benchmark_scenario_with_trace  # noqa: E402


DEFAULT_FACTOR_PATH = LCA_LAYER / "private" / "lca_impact_factors_private.csv"
SCREENING_FACTOR_PATH = LCA_LAYER / "lca_impact_factors_screening_defaults.csv"


def _repo_path_text(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", help="Goldeneye scenario, for example goldeneye_poster.")
    parser.add_argument("--nsta-id", help="NSTA pipeline number, for example PL774.")
    parser.add_argument("--nsta-rank", type=int, help="NSTA ranking number.")
    parser.add_argument("--nsta-name", help="Unique text in the NSTA pipeline name.")
    parser.add_argument(
        "--impact-factors",
        help="Explicit impact-factor CSV path. Overrides --factor-mode.",
    )
    parser.add_argument(
        "--factor-mode",
        choices=["screening", "private"],
        default="screening",
        help="Use public screening defaults or the ignored private ecoinvent/openLCA/Brightway factor file.",
    )
    parser.add_argument(
        "--create-factor-template",
        action="store_true",
        help="Create the private factor CSV template if it does not exist.",
    )
    return parser


def _load_scenario(args: argparse.Namespace):
    if args.scenario:
        scenarios = read_scenario_assumptions(
            SCREENING_LAYER / "goldeneye_assumptions.csv"
        )
        if args.scenario not in scenarios:
            available = ", ".join(sorted(scenarios))
            raise ValueError(f"Unknown scenario '{args.scenario}'. Available: {available}")
        scenario = scenarios[args.scenario]
        row, trace = benchmark_scenario_with_trace(args.scenario, scenario)
        return (
            args.scenario,
            scenario,
            row["pre_lca_decision"],
            trace.get("refurbishment_work_scope_rows", []),
        )

    if args.nsta_id or args.nsta_rank or args.nsta_name:
        candidates = read_csv_rows(DATA_LAYER / "nsta_candidate_ranked.csv")
        defaults = read_defaults(SCREENING_LAYER / "nsta_screening_defaults.csv")
        nsta_row = find_nsta_candidate(
            candidates,
            nsta_id=args.nsta_id,
            rank=args.nsta_rank,
            name=args.nsta_name,
        )
        scenario = build_nsta_scenario(nsta_row=nsta_row, defaults=defaults)
        row, trace = benchmark_scenario_with_trace(scenario.name, scenario)
        return (
            scenario.name,
            scenario,
            row["pre_lca_decision"],
            trace.get("refurbishment_work_scope_rows", []),
        )

    raise ValueError("Choose --scenario or one of --nsta-id, --nsta-rank, --nsta-name.")


def _create_private_factor_template(path: Path, mapping_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    source_template = LCA_LAYER / "lca_impact_factors_template.csv"
    if source_template.exists():
        shutil.copyfile(source_template, path)
        return
    process_mapping = read_process_mapping(mapping_path)
    write_csv_rows(path, impact_factor_template_rows(process_mapping))


def _ensure_screening_defaults(path: Path) -> None:
    if not path.exists():
        write_csv_rows(path, screening_impact_factor_rows())


def main() -> int:
    args = build_parser().parse_args()
    process_mapping_path = LCA_LAYER / "lca_process_mapping.csv"
    if args.impact_factors:
        impact_factor_path = Path(args.impact_factors)
    elif args.create_factor_template:
        impact_factor_path = DEFAULT_FACTOR_PATH
    else:
        impact_factor_path = DEFAULT_FACTOR_PATH if args.factor_mode == "private" else SCREENING_FACTOR_PATH
    if args.factor_mode == "screening" and not args.impact_factors and not args.create_factor_template:
        _ensure_screening_defaults(impact_factor_path)

    if args.create_factor_template:
        _create_private_factor_template(impact_factor_path, process_mapping_path)
        print(f"Private factor template: {impact_factor_path}")
        if not (args.scenario or args.nsta_id or args.nsta_rank or args.nsta_name):
            return 0

    scenario_name, scenario, pre_lca_decision, work_scope_rows = _load_scenario(args)
    safe_name = safe_filename(scenario_name)
    process_mapping = read_process_mapping(process_mapping_path)
    impact_factors = read_impact_factors(impact_factor_path)
    inventory_rows = build_pipeline_lca_inventory(
        scenario,
        process_mapping=process_mapping,
        work_scope_rows=work_scope_rows,
    )
    impact_rows, summary = calculate_ecoinvent_impacts(
        inventory_rows,
        impact_factors,
        pre_lca_decision=pre_lca_decision,
    )
    summary["scenario"] = scenario_name
    summary["impact_factor_file"] = _repo_path_text(impact_factor_path)

    inventory_path = LCA_LAYER / f"lca_inventory_{safe_name}.csv"
    impact_path = LCA_LAYER / f"lca_impacts_{safe_name}.csv"
    results_path = LCA_LAYER / f"lca_results_{safe_name}.csv"
    trace_path = LCA_LAYER / f"lca_trace_{safe_name}.json"
    report_path = LCA_LAYER / f"lca_report_{safe_name}.md"

    write_csv_rows(inventory_path, inventory_rows)
    write_csv_rows(impact_path, impact_rows)
    write_csv_rows(results_path, [summary])
    write_lca_trace(
        trace_path,
        scenario_name=scenario_name,
        inventory_rows=inventory_rows,
        impact_rows=impact_rows,
        summary=summary,
    )
    write_ecoinvent_lca_report(
        report_path,
        scenario_name=scenario_name,
        inventory_path=inventory_path,
        impact_path=impact_path,
        results_path=results_path,
        trace_path=trace_path,
        factor_path=impact_factor_path,
        summary=summary,
        impact_rows=impact_rows,
    )

    print(f"Scenario: {scenario_name}")
    print(f"LCA status: {summary['lca_status']}")
    print(f"Report: {report_path}")
    print(f"Inventory: {inventory_path}")
    print(f"Impacts: {impact_path}")
    print(f"Results: {results_path}")
    print(f"Trace: {trace_path}")
    if summary["missing_mapping_keys"]:
        print(f"Missing factor keys: {summary['missing_mapping_keys']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
