"""Rank NSTA hydrocarbon pipeline candidates for first-pass CO2 reuse screening.

Inputs:

- data/processed/nsta_pipeline_attributes.csv

Outputs:

- data/processed/nsta_candidate_ranked.csv
- reports/nsta_candidate_ranking.md

This is a screening helper, not an engineering suitability model. It only ranks
pipelines that already have usable NSTA values for internal diameter, max
operating pressure, and wall thickness.
"""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
from typing import Any


HYDROCARBON_FLUIDS = {"GAS", "CONDENSATE", "MIXED HYDROCARBONS"}
ENGINEERING_FIELDS = ["INT_DIAM", "MX_OP_PRES", "THICKNESS"]
POSITIVE_NUMERIC_FIELDS = {"INT_DIAM", "MX_OP_PRES", "THICKNESS", "LENGTH_M", "DIAMETERMM"}
MISSING_NUMERIC_SENTINELS = {-9999, -9999.0}
MIN_STRATEGIC_LENGTH_M = 1000

KNOWN_CCS_TERMS = [
    "GOLDENEYE",
    "ATLANTIC",
    "CROMARTY",
    "MILLER",
    "HAMILTON",
    "CAMELOT",
    "BEATRICE",
    "ST FERGUS",
    "ST. FERGUS",
    "ACORN",
    "BRAE",
    "SAGE",
    "CAPTAIN",
    "FORTIES",
]


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    stripped = str(value).strip()
    return stripped == "" or stripped.upper() in {"N/A", "NA", "NULL", "UNKNOWN"}


def to_float(value: Any) -> float | None:
    if is_missing(value):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def is_usable_positive(field: str, value: Any) -> bool:
    number = to_float(value)
    if number is None:
        return False
    if number in MISSING_NUMERIC_SENTINELS:
        return False
    if field in POSITIVE_NUMERIC_FIELDS:
        return number > 0
    return True


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 1.0
    ordered = sorted(values)
    idx = int(round((len(ordered) - 1) * pct))
    return ordered[idx] or 1.0


def capped_norm(value: float | None, cap: float) -> float:
    if value is None or cap <= 0:
        return 0.0
    return min(value / cap, 1.0)


def status_score(status: str) -> float:
    status = status.strip().upper()
    if status == "NOT IN USE":
        return 1.0
    if status == "ACTIVE":
        return 0.7
    if status == "PRECOMMISSIONED":
        return 0.4
    return 0.1


def has_start_date(row: dict[str, str]) -> float:
    return 1.0 if not is_missing(row.get("START_DATE")) else 0.0


def searchable_text(row: dict[str, str]) -> str:
    parts = [
        row.get("NSTAPIPNO", ""),
        row.get("PIPE_NAME", ""),
        row.get("PIPE_SYS", ""),
        row.get("DESCRIPTIO", ""),
        row.get("COMMENTS", ""),
    ]
    return " | ".join(parts).upper()


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(markdown_cell(item) for item in row) + " |")
    return "\n".join(lines)


def markdown_cell(value: Any) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").replace("|", "/")
    return " ".join(text.split())


def candidate_filter(row: dict[str, str]) -> bool:
    fluid = row.get("FLUID", "").strip().upper()
    return fluid in HYDROCARBON_FLUIDS and all(
        is_usable_positive(field, row.get(field)) for field in ENGINEERING_FIELDS
    )


def is_pipeline_type(row: dict[str, Any]) -> bool:
    return str(row.get("INF_TYPE", "")).strip().upper() == "PIPELINE"


def is_strategic_pipeline(row: dict[str, Any]) -> bool:
    return is_pipeline_type(row) and (to_float(row.get("LENGTH_M")) or 0) >= MIN_STRATEGIC_LENGTH_M


def enrich_and_score(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    candidates = [row for row in rows if candidate_filter(row)]

    caps = {
        "INT_DIAM": percentile([to_float(row["INT_DIAM"]) or 0 for row in candidates], 0.95),
        "MX_OP_PRES": percentile([to_float(row["MX_OP_PRES"]) or 0 for row in candidates], 0.95),
        "THICKNESS": percentile([to_float(row["THICKNESS"]) or 0 for row in candidates], 0.95),
        "LENGTH_M": percentile(
            [to_float(row.get("LENGTH_M")) or 0 for row in candidates if is_usable_positive("LENGTH_M", row.get("LENGTH_M"))],
            0.95,
        ),
    }

    ranked: list[dict[str, Any]] = []
    for row in candidates:
        internal_diameter_mm = to_float(row.get("INT_DIAM"))
        max_pressure_barg = to_float(row.get("MX_OP_PRES"))
        thickness_mm = to_float(row.get("THICKNESS"))
        length_m = to_float(row.get("LENGTH_M"))

        score = (
            0.30 * capped_norm(internal_diameter_mm, caps["INT_DIAM"])
            + 0.25 * capped_norm(max_pressure_barg, caps["MX_OP_PRES"])
            + 0.20 * capped_norm(thickness_mm, caps["THICKNESS"])
            + 0.10 * capped_norm(length_m, caps["LENGTH_M"])
            + 0.10 * status_score(row.get("STATUS", ""))
            + 0.05 * has_start_date(row)
        )

        enriched = dict(row)
        enriched["LENGTH_KM"] = (length_m or 0) / 1000
        enriched["PIPELINE_TYPE"] = "yes" if is_pipeline_type(enriched) else "no"
        enriched["STRATEGIC_PIPELINE"] = "yes" if is_strategic_pipeline(enriched) else "no"
        enriched["SCREENING_SCORE"] = round(score * 100, 1)
        ranked.append(enriched)

    ranked.sort(key=lambda item: item["SCREENING_SCORE"], reverse=True)
    for index, row in enumerate(ranked, 1):
        row["RANK"] = index
    return ranked


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    preferred = [
        "RANK",
        "SCREENING_SCORE",
        "NSTAPIPNO",
        "PIPE_NAME",
        "REP_GROUP",
        "FLUID",
        "STATUS",
        "PIPE_SYS",
        "DIAMETERMM",
        "INT_DIAM",
        "MX_OP_PRES",
        "THICKNESS",
        "LENGTH_M",
        "LENGTH_KM",
        "PIPELINE_TYPE",
        "STRATEGIC_PIPELINE",
        "START_DATE",
        "END_DATE",
        "DESCRIPTIO",
        "COMMENTS",
    ]
    fieldnames = preferred + [key for key in rows[0] if key not in preferred]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def compact_row(row: dict[str, Any]) -> list[Any]:
    return [
        row.get("RANK", ""),
        row.get("SCREENING_SCORE", ""),
        row.get("NSTAPIPNO", ""),
        row.get("PIPE_NAME", ""),
        row.get("INF_TYPE", ""),
        row.get("FLUID", ""),
        row.get("STATUS", ""),
        row.get("INT_DIAM", ""),
        row.get("MX_OP_PRES", ""),
        row.get("THICKNESS", ""),
        f"{float(row.get('LENGTH_KM') or 0):.1f}",
        row.get("START_DATE", ""),
    ]


def term_matches(rows: list[dict[str, str]], ranked: list[dict[str, Any]]) -> list[list[Any]]:
    ranked_object_ids = {str(row.get("OBJECTID")): row for row in ranked}
    table: list[list[Any]] = []
    for term in KNOWN_CCS_TERMS:
        full_matches = [row for row in rows if term in searchable_text(row)]
        hydrocarbon_matches = [
            row
            for row in full_matches
            if row.get("FLUID", "").strip().upper() in HYDROCARBON_FLUIDS
        ]
        usable_matches = [
            ranked_object_ids[str(row.get("OBJECTID"))]
            for row in full_matches
            if str(row.get("OBJECTID")) in ranked_object_ids
        ]
        best = ""
        if usable_matches:
            best_row = sorted(usable_matches, key=lambda item: item["RANK"])[0]
            best = f"rank {best_row['RANK']}: {best_row.get('PIPE_NAME', '')}"
        elif full_matches:
            example = full_matches[0]
            best = f"not model-ready: {example.get('PIPE_NAME', '')}"
        table.append([term, len(full_matches), len(hydrocarbon_matches), len(usable_matches), best])
    return table


def write_report(path: Path, rows: list[dict[str, str]], ranked: list[dict[str, Any]]) -> None:
    active_not_in_use = [
        row for row in ranked if row.get("STATUS", "").strip().upper() in {"ACTIVE", "NOT IN USE"}
    ]
    pipeline_type_rows = [row for row in ranked if is_pipeline_type(row)]
    strategic_pipeline_rows = [row for row in ranked if is_strategic_pipeline(row)]
    long_pipeline_rows = [
        row for row in ranked if is_pipeline_type(row) and (to_float(row.get("LENGTH_M")) or 0) >= 10000
    ]
    top_rows = [compact_row(row) for row in strategic_pipeline_rows[:30]]
    known_rows = term_matches(rows, ranked)

    report = f"""# NSTA Candidate Ranking

Generated: {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

Input data: `data/processed/nsta_pipeline_attributes.csv`

Ranking script: `scripts/rank_nsta_candidates.py`

## What This Ranking Means

This is a first-pass data ranking, not an engineering approval.

The script ranks only hydrocarbon pipelines (`GAS`, `CONDENSATE`, `MIXED HYDROCARBONS`) with usable positive values for:

- internal diameter;
- max operating pressure;
- wall thickness.

The score favours larger internal diameter, higher operating pressure, thicker wall, longer route, more reusable-looking status, and presence of start date.

## Candidate Counts

| Group | Count |
| --- | --- |
| All NSTA records | {len(rows)} |
| Model-ready hydrocarbon candidates | {len(ranked)} |
| Model-ready candidates with `ACTIVE` or `NOT IN USE` status | {len(active_not_in_use)} |
| Model-ready records where `INF_TYPE = PIPELINE` | {len(pipeline_type_rows)} |
| Model-ready pipeline records at least {MIN_STRATEGIC_LENGTH_M / 1000:.0f} km long | {len(strategic_pipeline_rows)} |
| Model-ready pipeline records at least 10 km long | {len(long_pipeline_rows)} |

## Top 30 Model-Ready Pipeline Candidates At Least {MIN_STRATEGIC_LENGTH_M / 1000:.0f} km Long

{markdown_table(["Rank", "Score", "NSTA no.", "Pipeline", "Type", "Fluid", "Status", "ID mm", "Pressure barg", "Thickness mm", "Length km", "Start"], top_rows)}

## Known CCS / Reuse Name Check

{markdown_table(["Search term", "All NSTA matches", "Hydrocarbon matches", "Model-ready matches", "Best / example match"], known_rows)}

## Early Observations

- Goldeneye is present in the NSTA data, including the `20\" GAS GOLDENEYE - ST. FERGUS` line, but its NSTA engineering fields are zero in this extract, so it is not in the strict model-ready ranked set.
- This matches the project recollection that Goldeneye data was difficult to source and likely needed extra enrichment or assumptions in the student work.
- Atlantic and Cromarty names are present, but the obvious Shell gas lines in this extract also have zero engineering fields, so they are not model-ready from NSTA alone.
- The highest-ranked model-ready long pipeline records include CATS, SAGE, BBL, Schiehallion, Cygnus, Magnus/NLGP, and Bacton-Zeebrugge style trunk lines.
- This confirms that the missing student clean table probably depended on extra sources or assumptions for some high-value CCS candidates.
- The next step is targeted enrichment: take known CCS/reuse candidates first, then fill wall thickness, material grade, pressure, and start year from reports, decommissioning documents, and operator publications.

## Sources For Known-Name Checks

- BEIS/GOV.UK consultation and Annex A on re-use of oil and gas assets for CCUS: https://www.gov.uk/government/consultations/carbon-capture-usage-and-storage-ccus-projects-re-use-of-oil-and-gas-assets
- IEAGHG note on re-use case studies including Camelot, Atlantic & Cromarty, Hamilton, Goldeneye, and Beatrice: https://ieaghg.org/news/new-ieaghg-technical-report-2018-06-re-use-of-oil-gas-facilities-for-co2-transport-and-storage/
- NSTA Energy Pathfinder note on Atlantic and Cromarty decommissioning being held for CCUS re-use investigation: https://energypathfinder.nstauthority.co.uk/projects/207
- Shell Atlantic and Cromarty decommissioning page: https://www.shell.co.uk/about-us/sustainability/decommissioning/atlantic-and-cromarty.html
"""
    path.write_text(report, encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    input_path = root / "data" / "processed" / "nsta_pipeline_attributes.csv"
    output_path = root / "data" / "processed" / "nsta_candidate_ranked.csv"
    report_path = root / "reports" / "nsta_candidate_ranking.md"

    rows = read_rows(input_path)
    ranked = enrich_and_score(rows)
    write_csv(output_path, ranked)
    write_report(report_path, rows, ranked)

    print(f"Read {len(rows)} NSTA records")
    print(f"Wrote {len(ranked)} ranked candidates")
    print(output_path)
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
