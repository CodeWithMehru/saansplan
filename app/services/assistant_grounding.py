"""Deterministic resolvers and fallback generators for assistant Q&A."""

import re
from typing import Any

from app.core.aqi import indian_aqi_category
from app.engine.indoor_module import SQFT_PER_SQM, calculate_purifier_cadr
from app.services.kb import KnowledgeBase

NOON_HOUR = 12
MIDNIGHT_HOUR = 0
POOR_AQI_THRESHOLD = 120

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
INJECTION_TERMS = (
    "api key",
    "system prompt",
    "ignore instructions",
    "reveal secrets",
    "override instructions",
    "bypass guardrails",
    "developer mode",
    "disregard previous",
    "leak secrets",
    "dump config",
    "environment variables",
)


def extract_room_size_sqft(text: str) -> float | None:
    """Extract room area from query in square feet or square meters."""
    bounded = text[:1000]
    m_sqft = re.search(
        r"\b(\d+(?:\.\d+)?)\s*(?:sq\.?\s*ft|sqft|square\s*feet|square\s*foot)\b",
        bounded,
        re.IGNORECASE,
    )
    if m_sqft:
        return float(m_sqft.group(1))
    m_sqm = re.search(
        r"\b(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|square\s*meters|m2|m²)\b",
        bounded,
        re.IGNORECASE,
    )
    if m_sqm:
        return float(m_sqm.group(1)) * SQFT_PER_SQM
    return None


def _convert_12h_to_24h(hour: int, meridiem: str) -> int:
    """Convert 12-hour AM/PM hour to 24-hour clock."""
    if meridiem == "pm":
        return hour + NOON_HOUR if hour != NOON_HOUR else NOON_HOUR
    return MIDNIGHT_HOUR if hour == NOON_HOUR else hour


def _extract_12h_hour(text: str) -> int | None:
    """Parse 12-hour AM/PM format into 24-hour integer."""
    m_12h = re.search(r"\b(\d{1,2})\s*(am|pm)\b", text, re.IGNORECASE)
    if not m_12h:
        return None
    return _convert_12h_to_24h(int(m_12h.group(1)), m_12h.group(2).lower())


def _adjust_hindi_period_hour(hour: int, period: str) -> int:
    """Offset evening hours into 24-hour PM timeframe."""
    if period in ("shaam", "raat") and hour < NOON_HOUR:
        return hour + NOON_HOUR
    return hour


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
    return _adjust_hindi_period_hour(int(m_hi.group(2)), period)


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


def _find_kb_entry(kb: KnowledgeBase | None, entry_id: str) -> dict[str, Any] | None:
    """Look up an entry by ID from the knowledge base."""
    if not kb:
        return None
    for entry in kb.entries:
        if entry["id"] == entry_id:
            return entry
    return None


def _has_entry_id(entries: list[dict[str, Any]], entry_id: str) -> bool:
    """Check if an entry with the designated ID exists in the list."""
    return any(entry["id"] == entry_id for entry in entries)


def _attach_cadr_kb_entry(entries: list[dict[str, Any]], kb: KnowledgeBase | None) -> None:
    """Prepend purifier sizing documentation to retrieved entries."""
    if not _has_entry_id(entries, "purifier-sizing"):
        entry = _find_kb_entry(kb, "purifier-sizing")
        if entry is not None:
            entries.insert(0, entry)


def resolve_cadr(
    room_sqft: float | None, entries: list[dict[str, Any]], kb: KnowledgeBase | None = None
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
    _attach_cadr_kb_entry(entries, kb)
    return info, cadr_cfm


def _is_valid_hour(hour: int | None, total_hours: int) -> bool:
    """Check if asked hour is within the available forecast window."""
    return hour is not None and 0 <= hour < total_hours


def _ensure_cpcb_breakpoint_entry(
    entries: list[dict[str, Any]], kb: KnowledgeBase | None = None
) -> None:
    """Attach CPCB breakpoint reference to KB context if absent."""
    if not _has_entry_id(entries, "cpcb-aqi-breakpoints"):
        entry = _find_kb_entry(kb, "cpcb-aqi-breakpoints")
        if entry is not None:
            entries.append(entry)


def resolve_walk(
    asked_hour: int | None,
    today_pm25: list[float],
    entries: list[dict[str, Any]],
    kb: KnowledgeBase | None = None,
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
    _ensure_cpcb_breakpoint_entry(entries, kb)
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


def _fallback_walk(asked_hour: int, walk_info: dict[str, Any] | None, city: str) -> dict[str, Any]:
    """Return deterministic fallback for walk / outdoor safety queries."""
    h12 = (
        f"{asked_hour - NOON_HOUR} pm"
        if asked_hour > NOON_HOUR
        else (f"{asked_hour} am" if asked_hour > MIDNIGHT_HOUR else "12 am")
    )
    if walk_info:
        cond = (
            f"forecast PM2.5 is {walk_info['pm25']} µg/m³ with "
            f"AQI {walk_info['aqi']} ({walk_info['category']})"
        )
    else:
        cond = "check local AQI levels before heading out"
    return {
        "answer": (
            f"At {h12} in {city}, {cond}. Strenuous outdoor walking "
            "during peak smog is not advised; consider indoor exercise [cpcb-aqi-breakpoints]."
        ),
        "kb_ids": ["cpcb-aqi-breakpoints"],
        "safety_redirect": False,
    }


def _try_fallback_cadr(room_sqft: float | None, cadr_cfm: int | None) -> dict[str, Any] | None:
    """Build CADR fallback if both square footage and CADR are available."""
    if room_sqft is not None and cadr_cfm is not None:
        return _fallback_cadr(room_sqft, cadr_cfm)
    return None


def _try_fallback_walk(
    asked_hour: int | None, walk_info: dict[str, Any] | None, city: str
) -> dict[str, Any] | None:
    """Build walk advisory fallback if hour is available."""
    if asked_hour is not None:
        return _fallback_walk(asked_hour, walk_info, city)
    return None


def _fallback_generic_or_entry(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Return top retrieved entry or general CPCB advisory fallback."""
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


def build_deterministic_fallback(
    cadr_data: tuple[float | None, int | None],
    walk_data: tuple[int | None, dict[str, Any] | None, str],
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return verified deterministic fallback answer when model call fails."""
    cadr_fb = _try_fallback_cadr(cadr_data[0], cadr_data[1])
    if cadr_fb:
        return cadr_fb
    walk_fb = _try_fallback_walk(walk_data[0], walk_data[1], walk_data[2])
    if walk_fb:
        return walk_fb
    return _fallback_generic_or_entry(entries)
