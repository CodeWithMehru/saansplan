"""Family air-quality plan API with forecast, cleaner day, emissions, and indoor modules."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.config import RATE_LIMIT
from app.core.settings import Settings, get_settings
from app.limiting import limiter
from app.models import PlanRequest, Routine
from app.services import plan_service
from app.services.air_quality import fetch_air_quality
from app.services.llm import explain_with_fallback, parse_routine
from app.services.plan_service import default_routine

router = APIRouter()


async def _resolve_routine(payload: PlanRequest) -> Routine:
    """Resolve routine using configured or monkeypatched parser."""
    return await plan_service.resolve_routine(payload, parse_routine_fn=parse_routine)


async def _generate_explanation(engine: Any, language: str) -> dict[str, Any]:
    """Generate explanation using configured or monkeypatched explainer."""
    return await plan_service.generate_explanation(
        engine, language, explain_fn=explain_with_fallback
    )


_extract_primary_commute = plan_service.extract_primary_commute
_execute_plan_pipeline = plan_service.execute_plan_pipeline

__all__ = [
    "_execute_plan_pipeline",
    "_extract_primary_commute",
    "_generate_explanation",
    "_resolve_routine",
    "create_plan",
    "default_routine",
    "explain_with_fallback",
    "fetch_air_quality",
    "parse_routine",
    "router",
]


@router.post("/api/plan")
@limiter.limit(RATE_LIMIT)
async def create_plan(
    request: Request,
    payload: PlanRequest,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Fetch AQ, parse routine, run physical engines, and return full suite of recommendations."""
    client = getattr(request.app.state, "http_client", None)
    return await plan_service.execute_plan_pipeline(
        payload,
        client,
        fetch_aq_fn=fetch_air_quality,
        parse_routine_fn=parse_routine,
        explain_fn=explain_with_fallback,
    )
