import csv
import json
import tempfile
import unittest
from pathlib import Path

from repurposing_pipelines.dashboard_assets import build_candidate_route_asset


class DashboardAssetTests(unittest.TestCase):
    def test_build_candidate_route_asset_filters_and_downsamples(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ranked_path = root / "ranked.csv"
            raw_path = root / "raw.geojson"
            output_path = root / "routes.json"

            with ranked_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["RANK", "SCREENING_SCORE", "NSTAPIPNO", "PIPE_NAME", "FLUID", "STATUS", "LENGTH_KM"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "RANK": "1",
                        "SCREENING_SCORE": "75",
                        "NSTAPIPNO": "PL1",
                        "PIPE_NAME": "Test pipeline",
                        "FLUID": "GAS",
                        "STATUS": "ACTIVE",
                        "LENGTH_KM": "10",
                    }
                )

            raw_payload = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "NSTAPIPNO": "PL1",
                            "PIPE_NAME": "Test pipeline",
                            "FLUID": "GAS",
                            "STATUS": "ACTIVE",
                        },
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[float(index), 57.0] for index in range(10)],
                        },
                    },
                    {
                        "type": "Feature",
                        "properties": {"NSTAPIPNO": "PL999"},
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[0.0, 58.0], [1.0, 58.0]],
                        },
                    },
                ],
            }
            raw_path.write_text(json.dumps(raw_payload), encoding="utf-8")

            summary = build_candidate_route_asset(
                raw_geojson_path=raw_path,
                ranked_csv_path=ranked_path,
                output_path=output_path,
                max_points_per_part=4,
            )

            self.assertEqual(summary["candidate_count"], 1)
            self.assertEqual(summary["route_part_count"], 1)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["routes"][0]["pipeline_id"], "PL1")
            self.assertLessEqual(len(payload["routes"][0]["path"]), 5)
            self.assertEqual(payload["routes"][0]["path"][0], [0.0, 57.0])
            self.assertEqual(payload["routes"][0]["path"][-1], [9.0, 57.0])


if __name__ == "__main__":
    unittest.main()
