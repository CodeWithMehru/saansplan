"""Unit tests for app.core.settings module."""

from __future__ import annotations

import pytest

from app.core.settings import get_settings, is_proxy_trusted


def test_settings_defaults() -> None:
    """Verify default configuration settings from get_settings()."""
    settings = get_settings()
    assert settings.groq_model == "openai/gpt-oss-20b"
    assert "30/minute" in settings.rate_limit
    assert settings.cache_ttl_seconds == 1800
    assert "air-quality" in settings.air_quality_endpoint
    assert "geocoding" in settings.geocoding_endpoint


def test_get_settings_singleton() -> None:
    """Verify get_settings returns a cached Settings instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_is_proxy_trusted_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify proxy trust evaluation with environment variables."""
    monkeypatch.setenv("TRUST_PROXY", "true")
    assert is_proxy_trusted() is True

    monkeypatch.setenv("TRUST_PROXY", "1")
    assert is_proxy_trusted() is True

    monkeypatch.setenv("TRUST_PROXY", "false")
    assert is_proxy_trusted() is False

    monkeypatch.delenv("TRUST_PROXY", raising=False)
    assert is_proxy_trusted() is False
