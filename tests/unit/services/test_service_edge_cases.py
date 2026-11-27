"""Targeted edge-case tests for core, routers, and services."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.aqi import indian_aqi_category
from app.core.cache import BoundedTTLCache
from app.routers.geocode import geocode
from app.routers.plan import (
    _extract_primary_commute,
    _generate_explanation,
    _resolve_routine,
    default_routine,
)
from app.schemas.family import AgeGroup, FamilyMember
from app.schemas.plan import PlanRequest
from app.schemas.routine import Activity, ActivityPlace, HomeSetup, Intensity, Routine, TravelMode
from app.services.air_quality import clear_air_quality_cache, fetch_air_quality
from app.services.assistant import (
    _ensure_cpcb_breakpoint_entry,
    _is_valid_hour,
    answer_question,
    extract_hour,
    resolve_cadr,
)


def test_aqi_category_out_of_bounds() -> None:
    """Test indian_aqi_category handles negative and extreme pm2.5 cleanly."""
    assert indian_aqi_category(-10.0)[0] == "Good"
    assert indian_aqi_category(1000.0)[0] == "Severe"


def test_cache_expiration_and_overwriting() -> None:
    """Test BoundedTTLCache expiration on get, key overwrite, and eviction on set."""
    cache = BoundedTTLCache(max_size=3, ttl_seconds=0.05)
    cache.set("k1", "v1")
    cache.set("k1", "v1_new")  # overwrite key
    assert cache.get("k1") == "v1_new"

    # Wait for expiry
    import time

    time.sleep(0.06)
    assert cache.get("k1") is None  # expired during get()

    # Eviction of expired items during set()
    cache.set("k2", "v2")
    time.sleep(0.06)
    cache.set("k3", "v3")  # cleans up k2
    assert cache.get("k2") is None
    assert cache.get("k3") == "v3"


@pytest.mark.asyncio
async def test_cache_get_or_compute_exceptions_and_double_check() -> None:
    """Test cache exception propagation and double-check locking."""
    cache = BoundedTTLCache(max_size=5, ttl_seconds=60.0)

    async def failing_compute() -> str:
        raise ValueError("Computation failed")

    with pytest.raises(ValueError, match="Computation failed"):
        await cache.get_or_compute("err_key", failing_compute)

    # Calling again after exception does not freeze
    async def successful_compute() -> str:
        return "success"

    res = await cache.get_or_compute("err_key", successful_compute)
    assert res == "success"


@pytest.mark.asyncio
async def test_geocode_missing_coordinates_and_error() -> None:
    """Test geocode handling of malformed records and upstream failure."""
    req = Request({"type": "http", "method": "GET", "path": "/api/geocode", "headers": []})

    # Response with missing latitude or longitude
    mock_payload = {
        "results": [
            {"name": "NoLat", "longitude": 77.0},
            {"name": "NoLon", "latitude": 28.0},
            {"name": "Valid", "latitude": 28.6, "longitude": 77.2, "country": "India"},
        ]
    }

    mock_resp = httpx.Response(200, json=mock_payload, request=httpx.Request("GET", "http://test"))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await geocode(req, name="Delhi")
        assert len(result["results"]) == 1
        assert result["results"][0]["name"] == "Valid"

    # Upstream 500 error triggers retry and HTTPException 502
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=httpx.Request("GET", "http://test"),
            response=httpx.Response(500, request=httpx.Request("GET", "http://test")),
        )
        with pytest.raises(HTTPException) as exc_info:
            await geocode(req, name="FailCity")
        assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_air_quality_client_and_error() -> None:
    """Test fetch_air_quality with custom client and error backoff."""
    clear_air_quality_cache()

    # Pass client directly
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = httpx.Response(
        200,
        json={"hourly": {"pm2_5": [50.0] * 24, "us_aqi": [100] * 24, "time": ["T"] * 24}},
        request=httpx.Request("GET", "http://test"),
    )
    mock_client.get.return_value = mock_resp

    res = await fetch_air_quality(28.6, 77.2, forecast_days=1, client=mock_client)
    assert len(res["pm25"]) == 24
    clear_air_quality_cache()

    # Failure raising RuntimeError
    failing_client = AsyncMock(spec=httpx.AsyncClient)
    failing_client.get.side_effect = httpx.ConnectTimeout("Timeout")
    with pytest.raises(RuntimeError, match="Air-quality service unavailable"):
        await fetch_air_quality(28.6, 77.2, forecast_days=1, client=failing_client)
    clear_air_quality_cache()


@pytest.mark.asyncio
async def test_plan_helpers_fallback_routine() -> None:
    """Test default_routine, _resolve_routine exception fallback, and primary commute."""
    member = FamilyMember(name="A", age_group=AgeGroup.adult, sensitive=False)
    # request with explicit routine
    routine = Routine(
        activities=[
            Activity(
                label="Commute",
                start_hour=9,
                duration_min=30,
                place=ActivityPlace.vehicle,
                mode=TravelMode.none,
                intensity=Intensity.light,
                member_refs=[0],
            )
        ],
        home=HomeSetup(
            heating="none",
            cooking="lpg",
            windows="mostly_closed",
            purifier=False,
            has_chimney=False,
        ),
    )
    req = PlanRequest(latitude=28.6, longitude=77.2, members=[member], routine=routine)
    assert default_routine(req) == routine

    # _resolve_routine with failing LLM parsing falls back to default
    req_text = PlanRequest(
        latitude=28.6, longitude=77.2, members=[member], routine_text="subah walk par jata hu"
    )
    with patch("app.routers.plan.parse_routine", new_callable=AsyncMock) as mock_parse:
        mock_parse.side_effect = RuntimeError("Parse failed")
        resolved = await _resolve_routine(req_text)
        assert isinstance(resolved, Routine)

    # _extract_primary_commute when mode is none
    assert _extract_primary_commute(routine) == "none"

    # _generate_explanation exception fallback
    with patch("app.routers.plan.explain_with_fallback", new_callable=AsyncMock) as mock_exp:
        mock_exp.side_effect = RuntimeError("LLM failed")
        expl = await _generate_explanation({}, "en")
        assert expl["ai_available"] is False
        assert "AI explanation unavailable" in expl["explanation"]


def test_assistant_hour_and_cadr_resolvers() -> None:
    """Test 12am clock extraction, Hindi phrases, CADR insertion, and CPCB ensure."""
    assert extract_hour("walk at 12am") == 0
    assert extract_hour("subah 6 baje") == 6
    assert extract_hour("dopahar 12 baje") == 12

    # CADR resolution inserts purifier-sizing if missing
    entries: list[dict[str, str]] = [{"id": "other-id", "content": "text"}]
    info, cfm = resolve_cadr(150.0, entries)
    assert cfm == 100
    assert any(e["id"] == "purifier-sizing" for e in entries)

    # _is_valid_hour edge cases
    assert _is_valid_hour(-1, 24) is False
    assert _is_valid_hour(24, 24) is False
    assert _is_valid_hour(12, 24) is True

    # _ensure_cpcb_breakpoint_entry
    empty_entries: list[dict[str, str]] = []
    _ensure_cpcb_breakpoint_entry(empty_entries)
    assert any(e["id"] == "cpcb-aqi-breakpoints" for e in empty_entries)


@pytest.mark.asyncio
async def test_assistant_deterministic_fallbacks_on_groq_failure() -> None:
    """Test answer_question falls back deterministically when Groq chat fails."""
    with patch("app.services.assistant.groq_chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = RuntimeError("Groq API error")
        with patch("app.services.assistant.fetch_air_quality", new_callable=AsyncMock) as mock_aq:
            mock_aq.return_value = {
                "pm25": [150.0] * 24,
                "aqi": [220] * 24,
                "times": ["T"] * 24,
                "timezone": "Asia/Kolkata",
            }
            # Purifier question
            resp = await answer_question(
                "purifier for 150 sq ft room", location=(28.6, 77.2, "Delhi")
            )
            assert "100 CFM" in resp["answer"]
            assert resp["safety_redirect"] is False

            # Walk question
            resp_walk = await answer_question("can I walk at 6 pm?", location=(28.6, 77.2, "Delhi"))
            assert resp_walk["safety_redirect"] is False
            assert "AQI" in resp_walk["answer"]
