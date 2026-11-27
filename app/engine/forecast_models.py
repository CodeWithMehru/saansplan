"""Domain models for 5-day air quality forecast windows and daily metrics."""

from __future__ import annotations

from dataclasses import dataclass

from app.engine.base_model import FrozenDomainModel


@dataclass(frozen=True)
class ForecastWindow(FrozenDomainModel):
    """Time window range in 24-hour clock."""

    start_hour: int
    end_hour: int


@dataclass(frozen=True)
class ForecastDay(FrozenDomainModel):
    """Daily forecast summary with extrema windows and stagnation indicators."""

    day_index: int
    avg_pm25: float
    max_pm25: float
    min_pm25: float
    peak_aqi: int
    indian_category: str
    category_slug: str
    is_severe: bool
    worst_window: ForecastWindow | dict[str, int]
    best_window: ForecastWindow | dict[str, int]
    safest_airing_hour: int
    is_stagnant: bool
    avg_wind_speed_mps: float
