"""Tests for standalone LCA activity metadata extraction."""

from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.lca_activity_extraction import (  # noqa: E402
    default_activity_queries,
    extract_activity_candidates,
    extract_lca_activity_data,
    preferred_mapping_rows,
)


class LcaActivityExtractionTest(unittest.TestCase):
    def test_activity_candidates_match_expected_mapping(self) -> None:
        rows = [
            {
                "source_name": "test",
                "activity_name": "steel production, low-alloyed, hot rolled",
                "location": "RER",
                "reference_product": "steel, low-alloyed, hot rolled",
                "unit": "kg",
            },
            {
                "source_name": "test",
                "activity_name": "market for diesel, low-sulfur",
                "location": "Europe without Switzerland",
                "reference_product": "diesel, low-sulfur",
                "unit": "MJ",
            },
        ]

        candidates = extract_activity_candidates(
            source_rows=rows,
            queries=default_activity_queries(),
            max_per_mapping=3,
        )

        steel = [row for row in candidates if row["mapping_key"] == "pipeline_steel"][0]
        diesel = [row for row in candidates if row["mapping_key"] == "diesel_machinery"][0]
        self.assertEqual(steel["activity_name"], "steel production, low-alloyed, hot rolled")
        self.assertEqual(diesel["reference_product"], "diesel, low-sulfur")

    def test_project_package_is_not_treated_as_single_database_activity(self) -> None:
        rows = [
            {
                "source_name": "test",
                "activity_name": "market for diesel, low-sulfur",
                "location": "Europe without Switzerland",
                "reference_product": "diesel, low-sulfur",
                "unit": "MJ",
            },
        ]
        queries = default_activity_queries()
        candidates = extract_activity_candidates(
            source_rows=rows,
            queries=queries,
            max_per_mapping=3,
        )

        preferred = preferred_mapping_rows(candidates, queries)

        refurbishment = [
            row for row in preferred if row["mapping_key"] == "refurbishment_activity"
        ][0]
        self.assertEqual(
            refurbishment["activity_name"],
            "user-defined pipeline refurbishment package",
        )
        self.assertEqual(refurbishment["review_status"], "needs_private_package_factor")

    def test_standalone_extractor_writes_outputs_from_lookup(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            ecoinvent = temp / "ecoinvent"
            datasets = ecoinvent / "datasets"
            datasets.mkdir(parents=True)
            (datasets / "dummy.spold").write_text("<xml/>", encoding="utf-8")
            lookup = ecoinvent / "FilenameToActivtiyLookup.csv"
            lookup.write_text(
                "FileName;ActivityName;Location;ReferenceProduct;Unit\n"
                "steel.spold;steel production, low-alloyed, hot rolled;RER;steel, low-alloyed, hot rolled;kg\n"
                "pipe.spold;market for pipeline, natural gas, long distance, high capacity, offshore;GLO;pipeline, natural gas, long distance, high capacity, offshore;km\n",
                encoding="utf-8",
            )

            summary = extract_lca_activity_data(
                ecoinvent_dir=ecoinvent,
                activity_csvs=[],
                query_path=None,
                candidates_path=temp / "candidates.csv",
                preferred_mapping_path=temp / "preferred.csv",
                report_path=temp / "report.md",
                max_per_mapping=2,
            )

            self.assertEqual(summary["source_count"], 1)
            self.assertTrue((temp / "candidates.csv").exists())
            self.assertTrue((temp / "preferred.csv").exists())
            report = (temp / "report.md").read_text(encoding="utf-8")
            self.assertIn("activity metadata only", report)
            self.assertIn("pipeline_steel", report)


if __name__ == "__main__":
    unittest.main()
