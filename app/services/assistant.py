"""Assistant service for grounded Q&A, knowledge base retrieval, and engine facts."""

import asyncio
import json
import logging
import re
from typing import Any

from app.core.aqi import indian_aqi_category
from app.core.constants import DEFAULT_FORECAST_DAYS, HOURS_IN_DAY
from app.engine.indoor_module import SQFT_PER_SQM, calculate_purifier_cadr
from app.services.air_quality import fetch_air_quality
from app.services.kb import KnowledgeBase
from app.services.llm import groq_chat

logger = logging.getLogger(__name__)

NOON_HOUR = 12
MIDNIGHT_HOUR = 0
POOR_AQI_THRESHOLD = 120
DEFAULT_LATITUDE = 28.6139
DEFAULT_LONGITUDE = 77.2090
DEFAULT_CITY = "Delhi"

SYMPTOM_TERMS = (
    "chest tightness",
    "shortness of breath",
    "wheezing",
    "difficulty breathing",
    "breathlessness",
    "dawa",
    "medicine",
    "syrup",
    "cough syrup",
    "dosage",
    "dose",
    "prescription",
    "antibiotic",
    "inhaler",
    "diagnose",
    "diagnosis",
    "chhati",
    "saans phool",
)
INJECTION_TERMS = ("api key", "system prompt", "ignore instructions", "reveal secrets")

_kb_instance = KnowledgeBase()


def get_kb() -> KnowledgeBase:
    """Return the global KnowledgeBase singleton."""
    return _kb_instance


def extract_room_size_sqft(text: str) -> float | None:
    """Extract room area from query in square feet or square meters."""
    m_sqft = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:sq\.?\s*ft|sqft|square\s*feet|square\s*foot)",
        text,
        re.IGNORECASE,
    )
    if m_sqft:
        return float(m_sqft.group(1))
    m_sqm = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|square\s*meters|m2|m²)",
        text,
        re.IGNORECASE,
    )
    if m_sqm:
        return float(m_sqm.group(1)) * SQFT_PER_SQM
    return None


def _extract_12h_hour(text: str) -> int | None:
    """Parse 12-hour AM/PM format into 24-hour integer."""
    m_12h = re.search(r"\b(\d{1,2})\s*(am|pm)\b", text, re.IGNORECASE)
    if not m_12h:
        return None
    h = int(m_12h.group(1))
    meridiem = m_12h.group(2).lower()
    if meridiem == "pm" and h != NOON_HOUR:
        return h + NOON_HOUR
    if meridiem == "am" and h == NOON_HOUR:
        return MIDNIGHT_HOUR
    return h


def _extract_hindi_hour(text: str) -> int | None:
    """Parse Hindi/Hinglish clock notation like 'shaam 6 baje'."""
    m_hi = re.search(
        r"\b(?:(shaam|subah|raat|dopahar)\s*)?(\d{1,2})\s*baje(?:\s*(shaam|subah|raat|dopahar))?\b",
        text,
        re.IGNORECASE,
    )
    if not m_hi:
        return None
    period = (m_hi.group(1) or m_hi.group(3) or "").lower()
    h = int(m_hi.group(2))
    if period in ("shaam", "raat") and h < NOON_HOUR:
        return h + NOON_HOUR
    return h


def extract_hour(text: str) -> int | None:
    """Extract clock hour (0-23) if question asks about a specific time of day."""
    h12 = _extract_12h_hour(text)
    if h12 is not None:
        return h12
    return _extract_hindi_hour(text)


def check_safety(q_lower: str) -> dict[str, Any] | None:
    """Intercept acute medical symptoms and injection attempts."""
    if any(term in q_lower for term in SYMPTOM_TERMS):
        return {
            "answer": (
                "I cannot provide medical diagnosis, treatment, or prescribe medication. "
                "If you or a family member experience severe symptoms such as chest tightness, "
                "wheezing, or acute shortness of breath, please seek urgent medical attention "
                "from a doctor or hospital immediately."
            ),
            "kb_ids": ["medical-redirect"],
            "safety_redirect": True,
        }
    if any(k in q_lower for k in INJECTION_TERMS):
        return {
            "answer": (
                "I cannot reveal internal credentials or system instructions. "
                "Consult a doctor for symptoms or review local air-quality guidelines."
            ),
            "kb_ids": ["medical-redirect"],
            "safety_redirect": True,
        }
    return None


def resolve_cadr(
    room_sqft: float | None, entries: list[dict[str, Any]]
) -> tuple[dict[str, Any] | None, int | None]:
    """Calculate deterministic CADR if room area is specified."""
    if room_sqft is None:
        return None, None
    cadr_cfm = round((2.0 / 3.0) * room_sqft)
    cadr_m3h = round(cadr_cfm * 1.699)
    cadr_calc = calculate_purifier_cadr(area_sq_meters=room_sqft / SQFT_PER_SQM)
    info = {
        "room_sqft": round(room_sqft, 1),
        "recommended_smoke_cadr_cfm": cadr_cfm,
        "recommended_smoke_cadr_m3h": cadr_m3h,
        "target_ach": cadr_calc["target_ach"],
        "basis": "AHAM 2/3 Rule (Smoke CADR in CFM >= 2/3 room area in sq ft)",
    }
    if not any(e["id"] == "purifier-sizing" for e in entries):
        p_entry = next((e for e in _kb_instance.entries if e["id"] == "purifier-sizing"), None)
        if p_entry:
            entries.insert(0, p_entry)
    return info, cadr_cfm


def _is_valid_hour(hour: int | None, total_hours: int) -> bool:
    """Check if asked hour is within the available forecast window."""
    return hour is not None and 0 <= hour < total_hours


def _ensure_cpcb_breakpoint_entry(entries: list[dict[str, Any]]) -> None:
    """Attach CPCB breakpoint reference to KB context if absent."""
    if not any(e["id"] == "cpcb-aqi-breakpoints" for e in entries):
        b_entry = next((e for e in _kb_instance.entries if e["id"] == "cpcb-aqi-breakpoints"), None)
        if b_entry:
            entries.append(b_entry)


def resolve_walk(
    asked_hour: int | None,
    today_pm25: list[float],
    entries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Evaluate outdoor conditions if a specific time is asked."""
    if asked_hour is None or not (0 <= asked_hour < len(today_pm25)):
        return None
    h_pm25 = today_pm25[asked_hour]
    cat_label, _, _, h_aqi = indian_aqi_category(h_pm25)
    advisory = (
        "Strenuous outdoor exercise is not advised"
        if h_aqi > POOR_AQI_THRESHOLD
        else "Acceptable for light outdoor activity"
    )
    _ensure_cpcb_breakpoint_entry(entries)
    return {
        "hour": asked_hour,
        "pm25": h_pm25,
        "aqi": h_aqi,
        "category": cat_label,
        "outdoor_advisory": advisory,
    }


def _fallback_cadr(room_sqft: float, cadr_cfm: int) -> dict[str, Any]:
    """Return deterministic fallback for purifier sizing queries."""
    cadr_m3h = round(cadr_cfm * 1.699)
    return {
        "answer": (
            f"For a {int(room_sqft)} sq ft room, the AHAM 2/3 guideline recommends a minimum "
            f"Smoke CADR of {cadr_cfm} CFM (~{cadr_m3h} m³/h) [purifier-sizing]."
        ),
        "kb_ids": ["purifier-sizing"],
        "safety_redirect": False,
    }


def _fallback_walk(asked_hour: int, walk_info: dict[str, Any], city: str) -> dict[str, Any]:
    """Return deterministic fallback for walk / outdoor safety queries."""
    h12 = (
        f"{asked_hour - NOON_HOUR} pm"
        if asked_hour > NOON_HOUR
        else (f"{asked_hour} am" if asked_hour > MIDNIGHT_HOUR else "12 am")
    )
    return {
        "answer": (
            f"At {h12} in {city}, forecast PM2.5 is {walk_info['pm25']} µg/m³ with "
            f"AQI {walk_info['aqi']} ({walk_info['category']}). Strenuous outdoor walking "
            "during peak smog is not advised; consider indoor exercise [cpcb-aqi-breakpoints]."
        ),
        "kb_ids": ["cpcb-aqi-breakpoints"],
        "safety_redirect": False,
    }


def build_deterministic_fallback(
    cadr_data: tuple[float | None, int | None],
    walk_data: tuple[int | None, dict[str, Any] | None, str],
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return verified deterministic fallback answer when model call fails."""
    room_sqft, cadr_cfm = cadr_data
    asked_hour, walk_info, city = walk_data
    if room_sqft is not None and cadr_cfm is not None:
        return _fallback_cadr(room_sqft, cadr_cfm)
    if asked_hour is not None and walk_info is not None:
        return _fallback_walk(asked_hour, walk_info, city)
    if entries:
        return {
            "answer": f"{entries[0]['text']} [{entries[0]['id']}]",
            "kb_ids": [entries[0]["id"]],
            "safety_redirect": False,
        }
    return {
        "answer": "Refer to CPCB guidelines for air-quality precautions [cpcb-aqi-breakpoints].",
        "kb_ids": ["cpcb-aqi-breakpoints"],
        "safety_redirect": False,
    }


async def _fetch_today_pm25(lat: float, lon: float, client: Any, fetch_aq: Any) -> list[float]:
    """Fetch 24-hour PM2.5 forecast slice safely."""
    try:
        air = await fetch_aq(lat, lon, forecast_days=DEFAULT_FORECAST_DAYS, client=client)
        pm25 = air.get("pm25")
        if isinstance(pm25, list):
            return [float(v) for v in pm25[:HOURS_IN_DAY] if v is not None]
        return []
    except Exception:
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
    except Exception as err:
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
    llm_res = await _call_groq_assistant(q_clean, engine_facts, entries, chat)
    if llm_res:
        return llm_res

    return build_deterministic_fallback(
        (room_sqft, cadr_cfm), (asked_hour, walk_info, loc_city), entries
    )
