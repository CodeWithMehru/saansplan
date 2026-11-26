"""Family air-quality plan orchestration service.

Executes physical exposure simulations, behavioral swaps, emissions analysis,
cleaner day optimization, and grounded LLM explanation generation.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from app.core.constants import DEFAULT_FORECAST_DAYS, HOURS_IN_DAY
from app.engine.alternatives import indoor_hacks, sustainable_alternatives
from app.engine.cleaner_day import generate_cleaner_day
from app.engine.community import (
    generate_whatsapp_share_url,
    get_rwa_checklist,
    get_school_day_advisory,
)
from app.engine.domain_models import AirQualityData, ExposureResult
from app.engine.emissions import calculate_emissions_and_cost
from app.engine.exposure import simulate_exposure
from app.engine.forecast import analyze_forecast
from app.engine.indoor_module import (
    calculate_purifier_cadr,
    get_diy_box_fan_guide,
    get_room_checklists,
)
from app.engine.personas import get_personas
from app.engine.swaps import generate_swaps
from app.models import HomeSetup, PlanRequest, Routine
from app.services.air_quality import fetch_air_quality
from app.services.llm import explain_with_fallback, parse_routine

DEFAULT_ROOM_AREA_SQM = 15.0


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


async def _parse_text_routine(text: str, parse_fn: Any, payload: PlanRequest) -> Routine:
    """Parse text into routine using LLM parser with safe fallback."""
    try:
        return await asyncio.wait_for(parse_fn(text), timeout=6.0)
    except Exception:  # noqa: BLE001  # Safe routine parsing fallback
        return default_routine(payload)


async def _resolve_routine(payload: PlanRequest, parse_routine_fn: Any = None) -> Routine:
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


def _build_indoor_module() -> dict[str, Any]:
    """Assemble static and calculated indoor interventions."""
    cadr = calculate_purifier_cadr(area_sq_meters=DEFAULT_ROOM_AREA_SQM)
    diy = get_diy_box_fan_guide()
    return {
        "room_checklists": get_room_checklists(),
        "purifier_sizing_default": cadr.to_dict() if hasattr(cadr, "to_dict") else cadr,
        "diy_box_fan_guide": diy.to_dict() if hasattr(diy, "to_dict") else diy,
    }


def _build_community_payload(
    city: str | None,
    peak_aqi: int,
    category: str,
    swaps: Any,
    cleaner_day: Any,
) -> dict[str, Any]:
    """Generate shareable community advisory texts and links."""
    summary = (
        f"SaansPlan Family Summary:\n"
        f"Location: {city or 'My City'} (AQI {peak_aqi} - {category})\n"
        f"Top swap: {swaps[0]['description_key'] if swaps else 'Keep windows closed'}\n"
        f"Dose reduction: {cleaner_day['percent_reduction']}% cleaner routine.\n"
        f"Check full low-emission day plan on SaansPlan."
    )
    return {
        "school_advisory": get_school_day_advisory(max_aqi=peak_aqi, indian_category=category),
        "rwa_checklist": get_rwa_checklist(),
        "whatsapp_url": generate_whatsapp_share_url(summary),
        "shareable_text": summary,
    }


async def _generate_explanation(
    engine: Any,
    language: str,
    explain_fn: Any = None,
) -> dict[str, Any]:
    """Generate grounded LLM explanation with deterministic fallback."""
    fn = explain_fn or explain_with_fallback
    try:
        res: Any = await asyncio.wait_for(fn(engine, language), timeout=15.0)
        out = res.to_dict() if hasattr(res, "to_dict") else res
        return dict(out)
    except Exception:  # noqa: BLE001  # Safe explanation fallback
        return {
            "explanation": "AI explanation unavailable. Deterministic engine estimates are ready.",
            "ai_available": False,
        }


async def _fetch_plan_inputs(
    payload: PlanRequest,
    client: Any,
    fetch_aq_fn: Any = None,
    parse_routine_fn: Any = None,
) -> tuple[AirQualityData, Routine]:
    """Fetch air quality data and resolve routine concurrently."""
    fetch_fn = fetch_aq_fn or fetch_air_quality
    air_task = fetch_fn(
        payload.latitude, payload.longitude, forecast_days=DEFAULT_FORECAST_DAYS, client=client
    )
    routine_task = _resolve_routine(payload, parse_routine_fn=parse_routine_fn)
    air, routine = await asyncio.gather(air_task, routine_task)
    return air, routine


def _as_dict(item: Any) -> Any:
    """Normalize domain model or dict to primitive mapping."""
    return item.to_dict() if hasattr(item, "to_dict") else item


def _to_dicts(seq: Any) -> list[Any]:
    """Convert sequence of domain models to primitive dictionaries."""
    return [_as_dict(item) for item in seq]


def _compute_exposure_and_swaps(
    air: AirQualityData | dict[str, Any], routine: Routine, members: list[Any]
) -> tuple[ExposureResult, list[dict[str, Any]]]:
    """Calculate hourly physical exposure and rank behavioral swaps."""
    pm25 = air["pm25"][:HOURS_IN_DAY] if len(air["pm25"]) >= HOURS_IN_DAY else air["pm25"]
    aqi = air["aqi"][:HOURS_IN_DAY] if len(air["aqi"]) >= HOURS_IN_DAY else air["aqi"]
    engine = simulate_exposure(pm25, aqi, members, routine)
    swaps = generate_swaps(pm25, aqi, members, routine)
    swaps_dicts = _to_dicts(swaps)
    engine["top_swap"] = swaps_dicts[0] if swaps_dicts else None
    engine["top_swaps"] = swaps_dicts
    engine["indoor_hacks"] = _to_dicts(indoor_hacks())
    engine["sustainable_alternatives"] = _to_dicts(sustainable_alternatives())
    return engine, swaps_dicts


def _compute_cleaner_and_emissions(
    air: AirQualityData | dict[str, Any], routine: Routine, members: list[Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Generate cleaner routine shift and household emissions/cost analysis."""
    pm25 = air["pm25"][:HOURS_IN_DAY] if len(air["pm25"]) >= HOURS_IN_DAY else air["pm25"]
    aqi = air["aqi"][:HOURS_IN_DAY] if len(air["aqi"]) >= HOURS_IN_DAY else air["aqi"]
    cleaner = generate_cleaner_day(pm25, aqi, members, routine)
    cleaner_dict = _as_dict(cleaner)
    primary_commute = _extract_primary_commute(routine)
    emissions = calculate_emissions_and_cost(
        commute_mode=primary_commute,
        cooking_fuel=str(routine.home.cooking),
        heating_fuel=str(routine.home.heating),
    )
    emissions_dict = _as_dict(emissions)
    return cleaner_dict, emissions_dict


@dataclass(frozen=True)
class PlanExecutionArtifacts:
    """Artifacts produced by the multi-engine calculation pipeline."""

    payload: PlanRequest
    air: AirQualityData | dict[str, Any]
    engine: ExposureResult
    swaps_dicts: list[dict[str, Any]]
    forecast_days: Any
    cleaner_day_dict: dict[str, Any]
    emissions_dict: dict[str, Any]
    community: dict[str, Any]
    explanation: dict[str, Any]


def _format_plan_response(artifacts: PlanExecutionArtifacts) -> dict[str, Any]:
    """Package calculation engines and guidance into stable JSON response envelope."""
    peak = max(artifacts.engine["hourly"], key=lambda row: row["pm25"])
    personas_dict = {k: _as_dict(v) for k, v in get_personas().items()}
    return {
        "location": {
            "latitude": artifacts.payload.latitude,
            "longitude": artifacts.payload.longitude,
            "city": artifacts.payload.city,
            "timezone": artifacts.air["timezone"],
            "source": artifacts.air["source"],
        },
        "exposure": _as_dict(artifacts.engine),
        "top_swaps": artifacts.swaps_dicts,
        "hourly": _to_dicts(artifacts.engine["hourly"]),
        "indoor_hacks": artifacts.engine["indoor_hacks"],
        "sustainable_alternatives": artifacts.engine["sustainable_alternatives"],
        "peak_pm25_hour": peak["hour"],
        "forecast": _to_dicts(artifacts.forecast_days),
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
    client: Any,
    fetch_aq_fn: Any = None,
    parse_routine_fn: Any = None,
    explain_fn: Any = None,
) -> dict[str, Any]:
    """Execute exposure, swaps, forecast, cleaner day, and emissions pipelines."""
    air, routine = await _fetch_plan_inputs(
        payload, client, fetch_aq_fn=fetch_aq_fn, parse_routine_fn=parse_routine_fn
    )
    engine, swaps_dicts = _compute_exposure_and_swaps(air, routine, payload.members)
    cleaner_day_dict, emissions_dict = _compute_cleaner_and_emissions(air, routine, payload.members)
    engine["cleaner_day"] = cleaner_day_dict

    forecast_days = analyze_forecast(
        air["pm25"], air.get("wind_speed"), forecast_days=DEFAULT_FORECAST_DAYS
    )
    peak_aqi = engine.get("peak_aqi", 250)
    category = engine["hourly"][0].get("indian_category", "Poor") if engine["hourly"] else "Poor"
    community = _build_community_payload(
        payload.city, peak_aqi, category, swaps_dicts, cleaner_day_dict
    )
    explanation = await _generate_explanation(engine, payload.language, explain_fn=explain_fn)

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
    "PlanExecutionArtifacts",
    "default_routine",
    "execute_plan_pipeline",
    "extract_primary_commute",
    "generate_explanation",
    "resolve_routine",
]
