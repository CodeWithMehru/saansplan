"""Domain models for cleaner day optimized routine comparisons."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.engine.base_model import FrozenDomainModel
from app.schemas.routine import Routine


@dataclass(frozen=True)
class CleanerDayHourlyRow(FrozenDomainModel):
    """Hourly comparison row between baseline and cleaner day."""

    hour: int
    pm25: float
    aqi: int
    category: str
    category_slug: str
    exposure_before: float
    exposure_after: float
    difference: float = 0.0


@dataclass(frozen=True)
class CleanerDayResult(FrozenDomainModel):
    """Complete optimized schedule comparison against baseline routine."""

    total_exposure_before: float
    total_exposure_after: float
    percent_reduction: float
    inhaled_saved_ug: float
    inhaled_saved_range_ug: tuple[float, float]
    changes: list[dict[str, str | int | float]]
    routine: Routine
    hourly_comparison: Sequence[CleanerDayHourlyRow]
