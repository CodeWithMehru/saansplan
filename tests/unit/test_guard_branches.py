"""Number guard branch coverage tests."""

from app.services.guard import allowed_numbers, rejected_numbers, templated_explanation


def test_allowed_numbers_include_top_swap_and_peaks() -> None:
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
    }
    allowed = allowed_numbers(engine)
    assert 312.0 in allowed
    assert 29.0 in allowed


def test_rejected_number_is_reported() -> None:
    engine = {"peak_hour": 18, "peak_aqi": 312, "top_swap": {"percent_reduction": 29}}
    assert rejected_numbers("AQI 312 and 45%", engine) == {45.0}


def test_template_english_and_empty_swap_paths() -> None:
    engine = {"peak_hour": 18, "peak_aqi": 312, "top_swap": None}
    assert "312" in templated_explanation(engine, "en")
    assert "312" in templated_explanation(engine, "hinglish")
