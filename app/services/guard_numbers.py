"""Number extraction, whitelist validation, and numeric grounding checks."""

import re
from collections.abc import Mapping, Sequence
from typing import Any

from app.services.guard_wording import NOON, has_past_tense, has_raw_hour_zero, has_raw_units

_NUMBER = re.compile(r"(?<![A-Za-z])[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?![A-Za-z])")
EXPECTED_RANGE_LEN = 2


def extract_numbers(text: str) -> set[float]:
    """Extract numeric values from assistant text, omitting clock colons."""
    text_without_clocks = re.sub(
        r"\b\d{1,2}:\d{2}\b",
        lambda match: match.group().split(":", 1)[0],
        text,
    )
    return {float(match) for match in _NUMBER.findall(text_without_clocks)}


def _to_12h_and_24h(hour: int | float) -> set[float]:
    """Return both 24h and 12h clock representations for an hour."""
    h = int(hour) % 24
    h12 = NOON if h % NOON == 0 else h % NOON
    return {float(h), float(h12)}


def _round_variations(val: int | float) -> set[float]:
    """Return standard rounded variations for a numeric quantity."""
    return {float(val), round(float(val)), round(float(val), 1), float(int(val))}


def _extract_hour_values(source: Mapping[str, Any], keys: tuple[str, ...]) -> set[float]:
    """Extract clock hours and their 12h/24h variations for designated keys."""
    values: set[float] = set()
    for key in keys:
        val = source.get(key)
        if isinstance(val, int | float):
            values.update(_to_12h_and_24h(val))
    return values


def _allowed_hours(engine: Mapping[str, Any]) -> set[float]:
    """Extract peak and swap hours with their 12h and 24h clock representations."""
    values = _extract_hour_values(engine, ("peak_hour", "highest_aqi_hour"))
    values.update(_extract_hour_values(engine.get("top_swap") or {}, ("from_hour", "to_hour")))
    return values


def _allowed_aqi(engine: Mapping[str, Any]) -> set[float]:
    """Extract peak AQI with rounded variations."""
    values: set[float] = set()
    for key in ("peak_aqi", "highest_aqi"):
        val = engine.get(key)
        if isinstance(val, int | float):
            values.update({float(val), round(float(val)), round(float(val), 1)})
    return values


def _collect_numeric_variations(items: Sequence[Any]) -> set[float]:
    """Extract rounded variations for all numbers in a sequence."""
    values: set[float] = set()
    for item in items:
        if isinstance(item, int | float):
            values.update(_round_variations(item))
    return values


def _allowed_saved_ug(cleaner: Mapping[str, Any]) -> set[float]:
    """Extract micrograms saved and uncertainty range values."""
    values = _collect_numeric_variations([cleaner.get("inhaled_saved_ug")])
    saved_range = cleaner.get("inhaled_saved_range_ug")
    if isinstance(saved_range, list | tuple) and len(saved_range) == EXPECTED_RANGE_LEN:
        values.update(_collect_numeric_variations(saved_range))
    return values


def _allowed_dose_reductions(engine: Mapping[str, Any]) -> set[float]:
    """Extract percentage reductions and micrograms saved with reasonable rounded forms."""
    values: set[float] = set()
    cleaner = engine.get("cleaner_day") or {}
    top = engine.get("top_swap") or {}

    pct = cleaner.get("percent_reduction") or top.get("percent_reduction")
    if isinstance(pct, int | float):
        values.update(_round_variations(pct))

    return values | _allowed_saved_ug(cleaner)


def allowed_numbers(engine: Mapping[str, Any]) -> set[float]:
    """Build allowed summary facts and sensible rounded forms from UI units only."""
    return _allowed_hours(engine) | _allowed_aqi(engine) | _allowed_dose_reductions(engine)


def rejected_numbers(text: str, engine: Mapping[str, Any]) -> set[float]:
    """Return numbers present in text but absent from the compact engine whitelist."""
    return extract_numbers(text) - allowed_numbers(engine)


def validate_number_guard(text: str, engine: Mapping[str, Any]) -> bool:
    """Reject text containing forbidden past tense, raw units, hour 0, or foreign numbers."""
    if has_past_tense(text):
        return False
    if has_raw_units(text):
        return False
    if has_raw_hour_zero(text):
        return False
    extracted = extract_numbers(text)
    return extracted.issubset(allowed_numbers(engine))
