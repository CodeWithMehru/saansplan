"""Domain models for cumulative family physical exposure simulation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.engine.base_model import FrozenDomainModel
from app.engine.cleaner_day_models import CleanerDayResult
from app.engine.swaps_models import IndoorHack, SustainableAlternative, SwapRecommendation


@dataclass(frozen=True)
class HourlyExposureRow(FrozenDomainModel):
    """Hourly atmospheric exposure and Indian AQI metrics."""

    hour: int
    pm25: float
    aqi: int
    exposure: float
    interpolated: bool
    indian_aqi: int
    indian_category: str


@dataclass(frozen=True)
class MemberExposure(FrozenDomainModel):
    """Individual family member cumulative exposure."""

    name: str
    exposure: float


@dataclass(frozen=True)
class ExposureResult(FrozenDomainModel):
    """Cumulative daily family exposure simulation output."""

    total_before: float
    members: Sequence[MemberExposure]
    hourly: Sequence[HourlyExposureRow]
    peak_hour: int
    peak_aqi: int
    highest_aqi_hour: int
    highest_aqi: int
    estimate_label: str
    top_swap: SwapRecommendation | None = None
    top_swaps: Sequence[SwapRecommendation] | None = None
    indoor_hacks: Sequence[IndoorHack] | None = None
    sustainable_alternatives: Sequence[SustainableAlternative] | None = None
    cleaner_day: CleanerDayResult | None = None
