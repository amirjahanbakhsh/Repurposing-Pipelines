"""Build lightweight files used by the Streamlit dashboard."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.dashboard_assets import (  # noqa: E402
    build_candidate_route_asset,
    build_all_routes_asset,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-geojson",
        type=Path,
        default=ROOT / "data" / "raw" / "nsta_pipeline_linear.geojson",
        help="Raw NSTA pipeline GeoJSON extracted by scripts/extract_nsta_pipeline_data.py.",
    )
    parser.add_argument(
        "--ranked-csv",
        type=Path,
        default=ROOT / "model_layers" / "01_data_foundation" / "nsta_candidate_ranked.csv",
        help="Ranked NSTA candidate CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "app" / "assets" / "nsta_candidate_routes.json",
        help="Compact dashboard route JSON to create.",
    )
    parser.add_argument(
        "--max-points-per-part",
        type=int,
        default=220,
        help="Maximum points retained for each route part for visual rendering.",
    )
    parser.add_argument(
        "--output-all",
        type=Path,
        default=ROOT / "app" / "assets" / "nsta_all_routes.json",
        help="Compact route JSON with ALL NSTA pipelines (for full map view).",
    )
    parser.add_argument(
        "--max-points-all",
        type=int,
        default=60,
        help="Max points per route part in the all-pipelines asset (lower = smaller file).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_candidate_route_asset(
        raw_geojson_path=args.raw_geojson,
        ranked_csv_path=args.ranked_csv,
        output_path=args.output,
        max_points_per_part=args.max_points_per_part,
    )
    print("Dashboard route asset created")
    for key, value in summary.items():
        print(f"{key}: {value}")

    print("")
    print("Building all-pipelines route asset …")
    all_summary = build_all_routes_asset(
        raw_geojson_path=args.raw_geojson,
        ranked_csv_path=args.ranked_csv,
        output_path=args.output_all,
        max_points_per_part=args.max_points_all,
    )
    print("All-pipelines route asset created")
    for key, value in all_summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
