"""Number guard edge-case tests."""

from __future__ import annotations

from app.services.guard_numbers import allowed_numbers, rejected_numbers
from app.services.guard_safety import templated_explanation


def test_allowed_numbers_include_top_swap_and_peaks() -> None:
    """Verify allowed numbers include peak AQI and swap percentages."""
    engine = {
        "peak_hour": 18,
        "peak_aqi": 312,
        "top_swap": {
            "from_hour": 18,
            "to_hour": 13,
            "percent_reduction": 29,
            "exposure_before": 100,
            "exposure_after": 71,
        },
        "cleaner_day": {
            "percent_reduction": 29.5,
            "inhaled_saved_ug": 24.5,
            "inhaled_saved_range_ug": (18.4, 30.6),
        },
    }
    allowed = allowed_numbers(engine)
    assert 312.0 in allowed
    assert 29.0 in allowed
    assert 29.5 in allowed
    assert 24.5 in allowed
    assert 18.4 in allowed
    assert 30.6 in allowed
    assert 6.0 in allowed  # 18h -> 6pm
    assert 1.0 in allowed  # 13h -> 1pm
    assert 100.0 not in allowed  # Raw exposure numbers strictly excluded
    assert 71.0 not in allowed


def test_rejected_number_is_reported() -> None:
    """Verify numbers outside engine values are rejected."""
    engine = {"peak_hour": 18, "peak_aqi": 312, "top_swap": {"percent_reduction": 29}}
    assert rejected_numbers("AQI 312 and 45%", engine) == {45.0}


def test_template_english_and_empty_swap_paths() -> None:
    """Verify fallback template handles missing swaps in multiple locales."""
    engine = {"peak_hour": 18, "peak_aqi": 312, "top_swap": None}
    assert "312" in templated_explanation(engine, "en")
    assert "312" in templated_explanation(engine, "hinglish")
