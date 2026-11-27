"""Unit tests for app.engine.community module."""

from __future__ import annotations

from app.engine.community import (
    generate_whatsapp_share_url,
    get_rwa_checklist,
    get_school_day_advisory,
)


def test_school_advisory_severe_aqi_alert() -> None:
    """Verify severe smog triggers high severity school advisory."""
    adv = get_school_day_advisory(max_aqi=350, indian_category="Severe")
    assert adv["severity"] == "high"
    assert "SEVERE SMOG ALERT" in adv["actions"][0]


def test_school_advisory_moderate_aqi() -> None:
    """Verify moderate AQI advisory suggests outdoor precautions."""
    adv = get_school_day_advisory(max_aqi=150, indian_category="Moderate")
    assert adv["severity"] == "moderate"
    assert len(adv["actions"]) > 0


def test_whatsapp_share_url_generation() -> None:
    """Verify WhatsApp share URL contains encoded text."""
    url = generate_whatsapp_share_url("Delhi peak AQI 312 (Severe)")
    assert "https://wa.me/?text=" in url
    assert "Delhi" in url


def test_rwa_checklist_generation() -> None:
    """Verify RWA checklist returns actionable community advisories."""
    checklist = get_rwa_checklist()
    assert len(checklist.items) >= 3
    assert checklist.title != ""
