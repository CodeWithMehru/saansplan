# ADR 0001: Layered Hexagonal Architecture and Boundary Isolation

## Status
Accepted

## Context
SaansPlan is a high-reliability air-quality assistant that operates under severe smog conditions where calculation correctness is vital for user safety. In previous iterations, data parsing, meteorological calculations, external API calls, and web route handlers were coupled across shared utility modules. This increased cyclomatic complexity and created circular dependencies, making testing difficult and risking ungrounded numbers.

## Decision
We enforce a strict layered hexagonal architecture with clear directional boundaries:
1. **Core (`app/core/`)**: Cross-cutting infrastructure primitives (settings, caching, rate limiting). Imports only standard library and third-party dependencies.
2. **Engine (`app/engine/`)**: Pure, deterministic calculations (exposure dosage, 5-day smog forecasts, routine optimization, indoor CADR, emissions). The engine is completely isolated: it imports NO code from `app/services/` or `app/routers/` and executes zero network I/O.
3. **Services (`app/services/`)**: Orchestration and external integration (Open-Meteo client, Groq LLM client, prompt verification guards). Services invoke engine functions and external APIs, returning typed domain structures. Services never import from `app/routers/`.
4. **Routers (`app/routers/`)**: Pure HTTP adapters. Handlers perform schema validation, pass inputs to services/engine, and return typed Pydantic responses. Each handler is constrained to at most 15 lines of code.

Directional dependency flow:
`Routers` -> `Services` -> `Engine` -> `Core`

## Consequences
- Engine functions are 100% deterministic and unit-testable with millisecond execution latency (<10 ms).
- Structural integrity is enforced continuously by automated AST boundary tests (`tests/unit/test_architecture_boundaries.py`).
- No business logic or external API coupling leaks into the HTTP transport layer.
