"""Domain models for community school advisories and RWA collective checklists."""

from __future__ import annotations

from dataclasses import dataclass

from app.engine.base_model import FrozenDomainModel


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

    school_advisory: SchoolAdvisory | dict[str, object]
    rwa_checklist: RwaChecklist | dict[str, object]
    whatsapp_url: str
    shareable_text: str
