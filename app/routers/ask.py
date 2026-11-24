"""Grounded ask-SaansPlan route with server-side engine facts and LLM answers."""

from typing import Any

from fastapi import APIRouter, Request

from app.limiting import limiter
from app.models import AskRequest
from app.services.air_quality import fetch_air_quality
from app.services.assistant import (
    answer_question,
    build_deterministic_fallback,
    check_safety,
    extract_hour,
    extract_room_size_sqft,
    get_kb,
    resolve_cadr,
    resolve_walk,
)
from app.services.llm import groq_chat

router = APIRouter()
kb = get_kb()

# Backward compatibility aliases for existing tests
_check_safety = check_safety
_resolve_cadr = resolve_cadr
_resolve_walk = resolve_walk
_build_deterministic_fallback = build_deterministic_fallback

__all__ = [
    "_build_deterministic_fallback",
    "_check_safety",
    "_resolve_cadr",
    "_resolve_walk",
    "ask",
    "extract_hour",
    "extract_room_size_sqft",
    "fetch_air_quality",
    "groq_chat",
    "kb",
    "router",
]


@router.post("/api/ask")
@limiter.limit("15/minute")
async def ask(request: Request, payload: AskRequest) -> dict[str, Any]:
    """Provide grounded answers using server-side engine facts, KB entries, and Groq."""
    client = getattr(request.app.state, "http_client", None)
    return await answer_question(
        question=payload.question,
        location=(payload.latitude, payload.longitude, payload.city),
        client=client,
        chat_fn=groq_chat,
        fetch_aq_fn=fetch_air_quality,
    )
