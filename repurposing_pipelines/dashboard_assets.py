"""Helpers for building lightweight dashboard assets."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _normalise_pipeline_id(value: Any) -> str:
    return str(value or "").strip().upper()


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _downsample_path(path: list[list[float]], max_points: int) -> list[list[float]]:
    if max_points < 2 or len(path) <= max_points:
        return path
    step = (len(path) - 1) / float(max_points - 1)
    sampled: list[list[float]] = []
    last_index = -1
    for sample_index in range(max_points):
        source_index = round(sample_index * step)
        if source_index == last_index:
            continue
        sampled.append(path[source_index])
        last_index = source_index
    if sampled[-1] != path[-1]:
        sampled.append(path[-1])
    return sampled


def _clean_path(raw_path: list[Any], max_points: int) -> list[list[float]]:
    cleaned: list[list[float]] = []
    for point in raw_path:
        if not isinstance(point, list) or len(point) < 2:
            continue
        lon = _float_or_none(point[0])
        lat = _float_or_none(point[1])
        if lon is None or lat is None:
            continue
        cleaned.append([round(lon, 6), round(lat, 6)])
    return _downsample_path(cleaned, max_points)


def _geometry_paths(geometry: dict[str, Any], max_points: int) -> list[list[list[float]]]:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geometry_type == "LineString" and isinstance(coordinates, list):
        path = _clean_path(coordinates, max_points)
        return [path] if len(path) >= 2 else []
    if geometry_type == "MultiLineString" and isinstance(coordinates, list):
        paths: list[list[list[float]]] = []
        for raw_path in coordinates:
            if isinstance(raw_path, list):
                path = _clean_path(raw_path, max_points)
                if len(path) >= 2:
                    paths.append(path)
        return paths
    return []


def _path_bounds(path: list[list[float]]) -> dict[str, float]:
    longitudes = [point[0] for point in path]
    latitudes = [point[1] for point in path]
    return {
        "min_lon": min(longitudes),
        "max_lon": max(longitudes),
        "min_lat": min(latitudes),
        "max_lat": max(latitudes),
    }


def _portable_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def build_candidate_route_asset(
    *,
    raw_geojson_path: Path,
    ranked_csv_path: Path,
    output_path: Path,
    max_points_per_part: int = 220,
) -> dict[str, Any]:
    """Create a compact route JSON for the Streamlit dashboard (candidates only)."""

    with ranked_csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        ranked_rows = list(csv.DictReader(handle))

    ranked_by_id = {
        _normalise_pipeline_id(row.get("NSTAPIPNO")): row
        for row in ranked_rows
        if _normalise_pipeline_id(row.get("NSTAPIPNO"))
    }

    with raw_geojson_path.open("r", encoding="utf-8") as handle:
        raw_geojson = json.load(handle)

    route_records: list[dict[str, Any]] = []
    feature_count_by_pipeline: dict[str, int] = {}

    for feature in raw_geojson.get("features", []):
        properties = feature.get("properties") or {}
        pipeline_id = _normalise_pipeline_id(properties.get("NSTAPIPNO"))
        if pipeline_id not in ranked_by_id:
            continue
        ranked = ranked_by_id[pipeline_id]
        paths = _geometry_paths(feature.get("geometry") or {}, max_points_per_part)
        for part_index, path in enumerate(paths, start=1):
            bounds = _path_bounds(path)
            feature_count_by_pipeline[pipeline_id] = feature_count_by_pipeline.get(pipeline_id, 0) + 1
            route_records.append(
                {
                    "pipeline_id": pipeline_id,
                    "pipeline_name": properties.get("PIPE_NAME") or ranked.get("PIPE_NAME") or pipeline_id,
                    "rank": int(float(ranked.get("RANK") or 0)),
                    "screening_score": _float_or_none(ranked.get("SCREENING_SCORE")),
                    "fluid": properties.get("FLUID") or ranked.get("FLUID"),
                    "status": properties.get("STATUS") or ranked.get("STATUS"),
                    "length_km": _float_or_none(ranked.get("LENGTH_KM") or properties.get("LENGTH_M")),
                    "part_index": part_index,
                    "path": path,
                    "start": path[0],
                    "end": path[-1],
                    "bounds": bounds,
                }
            )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_geojson": _portable_path(raw_geojson_path),
        "source_ranked_csv": _portable_path(ranked_csv_path),
        "candidate_count": len(ranked_by_id),
        "route_part_count": len(route_records),
        "pipelines_with_routes": len(feature_count_by_pipeline),
        "max_points_per_part": max_points_per_part,
        "routes": route_records,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")

    return {
        "candidate_count": len(ranked_by_id),
        "route_part_count": len(route_records),
        "pipelines_with_routes": len(feature_count_by_pipeline),
        "output_path": str(output_path),
    }


def build_all_routes_asset(
    *,
    raw_geojson_path: Path,
    ranked_csv_path: Path,
    output_path: Path,
    max_points_per_part: int = 60,
) -> dict[str, Any]:
    """Create a compact route JSON for ALL NSTA pipelines.

    Candidates (those in ranked_csv_path) are tagged is_candidate=True so the
    map can colour them differently.  Non-candidates are still pickable so users
    can click any pipeline to view its properties.
    """

    with ranked_csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        ranked_rows = list(csv.DictReader(handle))

    ranked_by_id: dict[str, dict[str, Any]] = {
        _normalise_pipeline_id(row.get("NSTAPIPNO")): row
        for row in ranked_rows
        if _normalise_pipeline_id(row.get("NSTAPIPNO"))
    }

    with raw_geojson_path.open("r", encoding="utf-8") as handle:
        raw_geojson = json.load(handle)

    route_records: list[dict[str, Any]] = []
    feature_count_by_pipeline: dict[str, int] = {}
    all_pipeline_ids: set[str] = set()

    for feature in raw_geojson.get("features", []):
        properties = feature.get("properties") or {}
        pipeline_id = _normalise_pipeline_id(properties.get("NSTAPIPNO"))
        if not pipeline_id:
            continue

        is_candidate = pipeline_id in ranked_by_id
        ranked = ranked_by_id.get(pipeline_id, {})

        paths = _geometry_paths(feature.get("geometry") or {}, max_points_per_part)
        for part_index, path in enumerate(paths, start=1):
            bounds = _path_bounds(path)
            feature_count_by_pipeline[pipeline_id] = feature_count_by_pipeline.get(pipeline_id, 0) + 1
            all_pipeline_ids.add(pipeline_id)

            length_m = _float_or_none(properties.get("LENGTH_M"))
            length_km_val = _float_or_none(ranked.get("LENGTH_KM")) or (
                length_m / 1000.0 if length_m is not None else None
            )

            route_records.append(
                {
                    "pipeline_id": pipeline_id,
                    "pipeline_name": (
                        properties.get("PIPE_NAME") or ranked.get("PIPE_NAME") or pipeline_id
                    ),
                    "is_candidate": is_candidate,
                    "rank": int(float(ranked.get("RANK") or 0)) if is_candidate else None,
                    "screening_score": _float_or_none(ranked.get("SCREENING_SCORE")) if is_candidate else None,
                    "fluid": properties.get("FLUID") or ranked.get("FLUID") or "",
                    "status": properties.get("STATUS") or ranked.get("STATUS") or "",
                    "diameter_mm": _float_or_none(properties.get("DIAMETERMM")),
                    "length_km": length_km_val,
                    "max_op_pressure": _float_or_none(
                        ranked.get("MX_OP_PRES") or properties.get("MX_OP_PRES")
                    ),
                    "operator": properties.get("REP_OPERTR") or "",
                    "part_index": part_index,
                    "path": path,
                    "start": path[0],
                    "end": path[-1],
                    "bounds": bounds,
                }
            )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_geojson": _portable_path(raw_geojson_path),
        "source_ranked_csv": _portable_path(ranked_csv_path),
        "total_pipeline_count": len(all_pipeline_ids),
        "candidate_count": len(ranked_by_id),
        "route_part_count": len(route_records),
        "pipelines_with_routes": len(feature_count_by_pipeline),
        "max_points_per_part": max_points_per_part,
        "routes": route_records,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, separators=(",", ":"))
        handle.write("\n")

    return {
        "total_pipeline_count": len(all_pipeline_ids),
        "candidate_count": len(ranked_by_id),
        "route_part_count": len(route_records),
        "pipelines_with_routes": len(feature_count_by_pipeline),
        "output_path": str(output_path),
    }
