"""Family air-quality plan API."""

import asyncio
from typing import Any

from fastapi import APIRouter, Request

from app.config import RATE_LIMIT
from app.engine.alternatives import indoor_hacks, sustainable_alternatives
from app.engine.exposure import simulate_exposure
from app.engine.swaps import generate_swaps
from app.limiting import limiter
from app.models import PlanRequest, Routine
from app.services.air_quality import fetch_air_quality
from app.services.llm import explain_with_fallback, parse_routine

router = APIRouter()


def default_routine(request: PlanRequest) -> Routine:
    """Build a safe form-only fallback routine if no text or routine is supplied."""
    from app.models import HomeSetup

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


@router.post("/api/plan")
@limiter.limit(RATE_LIMIT)
async def create_plan(request: Request, payload: PlanRequest) -> dict[str, Any]:
    """Fetch AQ, optionally parse text with Groq, run engine and return all UI data."""

    async def get_routine() -> Routine:
        if payload.routine_text.strip() and payload.routine is None:
            try:
                return await asyncio.wait_for(parse_routine(payload.routine_text), timeout=6.0)
            except Exception:
                return default_routine(payload)
        return payload.routine or default_routine(payload)

    air_task = fetch_air_quality(payload.latitude, payload.longitude)
    routine_task = get_routine()
    air, routine = await asyncio.gather(air_task, routine_task)

    engine = simulate_exposure(air["pm25"], air["aqi"], payload.members, routine)
    swaps = generate_swaps(air["pm25"], air["aqi"], payload.members, routine)
    engine["top_swap"] = swaps[0] if swaps else None
    engine["top_swaps"] = swaps
    engine["indoor_hacks"] = indoor_hacks()
    engine["sustainable_alternatives"] = sustainable_alternatives()

    try:
        explanation = await asyncio.wait_for(
            explain_with_fallback(engine, payload.language), timeout=12.0
        )
    except Exception:
        explanation = {
            "explanation": "AI explanation unavailable. Engine estimates are ready.",
            "ai_available": False,
        }

    pm25 = engine["hourly"]
    peak = max(pm25, key=lambda row: row["pm25"])
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
        "explanation": explanation,
        "estimate_label": "All values are estimates",
    }
