# ADR 0006: Injectable Typed Plan Dependencies

## Status
Accepted

## Context
The plan service orchestration pipeline previously relied on loose function parameters or implicit imports for external network calls and parser seams (`fetch_air_quality`, `parse_routine`, `explain_with_fallback`, `client`). Passing these individually expanded function signatures beyond lint thresholds (Ruff PLR0913) and hindered clean mock injection in automated tests.

## Decision
We introduce a typed, immutable dependency bag `PlanDependencies` in `app/services/plan_service.py`:
1. **Explicit Callable Types**: Define explicit awaitable protocols `FetchAirQualityFn`, `ParseRoutineFn`, and `ExplainFn`.
2. **Dependency Container**: Package optional client and seam functions into `@dataclass(frozen=True) class PlanDependencies`.
3. **Clean Route Layer**: Router endpoint handlers pass the configured dependencies via `PlanDependencies` into `execute_plan_pipeline(payload, deps=deps)`.
4. **Isolated Helper Modules**: Helper extraction (`plan_builder.py`) and regex extraction (`assistant_extractors.py`) keep service orchestration files focused and concise ($\le 250$ lines).

## Consequences
- Function parameter counts remain within clean architectural limits ($\le 3$ parameters).
- Unit and security tests can inject custom mock seams with full static type verification (`mypy --strict`).
- Clear separation between pipeline execution flow and payload assembly logic.
