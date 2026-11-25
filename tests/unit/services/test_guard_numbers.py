"""Unit tests for app.services.guard_numbers module."""

from __future__ import annotations

from app.services.guard_numbers import allowed_numbers, extract_numbers, validate_number_guard


def test_extract_numbers_values() -> None:
    """Verify extraction of floats and integers from string."""
    assert extract_numbers("35.5 µg/m3 and 120 AQI at 6 pm") == {35.5, 120.0, 6.0}
    assert extract_numbers("no numbers here") == set()


def test_validate_number_guard_accepts_whitelisted() -> None:
    """Validate numbers that are strictly within allowed whitelist."""
    engine = {
        "highest_aqi_hour": 18,
        "highest_aqi": 250,
        "cleaner_day": {
            "inhaled_saved_ug": 250.0,
            "percent_reduction": 30.0,
            "inhaled_saved_range_ug": [187.5, 312.5],
        },
    }
    allowed = allowed_numbers(engine)
    assert 250.0 in allowed
    assert 30.0 in allowed
    assert (
        validate_number_guard("Could reduce by ~30% with 250 µg saved around 6 pm", engine) is True
    )


def test_validate_number_guard_rejects_hallucination() -> None:
    """Reject numerals that are ungrounded in the engine facts."""
    engine = {
        "highest_aqi_hour": 10,
        "highest_aqi": 80,
        "cleaner_day": {"inhaled_saved_ug": 100.0, "percent_reduction": 20.0},
    }
    assert validate_number_guard("Could reduce by 99% saving 999 µg", engine) is False
