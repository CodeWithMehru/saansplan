"""Frozen domain models for pure calculation engines and services."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass, fields
from typing import Any

from app.schemas.routine import Routine


@dataclass(frozen=True)
class FrozenDomainModel:
    """Base class for frozen domain dataclasses with dict-like mapping access."""

    def to_dict(self) -> dict[str, Any]:
        """Convert dataclass and all nested structures to primitive dictionary."""
        return asdict(self)

    def __getitem__(self, key: str) -> Any:
        """Allow subscript access for backwards compatibility."""
        if hasattr(self, key):
            val = getattr(self, key)
            if isinstance(val, FrozenDomainModel):
                return val.to_dict()
            return val
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow mutation for plan assembly."""
        object.__setattr__(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """Provide fallback dictionary-like retrieval."""
        val = getattr(self, key, default)
        if isinstance(val, FrozenDomainModel):
            return val.to_dict()
        return val

    def __contains__(self, key: object) -> bool:
        """Check field membership."""
        if not isinstance(key, str):
            return False
        return hasattr(self, key)

    def keys(self) -> list[str]:
        """Return list of declared field names."""
        return [f.name for f in fields(self)]

    def __iter__(self) -> Iterator[str]:
        """Iterate over declared field names."""
        return iter(self.keys())

    def __len__(self) -> int:
        """Return number of declared fields."""
        return len(fields(self))


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

    def to_dict(self) -> dict[str, Any]:
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
    changes: list[dict[str, Any]]
    routine: Routine
    hourly_comparison: Sequence[CleanerDayHourlyRow]


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

    def to_dict(self) -> dict[str, Any]:
        """Convert dataclass to dict, omitting pm_saved_g if None and is_free for non-commute."""
        d = asdict(self)
        if self.pm_saved_g is None:
            d.pop("pm_saved_g", None)
        if self.category != "commute":
            d.pop("is_free", None)
        return d


def _model_to_dict(model: Any) -> Any:
    """Normalize model to primitive dict representation."""
    return model.to_dict() if hasattr(model, "to_dict") else model


def _models_to_dict_list(models: Sequence[Any]) -> list[Any]:
    """Convert sequence of models to list of primitive dictionaries."""
    return [_model_to_dict(m) for m in models]


@dataclass(frozen=True)
class EmissionsResult(FrozenDomainModel):
    """Weekly household transit, cooking, and heating emissions analysis."""

    current: EmissionsCurrent
    alternatives: Sequence[EmissionsOption]
    all_alternatives: Sequence[EmissionsOption]
    budget_filter: str

    def to_dict(self) -> dict[str, Any]:
        """Convert result to clean dictionary matching exact schema."""
        return {
            "current": _model_to_dict(self.current),
            "alternatives": _models_to_dict_list(self.alternatives),
            "all_alternatives": _models_to_dict_list(self.all_alternatives),
            "budget_filter": self.budget_filter,
        }


@dataclass(frozen=True)
class PurifierCadr(FrozenDomainModel):
    """Room sizing AHAM CADR computation."""

    room_area_m2: float
    room_area_sqft: float
    ceiling_height_m: float
    volume_m3: float
    recommended_smoke_cadr_cfm: int
    recommended_smoke_cadr_m3h: int
    target_ach: int
    rule_basis: str


@dataclass(frozen=True)
class DiyBoxFanGuide(FrozenDomainModel):
    """Step-by-step Corsi-Rosenthal / DIY box fan air cleaner setup."""

    title: str
    estimated_cost_inr: str
    materials: list[str]
    assembly_steps: list[str]
    safety_warnings: list[str]
    filter_efficiency: str


@dataclass(frozen=True)
class RoomChecklistItem(FrozenDomainModel):
    """Targeted indoor room action."""

    action: str
    reduction_estimate: str
    source: str


@dataclass(frozen=True)
class SchoolAdvisory(FrozenDomainModel):
    """School and children attendance guidance based on peak AQI."""

    title: str
    severity: str
    category: str
    actions: list[str]
    shareable_text: str


@dataclass(frozen=True)
class RwaChecklistItem(FrozenDomainModel):
    """RWA checklist entry."""

    category: str
    action: str
    guidance: str


@dataclass(frozen=True)
class RwaChecklist(FrozenDomainModel):
    """Neighborhood and apartment community collective air interventions."""

    title: str
    disclaimer: str
    items: list[RwaChecklistItem | dict[str, str]]


@dataclass(frozen=True)
class CommunityPayload(FrozenDomainModel):
    """Community advisories, checklists, and shareable links."""

    school_advisory: SchoolAdvisory | dict[str, Any]
    rwa_checklist: RwaChecklist | dict[str, Any]
    whatsapp_url: str
    shareable_text: str


@dataclass(frozen=True)
class IndoorModulePayload(FrozenDomainModel):
    """Indoor interventions, purifier CADR, and room checklists."""

    room_checklists: dict[str, list[dict[str, Any]]]
    purifier_sizing_default: PurifierCadr | dict[str, Any]
    diy_box_fan_guide: DiyBoxFanGuide | dict[str, Any]


@dataclass(frozen=True)
class PersonaMember(FrozenDomainModel):
    """Preset family member entry."""

    name: str
    ageGroup: str  # noqa: N815
    sensitive: bool


@dataclass(frozen=True)
class PersonaPreset(FrozenDomainModel):
    """Urban Indian lifestyle persona preset."""

    id: str
    name: str
    description: str
    members: list[PersonaMember | dict[str, Any]]
    routine_text: str
    commute: str
    outdoor_minutes: int
    cooking: str
    heating: str
    windows: str
    purifier: bool
    budget: str


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
