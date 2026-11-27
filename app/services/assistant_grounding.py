"""Deterministic resolvers and fallback generators for assistant Q&A."""

from __future__ import annotations

from typing import TypedDict

from app.core.aqi import indian_aqi_category
from app.engine.indoor_guidance import SQFT_PER_SQM, calculate_purifier_cadr
from app.services.assistant_extractors import (
    MIDNIGHT_HOUR,
    NOON_HOUR,
    POOR_AQI_THRESHOLD,
    AssistantResult,
    SafetyResult,
    _extract_12h_hour,
    _extract_hindi_hour,
    check_safety,
    extract_hour,
    extract_room_size_sqft,
)
from app.services.kb import KBEntry, KnowledgeBase


class WalkInfo(TypedDict):
    """Walk advisory conditions."""

    hour: int
    pm25: float
    aqi: int
    category: str
    outdoor_advisory: str


class CadrInfo(TypedDict):
    """Purifier CADR sizing info."""

    room_sqft: float
    recommended_smoke_cadr_cfm: int
    recommended_smoke_cadr_m3h: int
    target_ach: int
    basis: str


def _find_kb_entry(kb: KnowledgeBase | None, entry_id: str) -> KBEntry | None:
    """Look up an entry by ID from the knowledge base."""
    if not kb:
        return None
    for entry in kb.entries:
        if entry["id"] == entry_id:
            return entry
    return None


def _has_entry_id(entries: list[KBEntry], entry_id: str) -> bool:
    """Check if an entry with the designated ID exists in the list."""
    return any(entry["id"] == entry_id for entry in entries)


def _attach_cadr_kb_entry(entries: list[KBEntry], kb: KnowledgeBase | None) -> None:
    """Prepend purifier sizing documentation to retrieved entries."""
    if not _has_entry_id(entries, "purifier-sizing"):
        entry = _find_kb_entry(kb, "purifier-sizing")
        if entry is not None:
            entries.insert(0, entry)


def resolve_cadr(
    room_sqft: float | None, entries: list[KBEntry], kb: KnowledgeBase | None = None
) -> tuple[CadrInfo | None, int | None]:
    """Calculate deterministic CADR if room area is specified."""
    if room_sqft is None:
        return None, None
    cadr_cfm = round((2.0 / 3.0) * room_sqft)
    cadr_m3h = round(cadr_cfm * 1.699)
    cadr_calc = calculate_purifier_cadr(area_sq_meters=room_sqft / SQFT_PER_SQM)
    info: CadrInfo = {
        "room_sqft": round(room_sqft, 1),
        "recommended_smoke_cadr_cfm": cadr_cfm,
        "recommended_smoke_cadr_m3h": cadr_m3h,
        "target_ach": cadr_calc.target_ach,
        "basis": "AHAM 2/3 Rule (Smoke CADR in CFM >= 2/3 room area in sq ft)",
    }
    _attach_cadr_kb_entry(entries, kb)
    return info, cadr_cfm


def _is_valid_hour(hour: int | None, total_hours: int) -> bool:
    """Check if asked hour is within the available forecast window."""
    return hour is not None and 0 <= hour < total_hours


def _ensure_cpcb_breakpoint_entry(entries: list[KBEntry], kb: KnowledgeBase | None = None) -> None:
    """Attach CPCB breakpoint reference to KB context if absent."""
    if not _has_entry_id(entries, "cpcb-aqi-breakpoints"):
        entry = _find_kb_entry(kb, "cpcb-aqi-breakpoints")
        if entry is not None:
            entries.append(entry)


def resolve_walk(
    asked_hour: int | None,
    today_pm25: list[float],
    entries: list[KBEntry],
    kb: KnowledgeBase | None = None,
) -> WalkInfo | None:
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


def _fallback_cadr(room_sqft: float, cadr_cfm: int) -> AssistantResult:
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


def _fallback_walk(asked_hour: int, walk_info: WalkInfo | None, city: str) -> AssistantResult:
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


def _try_fallback_cadr(room_sqft: float | None, cadr_cfm: int | None) -> AssistantResult | None:
    """Build CADR fallback if both square footage and CADR are available."""
    if room_sqft is not None and cadr_cfm is not None:
        return _fallback_cadr(room_sqft, cadr_cfm)
    return None


def _try_fallback_walk(
    asked_hour: int | None, walk_info: WalkInfo | None, city: str
) -> AssistantResult | None:
    """Build walk advisory fallback if hour is available."""
    if asked_hour is not None:
        return _fallback_walk(asked_hour, walk_info, city)
    return None


def _fallback_generic_or_entry(entries: list[KBEntry]) -> AssistantResult:
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
    walk_data: tuple[int | None, WalkInfo | None, str],
    entries: list[KBEntry],
) -> AssistantResult:
    """Return verified deterministic fallback answer when model call fails."""
    cadr_fb = _try_fallback_cadr(cadr_data[0], cadr_data[1])
    if cadr_fb:
        return cadr_fb
    walk_fb = _try_fallback_walk(walk_data[0], walk_data[1], walk_data[2])
    if walk_fb:
        return walk_fb
    return _fallback_generic_or_entry(entries)


__all__ = [
    "AssistantResult",
    "CadrInfo",
    "SafetyResult",
    "WalkInfo",
    "_ensure_cpcb_breakpoint_entry",
    "_extract_12h_hour",
    "_extract_hindi_hour",
    "_is_valid_hour",
    "build_deterministic_fallback",
    "check_safety",
    "extract_hour",
    "extract_room_size_sqft",
    "resolve_cadr",
    "resolve_walk",
]
