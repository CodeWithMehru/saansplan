"""Family air-quality plan API with forecast, cleaner day, emissions, and indoor modules."""

import asyncio
from typing import Any

from fastapi import APIRouter, Request

from app.config import RATE_LIMIT
from app.core.constants import DEFAULT_FORECAST_DAYS, HOURS_IN_DAY
from app.engine.alternatives import indoor_hacks, sustainable_alternatives
from app.engine.cleaner_day import generate_cleaner_day
from app.engine.community import (
    generate_whatsapp_share_url,
    get_rwa_checklist,
    get_school_day_advisory,
)
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
from app.limiting import limiter
from app.models import HomeSetup, PlanRequest, Routine
from app.services.air_quality import fetch_air_quality
from app.services.llm import explain_with_fallback, parse_routine

router = APIRouter()

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


async def _resolve_routine(payload: PlanRequest) -> Routine:
    """Resolve routine from free text with LLM parser or return validated routine."""
    if payload.routine_text.strip() and payload.routine is None:
        try:
            return await asyncio.wait_for(parse_routine(payload.routine_text), timeout=6.0)
        except Exception:
            return default_routine(payload)
    return payload.routine or default_routine(payload)


def _extract_primary_commute(routine: Routine) -> str:
    """Extract primary commute mode from active routine activities."""
    for act in routine.activities:
        if act.mode.value != "none":
            return act.mode.value
    return "none"


def _build_indoor_module() -> dict[str, Any]:
    """Assemble static and calculated indoor interventions."""
    return {
        "room_checklists": get_room_checklists(),
        "purifier_sizing_default": calculate_purifier_cadr(area_sq_meters=DEFAULT_ROOM_AREA_SQM),
        "diy_box_fan_guide": get_diy_box_fan_guide(),
    }


def _build_community_payload(
    city: str | None,
    peak_aqi: int,
    category: str,
    swaps: list[dict[str, Any]],
    cleaner_day: dict[str, Any],
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


async def _generate_explanation(engine: dict[str, Any], language: str) -> dict[str, Any]:
    """Generate grounded LLM explanation with deterministic fallback."""
    try:
        return await asyncio.wait_for(explain_with_fallback(engine, language), timeout=15.0)
    except Exception:
        return {
            "explanation": "AI explanation unavailable. Deterministic engine estimates are ready.",
            "ai_available": False,
        }


@router.post("/api/plan")
@limiter.limit(RATE_LIMIT)
async def create_plan(request: Request, payload: PlanRequest) -> dict[str, Any]:
    """Fetch AQ, parse routine, run physical engines, and return full suite of recommendations."""
    client = getattr(request.app.state, "http_client", None)
    air_task = fetch_air_quality(
        payload.latitude, payload.longitude, forecast_days=DEFAULT_FORECAST_DAYS, client=client
    )
    routine_task = _resolve_routine(payload)
    air, routine = await asyncio.gather(air_task, routine_task)

    today_pm25 = air["pm25"][:HOURS_IN_DAY] if len(air["pm25"]) >= HOURS_IN_DAY else air["pm25"]
    today_aqi = air["aqi"][:HOURS_IN_DAY] if len(air["aqi"]) >= HOURS_IN_DAY else air["aqi"]

    engine = simulate_exposure(today_pm25, today_aqi, payload.members, routine)
    swaps = generate_swaps(today_pm25, today_aqi, payload.members, routine)
    engine["top_swap"] = swaps[0] if swaps else None
    engine["top_swaps"] = swaps
    engine["indoor_hacks"] = indoor_hacks()
    engine["sustainable_alternatives"] = sustainable_alternatives()

    forecast_days = analyze_forecast(
        air["pm25"], air.get("wind_speed"), forecast_days=DEFAULT_FORECAST_DAYS
    )
    cleaner_day = generate_cleaner_day(today_pm25, today_aqi, payload.members, routine)
    engine["cleaner_day"] = cleaner_day

    primary_commute = _extract_primary_commute(routine)
    emissions = calculate_emissions_and_cost(
        commute_mode=primary_commute,
        cooking_fuel=routine.home.cooking,
        heating_fuel=routine.home.heating,
    )

    peak_aqi = engine.get("peak_aqi", 250)
    category = engine["hourly"][0].get("indian_category", "Poor") if engine["hourly"] else "Poor"
    community = _build_community_payload(payload.city, peak_aqi, category, swaps, cleaner_day)
    explanation = await _generate_explanation(engine, payload.language)

    pm25_rows = engine["hourly"]
    peak = max(pm25_rows, key=lambda row: row["pm25"])

    return {
        "location": {
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "city": payload.city,
            "timezone": air["timezone"],
            "source": air["source"],
        },
        "exposure": engine,
        "top_swaps": swaps,
        "hourly": engine["hourly"],
        "indoor_hacks": engine["indoor_hacks"],
        "sustainable_alternatives": engine["sustainable_alternatives"],
        "peak_pm25_hour": peak["hour"],
        "forecast": forecast_days,
        "cleaner_day": cleaner_day,
        "emissions": emissions,
        "indoor_module": _build_indoor_module(),
        "personas": get_personas(),
        "community": community,
        "explanation": explanation,
        "estimate_label": "All values are estimates",
    }
