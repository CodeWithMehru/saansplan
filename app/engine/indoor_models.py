"""Domain models for indoor air filtration, CADR sizing, and room interventions."""

from __future__ import annotations

from dataclasses import dataclass

from app.engine.base_model import FrozenDomainModel


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
class IndoorModulePayload(FrozenDomainModel):
    """Indoor interventions, purifier CADR, and room checklists."""

    room_checklists: dict[str, list[dict[str, str]]]
    purifier_sizing_default: PurifierCadr | dict[str, object]
    diy_box_fan_guide: DiyBoxFanGuide | dict[str, object]
