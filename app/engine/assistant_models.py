"""Domain models for atmospheric forecasts, assistant answers, and LLM explanations."""

from __future__ import annotations

from dataclasses import dataclass

from app.engine.base_model import FrozenDomainModel


@dataclass(frozen=True)
class AirQualityData(FrozenDomainModel):
    """Atmospheric conditions payload from Open-Meteo."""

    pm25: list[float | None]
    aqi: list[float | None]
    times: list[str]
    wind_speed: list[float | None] | None
    timezone: str
    source: str


@dataclass(frozen=True)
class ExplanationResult(FrozenDomainModel):
    """Grounded explanation with fallback indicator."""

    explanation: str
    ai_available: bool


@dataclass(frozen=True)
class AssistantAnswer(FrozenDomainModel):
    """Grounded answer from Ask SaansPlan assistant."""

    answer: str
    kb_ids: list[str]
    safety_redirect: bool = False
    verified: bool = True
