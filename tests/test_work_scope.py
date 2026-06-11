"""Tests for quantified refurbishment work-scope generation."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.assumptions import read_scenario_assumptions  # noqa: E402
from repurposing_pipelines.corrosion import evaluate_corrosion  # noqa: E402
from repurposing_pipelines.hydraulics import evaluate_capacity  # noqa: E402
from repurposing_pipelines.integrity import evaluate_integrity  # noqa: E402
from repurposing_pipelines.repurposing_gate import evaluate_repurposing_gate  # noqa: E402
from repurposing_pipelines.work_scope import (  # noqa: E402
    build_refurbishment_work_scope_rows,
    evaluate_refurbishment_work_scope,
)


class WorkScopeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        assumptions_path = (
            ROOT
            / "model_layers"
            / "06_screening_and_decision"
            / "goldeneye_assumptions.csv"
        )
        cls.scenario = read_scenario_assumptions(assumptions_path)["goldeneye_poster"]

    def test_gate_items_become_quantified_cost_and_lca_rows(self) -> None:
        capacity = evaluate_capacity(self.scenario)
        corrosion = evaluate_corrosion(self.scenario)
        integrity = evaluate_integrity(self.scenario, corrosion=corrosion)
        gate = evaluate_repurposing_gate(
            self.scenario,
            capacity=capacity,
            corrosion=corrosion,
            integrity=integrity,
        )

        rows = build_refurbishment_work_scope_rows(
            self.scenario,
            repurposing_gate=gate,
            integrity=integrity,
        )
        result = evaluate_refurbishment_work_scope(
            self.scenario,
            repurposing_gate=gate,
            integrity=integrity,
        )

        ids = {row["work_item_id"] for row in rows}
        self.assertIn("cleaning_drying_and_debris_assessment", ids)
        self.assertIn("replacement_or_refurbishment_steel", ids)
        self.assertIn("refurbishment_activity_package", ids)
        replacement = [
            row for row in rows if row["work_item_id"] == "replacement_or_refurbishment_steel"
        ][0]
        package = [
            row for row in rows if row["work_item_id"] == "refurbishment_activity_package"
        ][0]
        self.assertGreater(replacement["quantity_base"], 0)
        self.assertEqual(replacement["lca_mapping_key"], "pipeline_steel")
        self.assertEqual(package["quantity_base"], 101.68)
        self.assertEqual(package["lca_mapping_key"], "refurbishment_activity")
        self.assertEqual(result.output_map()["refurbishment_work_scope_item_count"], len(rows))


if __name__ == "__main__":
    unittest.main()
