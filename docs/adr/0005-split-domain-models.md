# ADR 0005: Bounded-Context Model Decomposition

## Status
Accepted

## Context
Previously, all frozen domain models across the application resided in a single monolithic file (`domain_models.py`, 434 lines). While immutable and strictly typed, co-locating models for exposure, forecasts, emissions, cleaner day, indoor sizing, community kits, personas, and assistant responses in one file violated single responsibility and created bloated dependency graphs where simple modules had to import from a large catch-all file.

## Decision
We decompose domain models into explicit bounded-context modules under `app/engine/`:
1. `base_model.py`: Base `FrozenDomainModel` providing mapping access protocol and dictionary serialization.
2. `exposure_models.py`: `HourlyExposureRow`, `MemberExposure`, `ExposureResult`.
3. `swaps_models.py`: `SwapRecommendation`, `IndoorHack`, `SustainableAlternative`.
4. `forecast_models.py`: `ForecastWindow`, `ForecastDay`.
5. `cleaner_day_models.py`: `CleanerDayHourlyRow`, `CleanerDayResult`.
6. `emissions_models.py`: `EmissionsCurrent`, `EmissionsOption`, `EmissionsResult`.
7. `indoor_models.py`: `PurifierCadr`, `DiyBoxFanGuide`, `RoomChecklistItem`, `IndoorModulePayload`.
8. `community_models.py`: `SchoolAdvisory`, `RwaChecklistItem`, `RwaChecklist`, `CommunityPayload`.
9. `persona_models.py`: `PersonaMember`, `PersonaPreset`.
10. `assistant_models.py`: `AirQualityData`, `ExplanationResult`, `AssistantAnswer`.

All call sites import directly from their specific bounded-context module without re-export facades.

## Consequences
- Every Python source file in `app/` is now $\le 250$ lines (100% modular).
- Modules import only the models relevant to their domain concern.
- Structural boundary tests in `tests/unit/test_architecture_boundaries.py` verify that model modules remain pure without importing services or routers.
- Zero runtime overhead and full preservation of JSON snapshot compatibility.
