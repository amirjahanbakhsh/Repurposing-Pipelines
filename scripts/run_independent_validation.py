"""Run independent validation checks for the current benchmark model."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.validation import run_independent_validation  # noqa: E402


def main() -> int:
    results = run_independent_validation(
        assumptions_path=ROOT / "data" / "benchmarks" / "goldeneye_assumptions.csv",
        validation_dir=ROOT / "data" / "validation",
        report_path=ROOT / "reports" / "independent_validation_report.md",
    )
    print("Independent validation completed.")
    print(f"CO2 property checks: {len(results['property'])}")
    print(f"Capacity checks: {len(results['capacity'])}")
    print(f"Integrity checks: {len(results['integrity'])}")
    print(f"Cost checks: {len(results['cost'])}")
    print(f"Report: {ROOT / 'reports' / 'independent_validation_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
