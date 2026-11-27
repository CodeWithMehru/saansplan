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


def _as_int(val: object, default: int) -> int:
    """Safely cast integer or numeric string with fallback default."""
    if isinstance(val, int | float | str):
        try:
            return int(val)
        except (ValueError, TypeError):
            return default
    return default


def _as_mapping(val: object) -> Mapping[str, object]:
    """Safely cast to mapping with empty dict fallback."""
    if isinstance(val, Mapping):
        return val
    return {}


def _as_float(val: object) -> float | None:
    """Safely cast float or numeric string with None fallback."""
    if isinstance(val, int | float | str):
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    return None


def _extract_saved_range(cleaner: Mapping[str, object]) -> list[float] | None:
    """Extract and validate numeric saved range bounds."""
    raw = cleaner.get("inhaled_saved_range_ug")
    if isinstance(raw, list | tuple):
        return [float(x) for x in raw if isinstance(x, int | float | str)]
    return None


def templated_explanation(
    engine: ExposureResult | Mapping[str, object], language: str = "hinglish"
) -> str:
    """Return a safe deterministic hypothetical explanation using 12h clock and UI units."""
    peak_hour = _as_int(engine.get("peak_hour"), 18)
    peak_aqi = _as_int(engine.get("peak_aqi"), 200)

    cleaner = _as_mapping(engine.get("cleaner_day"))
    top = _as_mapping(engine.get("top_swap"))

    time_str = format_hour_12h(peak_hour, language)
    pct_val = cleaner.get("percent_reduction") or top.get("percent_reduction", 25)
    pct: int | float = pct_val if isinstance(pct_val, int | float) else 25

    saved_ug = _as_float(cleaner.get("inhaled_saved_ug"))
    saved_range = _extract_saved_range(cleaner)

    if language == "en":
        return _template_en(time_str, peak_aqi, pct, saved_ug, saved_range)
    if language == "hi":
        return _template_hi(time_str, peak_aqi, pct, saved_ug, saved_range)
    return _template_hi(time_str, peak_aqi, pct, saved_ug, saved_range)
