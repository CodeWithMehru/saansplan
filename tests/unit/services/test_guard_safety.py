"""Unit tests for app.services.guard_safety module."""

from __future__ import annotations

from app.services.guard_safety import templated_explanation


def test_templated_explanation_contains_required_fields() -> None:
    """Deterministic fallback must produce formatted explanations in all languages."""
    engine = {
        "peak_hour": 18,
        "peak_aqi": 250,
        "cleaner_day": {
            "percent_reduction": 30.0,
            "inhaled_saved_ug": 240.0,
            "inhaled_saved_range_ug": [180.0, 300.0],
        },
    }
    en = templated_explanation(engine, language="en")
    assert "240" in en
    assert "30" in en
    assert "estimate" in en.lower()

    hi = templated_explanation(engine, language="hi")
    assert "240" in hi
    assert "30" in hi

    hing = templated_explanation(engine, language="hinglish")
    assert "240" in hing
    assert "30" in hing

    # Test when saved_ug is None
    engine_no_saved = {
        "peak_hour": 18,
        "peak_aqi": 250,
        "cleaner_day": {"percent_reduction": 30.0},
    }
    en_no_saved = templated_explanation(engine_no_saved, language="en")
    assert "None" not in en_no_saved
    assert "save approximately" not in en_no_saved
