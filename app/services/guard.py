"""LLM output number guard, hypothetical phrasing checks, and deterministic template fallback."""

import re
from typing import Any

_NUMBER = re.compile(r"(?<![A-Za-z])[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?![A-Za-z])")

NOON = 12
MIDNIGHT = 0
EARLY_MORNING = 5
AFTERNOON = 17
EVENING = 20
EXPECTED_RANGE_LEN = 2

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


def _format_hinglish_hour(h: int) -> str:
    if h == MIDNIGHT:
        return "raat 12 baje"
    if h == NOON:
        return "dopahar 12 baje"
    if h < EARLY_MORNING or h >= EVENING:
        period = "raat"
    elif h < NOON:
        period = "subah"
    elif h < AFTERNOON:
        period = "dopahar"
    else:
        period = "shaam"
    display_h = h if h <= NOON else h - NOON
    return f"{period} {display_h} baje"


def format_hour_12h(hour: int, language: str = "en") -> str:
    """Format hour (0-23) into 12-hour clock representation without raw hour 0."""
    h = hour % 24
    if language != "en":
        return _format_hinglish_hour(h)
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


def extract_numbers(text: str) -> set[float]:
    """Extract numeric values from assistant text."""
    text_without_clocks = re.sub(
        r"\b\d{1,2}:\d{2}\b",
        lambda match: match.group().split(":", 1)[0],
        text,
    )
    return {float(match) for match in _NUMBER.findall(text_without_clocks)}


def allowed_numbers(engine: dict[str, Any]) -> set[float]:
    """Build allowed summary facts and sensible rounded forms from UI units only."""
    values: set[float] = set()

    for key in ("peak_hour", "highest_aqi_hour"):
        val = engine.get(key)
        if isinstance(val, int | float):
            h = int(val) % 24
            h12 = NOON if h % NOON == 0 else h % NOON
            values.update({float(h), float(h12)})

    for key in ("peak_aqi", "highest_aqi"):
        val = engine.get(key)
        if isinstance(val, int | float):
            values.update({float(val), round(float(val)), round(float(val), 1)})

    cleaner = engine.get("cleaner_day") or {}
    top = engine.get("top_swap") or {}

    pct = cleaner.get("percent_reduction") or top.get("percent_reduction")
    if isinstance(pct, int | float):
        values.update({float(pct), round(float(pct)), round(float(pct), 1), float(int(pct))})

    saved_ug = cleaner.get("inhaled_saved_ug")
    if isinstance(saved_ug, int | float):
        values.update(
            {
                float(saved_ug),
                round(float(saved_ug)),
                round(float(saved_ug), 1),
                float(int(saved_ug)),
            }
        )

    saved_range = cleaner.get("inhaled_saved_range_ug")
    if isinstance(saved_range, list | tuple) and len(saved_range) == EXPECTED_RANGE_LEN:
        for r_val in saved_range:
            if isinstance(r_val, int | float):
                values.update(
                    {
                        float(r_val),
                        round(float(r_val)),
                        round(float(r_val), 1),
                        float(int(r_val)),
                    }
                )

    for h_key in ("from_hour", "to_hour"):
        h_val = top.get(h_key)
        if isinstance(h_val, int | float):
            h = int(h_val) % 24
            h12 = NOON if h % NOON == 0 else h % NOON
            values.update({float(h), float(h12)})

    return values


def rejected_numbers(text: str, engine: dict[str, Any]) -> set[float]:
    """Return numbers present in text but absent from the compact engine whitelist."""
    return extract_numbers(text) - allowed_numbers(engine)


def validate_number_guard(text: str, engine: dict[str, Any]) -> bool:
    """Reject text containing forbidden past tense, raw units, hour 0, or foreign numbers."""
    if has_past_tense(text):
        return False
    if has_raw_units(text):
        return False
    if has_raw_hour_zero(text):
        return False
    extracted = extract_numbers(text)
    return extracted.issubset(allowed_numbers(engine))


def templated_explanation(engine: dict[str, Any], language: str = "hinglish") -> str:
    """Return a safe deterministic hypothetical explanation using 12h clock and UI units."""
    peak_hour = int(engine.get("peak_hour", 18))
    peak_aqi = int(engine.get("peak_aqi", 200))
    cleaner = engine.get("cleaner_day") or {}
    top = engine.get("top_swap") or {}

    time_str = format_hour_12h(peak_hour, language)
    pct = cleaner.get("percent_reduction") or top.get("percent_reduction", 25.0)
    saved_ug = cleaner.get("inhaled_saved_ug")
    saved_range = cleaner.get("inhaled_saved_range_ug")

    if language == "en":
        dose_str = ""
        if saved_ug is not None and saved_range:
            dose_str = (
                f" and save approximately {saved_ug} µg inhaled PM2.5 "
                f"(estimate range {saved_range[0]} to {saved_range[1]} µg)"
            )
        return (
            f"Peak pollution is expected around {time_str} with AQI {peak_aqi}. "
            f"Following the routine adjustments could reduce about {pct}% (estimate) of exposure"
            f"{dose_str}. These are hypothetical estimates, not medical advice. "
            "Consult a doctor for symptoms or at-risk members."
        )

    # Hinglish / Hindi
    dose_str_hi = ""
    if saved_ug is not None and saved_range:
        dose_str_hi = (
            f", jisse lagbhag {saved_ug} µg PM2.5 bach sakti hai "
            f"(range {saved_range[0]} se {saved_range[1]} µg)"
        )
    return (
        f"Pradushan sabse zyada {time_str} ke dauran AQI {peak_aqi} tak ho sakta hai. "
        f"Routine badalne se lagbhag {pct}% tak exposure kam ho sakta hai (anumaan){dose_str_hi}. "
        "Ye anumaan hai, doctor ki salah nahi."
    )
