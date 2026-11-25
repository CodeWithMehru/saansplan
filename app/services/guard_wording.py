"""Wording guards, past-tense filters, and clock formatting for LLM explanations."""

import re

NOON = 12
MIDNIGHT = 0
EARLY_MORNING = 5
AFTERNOON = 17
EVENING = 20

PAST_TENSE_PATTERNS = [
    re.compile(r"\b(dropped|decreased|fell|lowered|slashed)\b", re.IGNORECASE),
    re.compile(r"\b(?:was\s+)?(?:reduced|cut)\s+(?:the\s+)?exposure\b", re.IGNORECASE),
    re.compile(
        r"\bexposure\s+(?:was\s+)?(?:reduced|dropped|decreased|cut|lowered)\b", re.IGNORECASE
    ),
    re.compile(r"\bwas\s+(?:reduced|lowered|cut|decreased)\b", re.IGNORECASE),
    re.compile(r"\b(?:reduced|lowered|cut)\s+(?:it\s+)?from\s+\d+", re.IGNORECASE),
    re.compile(
        r"\b(kam\s+hua|kam\s+hue|kam\s+hui|kam\s+ho\s+gaya|kam\s+ho\s+gaye|kam\s+ho\s+gayi)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(ghat\s+gaya|ghat\s+gaye|ghat\s+gayi|drop\s+hua|drop\s+ho\s+gaya)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bkam\s+kiya\b", re.IGNORECASE),
]


def _get_hinglish_period(hour_24: int) -> str:
    """Determine time period descriptor for Hinglish hour formatting."""
    if hour_24 < EARLY_MORNING or hour_24 >= EVENING:
        return "raat"
    if hour_24 < NOON:
        return "subah"
    if hour_24 < AFTERNOON:
        return "dopahar"
    return "shaam"


def format_hinglish_hour(hour_24: int) -> str:
    """Format hour for Hinglish text (e.g., 'shaam 6 baje', 'subah 8 baje')."""
    if hour_24 == MIDNIGHT:
        return "raat 12 baje"
    if hour_24 == NOON:
        return "dopahar 12 baje"
    period = _get_hinglish_period(hour_24)
    display_h = hour_24 if hour_24 <= NOON else hour_24 - NOON
    return f"{period} {display_h} baje"


def format_hour_12h(hour: int, language: str = "en") -> str:
    """Format hour (0-23) into 12-hour clock representation without raw hour 0."""
    h = hour % 24
    if language != "en":
        return format_hinglish_hour(h)
    if h == MIDNIGHT:
        return "12 am"
    if h == NOON:
        return "12 pm"
    if h < NOON:
        return f"{h} am"
    return f"{h - NOON} pm"


def has_past_tense(text: str) -> bool:
    """Check if text contains forbidden past-tense claims for hypothetical plans."""
    return any(p.search(text) for p in PAST_TENSE_PATTERNS)


def has_raw_units(text: str) -> bool:
    """Check if text references raw exposure units."""
    return bool(
        re.search(
            r"\b(?:exposure|total)\s+(?:before|after|was|is)?\s*\d{3,}\b", text, re.IGNORECASE
        )
    )


def has_raw_hour_zero(text: str) -> bool:
    """Check if text references raw hour 0 instead of 12-hour clock."""
    return bool(
        re.search(r"\b(?:peak\s+)?hour\s+0\b", text, re.IGNORECASE) or re.search(r"\b0:00\b", text)
    )
