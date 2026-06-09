"""Small unit-conversion helpers."""

from __future__ import annotations

from .constants import SECONDS_PER_YEAR


def mtpa_to_kg_per_s(mtpa: float) -> float:
    return mtpa * 1e9 / SECONDS_PER_YEAR


def kg_per_s_to_mtpa(kg_per_s: float) -> float:
    return kg_per_s * SECONDS_PER_YEAR / 1e9
