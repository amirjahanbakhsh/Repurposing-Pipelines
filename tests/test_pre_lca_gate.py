"""Tests for the pre-LCA decision gate."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.gates import evaluate_pre_lca_gate  # noqa: E402
from repurposing_pipelines.trace import InputRecord, ModuleResult, OutputRecord  # noqa: E402


def module(name: str, status: str, outputs: list[OutputRecord]) -> ModuleResult:
    return ModuleResult(module=name, model_version="test", status=status, outputs=outputs)


class PreLcaGateTest(unittest.TestCase):
    def test_gate_passes_when_modules_pass_and_inputs_are_strong(self) -> None:
        capacity = ModuleResult(
            module="capacity",
            model_version="test",
            status="pass",
            inputs=[InputRecord("inner_diameter_in", 18.0, "in", quality="reported")],
            outputs=[
                OutputRecord("capacity_mtpa", 10.0),
                OutputRecord("required_design_mtpa", 5.0),
            ],
        )
        integrity = module(
            "integrity",
            "pass",
            [
                OutputRecord("remaining_life_years", 30.0),
                OutputRecord("available_wall_thickness_mm", 5.0),
            ],
        )
        cost = module("cost", "pass", [OutputRecord("cost_total_usd_2025", 100_000_000)])

        result = evaluate_pre_lca_gate(capacity=capacity, integrity=integrity, cost=cost)

        self.assertEqual(result.status, "pass")
        self.assertEqual(result.output_map()["pre_lca_decision"], "pass")

    def test_gate_is_marginal_when_assumptions_remain(self) -> None:
        capacity = ModuleResult(
            module="capacity",
            model_version="test",
            status="pass",
            inputs=[InputRecord("inner_diameter_in", 18.0, "in", quality="assumed")],
            outputs=[
                OutputRecord("capacity_mtpa", 10.0),
                OutputRecord("required_design_mtpa", 5.0),
            ],
        )
        integrity = module(
            "integrity",
            "pass",
            [
                OutputRecord("remaining_life_years", 30.0),
                OutputRecord("available_wall_thickness_mm", 5.0),
            ],
        )
        cost = module("cost", "pass", [OutputRecord("cost_total_usd_2025", 100_000_000)])

        result = evaluate_pre_lca_gate(capacity=capacity, integrity=integrity, cost=cost)

        self.assertEqual(result.status, "marginal")
        self.assertIn("inner_diameter_in", result.output_map()["pre_lca_reasons"])

    def test_gate_fails_when_upstream_module_fails(self) -> None:
        capacity = module(
            "capacity",
            "fail",
            [
                OutputRecord("capacity_mtpa", 3.0),
                OutputRecord("required_design_mtpa", 5.0),
            ],
        )
        integrity = module(
            "integrity",
            "pass",
            [
                OutputRecord("remaining_life_years", 30.0),
                OutputRecord("available_wall_thickness_mm", 5.0),
            ],
        )
        cost = module("cost", "pass", [OutputRecord("cost_total_usd_2025", 100_000_000)])

        result = evaluate_pre_lca_gate(capacity=capacity, integrity=integrity, cost=cost)

        self.assertEqual(result.status, "fail")
        self.assertIn("capacity", result.output_map()["pre_lca_reasons"])

    def test_gate_reports_insufficient_data_when_outputs_are_missing(self) -> None:
        capacity = module("capacity", "pass", [OutputRecord("capacity_mtpa", 10.0)])
        integrity = module(
            "integrity",
            "pass",
            [
                OutputRecord("remaining_life_years", 30.0),
                OutputRecord("available_wall_thickness_mm", 5.0),
            ],
        )
        cost = module("cost", "pass", [OutputRecord("cost_total_usd_2025", 100_000_000)])

        result = evaluate_pre_lca_gate(capacity=capacity, integrity=integrity, cost=cost)

        self.assertEqual(result.status, "insufficient_data")
        self.assertIn("required_design_mtpa", result.warnings[0].message)


if __name__ == "__main__":
    unittest.main()
