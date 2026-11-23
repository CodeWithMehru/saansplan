"""LLM output number guard and deterministic template fallback."""

import re
from typing import Any

_NUMBER = re.compile(r"(?<![A-Za-z])[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?![A-Za-z])")


def extract_numbers(text: str) -> set[float]:
    """Extract numeric values from assistant text."""
    text_without_clocks = re.sub(
        r"\b\d{1,2}:\d{2}\b",
        lambda match: match.group().split(":", 1)[0],
        text,
    )
    return {float(match) for match in _NUMBER.findall(text_without_clocks)}


def allowed_numbers(engine: dict[str, Any]) -> set[float]:
    """Build allowed summary facts and sensible rounded forms."""
    values: set[float] = set()
    swap = engine.get("top_swap")
    if swap:
        for key in (
            "total_before",
            "total_after",
            "exposure_before",
            "exposure_after",
            "percent_reduction",
            "from_hour",
            "to_hour",
        ):
            value = swap.get(key)
            if isinstance(value, int | float):
                values.update({float(value), round(float(value)), round(float(value), 1)})
    for key in (
        "total_before",
        "total_after",
        "peak_hour",
        "peak_aqi",
        "highest_aqi_hour",
        "highest_aqi",
    ):
        value = engine.get(key)
        if isinstance(value, int | float):
            values.update({float(value), round(float(value)), round(float(value), 1)})
    return values


def rejected_numbers(text: str, engine: dict[str, Any]) -> set[float]:
    """Return numbers present in text but absent from the compact engine whitelist."""
    return extract_numbers(text) - allowed_numbers(engine)


def validate_number_guard(text: str, engine: dict[str, Any]) -> bool:
    """Reject text containing numbers absent from engine output."""
    extracted = extract_numbers(text)
    return extracted.issubset(allowed_numbers(engine))


def templated_explanation(engine: dict[str, Any], language: str = "hinglish") -> str:
    """Return a safe deterministic explanation without an AI call."""
    peak_hour = int(engine["peak_hour"])
    peak_aqi = int(engine["peak_aqi"])
    top = engine.get("top_swap")
    if language == "en":
        if top:
            return (
                f"The highest exposure period is around {peak_hour}:00 with AQI {peak_aqi}. "
                f"The top estimated swap may reduce exposure by {top['percent_reduction']}%. "
                "These are estimates, not medical advice. Consult a doctor "
                "for symptoms or at-risk members."
            )
        return (
            f"The highest exposure period is around {peak_hour}:00 with AQI {peak_aqi}. "
            "No positive swap was found. These are estimates, not medical advice."
        )
    if top:
        return (
            f"Aaj {peak_hour} baje AQI sabse kharab ho sakta hai ({peak_aqi}). "
            f"Top swap se exposure lagbhag {top['percent_reduction']}% kam ho sakta hai. "
            "Ye anumaan hai, doctor ki salah nahi."
        )
    return (
        f"Aaj {peak_hour} baje AQI sabse kharab ho sakta hai ({peak_aqi}). "
        "Abhi koi positive swap nahi mila. Ye anumaan hai, doctor ki salah nahi."
    )
