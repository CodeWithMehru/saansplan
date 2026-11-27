"""Unit tests for app.core.aqi module."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core import aqi
from app.core.aqi import indian_aqi_category


def test_aqi_category_equal_breakpoints_returns_breakpoint_label() -> None:
    """Verify indian_aqi_category when pm_high equals pm_low in breakpoint table."""
    mock_bp = [(50.0, 50.0, 50, 50, "EqualTest", "equal-test")]
    with patch.object(aqi, "CPCB_PM25_BREAKPOINTS", mock_bp):
        label, slug, _aq_low, aq = indian_aqi_category(50.0)
        assert label == "EqualTest"
        assert slug == "equal-test"
        assert aq == 50


@pytest.mark.parametrize(
    ("pm25", "expected_label", "expected_slug"),
    [
        (-10.0, "Good", "good"),
        (0.0, "Good", "good"),
        (25.0, "Good", "good"),
        (45.0, "Satisfactory", "satisfactory"),
        (80.0, "Moderately polluted", "moderate"),
        (100.0, "Poor", "poor"),
        (200.0, "Very poor", "very-poor"),
        (300.0, "Severe", "severe"),
        (1000.0, "Severe", "severe"),
    ],
)
def test_aqi_category_boundaries_and_extremes(
    pm25: float, expected_label: str, expected_slug: str
) -> None:
    """Verify standard CPCB category mapping across negative, bounded, and extreme PM2.5 values."""
    label, slug, _aq_low, _aq = indian_aqi_category(pm25)
    assert label == expected_label
    assert slug == expected_slug
