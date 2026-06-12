"""Tests for applying unit-cost factors to refurbishment work-scope rows."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.refurbishment_cost import (  # noqa: E402
    calculate_refurbishment_costs,
    unit_cost_template_rows,
)


class RefurbishmentCostTest(unittest.TestCase):
    def test_missing_unit_costs_block_final_cost(self) -> None:
        work_scope_rows = [
            {
                "scenario": "test",
                "pipeline_name": "Test pipeline",
                "gate_status": "marginal",
                "work_item_id": "inspection",
                "quantity_low": 8,
                "quantity_base": 10,
                "quantity_high": 12,
                "unit": "km",
                "cost_include": "yes",
                "cost_driver": "inspection_per_km",
            }
        ]

        _rows, summary = calculate_refurbishment_costs(work_scope_rows, {})

        self.assertEqual(summary[0]["refurbishment_cost_status"], "blocked_missing_unit_costs")
        self.assertEqual(summary[0]["missing_cost_drivers"], "inspection_per_km")

    def test_available_unit_costs_calculate_low_base_high(self) -> None:
        work_scope_rows = [
            {
                "scenario": "test",
                "pipeline_name": "Test pipeline",
                "gate_status": "marginal",
                "work_item_id": "inspection",
                "quantity_low": 8,
                "quantity_base": 10,
                "quantity_high": 12,
                "unit": "km",
                "cost_include": "yes",
                "cost_driver": "inspection_per_km",
            },
            {
                "scenario": "test",
                "pipeline_name": "Test pipeline",
                "gate_status": "marginal",
                "work_item_id": "lca_package",
                "quantity_low": 8,
                "quantity_base": 10,
                "quantity_high": 12,
                "unit": "km",
                "cost_include": "no",
                "cost_driver": "not_for_direct_cost_sum",
            },
        ]
        factors = {
            "inspection_per_km": {
                "unit_cost_low_usd_2025": "100",
                "unit_cost_base_usd_2025": "200",
                "unit_cost_high_usd_2025": "300",
                "source": "test",
                "quality": "test",
            }
        }

        rows, summary = calculate_refurbishment_costs(work_scope_rows, factors)

        self.assertEqual(summary[0]["refurbishment_cost_status"], "conditional_result")
        self.assertEqual(summary[0]["cost_low_usd_2025"], 800)
        self.assertEqual(summary[0]["cost_base_usd_2025"], 2000)
        self.assertEqual(summary[0]["cost_high_usd_2025"], 3600)
        self.assertEqual(rows[1]["factor_status"], "not_required")

    def test_template_contains_current_work_scope_drivers(self) -> None:
        drivers = {row["cost_driver"] for row in unit_cost_template_rows()}

        self.assertIn("inspection_per_km", drivers)
        self.assertIn("cleaning_drying_per_km", drivers)
        self.assertIn("replacement_steel_kg", drivers)


if __name__ == "__main__":
    unittest.main()
