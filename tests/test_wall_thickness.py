"""Tests for wall-thickness pressure sanity checks."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.wall_thickness import (  # noqa: E402
    barlow_minimum_wall_thickness_mm,
    build_nsta_wall_thickness_check_rows,
    pressure_wall_status,
)


class WallThicknessTest(unittest.TestCase):
    def test_barlow_formula_reproduces_goldeneye_sanity_value(self) -> None:
        minimum_wall = barlow_minimum_wall_thickness_mm(
            pressure_mpa=11.996878,
            outer_diameter_mm=508.0,
            smys_mpa=413.7,
            design_factor=0.72,
        )

        self.assertAlmostEqual(minimum_wall, 10.230195, places=5)

    def test_pressure_wall_status_flags_negative_margin(self) -> None:
        status = pressure_wall_status(
            reported_wall_thickness_mm=8.0,
            minimum_wall_thickness_mm=10.0,
            review_margin_fraction=0.20,
        )

        self.assertEqual(status, "fail_sanity")

    def test_nsta_wall_check_builds_rows_for_ranked_candidates(self) -> None:
        rows = build_nsta_wall_thickness_check_rows(
            candidates_path=ROOT / "model_layers" / "01_data_foundation" / "nsta_candidate_ranked.csv",
            defaults_path=ROOT / "model_layers" / "06_screening_and_decision" / "nsta_screening_defaults.csv",
            limit=1,
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["nsta_pipeline_number"], "PL774")
        self.assertGreater(rows[0]["barlow_min_wall_mm"], 0)
        self.assertIn(rows[0]["status"], {"pass_sanity", "review_required", "fail_sanity"})


if __name__ == "__main__":
    unittest.main()
