"""Traceable result objects shared by screening modules."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class InputRecord:
    name: str
    value: Any
    unit: str = ""
    source: str = ""
    quality: str = ""
    required: bool = True
    used_by: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass(frozen=True)
class OutputRecord:
    name: str
    value: Any
    unit: str = ""
    quality: str = "calculated"
    used_by: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass(frozen=True)
class AssumptionRecord:
    name: str
    value: Any
    unit: str = ""
    source: str = ""
    quality: str = "assumed"
    sensitivity_required: bool = False
    notes: str = ""


@dataclass(frozen=True)
class WarningRecord:
    level: str
    message: str
    affected_modules: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TraceStep:
    name: str
    formula: str
    inputs: list[str] = field(default_factory=list)
    result_name: str = ""
    notes: str = ""


@dataclass(frozen=True)
class ModuleResult:
    module: str
    model_version: str
    status: str
    inputs: list[InputRecord] = field(default_factory=list)
    outputs: list[OutputRecord] = field(default_factory=list)
    assumptions: list[AssumptionRecord] = field(default_factory=list)
    warnings: list[WarningRecord] = field(default_factory=list)
    trace: list[TraceStep] = field(default_factory=list)

    def output_map(self) -> dict[str, Any]:
        return {item.name: item.value for item in self.outputs}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def module_results_to_dicts(results: list[ModuleResult]) -> list[dict[str, Any]]:
    return [result.to_dict() for result in results]
