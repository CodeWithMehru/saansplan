"""Unit tests for app.services.guard_wording module."""

from __future__ import annotations

from app.services.guard_wording import (
    format_hour_12h,
    has_past_tense,
    has_raw_hour_zero,
    has_raw_units,
)


def test_has_past_tense_detection() -> None:
    """Detect past-tense verbs implying historical reductions."""
    assert has_past_tense("Your exposure dropped by 30%") is True
    assert has_past_tense("Pollution kam hua") is True
    assert has_past_tense("Could reduce about 25% (estimate)") is False
    assert has_past_tense("Lagbhag 25% kam ho sakta hai") is False


def test_has_raw_units_detection() -> None:
    """Detect raw ungrounded units or debug string exposure numbers."""
    assert has_raw_units("exposure 47872.35 se 29828.99 ho gaya") is True
    assert has_raw_units("saved 320 µg PM2.5 inhaled") is False


def test_has_raw_hour_zero() -> None:
    """Detect unformatted Hour 0."""
    assert has_raw_hour_zero("Peak hour 0") is True
    assert has_raw_hour_zero("Peak hour 12 am") is False


def test_format_hour_12h_conversions() -> None:
    """Format 24h integers into accessible 12-hour clock times."""
    assert format_hour_12h(0, "en") == "12 am"
    assert format_hour_12h(12, "en") == "12 pm"
    assert format_hour_12h(18, "en") == "6 pm"
    assert format_hour_12h(18, "hi") == "shaam 6 baje"
    assert format_hour_12h(18, "hinglish") == "shaam 6 baje"
