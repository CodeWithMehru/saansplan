"""Domain models for household emissions, cost estimates, and budget alternatives."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

from app.engine.base_model import FrozenDomainModel


@dataclass(frozen=True)
class EmissionsCurrent(FrozenDomainModel):
    """Current weekly baseline emissions across sectors."""

    commute_mode: str
    weekly_co2e_kg: float
    weekly_pm_g: float
    weekly_cost_inr: int | float


@dataclass(frozen=True)
class EmissionsOption(FrozenDomainModel):
    """Tiered emissions and financial alternative."""

    mode: str
    title: str
    category: str
    weekly_co2e_kg: float
    weekly_cost_inr: int | float
    co2e_saved_kg: float
    inr_saved_weekly: int | float
    upfront_cost_inr: int | float
    budget_tier: str
    is_free: bool = False
    pm_saved_g: float | None = None

    def to_dict(self) -> dict[str, object]:
        """Convert dataclass to dict, omitting pm_saved_g if None and is_free for non-commute."""
        d = asdict(self)
        if self.pm_saved_g is None:
            d.pop("pm_saved_g", None)
        if self.category != "commute":
            d.pop("is_free", None)
        return d


@dataclass(frozen=True)
class EmissionsResult(FrozenDomainModel):
    """Weekly household transit, cooking, and heating emissions analysis."""

    current: EmissionsCurrent
    alternatives: Sequence[EmissionsOption]
    all_alternatives: Sequence[EmissionsOption]
    budget_filter: str

    def to_dict(self) -> dict[str, object]:
        """Convert result to clean dictionary matching exact schema."""
        return {
            "current": self.current.to_dict(),
            "alternatives": [alt.to_dict() for alt in self.alternatives],
            "all_alternatives": [alt.to_dict() for alt in self.all_alternatives],
            "budget_filter": self.budget_filter,
        }
