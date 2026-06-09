"""Tests for running one selected pipeline scenario."""

from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.pipeline_screen import (  # noqa: E402
    available_scenarios,
    safe_filename,
    screen_one_pipeline,
)


class PipelineScreenTest(unittest.TestCase):
    def setUp(self) -> None:
        self.assumptions_path = ROOT / "data" / "benchmarks" / "goldeneye_assumptions.csv"

    def test_available_scenarios_lists_goldeneye_cases(self) -> None:
        scenarios = available_scenarios(self.assumptions_path)

        self.assertEqual(scenarios, ["goldeneye_dissertation", "goldeneye_poster"])

    def test_safe_filename_removes_spaces_and_symbols(self) -> None:
        self.assertEqual(safe_filename("Goldeneye Poster / Case"), "goldeneye_poster_case")

    def test_screen_one_pipeline_writes_outputs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            row = screen_one_pipeline(
                assumptions_path=self.assumptions_path,
                scenario_name="goldeneye_poster",
                output_csv_path=temp / "screen.csv",
                trace_path=temp / "trace.json",
                report_path=temp / "report.md",
            )

            self.assertEqual(row["scenario"], "goldeneye_poster")
            self.assertEqual(row["pre_lca_decision"], "marginal")
            self.assertTrue((temp / "screen.csv").exists())
            self.assertTrue((temp / "trace.json").exists())
            self.assertIn("Pipeline Screen", (temp / "report.md").read_text(encoding="utf-8"))

    def test_unknown_scenario_gives_clear_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            with self.assertRaisesRegex(ValueError, "Unknown scenario"):
                screen_one_pipeline(
                    assumptions_path=self.assumptions_path,
                    scenario_name="not_a_pipeline",
                    output_csv_path=temp / "screen.csv",
                    trace_path=temp / "trace.json",
                    report_path=temp / "report.md",
                )


if __name__ == "__main__":
    unittest.main()
