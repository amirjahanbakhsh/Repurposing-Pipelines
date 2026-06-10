"""Run Goldeneye benchmark calculations for dissertation and poster scenarios.

Inputs:

- model_layers/06_screening_and_decision/goldeneye_assumptions.csv

Outputs:

- model_layers/06_screening_and_decision/goldeneye_benchmark_outputs.csv
- model_layers/06_screening_and_decision/goldeneye_benchmark_trace.json
- model_layers/06_screening_and_decision/goldeneye_benchmark.md

The runner stays deliberately small. The engineering calculations live in
the reusable `repurposing_pipelines` package.
"""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.goldeneye import run_from_paths  # noqa: E402


def main() -> int:
    layer_dir = ROOT / "model_layers" / "06_screening_and_decision"
    assumptions_path = layer_dir / "goldeneye_assumptions.csv"
    output_path = layer_dir / "goldeneye_benchmark_outputs.csv"
    trace_path = layer_dir / "goldeneye_benchmark_trace.json"
    report_path = layer_dir / "goldeneye_benchmark.md"

    count = run_from_paths(
        assumptions_path=assumptions_path,
        output_path=output_path,
        trace_path=trace_path,
        report_path=report_path,
    )

    print(f"Read {count} Goldeneye scenarios")
    print(output_path)
    print(trace_path)
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
