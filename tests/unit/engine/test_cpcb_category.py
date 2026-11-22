"""Tests for PM2.5 and CPCB category mapping."""

import pytest

from app.core.aqi import indian_aqi_category


@pytest.mark.parametrize(
    ("pm25", "slug"),
    [
        (20.0, "good"),
        (50.0, "satisfactory"),
        (80.0, "moderate"),
        (100.0, "poor"),
        (200.0, "very-poor"),
        (300.0, "severe"),
    ],
)
def test_indian_category_boundaries(pm25: float, slug: str) -> None:
    _, actual_slug, _, _ = indian_aqi_category(pm25)
    assert actual_slug == slug
