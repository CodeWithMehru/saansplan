"""Unit tests for app.services.plan_service module."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.models import (
    Activity,
    ActivityPlace,
    AgeGroup,
    CookingFuel,
    FamilyMember,
    HeatingFuel,
    HomeSetup,
    Intensity,
    PlanRequest,
    Routine,
    TravelMode,
    WindowHabit,
)
from app.services.plan_service import (
    _build_community_payload,
    _build_indoor_module,
    _extract_primary_commute,
    _generate_explanation,
    _resolve_routine,
    default_routine,
)


def test_default_routine_creates_safe_home_setup() -> None:
    """Form-only plan request receives safe baseline home setup."""
    member = FamilyMember(age_group=AgeGroup.adult)
    req = PlanRequest(latitude=28.6, longitude=77.2, members=[member])
    routine = default_routine(req)
    assert routine.home.cooking == "lpg"
    assert routine.home.heating == "none"
    assert routine.home.windows == "mostly_closed"
    assert routine.home.purifier is False


def test_default_routine_preserves_supplied_routine() -> None:
    """When routine is provided, default_routine returns it unchanged."""
    member = FamilyMember(age_group=AgeGroup.adult)
    home = HomeSetup(
        heating="electric",
        cooking="induction",
        windows="mostly_open",
        purifier=True,
        has_chimney=True,
    )
    routine = Routine(activities=[], home=home)
    req = PlanRequest(latitude=28.6, longitude=77.2, members=[member], routine=routine)
    assert default_routine(req) is routine


def test_extract_primary_commute_modes() -> None:
    """Primary commute extracts first non-none transit activity."""
    home = HomeSetup(
        heating=HeatingFuel.none,
        cooking=CookingFuel.lpg,
        windows=WindowHabit.mostly_closed,
        purifier=False,
        has_chimney=False,
    )
    act1 = Activity(
        label="sleep",
        start_hour=0,
        duration_min=480,
        place=ActivityPlace.indoor,
        mode=TravelMode.none,
        intensity=Intensity.rest,
        member_refs=[0],
    )
    act2 = Activity(
        label="drive",
        start_hour=8,
        duration_min=45,
        place=ActivityPlace.vehicle,
        mode=TravelMode.car,
        intensity=Intensity.light,
        member_refs=[0],
    )
    routine = Routine(activities=[act1, act2], home=home)
    assert _extract_primary_commute(routine) == "car"

    routine_no_commute = Routine(activities=[act1], home=home)
    assert _extract_primary_commute(routine_no_commute) == "none"


def test_build_indoor_module_structure() -> None:
    """Indoor module contains room checklists, purifier CADR, and DIY guide."""
    res = _build_indoor_module()
    assert "room_checklists" in res
    assert "purifier_sizing_default" in res
    assert "diy_box_fan_guide" in res


def test_build_community_payload() -> None:
    """Community payload builds school advisory, RWA checklist, and share text."""
    res = _build_community_payload(
        city="Delhi",
        peak_aqi=260,
        category="Poor",
        swaps=[{"description_key": "Shift outdoor run"}],
        cleaner_day={"percent_reduction": 28},
    )
    assert "school_advisory" in res
    assert "rwa_checklist" in res
    assert "whatsapp_url" in res
    assert "Delhi" in res["shareable_text"]


@pytest.mark.asyncio
async def test_resolve_routine_fallback_on_parse_failure() -> None:
    """Malformed routine text gracefully falls back to default routine."""
    member = FamilyMember(age_group=AgeGroup.adult)
    req = PlanRequest(
        latitude=28.6,
        longitude=77.2,
        members=[member],
        routine_text="invalid garbage routine",
    )
    with patch(
        "app.services.plan_service.parse_routine",
        new_callable=AsyncMock,
        side_effect=RuntimeError("LLM down"),
    ):
        routine = await _resolve_routine(req)
        assert routine is not None
        assert routine.home.cooking == "lpg"


@pytest.mark.asyncio
async def test_generate_explanation_fallback_on_error() -> None:
    """Exception during explanation returns graceful fallback explanation."""
    with patch(
        "app.services.plan_service.explain_with_fallback",
        new_callable=AsyncMock,
        side_effect=TimeoutError("Timed out"),
    ):
        res = await _generate_explanation({}, "en")
        assert res["ai_available"] is False
        assert "unavailable" in res["explanation"]
