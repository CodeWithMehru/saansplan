# ADR 0003: Frozen Typed Domain Models and Dict Invariance

## Status
Accepted

## Context
Earlier versions passed loose dictionaries (`dict[str, Any]`) across engine calculations and service layers. This obscured schema contracts, prevented static type enforcement (mypy), and allowed accidental mutation of intermediate dosage values.

## Decision
We adopt frozen dataclasses (`app/engine/domain_models.py`) as the canonical data representation across the application:
1. **Immutability**: All domain models are decorated with `@dataclass(frozen=True)`.
2. **Explicit Typing**: Zero `Any` in public domain models; all fields use strict primitive types, enums, or nested domain models with comprehensive docstrings.
3. **Dict Compatibility Interface**: To preserve exact backwards compatibility and JSON snapshot equality, domain models implement mapping protocols (`__getitem__`, `get`, `keys`, `__iter__`, `to_dict()`).
4. **Serialization Invariance**: The `to_dict()` methods guarantee exact JSON schema fidelity, matching pre-existing snapshot characterization tests.

## Consequences
- Mypy strictly validates all domain calculations without `type: ignore` or `Any` escapes.
- Intermediate exposure models cannot be mutated in transit.
- Public JSON API contracts remain identical, verified by characterization snapshot suites.
