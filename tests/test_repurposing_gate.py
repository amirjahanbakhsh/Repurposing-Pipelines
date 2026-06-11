"""Tests for the evidence-based repurposing gate."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.assumptions import AssumptionValue, ScenarioAssumptions  # noqa: E402
from repurposing_pipelines.repurposing_gate import evaluate_repurposing_gate  # noqa: E402
from repurposing_pipelines.trace import ModuleResult, OutputRecord  # noqa: E402


def record(parameter: str, value: object, quality: str = "reported") -> AssumptionValue:
    return AssumptionValue(
        scenario="test",
        parameter=parameter,
        value=str(value),
        unit="",
        source="test",
        quality=quality,
        notes="test value",
    )


def scenario(**overrides: object) -> ScenarioAssumptions:
    values: dict[str, object] = {
        "pipeline_length_km": 10,
        "inner_diameter_in": 20,
        "nominal_wall_thickness_mm": 15,
        "minimum_wall_thickness_mm": 8,
        "pipe_grade": "X60",
        "inlet_pressure_psia": 1500,
        "outlet_pressure_psia": 1000,
        "transport_temperature_c": 12,
        "target_co2_phase": "gas_phase",
        "co2_water_content_ppmv": 30,
        "co2_water_spec_limit_ppmv": 40,
        "water_dew_point_margin_c": 8,
        "co2_composition_known": "yes",
        "material_certificates_available": "yes",
        "fracture_toughness_basis": "yes",
        "ili_mfl_available": "yes",
        "component_compatibility_screened": "yes",
        "lca_refurbishment_steel_fraction": 0.05,
    }
    values.update(overrides)
    records = {key: record(key, value) for key, value in values.items()}
    return ScenarioAssumptions(name="test", records=records)


def module(name: str, status: str, outputs: list[OutputRecord]) -> ModuleResult:
    return ModuleResult(module=name, model_version="test", status=status, outputs=outputs)


class RepurposingGateTest(unittest.TestCase):
    def test_gate_is_marginal_when_imr_work_scope_remains(self) -> None:
        capacity = module("capacity", "pass", [OutputRecord("average_pressure_mpa", 5.0)])
        corrosion = module("corrosion", "pass", [OutputRecord("corrosion_risk_level", "low")])
        integrity = module(
            "integrity",
            "pass",
            [
                OutputRecord("remaining_life_low_years", 20),
                OutputRecord("available_wall_thickness_mm", 5),
            ],
        )

        result = evaluate_repurposing_gate(
            scenario(),
            capacity=capacity,
            corrosion=corrosion,
            integrity=integrity,
        )

        outputs = result.output_map()
        self.assertEqual(result.status, "marginal")
        self.assertEqual(outputs["repurposing_phase_status"], "gas_phase_selected")
        self.assertGreaterEqual(outputs["repurposing_evidence_score"], 90)
        self.assertIn("co2_leak_detection_isolation_and_imr_plan", outputs["repurposing_work_scope_items"])
        self.assertIn("REF_OSTBY", outputs["repurposing_gate_cited_references"])

    def test_gate_fails_when_upstream_integrity_fails(self) -> None:
        capacity = module("capacity", "pass", [OutputRecord("average_pressure_mpa", 9.0)])
        corrosion = module("corrosion", "pass", [OutputRecord("corrosion_risk_level", "medium")])
        integrity = module(
            "integrity",
            "fail",
            [
                OutputRecord("remaining_life_low_years", 0),
                OutputRecord("available_wall_thickness_mm", -1),
            ],
        )

        result = evaluate_repurposing_gate(
            scenario(
                target_co2_phase="dense_phase",
                material_certificates_available="unknown",
                ili_mfl_available="unknown",
            ),
            capacity=capacity,
            corrosion=corrosion,
            integrity=integrity,
        )

        outputs = result.output_map()
        self.assertEqual(result.status, "fail")
        self.assertIn("integrity module failed", outputs["repurposing_showstoppers"])
        self.assertIn("fracture_and_decompression_screen", outputs["repurposing_work_scope_items"])


if __name__ == "__main__":
    unittest.main()
