"""Assistant service for grounded Q&A, knowledge base retrieval, and engine facts."""

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable, Sequence

import httpx

from app.core.constants import DEFAULT_FORECAST_DAYS, HOURS_IN_DAY
from app.engine.assistant_models import AirQualityData
from app.services.air_quality import fetch_air_quality
from app.services.assistant_grounding import (
    AssistantResult,
    CadrInfo,
    SafetyResult,
    WalkInfo,
    _is_valid_hour,
    build_deterministic_fallback,
    check_safety,
    extract_hour,
    extract_room_size_sqft,
)
from app.services.assistant_grounding import (
    _ensure_cpcb_breakpoint_entry as _ensure_cpcb_bp_res,
)
from app.services.assistant_grounding import (
    resolve_cadr as _resolve_cadr_resolver,
)
from app.services.assistant_grounding import (
    resolve_walk as _resolve_walk_resolver,
)
from app.services.kb import KBEntry, KnowledgeBase
from app.services.llm import groq_chat

ChatFn = Callable[[str, str, float], Awaitable[str]]
FetchAirQualityFn = Callable[
    [float, float, int, httpx.AsyncClient | None],
    Awaitable[AirQualityData],
]

logger = logging.getLogger(__name__)

DEFAULT_LATITUDE = 28.6139
DEFAULT_LONGITUDE = 77.2090
DEFAULT_CITY = "Delhi"

_kb_instance = KnowledgeBase()


def get_kb() -> KnowledgeBase:
    """Return the global KnowledgeBase singleton."""
    return _kb_instance


def _ensure_cpcb_breakpoint_entry(entries: list[KBEntry]) -> None:
    """Attach CPCB breakpoint reference to KB context if absent."""
    _ensure_cpcb_bp_res(entries, kb=_kb_instance)


def resolve_cadr(
    room_sqft: float | None, entries: list[KBEntry]
) -> tuple[CadrInfo | None, int | None]:
    """Calculate deterministic CADR with global KB instance."""
    return _resolve_cadr_resolver(room_sqft, entries, kb=_kb_instance)


def resolve_walk(
    asked_hour: int | None, today_pm25: list[float], entries: list[KBEntry]
) -> WalkInfo | None:
    """Evaluate outdoor conditions with global KB instance."""
    return _resolve_walk_resolver(asked_hour, today_pm25, entries, kb=_kb_instance)


async def _fetch_today_pm25(
    lat: float,
    lon: float,
    client: httpx.AsyncClient | None,
    fetch_aq: FetchAirQualityFn | None,
) -> list[float]:
    """Fetch 24-hour PM2.5 forecast slice safely."""
    try:
        fetch = fetch_aq or fetch_air_quality
        air = await fetch(lat, lon, DEFAULT_FORECAST_DAYS, client)
        pm25 = air.get("pm25") if hasattr(air, "get") else getattr(air, "pm25", None)
        if isinstance(pm25, Sequence):
            return [float(v) for v in pm25[:HOURS_IN_DAY] if isinstance(v, int | float)]
        return []
    except (
        httpx.HTTPError,
        TimeoutError,
        RuntimeError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        json.JSONDecodeError,
    ):
        return []


def _format_assistant_payload(
    question: str, engine_facts: dict[str, object], entries: list[KBEntry]
) -> str:
    """Format user prompt payload with grounding facts and retrieved entries."""
    return json.dumps(
        {
            "question": question,
            "deterministic_engine_facts": engine_facts,
            "grounded_kb_entries": [{"id": e["id"], "text": e["text"]} for e in entries],
        },
        ensure_ascii=False,
    )


def _parse_assistant_response(raw: str, entries: list[KBEntry]) -> AssistantResult | None:
    """Parse raw LLM JSON response and extract answer and citation ids."""
    try:
        parsed = json.loads(raw)
        ans_text = parsed.get("answer", "").strip()
        cited_ids = parsed.get("kb_ids") or [e["id"] for e in entries]
        if ans_text:
            return {"answer": ans_text, "kb_ids": cited_ids, "safety_redirect": False}
    except json.JSONDecodeError:
        pass
    return None


async def _call_groq_assistant(
    question: str,
    engine_facts: dict[str, object],
    entries: list[KBEntry],
    chat: ChatFn | None = None,
) -> AssistantResult | None:
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
    user_payload = _format_assistant_payload(question, engine_facts, entries)
    chat_call = chat or groq_chat
    try:
        raw = await asyncio.wait_for(chat_call(system, user_payload, 0.2), timeout=8.0)
        return _parse_assistant_response(raw, entries)
    except (
        httpx.HTTPError,
        TimeoutError,
        RuntimeError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ) as err:
        logger.warning("Groq ask generation fallback: %s", err)
    return None


def _build_engine_facts(
    city: str, cadr_info: CadrInfo | None, walk_info: WalkInfo | None
) -> dict[str, object]:
    """Assemble location and domain calculation facts for prompt injection."""
    facts: dict[str, object] = {"city": city}
    if cadr_info:
        facts["purifier_sizing"] = cadr_info
    if walk_info:
        facts["requested_hour_conditions"] = walk_info
    return facts


async def _assemble_assistant_context(
    q_clean: str,
    location: tuple[float | None, float | None, str | None],
    client: httpx.AsyncClient | None,
    fetch_aq: FetchAirQualityFn | None,
    entries: list[KBEntry],
) -> tuple[dict[str, object], float | None, int | None, int | None, WalkInfo | None, str]:
    """Assemble atmospheric context, CADR sizing, and walk conditions."""
    lat = location[0] or DEFAULT_LATITUDE
    lon = location[1] or DEFAULT_LONGITUDE
    loc_city = location[2] or DEFAULT_CITY

    today_pm25 = await _fetch_today_pm25(lat, lon, client, fetch_aq)
    room_sqft = extract_room_size_sqft(q_clean)
    cadr_info, cadr_cfm = resolve_cadr(room_sqft, entries)

    asked_hour = extract_hour(q_clean)
    walk_info = resolve_walk(asked_hour, today_pm25, entries)
    engine_facts = _build_engine_facts(loc_city, cadr_info, walk_info)
    return engine_facts, room_sqft, cadr_cfm, asked_hour, walk_info, loc_city


def _preliminary_check(question: str) -> AssistantResult | None:
    """Perform early exit validation for empty questions or clinical symptoms."""
    q_clean = question.strip()
    if not q_clean:
        return {
            "answer": "Please ask an air-quality question.",
            "kb_ids": [],
            "safety_redirect": False,
        }
    return check_safety(q_clean.lower())


async def answer_question(
    question: str,
    location: tuple[float | None, float | None, str | None] = (None, None, None),
    client: httpx.AsyncClient | None = None,
    chat_fn: ChatFn | None = None,
    fetch_aq_fn: FetchAirQualityFn | None = None,
) -> AssistantResult:
    """Provide grounded answer to an air-quality question."""
    prelim = _preliminary_check(question)
    if prelim:
        return prelim

    q_clean = question.strip()
    chat = chat_fn or groq_chat
    fetch_aq = fetch_aq_fn or fetch_air_quality

    entries = _kb_instance.retrieve(q_clean, limit=2, threshold=3)
    ctx = await _assemble_assistant_context(q_clean, location, client, fetch_aq, entries)
    facts, room_sqft, cadr_cfm, asked_h, walk_info, loc_city = ctx
    llm_res = await _call_groq_assistant(q_clean, facts, entries, chat)
    if llm_res:
        return llm_res

    return build_deterministic_fallback(
        (room_sqft, cadr_cfm), (asked_h, walk_info, loc_city), entries
    )


__all__ = [
    "AssistantResult",
    "SafetyResult",
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
