"""Wall-thickness pressure sanity checks for screening candidates."""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
from typing import Any


MODEL_VERSION = "wall_thickness_pressure_check_v0.1"

PIPE_GRADE_SMYS_MPA = {
    "X42": 289.6,
    "X52": 358.5,
    "X60": 413.7,
    "X65": 448.2,
    "X70": 482.6,
}


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text == "" or text.upper() in {"N/A", "NA", "NULL", "UNKNOWN"}


def _to_float(value: Any) -> float | None:
    if _is_missing(value):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _round(value: float | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def _require_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive; got {value!r}.")


def pipe_grade_smys_mpa(pipe_grade: str) -> float | None:
    """Return the screening SMYS value for a supported API 5L pipe grade."""
    return PIPE_GRADE_SMYS_MPA.get(pipe_grade.strip().upper())


def barlow_minimum_wall_thickness_mm(
    *,
    pressure_mpa: float,
    outer_diameter_mm: float,
    smys_mpa: float,
    design_factor: float,
) -> float:
    """Return simple Barlow-style pressure wall thickness in mm.

    Pressure and SMYS are both MPa, which are equivalent to N/mm2, so using
    outer diameter in mm returns a wall thickness in mm.
    """
    _require_positive("pressure_mpa", pressure_mpa)
    _require_positive("outer_diameter_mm", outer_diameter_mm)
    _require_positive("smys_mpa", smys_mpa)
    _require_positive("design_factor", design_factor)
    return pressure_mpa * outer_diameter_mm / (2 * smys_mpa * design_factor)


def pressure_wall_status(
    *,
    reported_wall_thickness_mm: float,
    minimum_wall_thickness_mm: float,
    review_margin_fraction: float,
) -> str:
    _require_positive("reported_wall_thickness_mm", reported_wall_thickness_mm)
    _require_positive("minimum_wall_thickness_mm", minimum_wall_thickness_mm)
    if review_margin_fraction < 0:
        raise ValueError("review_margin_fraction must be zero or positive.")

    margin_fraction = (
        reported_wall_thickness_mm - minimum_wall_thickness_mm
    ) / reported_wall_thickness_mm
    if margin_fraction < 0:
        return "fail_sanity"
    if margin_fraction < review_margin_fraction:
        return "review_required"
    return "pass_sanity"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_defaults(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["parameter"]: row for row in csv.DictReader(handle)}


def _status_notes(status: str, review_margin_fraction: float) -> str:
    if status == "fail_sanity":
        return (
            "Calculated pressure minimum exceeds reported wall thickness; "
            "verify NSTA dimensions, pressure basis, pipe grade, and design factor."
        )
    if status == "review_required":
        return (
            "Positive pressure margin, but below the screening review threshold "
            f"of {review_margin_fraction:.0%} of reported wall thickness."
        )
    return (
        "Reported wall thickness is above the simple pressure minimum by at "
        "least the screening review threshold."
    )


def build_nsta_wall_thickness_check_rows(
    *,
    candidates_path: Path,
    defaults_path: Path,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    candidates = read_csv_rows(candidates_path)
    if limit is not None:
        candidates = candidates[:limit]

    defaults = read_defaults(defaults_path)
    return [
        build_nsta_wall_thickness_check_row(candidate=candidate, defaults=defaults)
        for candidate in candidates
    ]


def build_nsta_wall_thickness_check_row(
    *,
    candidate: dict[str, str],
    defaults: dict[str, dict[str, str]],
) -> dict[str, Any]:
    pipe_grade = defaults.get("pipe_grade", {}).get("value", "X60").strip().upper()
    smys_mpa = _to_float(defaults.get("smys_mpa", {}).get("value"))
    if smys_mpa is None:
        smys_mpa = pipe_grade_smys_mpa(pipe_grade)
    design_factor = _to_float(defaults.get("design_factor", {}).get("value"))
    review_margin_fraction = _to_float(
        defaults.get("wall_pressure_margin_review_fraction", {}).get("value")
    )
    if review_margin_fraction is None:
        review_margin_fraction = 0.20

    nsta_id = candidate.get("NSTAPIPNO", "").strip()
    inner_diameter_mm = _to_float(candidate.get("INT_DIAM"))
    reported_wall_mm = _to_float(candidate.get("THICKNESS"))
    pressure_barg = _to_float(candidate.get("MX_OP_PRES"))
    length_km = _to_float(candidate.get("LENGTH_KM"))

    base_row: dict[str, Any] = {
        "nsta_rank": candidate.get("RANK", ""),
        "nsta_pipeline_number": nsta_id,
        "pipeline_name": candidate.get("PIPE_NAME", ""),
        "fluid": candidate.get("FLUID", ""),
        "nsta_status": candidate.get("STATUS", ""),
        "length_km": _round(length_km, 6),
        "pipe_grade": pipe_grade,
        "smys_mpa": _round(smys_mpa, 3),
        "design_factor": _round(design_factor, 3),
        "pressure_basis": "NSTA MX_OP_PRES barg plus atmospheric pressure for screening consistency",
        "max_operating_pressure_barg": _round(pressure_barg, 6),
        "inner_diameter_mm": _round(inner_diameter_mm, 3),
        "reported_wall_thickness_mm": _round(reported_wall_mm, 3),
        "review_margin_fraction": _round(review_margin_fraction, 6),
    }

    missing = [
        name
        for name, value in [
            ("INT_DIAM", inner_diameter_mm),
            ("THICKNESS", reported_wall_mm),
            ("MX_OP_PRES", pressure_barg),
            ("smys_mpa", smys_mpa),
            ("design_factor", design_factor),
        ]
        if value is None or value <= 0
    ]
    if missing:
        return {
            **base_row,
            "pressure_mpa_for_check": "",
            "outer_diameter_mm": "",
            "barlow_min_wall_mm": "",
            "pressure_margin_mm": "",
            "pressure_margin_fraction": "",
            "pressure_utilization_fraction": "",
            "status": "insufficient_data",
            "notes": "Missing or non-positive fields: " + "; ".join(missing),
        }

    assert inner_diameter_mm is not None
    assert reported_wall_mm is not None
    assert pressure_barg is not None
    assert smys_mpa is not None
    assert design_factor is not None

    outer_diameter_mm = inner_diameter_mm + 2 * reported_wall_mm
    pressure_mpa = (pressure_barg + 1.01325) * 0.1
    minimum_wall_mm = barlow_minimum_wall_thickness_mm(
        pressure_mpa=pressure_mpa,
        outer_diameter_mm=outer_diameter_mm,
        smys_mpa=smys_mpa,
        design_factor=design_factor,
    )
    pressure_margin_mm = reported_wall_mm - minimum_wall_mm
    pressure_margin_fraction = pressure_margin_mm / reported_wall_mm
    pressure_utilization_fraction = minimum_wall_mm / reported_wall_mm
    status = pressure_wall_status(
        reported_wall_thickness_mm=reported_wall_mm,
        minimum_wall_thickness_mm=minimum_wall_mm,
        review_margin_fraction=review_margin_fraction,
    )

    return {
        **base_row,
        "pressure_mpa_for_check": _round(pressure_mpa, 6),
        "outer_diameter_mm": _round(outer_diameter_mm, 3),
        "barlow_min_wall_mm": _round(minimum_wall_mm, 6),
        "pressure_margin_mm": _round(pressure_margin_mm, 6),
        "pressure_margin_fraction": _round(pressure_margin_fraction, 6),
        "pressure_utilization_fraction": _round(pressure_utilization_fraction, 6),
        "status": status,
        "notes": _status_notes(status, review_margin_fraction),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(_csv_safe_row(row) for row in rows)


def _csv_safe_value(value: Any) -> Any:
    if isinstance(value, str):
        return " ".join(value.replace("\r", " ").replace("\n", " ").split())
    return value


def _csv_safe_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: _csv_safe_value(value) for key, value in row.items()}


def _status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def _counts_table(counts: dict[str, int]) -> str:
    lines = ["| Status | Count |", "| --- | --- |"]
    for status, count in sorted(counts.items()):
        lines.append(f"| {status} | {count} |")
    return "\n".join(lines)


def _markdown_cell(value: Any) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").replace("|", "/")
    return " ".join(text.split())


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_markdown_cell(value) for value in row) + " |")
    return "\n".join(lines)


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sort_problem_rows(row: dict[str, Any]) -> tuple[int, float]:
    status_rank = {"fail_sanity": 0, "review_required": 1, "insufficient_data": 2}
    margin = _to_float(row.get("pressure_margin_fraction"))
    return (status_rank.get(str(row.get("status")), 3), margin if margin is not None else 999)


def write_report(
    path: Path,
    *,
    rows: list[dict[str, Any]],
    candidates_path: Path,
    defaults_path: Path,
    csv_path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    problem_rows = [row for row in rows if row.get("status") != "pass_sanity"]
    problem_rows = sorted(problem_rows, key=_sort_problem_rows)[:25]
    review_table = (
        _table(
            [
                "Rank",
                "NSTA no.",
                "Pipeline",
                "Length km",
                "Wall mm",
                "Min wall mm",
                "Margin %",
                "Status",
            ],
            [
                [
                    row.get("nsta_rank", ""),
                    row.get("nsta_pipeline_number", ""),
                    row.get("pipeline_name", ""),
                    f"{float(row.get('length_km') or 0):.1f}",
                    row.get("reported_wall_thickness_mm", ""),
                    row.get("barlow_min_wall_mm", ""),
                    (
                        f"{100 * float(row.get('pressure_margin_fraction')):.1f}"
                        if row.get("pressure_margin_fraction") not in {"", None}
                        else ""
                    ),
                    row.get("status", ""),
                ]
                for row in problem_rows
            ],
        )
        if problem_rows
        else "No rows were flagged by this screening check."
    )

    report = f"""# NSTA Wall-Thickness Pressure Check

Generated: {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

Model version: `{MODEL_VERSION}`

Candidate file: `{_display_path(candidates_path)}`

Default assumptions: `{_display_path(defaults_path)}`

CSV output: `{_display_path(csv_path)}`

## Purpose

This check applies a simple Barlow-style pressure wall-thickness calculation to the model-ready NSTA candidate list.

It is not a design-code calculation and it is not engineering approval. It is a triage check: it identifies candidates whose reported wall thickness is close to, or below, the pressure-based screening minimum before detailed integrity, inspection, and requalification evidence is gathered.

## Status Counts

{_counts_table(_status_counts(rows))}

## Flagged Candidates

{review_table}

## Formula

`minimum wall = pressure * outside diameter / (2 * SMYS * design factor)`

The current screening basis uses:

- pressure from NSTA `MX_OP_PRES` in barg plus atmospheric pressure for consistency with the current NSTA screening model;
- outside diameter estimated as `internal diameter + 2 * reported wall thickness`;
- default pipe grade and SMYS from `nsta_screening_defaults.csv`;
- default design factor from `nsta_screening_defaults.csv`;
- review flag when the pressure margin is below the configured wall-pressure margin threshold.

## Next Use

Use this report to prioritise integrity evidence collection. For flagged rows, check the true design pressure basis, diameter basis, wall schedule, material grade, corrosion allowance, inspection records, defects, and code/requalification method.
"""
    path.write_text(report, encoding="utf-8")
