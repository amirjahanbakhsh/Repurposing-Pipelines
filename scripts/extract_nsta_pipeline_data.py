"""Extract NSTA offshore pipeline data and run basic completeness checks.

This script uses the public ArcGIS FeatureServer for the NSTA UKCS offshore
pipeline linear layer. It writes:

- model_layers/01_data_foundation/nsta_pipeline_attributes.json
- model_layers/01_data_foundation/nsta_pipeline_metadata.json
- model_layers/01_data_foundation/nsta_pipeline_attributes.csv
- model_layers/01_data_foundation/nsta_pipeline_completeness.md

Use `--include-geometry` to also write:

- model_layers/01_data_foundation/nsta_pipeline_linear.geojson
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


LAYER_URL = (
    "https://services-eu1.arcgis.com/OZMfUznmLTnWccBc/arcgis/rest/services/"
    "UKCS%20offshore%20infrastructure%20pipeline%20linear%20ED50/FeatureServer/0"
)

KEY_FIELDS = [
    "FLUID",
    "STATUS",
    "INT_DIAM",
    "MX_OP_PRES",
    "THICKNESS",
    "START_DATE",
]

IDENTITY_FIELDS = [
    "OBJECTID",
    "NSTAPIPNO",
    "PIPE_NAME",
    "PIPE_SYS",
    "DESCRIPTIO",
    "DIAMETERMM",
    "LENGTH_M",
    "END_DATE",
    "END_REAS",
    "UNTRENCHED",
    "EXPOSED",
    "UPD_DATE",
]

HYDROCARBON_FLUIDS = {"GAS", "CONDENSATE", "MIXED HYDROCARBONS"}
POSITIVE_NUMERIC_FIELDS = {"INT_DIAM", "MX_OP_PRES", "THICKNESS", "LENGTH_M"}
MISSING_NUMERIC_SENTINELS = {-9999, -9999.0}


def fetch_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{url}?{query}", timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str):
        stripped = value.strip()
        return stripped == "" or stripped.upper() in {"N/A", "NA", "NULL", "UNKNOWN"}
    return False


def is_usable_value(field: str, value: Any) -> bool:
    if is_missing(value):
        return False
    if field in POSITIVE_NUMERIC_FIELDS:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return False
        if number in MISSING_NUMERIC_SENTINELS:
            return False
        return number > 0
    return True


def arcgis_date_to_iso(value: Any) -> str:
    if is_missing(value):
        return ""
    try:
        milliseconds = int(value)
    except (TypeError, ValueError):
        return str(value)
    epoch = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
    return (epoch + dt.timedelta(milliseconds=milliseconds)).date().isoformat()


def normalise_properties(properties: dict[str, Any], date_fields: set[str]) -> dict[str, Any]:
    cleaned = dict(properties)
    for field in date_fields:
        if field in cleaned:
            cleaned[field] = arcgis_date_to_iso(cleaned[field])
    return cleaned


def count_features() -> int:
    data = fetch_json(
        LAYER_URL + "/query",
        {"f": "json", "where": "1=1", "returnCountOnly": "true"},
    )
    return int(data["count"])


def layer_metadata() -> dict[str, Any]:
    return fetch_json(LAYER_URL, {"f": "json"})


def query_features(
    total_count: int,
    batch_size: int = 1000,
    include_geometry: bool = False,
) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for offset in range(0, total_count, batch_size):
        response_format = "geojson" if include_geometry else "json"
        data = fetch_json(
            LAYER_URL + "/query",
            {
                "f": response_format,
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "true" if include_geometry else "false",
                "orderByFields": "OBJECTID",
                "resultOffset": offset,
                "resultRecordCount": batch_size,
            },
        )
        batch = data.get("features", [])
        features.extend(batch)
        print(f"Fetched {len(features)} / {total_count}", flush=True)
    return features


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def completeness(rows: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    total = len(rows)
    stats: list[dict[str, Any]] = []
    for field in fields:
        present = sum(1 for row in rows if not is_missing(row.get(field)))
        stats.append(
            {
                "field": field,
                "present": present,
                "missing": total - present,
                "completeness": (present / total * 100) if total else 0,
            }
        )
    return stats


def usable_completeness(rows: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    total = len(rows)
    stats: list[dict[str, Any]] = []
    for field in fields:
        usable = sum(1 for row in rows if is_usable_value(field, row.get(field)))
        stats.append(
            {
                "field": field,
                "usable": usable,
                "not_usable": total - usable,
                "usability": (usable / total * 100) if total else 0,
            }
        )
    return stats


def top_values(rows: list[dict[str, Any]], field: str, limit: int = 12) -> list[tuple[str, int]]:
    values = Counter(str(row.get(field)).strip() for row in rows if not is_missing(row.get(field)))
    return values.most_common(limit)


def number_summary(rows: list[dict[str, Any]], field: str) -> dict[str, float | int | None]:
    values: list[float] = []
    for row in rows:
        value = row.get(field)
        if not is_usable_value(field, value):
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    if not values:
        return {"count": 0, "min": None, "median": None, "max": None}
    values.sort()
    midpoint = len(values) // 2
    median = values[midpoint] if len(values) % 2 else (values[midpoint - 1] + values[midpoint]) / 2
    return {"count": len(values), "min": values[0], "median": median, "max": values[-1]}


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]], include_geometry: bool) -> None:
    hydrocarbon_rows = [
        row for row in rows if str(row.get("FLUID", "")).strip().upper() in HYDROCARBON_FLUIDS
    ]
    active_or_not_in_use_hydrocarbon_rows = [
        row
        for row in hydrocarbon_rows
        if str(row.get("STATUS", "")).strip().upper() in {"ACTIVE", "NOT IN USE"}
    ]

    def stats_table(title: str, source_rows: list[dict[str, Any]]) -> str:
        stats = completeness(source_rows, KEY_FIELDS)
        table_rows = [
            [
                stat["field"],
                stat["present"],
                stat["missing"],
                f"{stat['completeness']:.1f}%",
            ]
            for stat in stats
        ]
        return f"## {title}\n\n" + markdown_table(
            ["Field", "Present", "Missing", "Completeness"], table_rows
        )

    def usable_stats_table(title: str, source_rows: list[dict[str, Any]]) -> str:
        stats = usable_completeness(source_rows, KEY_FIELDS)
        table_rows = [
            [
                stat["field"],
                stat["usable"],
                stat["not_usable"],
                f"{stat['usability']:.1f}%",
            ]
            for stat in stats
        ]
        return f"## {title}\n\n" + markdown_table(
            ["Field", "Usable", "Not usable", "Usable completeness"], table_rows
        )

    def rows_with_usable_fields(source_rows: list[dict[str, Any]], fields: list[str]) -> int:
        return sum(
            1
            for row in source_rows
            if all(is_usable_value(field, row.get(field)) for field in fields)
        )

    engineering_fields = ["INT_DIAM", "MX_OP_PRES", "THICKNESS"]
    engineering_fields_with_start = engineering_fields + ["START_DATE"]
    model_ready_rows = [
        [
            "Hydrocarbon candidates",
            len(hydrocarbon_rows),
            rows_with_usable_fields(hydrocarbon_rows, engineering_fields),
            rows_with_usable_fields(hydrocarbon_rows, engineering_fields_with_start),
        ],
        [
            "Active / not-in-use hydrocarbon",
            len(active_or_not_in_use_hydrocarbon_rows),
            rows_with_usable_fields(active_or_not_in_use_hydrocarbon_rows, engineering_fields),
            rows_with_usable_fields(active_or_not_in_use_hydrocarbon_rows, engineering_fields_with_start),
        ],
    ]

    numeric_rows = []
    for field in ["INT_DIAM", "MX_OP_PRES", "THICKNESS", "LENGTH_M"]:
        summary = number_summary(rows, field)
        numeric_rows.append(
            [
                field,
                summary["count"],
                summary["min"],
                summary["median"],
                summary["max"],
            ]
        )

    fluid_rows = [[value, count] for value, count in top_values(rows, "FLUID")]
    status_rows = [[value, count] for value, count in top_values(rows, "STATUS")]

    report = f"""# NSTA Pipeline Completeness Report

Generated: {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

Source layer: {LAYER_URL}

Extraction script: `scripts/extract_nsta_pipeline_data.py`

Total pipeline features: {len(rows)}

Hydrocarbon candidate features (`GAS`, `CONDENSATE`, `MIXED HYDROCARBONS`): {len(hydrocarbon_rows)}

Hydrocarbon features with status `ACTIVE` or `NOT IN USE`: {len(active_or_not_in_use_hydrocarbon_rows)}

Geometry extracted in this run: {"yes" if include_geometry else "no"}

{stats_table("Completeness - All Pipeline Features", rows)}

{stats_table("Completeness - Hydrocarbon Candidate Features", hydrocarbon_rows)}

{usable_stats_table("Usable Completeness - All Pipeline Features", rows)}

{usable_stats_table("Usable Completeness - Hydrocarbon Candidate Features", hydrocarbon_rows)}

{usable_stats_table("Usable Completeness - Active / Not-In-Use Hydrocarbon Features", active_or_not_in_use_hydrocarbon_rows)}

## Combined Readiness For Screening

{markdown_table(["Subset", "Total", "Usable ID + pressure + thickness", "Usable ID + pressure + thickness + start date"], model_ready_rows)}

## Valid Numeric Field Ranges - All Pipeline Features

{markdown_table(["Field", "Count", "Min", "Median", "Max"], numeric_rows)}

## Fluid Values

{markdown_table(["Fluid", "Count"], fluid_rows)}

## Status Values

{markdown_table(["Status", "Count"], status_rows)}

## Notes

- `START_DATE`, `END_DATE`, and `UPD_DATE` are converted from ArcGIS timestamps to ISO dates in the CSV.
- Completeness only checks whether a value is present. It does not prove the value is correct.
- Usable completeness treats `-9999`, zero, negative, and blank values as not usable for numeric engineering fields.
- Wall thickness, internal diameter, and max operating pressure should still be validated for key candidate pipelines before use in engineering calculations.
- Missing or assumed values should be shown clearly in the future app.
- Run `python scripts/extract_nsta_pipeline_data.py --include-geometry` when full map geometry is needed.
- The full GeoJSON geometry extract is large and is ignored by Git in `.gitignore`; use Git LFS or regenerate locally if it needs to be shared.
"""
    path.write_text(report, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-geometry",
        action="store_true",
        help="Also download full pipeline line geometry and write GeoJSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    data_layer = root / "model_layers" / "01_data_foundation"
    data_layer.mkdir(parents=True, exist_ok=True)

    metadata = layer_metadata()
    total_count = count_features()
    features = query_features(total_count, include_geometry=args.include_geometry)

    date_fields = {
        field["name"]
        for field in metadata.get("fields", [])
        if field.get("type") == "esriFieldTypeDate"
    }
    fieldnames = [field["name"] for field in metadata.get("fields", [])]

    if args.include_geometry:
        rows = [
            normalise_properties(feature.get("properties", {}), date_fields)
            for feature in features
        ]
        normalised_features = []
        for feature, row in zip(features, rows):
            updated = dict(feature)
            updated["properties"] = row
            normalised_features.append(updated)

        geojson = {
            "type": "FeatureCollection",
            "name": "nsta_pipeline_linear",
            "source": LAYER_URL,
            "features": normalised_features,
        }
        (data_layer / "nsta_pipeline_linear.geojson").write_text(
            json.dumps(geojson, ensure_ascii=False), encoding="utf-8"
        )
    else:
        rows = [
            normalise_properties(feature.get("attributes", {}), date_fields)
            for feature in features
        ]
        (data_layer / "nsta_pipeline_attributes.json").write_text(
            json.dumps(
                {
                    "source": LAYER_URL,
                    "features": rows,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    (data_layer / "nsta_pipeline_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    write_csv(data_layer / "nsta_pipeline_attributes.csv", rows, fieldnames)
    write_report(
        data_layer / "nsta_pipeline_completeness.md",
        rows,
        include_geometry=args.include_geometry,
    )

    print(f"Wrote {len(rows)} features")
    if args.include_geometry:
        print(data_layer / "nsta_pipeline_linear.geojson")
    else:
        print(data_layer / "nsta_pipeline_attributes.json")
    print(data_layer / "nsta_pipeline_attributes.csv")
    print(data_layer / "nsta_pipeline_completeness.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
