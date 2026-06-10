"""Regression tests for the Goldeneye benchmark scenarios."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.assumptions import read_scenario_assumptions  # noqa: E402
from repurposing_pipelines.goldeneye import benchmark_scenario_with_trace  # noqa: E402


class GoldeneyeBenchmarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        assumptions_path = (
            ROOT
            / "model_layers"
            / "06_screening_and_decision"
            / "goldeneye_assumptions.csv"
        )
        cls.scenarios = read_scenario_assumptions(assumptions_path)

    def test_dissertation_case_reproduces_headline_outputs(self) -> None:
        row, trace = benchmark_scenario_with_trace(
            "goldeneye_dissertation",
            self.scenarios["goldeneye_dissertation"],
        )

        self.assertAlmostEqual(row["capacity_mtpa"], 9.1307297977, places=6)
        self.assertAlmostEqual(row["remaining_life_years"], 77.94, places=2)
        self.assertEqual(row["cost_total_usd_2025"], 228_500_811)
        self.assertEqual(row["capacity_suitable"], "yes")
        self.assertEqual(row["pre_lca_decision"], "marginal")
        self.assertEqual(row["pre_lca_confidence"], "medium")
        self.assertEqual([result["module"] for result in trace["module_results"]], [
            "capacity",
            "corrosion",
            "integrity",
            "cost",
            "pre_lca_gate",
            "lca",
        ])
        self.assertEqual(row["corrosion_risk_level"], "medium")
        self.assertGreater(row["remaining_life_high_years"], row["remaining_life_years"])
        self.assertGreater(row["lca_proxy_saving_percent"], 0)

    def test_poster_case_reproduces_headline_outputs(self) -> None:
        row, trace = benchmark_scenario_with_trace(
            "goldeneye_poster",
            self.scenarios["goldeneye_poster"],
        )

        self.assertAlmostEqual(row["capacity_mtpa"], 9.9684465137, places=6)
        self.assertAlmostEqual(row["remaining_life_years"], 24.55, places=2)
        self.assertEqual(row["cost_total_usd_2025"], 228_500_811)
        self.assertEqual(row["capacity_suitable"], "yes")
        self.assertEqual(row["pre_lca_decision"], "marginal")
        self.assertIn("assumptions", row["pre_lca_reason_summary"])
        self.assertEqual(row["corrosion_risk_level"], "medium")
        self.assertGreater(row["remaining_life_high_years"], row["remaining_life_years"])
        self.assertGreater(row["lca_proxy_saving_percent"], 0)
        self.assertEqual(trace["model_version"], "goldeneye_benchmark_v0.4")


if __name__ == "__main__":
    unittest.main()
