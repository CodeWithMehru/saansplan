"""Domain models for behavioral substitutions and sustainable alternatives."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from app.engine.base_model import FrozenDomainModel


@dataclass(frozen=True)
class SwapRecommendation(FrozenDomainModel):
    """Actionable behavioral substitution to reduce pollutant dose."""

    key: str
    description_key: str
    exposure_before: float
    exposure_after: float
    percent_reduction: float
    emissions_note: str
    from_hour: int | None = None
    to_hour: int | None = None

    def to_dict(self) -> dict[str, object]:
        """Convert dataclass to dict, omitting from_hour/to_hour if None."""
        d = asdict(self)
        if self.from_hour is None:
            d.pop("from_hour", None)
        if self.to_hour is None:
            d.pop("to_hour", None)
        return d


@dataclass(frozen=True)
class IndoorHack(FrozenDomainModel):
    """Low-cost household interventions to lower indoor particulate accumulation."""

    key: str
    impact: str
    estimate: str


@dataclass(frozen=True)
class SustainableAlternative(FrozenDomainModel):
    """Long-term sustainable transit or fuel alternative with emissions savings."""

    key: str
    exposure_note: str
    emissions_note: str
