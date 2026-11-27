"""Targeted edge-case tests to achieve verified reliability across components."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import Response

from app.core import aqi
from app.core.cache import BoundedTTLCache
from app.core.error_handlers import not_found, validation_error
from app.core.middleware import (
    _apply_cache_headers,
    security_middleware,
)
from app.engine import cleaner_day, emissions, exposure, forecast
from app.engine.exposure_models import HourlyExposureRow
from app.engine.indoor_models import IndoorModulePayload, PurifierCadr
from app.engine.indoor_penetration import indoor_concentration
from app.main import (
    accessibility,
    lifespan,
    security_txt,
)
from app.schemas.family import AgeGroup, FamilyMember
from app.schemas.plan import PlanRequest
from app.schemas.routine import (
    Activity,
    ActivityPlace,
    HomeSetup,
    Intensity,
    Routine,
    TravelMode,
)
from app.services import assistant, assistant_grounding, guard_numbers, llm
from app.services.kb import KnowledgeBase


def test_aqi_category_equal_breakpoints() -> None:
    """Test indian_aqi_category when pm_high equals pm_low."""
    mock_bp = [(50.0, 50.0, 50, 50, "EqualTest", "equal-test")]
    with patch.object(aqi, "CPCB_PM25_BREAKPOINTS", mock_bp):
        label, _slug, _aq_low, aq = aqi.indian_aqi_category(50.0)
        assert label == "EqualTest"
        assert aq == 50


@pytest.mark.asyncio
async def test_cache_hits_and_cancelled_futures() -> None:
    """Test BoundedTTLCache fast-path hits and completed future handling."""
    cache: BoundedTTLCache[str] = BoundedTTLCache(max_size=5, ttl_seconds=60.0)
    cache.set("preloaded", "val")

    # Hit before lock
    res1 = await cache.get_or_compute("preloaded", AsyncMock())
    assert res1 == "val"

    # Future already done in _execute_compute
    loop = asyncio.get_running_loop()
    f1: asyncio.Future[str] = loop.create_future()
    f1.set_result("cancelled_or_early")
    await cache._execute_compute("k_done", AsyncMock(return_value="late"), f1)

    f2: asyncio.Future[str] = loop.create_future()
    f2.set_result("early_done")

    async def fail() -> str:
        raise RuntimeError("fail")

    await cache._execute_compute("k_fail", fail, f2)


def test_domain_models_protocols() -> None:
    """Test protocol methods on FrozenDomainModel instances."""
    row = HourlyExposureRow(
        hour=8,
        pm25=45.0,
        aqi=100,
        exposure=30.0,
        interpolated=False,
        indian_aqi=110,
        indian_category="Moderate",
    )
    # KeyError on missing subscript
    with pytest.raises(KeyError):
        _ = row["nonexistent_field"]

    # get() fallback
    assert row.get("nonexistent_field", "default_val") == "default_val"
    assert row.get("hour") == 8

    # __contains__ with non-string and missing
    assert 123 not in row  # non-string
    assert "nonexistent_field" not in row
    assert "hour" in row

    # keys, iter, len
    assert "hour" in set(row.keys())
    assert "hour" in list(row)
    assert len(row) == 7


def test_exposure_and_forecast_edge_cases() -> None:
    """Test edge cases in exposure interpolation and forecast day slicing."""
    assert exposure.interpolate_hourly([]) == ([], [])
    assert exposure._interpolate_between(1, 0, 2, [None, 50.0, 100.0]) == 0.0
    assert exposure._fill_missing_value(1, [0], [None]) == 0.0

    assert forecast.analyze_forecast([]) == []
    assert forecast._extract_day_data(10, [10.0] * 24, None) is None


def test_cleaner_day_out_of_range_member_and_purifier_active() -> None:
    """Test cleaner_day optimizer with purifier already on and out-of-range member ref."""
    member = FamilyMember(name="A", age_group=AgeGroup.adult, sensitive=False)
    home = HomeSetup(
        heating="none",
        cooking="other",
        windows="mostly_open",
        purifier=True,
        has_chimney=False,
    )
    routine = Routine(
        activities=[
            Activity(
                label="Commute",
                start_hour=9,
                duration_min=45,
                place=ActivityPlace.outdoor,
                mode=TravelMode.walk,
                intensity=Intensity.moderate,
                member_refs=[99],  # Out of range index
            )
        ],
        home=home,
    )
    res = cleaner_day.generate_cleaner_day([100.0] * 24, [100.0] * 24, [member], routine)
    assert res.total_exposure_before >= 0


def test_indoor_penetration_cooking_other() -> None:
    """Test indoor penetration when home cooking is 'other'."""
    home = HomeSetup(
        heating="none",
        cooking="other",
        windows="mostly_closed",
        purifier=False,
        has_chimney=False,
    )
    conc = indoor_concentration(100.0, home)
    assert conc > 0


def test_schema_control_characters() -> None:
    """Test plan request and routine validation for control characters."""
    with pytest.raises(ValueError, match="Control characters are not allowed"):
        PlanRequest(
            latitude=28.6,
            longitude=77.2,
            members=[FamilyMember(name="A", age_group=AgeGroup.adult)],
            routine_text="Test\x00bad",
        )

    req_none_city = PlanRequest(
        latitude=28.6,
        longitude=77.2,
        city=None,
        members=[FamilyMember(name="A", age_group=AgeGroup.adult)],
    )
    assert req_none_city.city is None

    with pytest.raises(ValueError, match="Control characters are not allowed"):
        Activity(
            label="Walk\x01Bad",
            start_hour=8,
            duration_min=30,
            place=ActivityPlace.outdoor,
            mode=TravelMode.walk,
            intensity=Intensity.light,
            member_refs=[0],
        )


@pytest.mark.asyncio
async def test_main_lifespan_and_middleware() -> None:
    """Test lifespan startup/shutdown and security middleware error handling."""
    dummy_app = FastAPI()
    async with lifespan(dummy_app):
        assert hasattr(dummy_app.state, "http_client")
        assert not dummy_app.state.http_client.is_closed

    # Test cache headers on static response
    resp = Response(content=b"console.log(1);", media_type="application/javascript")
    _apply_cache_headers(resp, "/static/app.js")
    assert "public" in resp.headers["Cache-Control"]
    assert "ETag" in resp.headers

    # Test middleware exception catch
    req = Request({"type": "http", "method": "GET", "path": "/test", "headers": []})

    async def throwing_call_next(r: Request) -> Response:
        raise RuntimeError("Internal crash")

    err_resp = await security_middleware(req, throwing_call_next)
    assert err_resp.status_code == 500

    # Test custom exception handlers
    nf_resp = await not_found(req, HTTPException(404))
    assert nf_resp.status_code == 404

    err = [{"loc": ("body",), "msg": "err", "type": "value_error"}]
    val_resp = await validation_error(req, RequestValidationError(errors=err))
    assert val_resp.status_code == 422


@pytest.mark.asyncio
async def test_accessibility_and_security_endpoints() -> None:
    """Test accessibility.html and security.txt endpoints return valid FileResponses."""
    a_resp = await accessibility()
    assert a_resp.path == "app/static/accessibility.html"

    s_resp = await security_txt()
    assert s_resp.path == "app/static/.well-known/security.txt"


@pytest.mark.asyncio
async def test_assistant_and_resolver_edge_cases() -> None:
    """Test assistant helper fallbacks and resolver edge cases."""
    # Empty question
    res = await assistant.answer_question("")
    assert "Please ask" in res["answer"]

    # _fetch_today_pm25 with non-list pm25
    mock_fetch = AsyncMock(return_value={"pm25": "invalid"})
    pm25 = await assistant._fetch_today_pm25(28.6, 77.2, None, mock_fetch)
    assert pm25 == []

    # _call_groq_assistant with empty text
    empty_chat = AsyncMock(return_value='{"answer": "   ", "kb_ids": []}')
    res_groq = await assistant._call_groq_assistant("question", {}, [], empty_chat)
    assert res_groq is None

    # resolver 12h hour with am
    h = assistant_grounding._extract_12h_hour("at 9 am")
    assert h == 9

    # _attach_cadr_kb_entry and _ensure_cpcb_breakpoint_entry with mock KB
    mock_kb = MagicMock(spec=KnowledgeBase)
    mock_kb.entries = []
    entries: list[dict[str, Any]] = []
    assistant_grounding._attach_cadr_kb_entry(entries, mock_kb)
    assert len(entries) == 0
    assistant_grounding._ensure_cpcb_breakpoint_entry(entries, mock_kb)
    assert len(entries) == 0


def test_guard_numbers_and_llm_parsing() -> None:
    """Test guard numbers range parsing and llm shift fact formatting."""
    # Non-number in saved_range
    bad_range = {"inhaled_saved_range_ug": ["low", "high"]}
    assert len(guard_numbers._allowed_saved_ug(bad_range)) == 0

    # Shift facts
    facts: dict[str, Any] = {}
    top = {"from_hour": 8, "to_hour": 14}
    llm._append_shift_facts(facts, top, "en")
    assert "8 am" in facts["suggested_shift_from"]
    assert "2 pm" in facts["suggested_shift_to"]

    # Rejected text in _parse_and_validate_llm_text
    engine = {"allowed": 10}
    clean = llm._parse_and_validate_llm_text('{"text": "Unallowed number 99999"}', engine)
    assert clean is None


def test_nested_domain_model_subscript_and_get() -> None:
    """Test subscript and get access returning dict for nested FrozenDomainModel."""
    cadr = PurifierCadr(
        room_area_m2=18.5,
        room_area_sqft=200.0,
        ceiling_height_m=2.7,
        volume_m3=50.0,
        recommended_smoke_cadr_cfm=150,
        recommended_smoke_cadr_m3h=255,
        target_ach=4,
        rule_basis="AHAM 2/3 rule",
    )
    payload = IndoorModulePayload(
        room_checklists={},
        purifier_sizing_default=cadr,
        diy_box_fan_guide={},
    )
    # Accessing nested model via [] returns converted dict
    cadr_dict = payload["purifier_sizing_default"]
    assert isinstance(cadr_dict, dict)
    assert cadr_dict["recommended_smoke_cadr_cfm"] == 150

    # Accessing nested model via .get() returns converted dict
    cadr_get = payload.get("purifier_sizing_default")
    assert isinstance(cadr_get, dict)
    assert cadr_get["recommended_smoke_cadr_cfm"] == 150


def test_emissions_cooking_induction_option() -> None:
    """Test _build_cooking_options when fuel is already induction."""
    opts = emissions._build_cooking_options("induction", 10.0, 5.0, 500.0)
    assert opts == []
