"""Family air-quality plan orchestration service.

Executes physical exposure simulations, behavioral swaps, emissions analysis,
cleaner day optimization, and grounded LLM explanation generation.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass

import httpx
from pydantic import ValidationError

from app.core.constants import DEFAULT_FORECAST_DAYS, HOURS_IN_DAY
from app.engine.alternatives import indoor_hacks, sustainable_alternatives
from app.engine.cleaner_day import generate_cleaner_day
from app.engine.community import (
    generate_whatsapp_share_url,
    get_rwa_checklist,
    get_school_day_advisory,
)
from app.engine.domain_models import (
    AirQualityData,
    ExposureResult,
    ForecastDay,
)
from app.engine.emissions import calculate_emissions_and_cost
from app.engine.exposure import simulate_exposure
from app.engine.forecast import analyze_forecast
from app.engine.indoor_guidance import (
    calculate_purifier_cadr,
    get_diy_box_fan_guide,
    get_room_checklists,
)
from app.engine.personas import get_personas
from app.engine.swaps import generate_swaps
from app.schemas.family import FamilyMember
from app.schemas.plan import PlanRequest
from app.schemas.routine import HomeSetup, Routine
from app.services.air_quality import fetch_air_quality
from app.services.llm import explain_with_fallback, parse_routine

DEFAULT_ROOM_AREA_SQM = 15.0

ParseRoutineFn = Callable[[str], Awaitable[Routine]]
FetchAirQualityFn = Callable[
    [float, float, int, httpx.AsyncClient | None],
    Awaitable[AirQualityData],
]
ExplainFn = Callable[[ExposureResult | Mapping[str, object], str], Awaitable[object]]


@dataclass(frozen=True)
class PlanDependencies:
    """Injectable external dependencies and seam functions for plan generation."""

    client: httpx.AsyncClient | None = None
    fetch_aq_fn: FetchAirQualityFn | None = None
    parse_routine_fn: ParseRoutineFn | None = None
    explain_fn: ExplainFn | None = None


def default_routine(request: PlanRequest) -> Routine:
    """Build a safe form-only fallback routine if no text or routine is supplied."""
    activities = request.routine.activities if request.routine else []
    if request.routine:
        return request.routine
    return Routine(
        activities=activities,
        home=HomeSetup(
            heating="none",
            cooking="lpg",
            windows="mostly_closed",
            purifier=False,
            has_chimney=False,
        ),
    )


async def _parse_text_routine(text: str, parse_fn: ParseRoutineFn, payload: PlanRequest) -> Routine:
    """Parse text into routine using LLM parser with safe fallback."""
    try:
        return await asyncio.wait_for(parse_fn(text), timeout=6.0)
    except (
        httpx.HTTPError,
        TimeoutError,
        RuntimeError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        ValidationError,
    ):
        return default_routine(payload)


async def _resolve_routine(
    payload: PlanRequest, parse_routine_fn: ParseRoutineFn | None = None
) -> Routine:
    """Resolve routine from free text with LLM parser or return validated routine."""
    if payload.routine_text.strip() and payload.routine is None:
        parse_fn = parse_routine_fn or parse_routine
        return await _parse_text_routine(payload.routine_text, parse_fn, payload)
    return payload.routine or default_routine(payload)


def _extract_primary_commute(routine: Routine) -> str:
    """Extract primary commute mode from active routine activities."""
    for act in routine.activities:
        if act.mode.value != "none":
            return act.mode.value
    return "none"


def _build_indoor_module() -> dict[str, object]:
    """Assemble static and calculated indoor interventions."""
    cadr = calculate_purifier_cadr(area_sq_meters=DEFAULT_ROOM_AREA_SQM)
    diy = get_diy_box_fan_guide()
    return {
        "room_checklists": get_room_checklists(),
        "purifier_sizing_default": cadr.to_dict(),
        "diy_box_fan_guide": diy.to_dict(),
    }


def _build_community_payload(
    city: str | None,
    peak_aqi: int,
    category: str,
    swaps: Sequence[dict[str, object]],
    cleaner_day: Mapping[str, object],
) -> dict[str, object]:
    """Generate shareable community advisory texts and links."""
    top_swap_desc = (
        str(swaps[0].get("description_key", "Keep windows closed"))
        if swaps
        else "Keep windows closed"
    )
    reduction = cleaner_day.get("percent_reduction", 0)
    summary = (
        f"SaansPlan Family Summary:\n"
        f"Location: {city or 'My City'} (AQI {peak_aqi} - {category})\n"
        f"Top swap: {top_swap_desc}\n"
        f"Dose reduction: {reduction}% cleaner routine.\n"
        f"Check full low-emission day plan on SaansPlan."
    )
    return {
        "school_advisory": get_school_day_advisory(
            max_aqi=peak_aqi, indian_category=category
        ).to_dict(),
        "rwa_checklist": get_rwa_checklist().to_dict(),
        "whatsapp_url": generate_whatsapp_share_url(summary),
        "shareable_text": summary,
    }


async def _generate_explanation(
    engine: ExposureResult | Mapping[str, object],
    language: str,
    explain_fn: ExplainFn | None = None,
) -> dict[str, object]:
    """Generate grounded LLM explanation with deterministic fallback."""
    fn = explain_fn or explain_with_fallback
    try:
        res = await asyncio.wait_for(fn(engine, language), timeout=15.0)
        out = res.to_dict() if hasattr(res, "to_dict") else res
        if isinstance(out, dict):
            return {str(k): v for k, v in out.items()}
        return {"explanation": str(out), "ai_available": True}
    except (
        httpx.HTTPError,
        TimeoutError,
        RuntimeError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ):
        return {
            "explanation": "AI explanation unavailable. Deterministic engine estimates are ready.",
            "ai_available": False,
        }


async def _fetch_plan_inputs(
    payload: PlanRequest,
    client: httpx.AsyncClient,
    fetch_aq_fn: FetchAirQualityFn | None = None,
    parse_routine_fn: ParseRoutineFn | None = None,
) -> tuple[AirQualityData, Routine]:
    """Fetch air quality data and resolve routine concurrently."""
    fetch_fn = fetch_aq_fn or fetch_air_quality
    air_task = fetch_fn(payload.latitude, payload.longitude, DEFAULT_FORECAST_DAYS, client)
    routine_task = _resolve_routine(payload, parse_routine_fn=parse_routine_fn)
    air, routine = await asyncio.gather(air_task, routine_task)
    return air, routine


def _extract_pm25_series(air: AirQualityData | Mapping[str, object]) -> list[float | None]:
    """Extract PM2.5 float values from AirQualityData or mapping."""
    raw = air.pm25 if isinstance(air, AirQualityData) else air.get("pm25")
    if isinstance(raw, Sequence):
        return [float(v) if isinstance(v, int | float) else None for v in raw]
    return []


def _extract_aqi_series(air: AirQualityData | Mapping[str, object]) -> list[float | None]:
    """Extract AQI integer values from AirQualityData or mapping."""
    raw = air.aqi if isinstance(air, AirQualityData) else air.get("aqi")
    if isinstance(raw, Sequence):
        return [float(v) if isinstance(v, int | float) else None for v in raw]
    return []


def _extract_wind_series(air: AirQualityData | Mapping[str, object]) -> list[float | None] | None:
    """Extract optional wind speed series from AirQualityData or mapping."""
    raw = air.wind_speed if isinstance(air, AirQualityData) else air.get("wind_speed")
    if isinstance(raw, Sequence):
        return [float(v) if isinstance(v, int | float) else None for v in raw]
    return None


def _extract_metadata(air: AirQualityData | Mapping[str, object]) -> tuple[str, str]:
    """Extract timezone and data source from AirQualityData or mapping."""
    tz = str(air.timezone if isinstance(air, AirQualityData) else air.get("timezone", "UTC"))
    src = str(air.source if isinstance(air, AirQualityData) else air.get("source", "Open-Meteo"))
    return tz, src


def _compute_exposure_and_swaps(
    air: AirQualityData | Mapping[str, object],
    routine: Routine,
    members: list[FamilyMember],
) -> tuple[ExposureResult, list[dict[str, object]]]:
    """Calculate hourly physical exposure and rank behavioral swaps."""
    pm25_series = _extract_pm25_series(air)
    pm25 = pm25_series[:HOURS_IN_DAY] if len(pm25_series) >= HOURS_IN_DAY else pm25_series
    aqi_series = _extract_aqi_series(air)
    aqi = aqi_series[:HOURS_IN_DAY] if len(aqi_series) >= HOURS_IN_DAY else aqi_series
    engine = simulate_exposure(pm25, aqi, members, routine)
    swaps = generate_swaps(pm25, aqi, members, routine)
    swaps_dicts = [s.to_dict() for s in swaps]
    engine["top_swap"] = swaps_dicts[0] if swaps_dicts else None
    engine["top_swaps"] = swaps_dicts
    engine["indoor_hacks"] = [h.to_dict() for h in indoor_hacks()]
    engine["sustainable_alternatives"] = [a.to_dict() for a in sustainable_alternatives()]
    return engine, swaps_dicts


def _compute_cleaner_and_emissions(
    air: AirQualityData | Mapping[str, object],
    routine: Routine,
    members: list[FamilyMember],
) -> tuple[dict[str, object], dict[str, object]]:
    """Generate cleaner routine shift and household emissions/cost analysis."""
    pm25_series = _extract_pm25_series(air)
    pm25 = pm25_series[:HOURS_IN_DAY] if len(pm25_series) >= HOURS_IN_DAY else pm25_series
    aqi_series = _extract_aqi_series(air)
    aqi = aqi_series[:HOURS_IN_DAY] if len(aqi_series) >= HOURS_IN_DAY else aqi_series
    cleaner = generate_cleaner_day(pm25, aqi, members, routine)
    cleaner_dict = cleaner.to_dict()
    primary_commute = _extract_primary_commute(routine)
    emissions = calculate_emissions_and_cost(
        commute_mode=primary_commute,
        cooking_fuel=str(routine.home.cooking),
        heating_fuel=str(routine.home.heating),
    )
    emissions_dict = emissions.to_dict()
    return cleaner_dict, emissions_dict


@dataclass(frozen=True)
class PlanExecutionArtifacts:
    """Artifacts produced by the multi-engine calculation pipeline."""

    payload: PlanRequest
    air: AirQualityData | Mapping[str, object]
    engine: ExposureResult
    swaps_dicts: list[dict[str, object]]
    forecast_days: Sequence[ForecastDay]
    cleaner_day_dict: dict[str, object]
    emissions_dict: dict[str, object]
    community: dict[str, object]
    explanation: dict[str, object]


def _format_plan_response(artifacts: PlanExecutionArtifacts) -> dict[str, object]:
    """Package calculation engines and guidance into stable JSON response envelope."""
    peak = max(artifacts.engine.hourly, key=lambda row: row.pm25)
    personas_dict = {k: v.to_dict() for k, v in get_personas().items()}
    tz, src = _extract_metadata(artifacts.air)
    return {
        "location": {
            "latitude": artifacts.payload.latitude,
            "longitude": artifacts.payload.longitude,
            "city": artifacts.payload.city,
            "timezone": tz,
            "source": src,
        },
        "exposure": artifacts.engine.to_dict(),
        "top_swaps": artifacts.swaps_dicts,
        "hourly": [h.to_dict() for h in artifacts.engine.hourly],
        "indoor_hacks": artifacts.engine["indoor_hacks"],
        "sustainable_alternatives": artifacts.engine["sustainable_alternatives"],
        "peak_pm25_hour": peak.hour,
        "forecast": [f.to_dict() for f in artifacts.forecast_days],
        "cleaner_day": artifacts.cleaner_day_dict,
        "emissions": artifacts.emissions_dict,
        "indoor_module": _build_indoor_module(),
        "personas": personas_dict,
        "community": artifacts.community,
        "explanation": artifacts.explanation,
        "estimate_label": "All values are estimates",
    }


async def execute_plan_pipeline(
    payload: PlanRequest,
    client: httpx.AsyncClient | None = None,
    deps: PlanDependencies | None = None,
) -> dict[str, object]:
    """Execute exposure, swaps, forecast, cleaner day, and emissions pipelines."""
    http_client = (deps.client if deps and deps.client else client) or httpx.AsyncClient()
    resolved_deps = deps or PlanDependencies(client=http_client)
    air, routine = await _fetch_plan_inputs(
        payload,
        http_client,
        fetch_aq_fn=resolved_deps.fetch_aq_fn,
        parse_routine_fn=resolved_deps.parse_routine_fn,
    )
    engine, swaps_dicts = _compute_exposure_and_swaps(air, routine, payload.members)
    cleaner_day_dict, emissions_dict = _compute_cleaner_and_emissions(air, routine, payload.members)
    engine["cleaner_day"] = cleaner_day_dict

    pm25_list = _extract_pm25_series(air)
    wind_list = _extract_wind_series(air)
    forecast_days = analyze_forecast(pm25_list, wind_list, forecast_days=DEFAULT_FORECAST_DAYS)
    peak_aqi_raw = engine.get("peak_aqi", 250)
    peak_aqi = int(peak_aqi_raw) if isinstance(peak_aqi_raw, int | float | str) else 250
    category = str(engine.hourly[0].indian_category) if engine.hourly else "Poor"
    community = _build_community_payload(
        payload.city, peak_aqi, category, swaps_dicts, cleaner_day_dict
    )
    explanation = await _generate_explanation(
        engine, payload.language, explain_fn=resolved_deps.explain_fn
    )

    artifacts = PlanExecutionArtifacts(
        payload=payload,
        air=air,
        engine=engine,
        swaps_dicts=swaps_dicts,
        forecast_days=forecast_days,
        cleaner_day_dict=cleaner_day_dict,
        emissions_dict=emissions_dict,
        community=community,
        explanation=explanation,
    )
    return _format_plan_response(artifacts)


resolve_routine = _resolve_routine
generate_explanation = _generate_explanation
extract_primary_commute = _extract_primary_commute

__all__ = [
    "ExplainFn",
    "FetchAirQualityFn",
    "ParseRoutineFn",
    "PlanDependencies",
    "PlanExecutionArtifacts",
    "default_routine",
    "execute_plan_pipeline",
    "extract_primary_commute",
    "generate_explanation",
    "resolve_routine",
]
