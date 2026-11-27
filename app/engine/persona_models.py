"""Domain models for lifestyle persona presets and member configurations."""

from __future__ import annotations

from dataclasses import dataclass

from app.engine.base_model import FrozenDomainModel


@dataclass(frozen=True)
class PersonaMember(FrozenDomainModel):
    """Preset family member entry."""

    name: str
    age_group: str
    sensitive: bool

    def to_dict(self) -> dict[str, object]:
        """Convert dataclass ensuring camelCase ageGroup in serialized output."""
        return {
            "name": self.name,
            "ageGroup": self.age_group,
            "sensitive": self.sensitive,
        }

    def __getitem__(self, key: str) -> object:
        """Allow subscript access supporting camelCase ageGroup."""
        if key == "ageGroup":
            return self.age_group
        return super().__getitem__(key)

    def get(self, key: str, default: object = None) -> object:
        """Provide fallback dictionary-like retrieval supporting camelCase ageGroup."""
        if key == "ageGroup":
            return self.age_group
        return super().get(key, default)


@dataclass(frozen=True)
class PersonaPreset(FrozenDomainModel):
    """Urban Indian lifestyle persona preset."""

    id: str
    name: str
    description: str
    members: list[PersonaMember | dict[str, object]]
    routine_text: str
    commute: str
    outdoor_minutes: int
    cooking: str
    heating: str
    windows: str
    purifier: bool
    budget: str

    def to_dict(self) -> dict[str, object]:
        """Convert preset and its member objects to primitive dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "members": [m.to_dict() if hasattr(m, "to_dict") else m for m in self.members],
            "routine_text": self.routine_text,
            "commute": self.commute,
            "outdoor_minutes": self.outdoor_minutes,
            "cooking": self.cooking,
            "heating": self.heating,
            "windows": self.windows,
            "purifier": self.purifier,
            "budget": self.budget,
        }
