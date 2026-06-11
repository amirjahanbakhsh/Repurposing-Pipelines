"""Extract shareable LCA activity metadata from private/local data sources.

The extractor is intentionally licence-safe. It reads local ecoinvent export
metadata and optional project CSVs, then writes candidate activity names,
locations, reference products, units, and match notes. It does not copy
ecoinvent unit-process inventories, exchanges, or private impact factors.
"""

from __future__ import annotations

import csv
import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MODEL_VERSION = "lca_activity_extraction_v0.1"
ECOSPOLD_LOOKUP_NAME = "FilenameToActivtiyLookup.csv"

PREFERRED_LOCATIONS = ["GB", "Europe without Switzerland", "RER", "GLO", "RoW"]

DEFAULT_ACTIVITY_QUERIES = [
    {
        "mapping_key": "pipeline_steel",
        "activity_group": "materials",
        "boundary_role": "new-build steel and refurbishment steel",
        "selection_type": "candidate",
        "search_terms": "steel, low-alloyed|market for steel, low-alloyed|steel production, low-alloyed",
        "preferred_activity_name": "",
        "preferred_location": "",
        "preferred_reference_product": "",
        "preferred_unit": "",
        "preferred_database": "",
        "preferred_review_status": "",
        "basis": "Steel mass is calculated from pipeline length, diameter, wall thickness and steel density.",
    },
    {
        "mapping_key": "offshore_pipeline_construction",
        "activity_group": "construction",
        "boundary_role": "new equivalent offshore pipeline construction",
        "selection_type": "candidate",
        "search_terms": "pipeline, natural gas, long distance, high capacity, offshore|market for pipeline",
        "preferred_activity_name": "",
        "preferred_location": "",
        "preferred_reference_product": "",
        "preferred_unit": "",
        "preferred_database": "",
        "preferred_review_status": "",
        "basis": "New-build comparison needs a construction activity for an equivalent offshore pipeline.",
    },
    {
        "mapping_key": "refurbishment_activity",
        "activity_group": "reuse_work_scope",
        "boundary_role": "reuse cleaning, inspection, repair, drying and recommissioning package",
        "selection_type": "project_package",
        "search_terms": "inspection|cleaning|maintenance|repair|diesel|vessel|machine operation",
        "preferred_activity_name": "user-defined pipeline refurbishment package",
        "preferred_location": "project",
        "preferred_reference_product": "pipeline refurbishment activity",
        "preferred_unit": "km",
        "preferred_database": "ecoinvent_derived",
        "preferred_review_status": "needs_private_package_factor",
        "basis": "Repurposing-gate work items are converted into an activity package; final factor is private/project-specific.",
    },
    {
        "mapping_key": "decommissioned_pipeline",
        "activity_group": "end_of_life",
        "boundary_role": "decommissioning, abandonment or disposal sensitivity",
        "selection_type": "candidate",
        "search_terms": "decommissioned pipeline, natural gas|pipeline decommission",
        "preferred_activity_name": "",
        "preferred_location": "",
        "preferred_reference_product": "",
        "preferred_unit": "",
        "preferred_database": "",
        "preferred_review_status": "",
        "basis": "End-of-life treatment can be included as a scenario or sensitivity case.",
    },
    {
        "mapping_key": "electricity",
        "activity_group": "operation",
        "boundary_role": "compression, pumping, monitoring and auxiliary power",
        "selection_type": "candidate",
        "search_terms": "electricity, medium voltage|market group for electricity|electricity voltage transformation",
        "preferred_activity_name": "",
        "preferred_location": "",
        "preferred_reference_product": "",
        "preferred_unit": "",
        "preferred_database": "",
        "preferred_review_status": "",
        "basis": "Operational energy is needed when compression, pumping or monitoring loads are allocated to the pipeline.",
    },
    {
        "mapping_key": "diesel_machinery",
        "activity_group": "construction_refurbishment",
        "boundary_role": "construction and refurbishment fuel or machinery proxy",
        "selection_type": "candidate",
        "search_terms": "diesel, low-sulfur|market for diesel|machine operation, diesel",
        "preferred_activity_name": "",
        "preferred_location": "",
        "preferred_reference_product": "",
        "preferred_unit": "",
        "preferred_database": "",
        "preferred_review_status": "",
        "basis": "Fuel proxy for construction/refurbishment equipment until vessel-specific data are selected.",
    },
    {
        "mapping_key": "freight_transport",
        "activity_group": "logistics",
        "boundary_role": "transport of materials, equipment and waste",
        "selection_type": "candidate",
        "search_terms": "transport, freight, lorry|freight|transport",
        "preferred_activity_name": "",
        "preferred_location": "",
        "preferred_reference_product": "",
        "preferred_unit": "",
        "preferred_database": "",
        "preferred_review_status": "",
        "basis": "Material and waste movement should be included when distances and masses are available.",
    },
    {
        "mapping_key": "scrap_steel",
        "activity_group": "end_of_life",
        "boundary_role": "scrap or waste steel sensitivity",
        "selection_type": "candidate",
        "search_terms": "scrap steel|treatment of scrap steel|steel scrap",
        "preferred_activity_name": "",
        "preferred_location": "",
        "preferred_reference_product": "",
        "preferred_unit": "",
        "preferred_database": "",
        "preferred_review_status": "",
        "basis": "Steel recycling/disposal choices can strongly affect results and must stay explicit.",
    },
]


@dataclass(frozen=True)
class ActivityQuery:
    mapping_key: str
    activity_group: str
    boundary_role: str
    selection_type: str
    search_terms: list[str]
    preferred_activity_name: str
    preferred_location: str
    preferred_reference_product: str
    preferred_unit: str
    preferred_database: str
    preferred_review_status: str
    basis: str


def read_csv_rows(path: Path, *, delimiter: str | None = None) -> list[dict[str, str]]:
    if delimiter is None:
        sample = path.read_text(encoding="utf-8-sig", errors="replace")[:4096]
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def default_activity_queries() -> list[ActivityQuery]:
    return [
        ActivityQuery(
            mapping_key=row["mapping_key"],
            activity_group=row["activity_group"],
            boundary_role=row["boundary_role"],
            selection_type=row.get("selection_type", "candidate"),
            search_terms=[term.strip() for term in row["search_terms"].split("|") if term.strip()],
            preferred_activity_name=row.get("preferred_activity_name", ""),
            preferred_location=row.get("preferred_location", ""),
            preferred_reference_product=row.get("preferred_reference_product", ""),
            preferred_unit=row.get("preferred_unit", ""),
            preferred_database=row.get("preferred_database", ""),
            preferred_review_status=row.get("preferred_review_status", ""),
            basis=row["basis"],
        )
        for row in DEFAULT_ACTIVITY_QUERIES
    ]


def read_activity_queries(path: Path | None) -> list[ActivityQuery]:
    if path is None or not path.exists():
        return default_activity_queries()
    rows = read_csv_rows(path)
    queries: list[ActivityQuery] = []
    for row in rows:
        raw_terms = row.get("search_terms", row.get("terms", ""))
        queries.append(
            ActivityQuery(
                mapping_key=row["mapping_key"],
                activity_group=row.get("activity_group", ""),
                boundary_role=row.get("boundary_role", ""),
                selection_type=row.get("selection_type", "candidate") or "candidate",
                search_terms=[term.strip() for term in raw_terms.split("|") if term.strip()],
                preferred_activity_name=row.get("preferred_activity_name", ""),
                preferred_location=row.get("preferred_location", ""),
                preferred_reference_product=row.get("preferred_reference_product", ""),
                preferred_unit=row.get("preferred_unit", ""),
                preferred_database=row.get("preferred_database", ""),
                preferred_review_status=row.get("preferred_review_status", ""),
                basis=row.get("basis", row.get("notes", "")),
            )
        )
    return queries


def _normalise_source_row(row: dict[str, str], *, source_name: str) -> dict[str, str]:
    def get(*names: str) -> str:
        for name in names:
            if name in row and row[name] is not None:
                return str(row[name]).strip()
        return ""

    return {
        "source_name": source_name,
        "source_file": get("FileName", "Filename", "filename", "file"),
        "activity_name": get("ActivityName", "activity_name", "activity", "name"),
        "location": get("Location", "location", "geography"),
        "reference_product": get("ReferenceProduct", "reference_product", "product"),
        "unit": get("Unit", "unit"),
        "database": get("Database", "database"),
        "system_model": get("SystemModel", "system_model"),
        "version": get("Version", "version"),
    }


def load_ecoinvent_metadata(ecoinvent_dir: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    lookup_path = ecoinvent_dir / ECOSPOLD_LOOKUP_NAME
    datasets_dir = ecoinvent_dir / "datasets"
    if not lookup_path.exists():
        raise FileNotFoundError(f"ecoinvent lookup file not found: {lookup_path}")

    rows = [
        _normalise_source_row(row, source_name="ecoinvent")
        for row in read_csv_rows(lookup_path, delimiter=";")
    ]
    dataset_count = len(list(datasets_dir.glob("*.spold"))) if datasets_dir.exists() else 0
    meta = {
        "source_name": "ecoinvent",
        "lookup_path": str(lookup_path),
        "datasets_dir": str(datasets_dir),
        "metadata_rows": len(rows),
        "dataset_file_count": dataset_count,
        "licence_note": "metadata only; unit-process inventories and impact factors are not exported",
    }
    return rows, meta


def load_activity_csv(path: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    rows = [
        _normalise_source_row(row, source_name=path.stem)
        for row in read_csv_rows(path)
    ]
    return rows, {
        "source_name": path.stem,
        "lookup_path": str(path),
        "metadata_rows": len(rows),
        "licence_note": "activity metadata only",
    }


def _match_score(row: dict[str, str], query: ActivityQuery) -> int:
    text = (
        f"{row.get('activity_name', '')} "
        f"{row.get('reference_product', '')} "
        f"{row.get('location', '')}"
    ).lower()
    score = 0
    for term in query.search_terms:
        if term.lower() in text:
            score += max(1, len(term.split()))
    if score == 0:
        return 0
    if row.get("location") in PREFERRED_LOCATIONS:
        score += max(1, len(PREFERRED_LOCATIONS) - PREFERRED_LOCATIONS.index(row["location"]))
    return score


def extract_activity_candidates(
    *,
    source_rows: list[dict[str, str]],
    queries: list[ActivityQuery],
    max_per_mapping: int = 10,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for query in queries:
        scored = [
            (row, _match_score(row, query))
            for row in source_rows
            if _match_score(row, query) > 0
        ]
        scored.sort(
            key=lambda item: (
                -item[1],
                PREFERRED_LOCATIONS.index(item[0]["location"])
                if item[0].get("location") in PREFERRED_LOCATIONS
                else len(PREFERRED_LOCATIONS),
                item[0].get("activity_name", ""),
            )
        )
        for rank, (row, score) in enumerate(scored[:max_per_mapping], start=1):
            candidates.append(
                {
                    "mapping_key": query.mapping_key,
                    "candidate_rank": rank,
                    "match_score": score,
                    "activity_group": query.activity_group,
                    "boundary_role": query.boundary_role,
                    "activity_name": row.get("activity_name", ""),
                    "location": row.get("location", ""),
                    "reference_product": row.get("reference_product", ""),
                    "unit": row.get("unit", ""),
                    "source_name": row.get("source_name", ""),
                    "source_file": row.get("source_file", ""),
                    "database": row.get("database", ""),
                    "system_model": row.get("system_model", ""),
                    "version": row.get("version", ""),
                    "basis": query.basis,
                    "licence_status": "shareable_metadata_only",
                    "review_status": "needs_lca_review",
                    "notes": "Candidate activity only; final selection and impact factor must be reviewed privately.",
                }
            )
        if not scored:
            candidates.append(
                {
                    "mapping_key": query.mapping_key,
                    "candidate_rank": "",
                    "match_score": 0,
                    "activity_group": query.activity_group,
                    "boundary_role": query.boundary_role,
                    "activity_name": "",
                    "location": "",
                    "reference_product": "",
                    "unit": "",
                    "source_name": "",
                    "source_file": "",
                    "database": "",
                    "system_model": "",
                    "version": "",
                    "basis": query.basis,
                    "licence_status": "shareable_metadata_only",
                    "review_status": "no_candidate_found",
                    "notes": "No candidate activity matched the search terms.",
                }
            )
    return candidates


def _match_count(candidates: list[dict[str, Any]], mapping_key: str) -> int:
    return sum(
        1
        for row in candidates
        if row["mapping_key"] == mapping_key and row.get("activity_name")
    )


def preferred_mapping_rows(
    candidates: list[dict[str, Any]],
    queries: list[ActivityQuery],
) -> list[dict[str, Any]]:
    rows = []
    project_package_keys = {
        query.mapping_key
        for query in queries
        if query.selection_type == "project_package"
    }
    for query in queries:
        if query.selection_type != "project_package":
            continue
        rows.append(
            {
                "mapping_key": query.mapping_key,
                "database": query.preferred_database or "project",
                "system_model": "",
                "version": "",
                "activity_name": query.preferred_activity_name,
                "location": query.preferred_location,
                "reference_product": query.preferred_reference_product,
                "unit": query.preferred_unit,
                "match_count": _match_count(candidates, query.mapping_key),
                "source": "standalone LCA activity extractor",
                "shareable": "yes",
                "review_status": query.preferred_review_status or "needs_private_package_factor",
                "notes": (
                    f"{query.basis} Candidate rows are components/proxies, "
                    "not a complete single ecoinvent process."
                ),
            }
        )
    for candidate in candidates:
        if candidate.get("candidate_rank") != 1:
            continue
        if candidate["mapping_key"] in project_package_keys:
            continue
        rows.append(
            {
                "mapping_key": candidate["mapping_key"],
                "database": candidate.get("database") or candidate.get("source_name", ""),
                "system_model": candidate.get("system_model", ""),
                "version": candidate.get("version", ""),
                "activity_name": candidate.get("activity_name", ""),
                "location": candidate.get("location", ""),
                "reference_product": candidate.get("reference_product", ""),
                "unit": candidate.get("unit", ""),
                "match_count": _match_count(candidates, candidate["mapping_key"]),
                "source": "standalone LCA activity extractor",
                "shareable": "yes",
                "review_status": candidate.get("review_status", ""),
                "notes": candidate.get("basis", ""),
            }
        )
    return rows


def write_activity_extraction_report(
    path: Path,
    *,
    candidates: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    output_paths: list[Path],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    source_lines = "\n".join(
        f"- {source['source_name']}: {source.get('metadata_rows', 0)} metadata rows"
        for source in sources
    )
    mapping_counts: dict[str, int] = {}
    for row in candidates:
        if row.get("activity_name"):
            mapping_counts[row["mapping_key"]] = mapping_counts.get(row["mapping_key"], 0) + 1
    count_lines = "\n".join(
        f"- `{key}`: {count} candidate(s)" for key, count in sorted(mapping_counts.items())
    )
    output_lines = "\n".join(f"- `{path.as_posix()}`" for path in output_paths)
    report = f"""# LCA Activity Extraction Report

Generated: {dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

Model version: `{MODEL_VERSION}`

## Purpose

This report lists candidate LCA activities for the pipeline repurposing model.

The extraction is licence-safe. It stores activity metadata only: names, locations, reference products, units, and mapping notes. It does not copy ecoinvent unit-process inventories, exchanges, or private impact factors.

## Sources Read

{source_lines or "- none"}

## Candidate Counts

{count_lines or "- no candidates found"}

## Output Files

{output_lines}

## How To Use This

1. Review the candidate activities.
2. Select the best activity for each `mapping_key`.
3. Use openLCA or Brightway privately to calculate the required impact factors.
4. Put private factors in `model_layers/05_lca/private/lca_impact_factors_private.csv`.

Rows marked as project packages, such as refurbishment, are not single database activities. Build their factor from the relevant work items, for example inspection, cleaning, drying, repair, replacement steel, vessel time, diesel use and logistics.

If the local lookup file does not include units, unit fields remain blank here and must be confirmed during private LCA review.

## Boundary Reminder

For the current pipeline-only LCA, include pipeline steel, construction/refurbishment, cleaning/drying/inspection/repair where data exist, operation energy if allocated, logistics, and end-of-life sensitivity.

Exclude capture plant, industrial emissions before capture, storage reservoir performance, and claimed avoided emissions from storing CO2 until the project moves to a full CCS-chain LCA.
"""
    path.write_text(report, encoding="utf-8")


def extract_lca_activity_data(
    *,
    ecoinvent_dir: Path | None,
    activity_csvs: list[Path],
    query_path: Path | None,
    candidates_path: Path,
    preferred_mapping_path: Path,
    report_path: Path,
    max_per_mapping: int = 10,
) -> dict[str, Any]:
    queries = read_activity_queries(query_path)
    all_rows: list[dict[str, str]] = []
    source_meta: list[dict[str, Any]] = []

    if ecoinvent_dir is not None:
        rows, meta = load_ecoinvent_metadata(ecoinvent_dir)
        all_rows.extend(rows)
        source_meta.append(meta)

    for path in activity_csvs:
        rows, meta = load_activity_csv(path)
        all_rows.extend(rows)
        source_meta.append(meta)

    candidates = extract_activity_candidates(
        source_rows=all_rows,
        queries=queries,
        max_per_mapping=max_per_mapping,
    )
    preferred = preferred_mapping_rows(candidates, queries)
    write_csv_rows(candidates_path, candidates)
    write_csv_rows(preferred_mapping_path, preferred)
    write_activity_extraction_report(
        report_path,
        candidates=candidates,
        sources=source_meta,
        output_paths=[candidates_path, preferred_mapping_path, report_path],
    )
    return {
        "source_count": len(source_meta),
        "source_rows": len(all_rows),
        "candidate_rows": len(candidates),
        "preferred_rows": len(preferred),
    }
