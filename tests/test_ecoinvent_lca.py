"""Tests for the ecoinvent-linked LCA workflow."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.assumptions import read_scenario_assumptions  # noqa: E402
from repurposing_pipelines.lca import (  # noqa: E402
    build_pipeline_lca_inventory,
    calculate_ecoinvent_impacts,
    read_process_mapping,
    screening_impact_factor_rows,
)


class EcoinventLcaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        assumptions_path = (
            ROOT
            / "model_layers"
            / "06_screening_and_decision"
            / "goldeneye_assumptions.csv"
        )
        mapping_path = ROOT / "model_layers" / "05_lca" / "lca_process_mapping.csv"
        cls.scenario = read_scenario_assumptions(assumptions_path)["goldeneye_poster"]
        cls.process_mapping = read_process_mapping(mapping_path)

    def test_inventory_contains_new_build_and_reuse_rows(self) -> None:
        rows = build_pipeline_lca_inventory(
            self.scenario,
            process_mapping=self.process_mapping,
        )
        row_names = {row["inventory_item"] for row in rows}

        self.assertIn("pipeline_steel_mass", row_names)
        self.assertIn("offshore_pipeline_construction", row_names)
        self.assertIn("refurbishment_steel", row_names)
        self.assertIn("pipeline_refurbishment_activity", row_names)

    def test_inventory_can_use_quantified_work_scope_rows(self) -> None:
        rows = build_pipeline_lca_inventory(
            self.scenario,
            process_mapping=self.process_mapping,
            work_scope_rows=[
                {
                    "work_item_id": "replacement_or_refurbishment_steel",
                    "quantity_low": 90,
                    "quantity_base": 100,
                    "quantity_high": 110,
                    "data_quality": "test_work_scope",
                },
                {
                    "work_item_id": "refurbishment_activity_package",
                    "quantity_low": 8,
                    "quantity_base": 10,
                    "quantity_high": 12,
                    "data_quality": "test_package",
                },
            ],
        )

        by_item = {row["inventory_item"]: row for row in rows}
        self.assertEqual(by_item["refurbishment_steel"]["quantity_base"], 100)
        self.assertEqual(by_item["refurbishment_steel"]["data_quality"], "test_work_scope")
        self.assertEqual(
            by_item["pipeline_refurbishment_activity"]["quantity_base"],
            10,
        )
        self.assertEqual(
            by_item["pipeline_refurbishment_activity"]["data_quality"],
            "test_package",
        )

    def test_missing_private_factors_blocks_final_lca_claim(self) -> None:
        inventory_rows = build_pipeline_lca_inventory(
            self.scenario,
            process_mapping=self.process_mapping,
        )
        _impact_rows, summary = calculate_ecoinvent_impacts(
            inventory_rows,
            {},
            pre_lca_decision="marginal",
        )

        missing = set(summary["missing_mapping_keys"].split("; "))
        self.assertEqual(summary["lca_status"], "blocked_missing_impact_factors")
        self.assertEqual(
            missing,
            {
                "pipeline_steel",
                "offshore_pipeline_construction",
                "refurbishment_activity",
            },
        )

    def test_private_factors_enable_conditional_lca_calculation(self) -> None:
        inventory_rows = build_pipeline_lca_inventory(
            self.scenario,
            process_mapping=self.process_mapping,
        )
        fake_factors = {
            "pipeline_steel": {"impact_factor_kgco2e_per_unit": 2.1},
            "offshore_pipeline_construction": {"impact_factor_kgco2e_per_unit": 95000},
            "refurbishment_activity": {"impact_factor_kgco2e_per_unit": 18000},
        }
        _impact_rows, summary = calculate_ecoinvent_impacts(
            inventory_rows,
            fake_factors,
            pre_lca_decision="marginal",
        )

        self.assertEqual(summary["lca_status"], "conditional_result")
        self.assertEqual(summary["missing_factor_count"], 0)
        self.assertGreater(summary["new_build_kgco2e_base"], 0)
        self.assertGreater(summary["reuse_kgco2e_base"], 0)
        self.assertGreater(summary["saving_kgco2e_base"], 0)

    def test_screening_factors_enable_screening_lca_result(self) -> None:
        inventory_rows = build_pipeline_lca_inventory(
            self.scenario,
            process_mapping=self.process_mapping,
        )
        factors = {
            row["mapping_key"]: {
                **row,
                "impact_factor_kgco2e_per_unit": float(row["impact_factor_kgco2e_per_unit"]),
            }
            for row in screening_impact_factor_rows()
        }

        _impact_rows, summary = calculate_ecoinvent_impacts(
            inventory_rows,
            factors,
            pre_lca_decision="marginal",
        )

        self.assertEqual(summary["lca_status"], "screening_result")
        self.assertEqual(summary["missing_factor_count"], 0)
        self.assertEqual(summary["factor_quality_summary"], "screening_default_unvalidated")


if __name__ == "__main__":
    unittest.main()
