"""Deterministic template fallbacks and medical disclaimer formatting."""

from __future__ import annotations

from typing import Any

from app.services.guard_wording import format_hour_12h


def _template_en(
    time_str: str,
    peak_aqi: int,
    pct: float,
    saved_ug: float | None,
    saved_range: list[float] | tuple[float, float] | None,
) -> str:
    """Render English deterministic explanation template."""
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


def _template_hi(
    time_str: str,
    peak_aqi: int,
    pct: float,
    saved_ug: float | None,
    saved_range: list[float] | tuple[float, float] | None,
) -> str:
    """Render Hinglish deterministic explanation template."""
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
        return _template_en(time_str, peak_aqi, pct, saved_ug, saved_range)
    return _template_hi(time_str, peak_aqi, pct, saved_ug, saved_range)
