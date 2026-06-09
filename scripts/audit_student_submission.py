"""Audit student notebooks and pipeline GeoJSON for traceability risks.

This script does not run the student model. It inspects structure, key fields,
and overlap with our processed NSTA tables.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ENGINEERING_FIELDS = [
    "NSTAPIPNO",
    "PIPE_NAME",
    "FLUID",
    "STATUS",
    "DIAMETERMM",
    "INT_DIAM",
    "MX_OP_PRES",
    "THICKNESS",
    "OD_IN",
    "ID_IN",
    "PIPE_GRADE",
    "START_DATE",
]


def load_notebook(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def cell_source(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return str(source)


def notebook_summary(path: Path) -> dict[str, Any]:
    notebook = load_notebook(path)
    cells = notebook.get("cells", [])
    code_cells = [cell for cell in cells if cell.get("cell_type") == "code"]
    markdown_cells = [cell for cell in cells if cell.get("cell_type") == "markdown"]

    definitions: list[dict[str, Any]] = []
    install_commands = 0
    generated_files = 0
    output_cells = 0

    for index, cell in enumerate(cells, start=1):
        source = cell_source(cell)
        if cell.get("outputs"):
            output_cells += 1
        if re.search(r"(?m)^\s*(?:!|%)?\s*pip\s+install\b", source):
            install_commands += 1
        if "%%writefile" in source or "open(" in source and ".py" in source:
            generated_files += 1

        names = re.findall(r"(?m)^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", source)
        if names:
            definitions.append({"cell": index, "functions": names})

    return {
        "path": str(path),
        "name": path.name,
        "total_cells": len(cells),
        "code_cells": len(code_cells),
        "markdown_cells": len(markdown_cells),
        "output_cells": output_cells,
        "install_commands": install_commands,
        "generated_files": generated_files,
        "definitions": definitions,
    }


def read_geojson_properties(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [feature.get("properties", {}) for feature in data.get("features", [])]


def is_missing_or_zero(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    try:
        return float(value) == 0.0
    except (TypeError, ValueError):
        return False


def read_csv_rows(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def id_value(row: dict[str, Any]) -> str:
    return str(row.get("NSTAPIPNO") or row.get("pipeline_number") or "").strip()


def grouped_by_id(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = id_value(row)
        if key:
            grouped[key].append(row)
    return grouped


def row_completeness(row: dict[str, Any]) -> int:
    return sum(not is_missing_or_zero(row.get(field)) for field in ENGINEERING_FIELDS)


def values_equivalent(left: Any, right: Any) -> bool:
    left_text = str(left if left is not None else "").strip()
    right_text = str(right if right is not None else "").strip()
    if left_text == right_text:
        return True
    try:
        return float(left_text) == float(right_text)
    except ValueError:
        return False


def best_attribute_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    return sorted(rows, key=row_completeness, reverse=True)[0]


def geojson_summary(
    props: list[dict[str, Any]],
    candidate_rows: list[dict[str, str]],
    attribute_rows: list[dict[str, str]],
) -> dict[str, Any]:
    ids = [id_value(row) for row in props if id_value(row)]
    candidate_ids = {id_value(row) for row in candidate_rows if id_value(row)}
    attribute_grouped = grouped_by_id(attribute_rows)
    attribute_ids = set(attribute_grouped)

    completeness = {}
    for field in ENGINEERING_FIELDS:
        missing = sum(is_missing_or_zero(row.get(field)) for row in props)
        completeness[field] = {
            "present": len(props) - missing,
            "missing_or_zero": missing,
            "total": len(props),
        }

    goldeneye = [
        row
        for row in props
        if "GOLDENEYE" in str(row.get("PIPE_NAME", "")).upper() or id_value(row) == "PL1978"
    ]

    overlap_candidates = sorted(set(ids).intersection(candidate_ids))
    overlap_attributes = sorted(set(ids).intersection(attribute_ids))

    differences: list[dict[str, Any]] = []
    for row in props:
        key = id_value(row)
        best = best_attribute_row(attribute_grouped.get(key, []))
        if best is None:
            continue
        for field in ["FLUID", "STATUS", "MX_OP_PRES", "THICKNESS", "START_DATE"]:
            student_value = str(row.get(field, "")).strip()
            nsta_value = str(best.get(field, "")).strip()
            if not values_equivalent(student_value, nsta_value):
                differences.append(
                    {
                        "NSTAPIPNO": key,
                        "PIPE_NAME": row.get("PIPE_NAME", ""),
                        "field": field,
                        "student": student_value,
                        "nsta": nsta_value,
                    }
                )

    return {
        "total_records": len(props),
        "fluid_counts": Counter(str(row.get("FLUID", "")).strip() or "(blank)" for row in props),
        "status_counts": Counter(str(row.get("STATUS", "")).strip() or "(blank)" for row in props),
        "unique_thickness": sorted({str(row.get("THICKNESS", "")).strip() for row in props}),
        "unique_mop": sorted({str(row.get("MX_OP_PRES", "")).strip() for row in props}),
        "completeness": completeness,
        "goldeneye": goldeneye,
        "candidate_overlap": overlap_candidates,
        "attribute_overlap": overlap_attributes,
        "differences": differences,
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def render_report(notebooks: list[dict[str, Any]], geo: dict[str, Any]) -> str:
    lines = ["# Student Submission Audit", ""]

    lines.extend(
        [
            "## Notebook Structure",
            "",
            markdown_table(
                [
                    "Notebook",
                    "Cells",
                    "Code cells",
                    "Markdown cells",
                    "Output cells",
                    "Install commands",
                    "Generated files",
                ],
                [
                    [
                        item["name"],
                        item["total_cells"],
                        item["code_cells"],
                        item["markdown_cells"],
                        item["output_cells"],
                        item["install_commands"],
                        item["generated_files"],
                    ]
                    for item in notebooks
                ],
            ),
            "",
            "## GeoJSON Completeness",
            "",
            markdown_table(
                ["Field", "Present", "Missing or zero", "Total"],
                [
                    [
                        field,
                        stats["present"],
                        stats["missing_or_zero"],
                        stats["total"],
                    ]
                    for field, stats in geo["completeness"].items()
                ],
            ),
            "",
            "## Dataset Summary",
            "",
            f"- Total student GeoJSON records: {geo['total_records']}",
            f"- Fluid counts: {dict(geo['fluid_counts'])}",
            f"- Status counts: {dict(geo['status_counts'])}",
            f"- Unique wall thickness values: {', '.join(geo['unique_thickness'])}",
            f"- Unique maximum operating pressure values: {', '.join(geo['unique_mop'])}",
            f"- Records found in full NSTA attribute table: {len(geo['attribute_overlap'])}",
            f"- Records found in model-ready ranked NSTA candidates: {len(geo['candidate_overlap'])}",
            "",
        ]
    )

    if geo["goldeneye"]:
        lines.extend(["## Goldeneye Records", ""])
        lines.append(
            markdown_table(
                ["NSTAPIPNO", "PIPE_NAME", "STATUS", "LENGTH_M", "MX_OP_PRES", "THICKNESS"],
                [
                    [
                        row.get("NSTAPIPNO", ""),
                        row.get("PIPE_NAME", ""),
                        row.get("STATUS", ""),
                        row.get("LENGTH_M", ""),
                        row.get("MX_OP_PRES", ""),
                        row.get("THICKNESS", ""),
                    ]
                    for row in geo["goldeneye"]
                ],
            )
        )
        lines.append("")

    lines.extend(
        [
            "## Data Differences To Investigate",
            "",
            "These are differences between the student GeoJSON and the best-matched row in our full NSTA attribute extraction.",
            "",
        ]
    )
    diff_rows = [
        [
            item["NSTAPIPNO"],
            item["PIPE_NAME"],
            item["field"],
            item["student"],
            item["nsta"],
        ]
        for item in geo["differences"][:40]
    ]
    if diff_rows:
        lines.append(markdown_table(["NSTAPIPNO", "PIPE_NAME", "Field", "Student", "NSTA"], diff_rows))
    else:
        lines.append("No differences found for compared fields.")
    lines.append("")

    lines.extend(
        [
            "## Main Interpretation",
            "",
            "- The notebooks are prototypes, not production-ready model code.",
            "- The GeoJSON looks like a manually enriched shortlist, not a clean source dataset.",
            "- Goldeneye is present but still has missing core engineering data.",
            "- The student work is useful as a reference, but every model and assumption needs validation before reuse.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", action="append", type=Path, default=[], help="Student .ipynb file.")
    parser.add_argument("--geojson", type=Path, required=True, help="Student pipeline GeoJSON.")
    parser.add_argument("--nsta-candidates", type=Path, help="Our ranked NSTA candidate CSV.")
    parser.add_argument("--nsta-attributes", type=Path, help="Our full NSTA attribute CSV.")
    parser.add_argument("--out", type=Path, help="Optional Markdown output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    notebook_reports = [notebook_summary(path) for path in args.notebook]
    props = read_geojson_properties(args.geojson)
    candidate_rows = read_csv_rows(args.nsta_candidates)
    attribute_rows = read_csv_rows(args.nsta_attributes)
    geo_report = geojson_summary(props, candidate_rows, attribute_rows)
    report = render_report(notebook_reports, geo_report)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
