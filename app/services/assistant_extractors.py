"""Query extraction, regex time/area parsers, and safety interceptors for assistant Q&A."""

from __future__ import annotations

import re
from typing import TypedDict

from app.engine.indoor_guidance import SQFT_PER_SQM


class AssistantResult(TypedDict):
    """Normalized assistant response structure."""

    answer: str
    kb_ids: list[str]
    safety_redirect: bool


SafetyResult = AssistantResult

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


def check_safety(q_lower: str) -> SafetyResult | None:
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
