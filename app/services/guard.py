"""LLM output number guard, hypothetical phrasing checks, and deterministic template fallback."""

from app.services.guard_numbers import (
    EXPECTED_RANGE_LEN,
    allowed_numbers,
    extract_numbers,
    rejected_numbers,
    validate_number_guard,
)
from app.services.guard_safety import templated_explanation
from app.services.guard_wording import (
    AFTERNOON,
    EARLY_MORNING,
    EVENING,
    MIDNIGHT,
    NOON,
    PAST_TENSE_PATTERNS,
    format_hinglish_hour,
    format_hour_12h,
    has_past_tense,
    has_raw_hour_zero,
    has_raw_units,
)

# Backward compatibility alias
_format_hinglish_hour = format_hinglish_hour

__all__ = [
    "AFTERNOON",
    "EARLY_MORNING",
    "EVENING",
    "EXPECTED_RANGE_LEN",
    "MIDNIGHT",
    "NOON",
    "PAST_TENSE_PATTERNS",
    "_format_hinglish_hour",
    "allowed_numbers",
    "extract_numbers",
    "format_hinglish_hour",
    "format_hour_12h",
    "has_past_tense",
    "has_raw_hour_zero",
    "has_raw_units",
    "rejected_numbers",
    "templated_explanation",
    "validate_number_guard",
]
