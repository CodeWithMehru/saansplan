"""Deterministic template fallbacks and medical disclaimer formatting."""

from __future__ import annotations

from collections.abc import Mapping

from app.engine.exposure_models import ExposureResult
from app.services.guard_wording import format_hour_12h


def _template_en(
    time_str: str,
    peak_aqi: int,
    pct: int | float,
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
    pct: int | float,
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


def templated_explanation(
    engine: ExposureResult | Mapping[str, object], language: str = "hinglish"
) -> str:
    """Return a safe deterministic hypothetical explanation using 12h clock and UI units."""
    peak_val = engine.get("peak_hour", 18)
    peak_hour = int(peak_val) if isinstance(peak_val, int | float | str) else 18
    aqi_val = engine.get("peak_aqi", 200)
    peak_aqi = int(aqi_val) if isinstance(aqi_val, int | float | str) else 200
    cleaner_raw = engine.get("cleaner_day")
    cleaner = cleaner_raw if isinstance(cleaner_raw, Mapping) else {}
    top_raw = engine.get("top_swap")
    top = top_raw if isinstance(top_raw, Mapping) else {}

    time_str = format_hour_12h(peak_hour, language)
    pct_raw = cleaner.get("percent_reduction") or top.get("percent_reduction", 25)
    pct: int | float = pct_raw if isinstance(pct_raw, int | float) else 25
    saved_ug_raw = cleaner.get("inhaled_saved_ug")
    saved_ug = float(saved_ug_raw) if isinstance(saved_ug_raw, int | float | str) else None
    saved_range_raw = cleaner.get("inhaled_saved_range_ug")
    saved_range = (
        [float(x) for x in saved_range_raw if isinstance(x, int | float | str)]
        if isinstance(saved_range_raw, list | tuple)
        else None
    )

    if language == "en":
        return _template_en(time_str, peak_aqi, pct, saved_ug, saved_range)
    return _template_hi(time_str, peak_aqi, pct, saved_ug, saved_range)
