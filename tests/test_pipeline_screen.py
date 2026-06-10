"""Tests for running one selected pipeline scenario."""

from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.pipeline_screen import (  # noqa: E402
    available_nsta_candidates,
    available_scenarios,
    screen_all_nsta_pipelines,
    screen_nsta_pipeline,
    safe_filename,
    screen_one_pipeline,
)


class PipelineScreenTest(unittest.TestCase):
    def setUp(self) -> None:
        screening_layer = ROOT / "model_layers" / "06_screening_and_decision"
        data_layer = ROOT / "model_layers" / "01_data_foundation"
        self.assumptions_path = screening_layer / "goldeneye_assumptions.csv"
        self.nsta_candidates_path = data_layer / "nsta_candidate_ranked.csv"
        self.nsta_defaults_path = screening_layer / "nsta_screening_defaults.csv"

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
            self.assertEqual(row["corrosion_risk_level"], "medium")
            self.assertGreater(row["lca_proxy_saving_percent"], 0)
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

    def test_available_nsta_candidates_lists_top_ranked_pipeline(self) -> None:
        candidates = available_nsta_candidates(self.nsta_candidates_path, limit=1)

        self.assertEqual(candidates[0]["NSTAPIPNO"], "PL774")
        self.assertEqual(candidates[0]["PIPE_NAME"], "CATS PIPELINE")

    def test_screen_nsta_pipeline_writes_outputs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            row = screen_nsta_pipeline(
                candidates_path=self.nsta_candidates_path,
                defaults_path=self.nsta_defaults_path,
                nsta_id="PL774",
                output_csv_path=temp / "screen.csv",
                trace_path=temp / "trace.json",
                report_path=temp / "report.md",
            )

            self.assertEqual(row["nsta_pipeline_number"], "PL774")
            self.assertEqual(row["pipeline_name"], "CATS PIPELINE")
            self.assertIn(row["pre_lca_decision"], {"pass", "marginal", "fail"})
            self.assertIn(row["corrosion_risk_level"], {"low", "medium", "high"})
            self.assertIn("lca_proxy_saving_percent", row)
            self.assertTrue((temp / "screen.csv").exists())
            self.assertTrue((temp / "trace.json").exists())
            self.assertIn("NSTA pipeline number", (temp / "report.md").read_text(encoding="utf-8"))

    def test_screen_all_nsta_pipelines_writes_batch_outputs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            rows = screen_all_nsta_pipelines(
                candidates_path=self.nsta_candidates_path,
                defaults_path=self.nsta_defaults_path,
                output_csv_path=temp / "batch.csv",
                trace_path=temp / "batch_trace.json",
                report_path=temp / "batch.md",
                limit=3,
            )

            self.assertEqual(len(rows), 3)
            self.assertTrue((temp / "batch.csv").exists())
            self.assertTrue((temp / "batch_trace.json").exists())
            report = (temp / "batch.md").read_text(encoding="utf-8")
            self.assertIn("NSTA Pipeline Batch Screening", report)
            self.assertIn("Screened pipelines: `3`", report)


if __name__ == "__main__":
    unittest.main()
