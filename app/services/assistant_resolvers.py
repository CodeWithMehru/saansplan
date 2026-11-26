"""Backward-compatibility shim for assistant_grounding."""

from app.services.assistant_grounding import (
    MIDNIGHT_HOUR,
    NOON_HOUR,
    POOR_AQI_THRESHOLD,
    _attach_cadr_kb_entry,
    _ensure_cpcb_breakpoint_entry,
    _extract_12h_hour,
    _extract_hindi_hour,
    _fallback_cadr,
    _fallback_walk,
    _is_valid_hour,
    build_deterministic_fallback,
    check_safety,
    extract_hour,
    extract_room_size_sqft,
    resolve_cadr,
    resolve_walk,
)

__all__ = [
    "MIDNIGHT_HOUR",
    "NOON_HOUR",
    "POOR_AQI_THRESHOLD",
    "_attach_cadr_kb_entry",
    "_ensure_cpcb_breakpoint_entry",
    "_extract_12h_hour",
    "_extract_hindi_hour",
    "_fallback_cadr",
    "_fallback_walk",
    "_is_valid_hour",
    "build_deterministic_fallback",
    "check_safety",
    "extract_hour",
    "extract_room_size_sqft",
    "resolve_cadr",
    "resolve_walk",
]
