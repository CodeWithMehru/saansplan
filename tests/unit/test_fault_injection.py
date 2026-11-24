"""Fault injection tests for upstream API failures and network anomalies."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from starlette.requests import Request

from app.core.limiting import client_ip
from app.routers.plan import _resolve_routine
from app.schemas.family import AgeGroup, FamilyMember
from app.schemas.plan import PlanRequest
from app.schemas.routine import Routine
from app.services.air_quality import clear_air_quality_cache, fetch_air_quality
from app.services.llm import explain_with_fallback


@pytest.mark.asyncio
async def test_fault_injection_open_meteo_500_and_malformed() -> None:
    """Test air quality service resilience against HTTP 500 and malformed responses."""
    clear_air_quality_cache()
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # 1. HTTP 500 Internal Server Error
    mock_client.get.side_effect = httpx.HTTPStatusError(
        "Internal Server Error",
        request=httpx.Request("GET", "http://test"),
        response=httpx.Response(500, request=httpx.Request("GET", "http://test")),
    )
    with pytest.raises(RuntimeError, match="Air-quality service unavailable"):
        await fetch_air_quality(28.6, 77.2, forecast_days=1, client=mock_client)
    clear_air_quality_cache()

    # 2. Malformed JSON missing hourly keys
    malformed_resp = httpx.Response(200, json={}, request=httpx.Request("GET", "http://test"))
    mock_client.get.side_effect = None
    mock_client.get.return_value = malformed_resp
    res = await fetch_air_quality(28.6, 77.2, forecast_days=1, client=mock_client)
    assert len(res["pm25"]) == 24
    assert res["pm25"][0] is None
    clear_air_quality_cache()


@pytest.mark.asyncio
async def test_fault_injection_groq_rate_limit_and_malformed_json() -> None:
    """Test LLM service resilience against Groq 429 rate limit and unparseable JSON."""
    member = FamilyMember(name="Test", age_group=AgeGroup.adult, sensitive=False)
    req = PlanRequest(latitude=28.6, longitude=77.2, members=[member], routine_text="walk at 6am")

    # 1. Parse routine with Groq 429
    with patch("app.services.llm.groq_chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = httpx.HTTPStatusError(
            "Rate limit exceeded",
            request=httpx.Request("POST", "http://groq"),
            response=httpx.Response(429, request=httpx.Request("POST", "http://groq")),
        )
        routine = await _resolve_routine(req)
        assert isinstance(routine, Routine)

    # 2. Parse routine with completely invalid non-JSON string
    with patch("app.services.llm.groq_chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "Sorry, as an AI I cannot help with that."
        routine = await _resolve_routine(req)
        assert isinstance(routine, Routine)

    # 3. Explain with fallback with Groq timeout
    with patch("app.services.llm.groq_chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = httpx.TimeoutException("Groq timeout")
        engine_facts = {
            "current_pm25": 180.0,
            "peak_pm25": 250.0,
            "peak_hour": 8,
            "swaps": [],
            "cleaner_day": {"percent_reduction": 25, "total_saved_ug": 500.0},
        }
        explanation = await explain_with_fallback(engine_facts, language="en")
        assert explanation["ai_available"] is False
        assert "25%" in explanation["explanation"]


@pytest.mark.asyncio
async def test_fault_injection_resolve_routine_timeout() -> None:
    """Test _resolve_routine timeout fallback to default routine."""
    member = FamilyMember(name="Test", age_group=AgeGroup.adult, sensitive=False)
    req = PlanRequest(
        latitude=28.6, longitude=77.2, members=[member], routine_text="walk in the park"
    )

    with patch("app.routers.plan.parse_routine", new_callable=AsyncMock) as mock_parse:
        mock_parse.side_effect = TimeoutError("Timed out")
        res = await _resolve_routine(req)
        assert isinstance(res, Routine)
        assert res.home.heating == "none"


def test_fault_injection_client_ip_headers() -> None:
    """Test client_ip extractor against spoofed headers and proxy settings."""
    req_untrusted = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(b"x-forwarded-for", b"203.0.113.195, 70.41.3.18")],
            "client": ("192.168.1.50", 12345),
        }
    )
    with (
        patch.dict("os.environ", {"TRUST_PROXY": "false"}),
        patch("app.core.limiting.get_settings") as mock_settings,
    ):
        mock_settings.return_value.trust_proxy = False
        assert client_ip(req_untrusted) == "192.168.1.50"

    with (
        patch.dict("os.environ", {"TRUST_PROXY": "true"}),
        patch("app.core.limiting.get_settings") as mock_settings,
    ):
        mock_settings.return_value.trust_proxy = True
        assert client_ip(req_untrusted) == "203.0.113.195"

    req_empty = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    assert client_ip(req_empty) == "unknown"
