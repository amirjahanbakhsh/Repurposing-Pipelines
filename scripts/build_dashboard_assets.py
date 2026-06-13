"""Build lightweight files used by the Streamlit dashboard."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repurposing_pipelines.dashboard_assets import build_candidate_route_asset  # noqa: E402


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


if __name__ == "__main__":
    main()
