"""Family air-quality plan orchestration service.

Executes physical exposure simulations, behavioral swaps, emissions analysis,
cleaner day optimization, and grounded LLM explanation generation.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass

import httpx
from pydantic import ValidationError

from app.core.constants import DEFAULT_FORECAST_DAYS, HOURS_IN_DAY
from app.engine.alternatives import indoor_hacks, sustainable_alternatives
from app.engine.assistant_models import AirQualityData
from app.engine.cleaner_day import generate_cleaner_day
from app.engine.emissions import calculate_emissions_and_cost
from app.engine.exposure import simulate_exposure
from app.engine.exposure_models import ExposureResult
from app.engine.swaps import generate_swaps
from app.schemas.family import FamilyMember
from app.schemas.plan import PlanRequest
from app.schemas.routine import Routine
from app.services.air_quality import fetch_air_quality
from app.services.llm import explain_with_fallback, parse_routine
from app.services.plan_builder import (
    PipelineOutputs,
    build_community_payload,
    build_indoor_module,
    build_plan_artifacts,
    default_routine,
    extract_aqi_series,
    extract_pm25_series,
    extract_primary_commute,
    format_plan_response,
)

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


def _compute_exposure_and_swaps(
    air: AirQualityData | Mapping[str, object],
    routine: Routine,
    members: list[FamilyMember],
) -> tuple[ExposureResult, list[dict[str, object]]]:
    """Calculate hourly physical exposure and rank behavioral swaps."""
    pm25_series = extract_pm25_series(air)
    pm25 = pm25_series[:HOURS_IN_DAY] if len(pm25_series) >= HOURS_IN_DAY else pm25_series
    aqi_series = extract_aqi_series(air)
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
    pm25_series = extract_pm25_series(air)
    pm25 = pm25_series[:HOURS_IN_DAY] if len(pm25_series) >= HOURS_IN_DAY else pm25_series
    aqi_series = extract_aqi_series(air)
    aqi = aqi_series[:HOURS_IN_DAY] if len(aqi_series) >= HOURS_IN_DAY else aqi_series
    cleaner = generate_cleaner_day(pm25, aqi, members, routine)
    cleaner_dict = cleaner.to_dict()
    primary_commute = extract_primary_commute(routine)
    emissions = calculate_emissions_and_cost(
        commute_mode=primary_commute,
        cooking_fuel=str(routine.home.cooking),
        heating_fuel=str(routine.home.heating),
    )
    emissions_dict = emissions.to_dict()
    return cleaner_dict, emissions_dict


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

    explanation = await _generate_explanation(
        engine, payload.language, explain_fn=resolved_deps.explain_fn
    )

    outputs = PipelineOutputs(
        swaps_dicts=swaps_dicts,
        cleaner_day_dict=cleaner_day_dict,
        emissions_dict=emissions_dict,
        explanation=explanation,
    )
    artifacts = build_plan_artifacts(payload, air, engine, outputs)
    return format_plan_response(artifacts)


resolve_routine = _resolve_routine
generate_explanation = _generate_explanation
_build_artifacts = build_plan_artifacts
_build_community_payload = build_community_payload
_build_indoor_module = build_indoor_module
_extract_primary_commute = extract_primary_commute

__all__ = [
    "ExplainFn",
    "FetchAirQualityFn",
    "ParseRoutineFn",
    "PipelineOutputs",
    "PlanDependencies",
    "_build_artifacts",
    "_build_community_payload",
    "_build_indoor_module",
    "_extract_primary_commute",
    "_generate_explanation",
    "_resolve_routine",
    "default_routine",
    "execute_plan_pipeline",
    "extract_primary_commute",
    "generate_explanation",
    "resolve_routine",
]
