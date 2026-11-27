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


def test_allowed_numbers_include_top_swap_and_peaks() -> None:
    """Verify allowed numbers include peak AQI, hourly conversions, and swap percentages."""
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
    assert 6.0 in allowed
    assert 1.0 in allowed
    assert 100.0 not in allowed
    assert 71.0 not in allowed


def test_rejected_number_is_reported() -> None:
    """Verify numbers outside engine values are rejected."""
    from app.services.guard_numbers import rejected_numbers

    engine = {"peak_hour": 18, "peak_aqi": 312, "top_swap": {"percent_reduction": 29}}
    assert rejected_numbers("AQI 312 and 45%", engine) == {45.0}


def test_guard_numbers_bad_saved_range() -> None:
    """Verify non-numeric values in saved_range are filtered out."""
    from app.services.guard_numbers import _allowed_saved_ug

    bad_range = {"inhaled_saved_range_ug": ["low", "high"]}
    assert len(_allowed_saved_ug(bad_range)) == 0
