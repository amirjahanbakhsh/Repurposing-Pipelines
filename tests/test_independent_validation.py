"""Tests for independent validation checks."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.assumptions import read_scenario_assumptions  # noqa: E402
from repurposing_pipelines.validation import (  # noqa: E402
    validate_co2_properties,
    validate_integrity_barlow_sanity,
)


class IndependentValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        assumptions_path = (
            ROOT
            / "model_layers"
            / "06_screening_and_decision"
            / "goldeneye_assumptions.csv"
        )
        cls.scenarios = read_scenario_assumptions(assumptions_path)

    def test_coolprop_property_validation_passes_density_for_goldeneye(self) -> None:
        try:
            rows = validate_co2_properties(self.scenarios)
        except RuntimeError as exc:
            self.skipTest(str(exc))

        density_rows = [
            row
            for row in rows
            if row["scenario"] == "goldeneye_poster"
            and row["parameter"] == "density_kg_per_m3"
        ]
        self.assertEqual(density_rows[0]["status"], "pass")
        self.assertLess(density_rows[0]["absolute_difference_percent"], 1.0)

    def test_barlow_sanity_check_flags_goldeneye_minimum_wall_basis(self) -> None:
        rows = validate_integrity_barlow_sanity(self.scenarios)
        poster = [row for row in rows if row["scenario"] == "goldeneye_poster"][0]

        self.assertEqual(poster["status"], "review_required")
        self.assertGreater(poster["barlow_min_wall_mm"], poster["scenario_min_wall_mm"])


if __name__ == "__main__":
    unittest.main()
