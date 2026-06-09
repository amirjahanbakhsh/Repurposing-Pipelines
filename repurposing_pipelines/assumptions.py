"""Load traceable scenario assumptions from CSV files."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .trace import AssumptionRecord, InputRecord


@dataclass(frozen=True)
class AssumptionValue:
    scenario: str
    parameter: str
    value: str
    unit: str
    source: str
    quality: str
    notes: str

    def parsed_value(self) -> Any:
        raw = self.value.strip()
        if raw == "":
            return None
        try:
            return float(raw)
        except ValueError:
            return raw

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScenarioAssumptions:
    name: str
    records: dict[str, AssumptionValue]

    def record(self, parameter: str) -> AssumptionValue:
        try:
            return self.records[parameter]
        except KeyError as exc:
            raise KeyError(f"Missing parameter '{parameter}' for scenario '{self.name}'") from exc

    def raw(self, parameter: str) -> str:
        return self.record(parameter).value

    def number(self, parameter: str) -> float:
        return float(self.raw(parameter))

    def optional_number(self, parameter: str) -> float | None:
        if parameter not in self.records:
            return None
        raw = self.raw(parameter).strip()
        if not raw:
            return None
        return float(raw)

    def input_record(
        self,
        parameter: str,
        *,
        required: bool = True,
        used_by: list[str] | None = None,
    ) -> InputRecord:
        record = self.record(parameter)
        return InputRecord(
            name=parameter,
            value=record.parsed_value(),
            unit=record.unit,
            source=record.source,
            quality=record.quality,
            required=required,
            used_by=used_by or [],
            notes=record.notes,
        )

    def input_records(self, parameters: list[str], *, used_by: list[str]) -> list[InputRecord]:
        return [self.input_record(parameter, used_by=used_by) for parameter in parameters]

    def assumption_record(
        self,
        parameter: str,
        *,
        sensitivity_required: bool = False,
    ) -> AssumptionRecord:
        record = self.record(parameter)
        return AssumptionRecord(
            name=parameter,
            value=record.parsed_value(),
            unit=record.unit,
            source=record.source,
            quality=record.quality,
            sensitivity_required=sensitivity_required,
            notes=record.notes,
        )

    def to_dicts(self) -> list[dict[str, Any]]:
        return [record.to_dict() for record in self.records.values()]


def read_scenario_assumptions(path: Path) -> dict[str, ScenarioAssumptions]:
    grouped: dict[str, dict[str, AssumptionValue]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            scenario = row["scenario"]
            parameter = row["parameter"]
            grouped.setdefault(scenario, {})[parameter] = AssumptionValue(
                scenario=scenario,
                parameter=parameter,
                value=row["value"],
                unit=row["unit"],
                source=row["source"],
                quality=row["quality"],
                notes=row["notes"],
            )

    return {
        scenario: ScenarioAssumptions(name=scenario, records=records)
        for scenario, records in grouped.items()
    }
