"""Assistant service for grounded Q&A, knowledge base retrieval, and engine facts."""

import asyncio
import json
import logging
from typing import Any

from app.core.constants import DEFAULT_FORECAST_DAYS, HOURS_IN_DAY
from app.services.air_quality import fetch_air_quality
from app.services.assistant_resolvers import (
    _ensure_cpcb_breakpoint_entry as _ensure_cpcb_bp_res,
)
from app.services.assistant_resolvers import (
    _is_valid_hour,
    build_deterministic_fallback,
    check_safety,
    extract_hour,
    extract_room_size_sqft,
)
from app.services.assistant_resolvers import (
    resolve_cadr as _resolve_cadr_resolver,
)
from app.services.assistant_resolvers import (
    resolve_walk as _resolve_walk_resolver,
)
from app.services.kb import KnowledgeBase
from app.services.llm import groq_chat

logger = logging.getLogger(__name__)

DEFAULT_LATITUDE = 28.6139
DEFAULT_LONGITUDE = 77.2090
DEFAULT_CITY = "Delhi"

_kb_instance = KnowledgeBase()


def get_kb() -> KnowledgeBase:
    """Return the global KnowledgeBase singleton."""
    return _kb_instance


def _ensure_cpcb_breakpoint_entry(entries: list[dict[str, Any]]) -> None:
    """Attach CPCB breakpoint reference to KB context if absent."""
    _ensure_cpcb_bp_res(entries, kb=_kb_instance)


def resolve_cadr(
    room_sqft: float | None, entries: list[dict[str, Any]]
) -> tuple[dict[str, Any] | None, int | None]:
    """Calculate deterministic CADR with global KB instance."""
    return _resolve_cadr_resolver(room_sqft, entries, kb=_kb_instance)


def resolve_walk(
    asked_hour: int | None,
    today_pm25: list[float],
    entries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Evaluate outdoor conditions with global KB instance."""
    return _resolve_walk_resolver(asked_hour, today_pm25, entries, kb=_kb_instance)


async def _fetch_today_pm25(lat: float, lon: float, client: Any, fetch_aq: Any) -> list[float]:
    """Fetch 24-hour PM2.5 forecast slice safely."""
    try:
        air = await fetch_aq(lat, lon, forecast_days=DEFAULT_FORECAST_DAYS, client=client)
        pm25 = air.get("pm25")
        if isinstance(pm25, list):
            return [float(v) for v in pm25[:HOURS_IN_DAY] if v is not None]
        return []
    except Exception:  # noqa: BLE001  # Safe air quality slice fallback
        return []


async def _call_groq_assistant(
    question: str,
    engine_facts: dict[str, Any],
    entries: list[dict[str, Any]],
    chat: Any,
) -> dict[str, Any] | None:
    """Send structured facts to Groq and parse response."""
    system = (
        "You are SaansPlan's grounded air-quality assistant. Answer using ONLY "
        "provided verified knowledge-base entries and deterministic engine facts. "
        "Cite relevant KB entry ids in brackets like [purifier-sizing] or [cpcb-aqi-breakpoints]. "
        "If purifier CADR is requested, explicitly cite the AHAM 2/3 guideline calculation. "
        "Respond in the exact language of the question (English, Hinglish, or Hindi). "
        "Keep the answer to 2-3 concise sentences. Never make up numbers. "
        'Return JSON: {"answer": "...", "kb_ids": ["..."]}.'
    )
    user_payload = json.dumps(
        {
            "question": question,
            "deterministic_engine_facts": engine_facts,
            "grounded_kb_entries": [{"id": e["id"], "text": e["text"]} for e in entries],
        },
        ensure_ascii=False,
    )
    try:
        raw = await asyncio.wait_for(chat(system, user_payload, 0.2), timeout=8.0)
        parsed = json.loads(raw)
        ans_text = parsed.get("answer", "").strip()
        cited_ids = parsed.get("kb_ids") or [e["id"] for e in entries]
        if ans_text:
            return {"answer": ans_text, "kb_ids": cited_ids, "safety_redirect": False}
    except Exception as err:  # noqa: BLE001  # Safe assistant generation fallback
        logger.warning("Groq ask generation fallback: %s", err)
    return None


def _build_engine_facts(
    city: str,
    cadr_info: dict[str, Any] | None,
    walk_info: dict[str, Any] | None,
) -> dict[str, Any]:
    """Assemble location and domain calculation facts for prompt injection."""
    facts: dict[str, Any] = {"city": city}
    if cadr_info:
        facts["purifier_sizing"] = cadr_info
    if walk_info:
        facts["requested_hour_conditions"] = walk_info
    return facts


async def _assemble_assistant_context(
    q_clean: str,
    location: tuple[float | None, float | None, str | None],
    client: Any,
    fetch_aq: Any,
    entries: list[dict[str, Any]],
) -> tuple[dict[str, Any], float | None, int | None, int | None, dict[str, Any] | None, str]:
    """Assemble atmospheric context, CADR sizing, and walk conditions."""
    req_lat, req_lon, req_city = location
    lat = req_lat or DEFAULT_LATITUDE
    lon = req_lon or DEFAULT_LONGITUDE
    loc_city = req_city or DEFAULT_CITY

    today_pm25 = await _fetch_today_pm25(lat, lon, client, fetch_aq)
    room_sqft = extract_room_size_sqft(q_clean)
    cadr_info, cadr_cfm = resolve_cadr(room_sqft, entries)

    asked_hour = extract_hour(q_clean)
    walk_info = resolve_walk(asked_hour, today_pm25, entries)
    engine_facts = _build_engine_facts(loc_city, cadr_info, walk_info)
    return engine_facts, room_sqft, cadr_cfm, asked_hour, walk_info, loc_city


async def answer_question(
    question: str,
    location: tuple[float | None, float | None, str | None] = (None, None, None),
    client: Any = None,
    chat_fn: Any = None,
    fetch_aq_fn: Any = None,
) -> dict[str, Any]:
    """Provide grounded answer to an air-quality question."""
    chat = chat_fn or groq_chat
    fetch_aq = fetch_aq_fn or fetch_air_quality

    q_clean = question.strip()
    if not q_clean:
        return {
            "answer": "Please ask an air-quality question.",
            "kb_ids": [],
            "safety_redirect": False,
        }

    safety_response = check_safety(q_clean.lower())
    if safety_response:
        return safety_response

    entries = _kb_instance.retrieve(q_clean, limit=2, threshold=3)
    facts, room_sqft, cadr_cfm, asked_h, walk_info, loc_city = await _assemble_assistant_context(
        q_clean, location, client, fetch_aq, entries
    )

    llm_res = await _call_groq_assistant(q_clean, facts, entries, chat)
    if llm_res:
        return llm_res

    return build_deterministic_fallback(
        (room_sqft, cadr_cfm), (asked_h, walk_info, loc_city), entries
    )


__all__ = [
    "_ensure_cpcb_breakpoint_entry",
    "_is_valid_hour",
    "answer_question",
    "build_deterministic_fallback",
    "check_safety",
    "extract_hour",
    "extract_room_size_sqft",
    "get_kb",
    "resolve_cadr",
    "resolve_walk",
]
