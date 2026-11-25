"""Unit tests for app.services.assistant_resolvers module."""

from __future__ import annotations

from app.services.assistant_resolvers import check_safety, resolve_cadr, resolve_walk


def test_check_safety_symptom_detection() -> None:
    """Check clinical symptom keywords detection."""
    result = check_safety("patient with chest tightness and acute shortness of breath")
    assert result is not None
    assert result["safety_redirect"] is True
    assert "doctor" in result["answer"].lower()


def test_check_safety_clean_query() -> None:
    """Air quality queries without clinical symptoms must return None."""
    assert check_safety("what is the aqi today in delhi?") is None
    assert check_safety("diy box fan filter guide") is None


def test_resolve_cadr_sqft() -> None:
    """Verify CADR calculation for square footage."""
    cadr_info, cadr_cfm = resolve_cadr(150.0, [])
    assert cadr_info is not None
    assert cadr_cfm is not None
    assert cadr_info["recommended_smoke_cadr_cfm"] == 100
    assert cadr_info["recommended_smoke_cadr_m3h"] > 0
    assert "AHAM" in cadr_info["basis"]


def test_resolve_walk_query() -> None:
    """Verify walk inquiry provides hourly guidance."""
    hourly_pm25 = [150.0] * 24
    walk_info = resolve_walk(18, hourly_pm25, [])
    assert walk_info is not None
    assert walk_info["hour"] == 18
    assert walk_info["pm25"] == 150.0
    assert "outdoor_advisory" in walk_info
