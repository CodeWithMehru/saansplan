"""Base domain model protocol and mapping emulation for immutability."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass, fields


@dataclass(frozen=True)
class FrozenDomainModel:
    """Base class for frozen domain dataclasses with dict-like mapping access."""

    def to_dict(self) -> dict[str, object]:
        """Convert dataclass and all nested structures to primitive dictionary."""
        return asdict(self)

    def __getitem__(self, key: str) -> object:
        """Allow subscript access for backwards compatibility."""
        if hasattr(self, key):
            val = getattr(self, key)
            if isinstance(val, FrozenDomainModel):
                return val.to_dict()
            return val
        raise KeyError(key)

    def __setitem__(self, key: str, value: object) -> None:
        """Allow mutation for plan assembly."""
        object.__setattr__(self, key, value)

    def get(self, key: str, default: object = None) -> object:
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


Mapping.register(FrozenDomainModel)
