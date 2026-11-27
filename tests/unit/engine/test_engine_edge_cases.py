"""Engine edge case tests for inhalation, school advisory, and empty activities."""

from __future__ import annotations

from app.engine.community import get_school_day_advisory
from app.engine.exposure import interpolate_hourly, simulate_exposure
from app.engine.inhaled import inhaled_micrograms, member_inhalation_scale
from app.schemas.family import AgeGroup, FamilyMember
from app.schemas.routine import (
    Activity,
    ActivityPlace,
    HomeSetup,
    Intensity,
    Routine,
    TravelMode,
)


def test_elderly_inhalation_scale() -> None:
    """Verify inhalation factor for elderly family members."""
    assert member_inhalation_scale("elderly") == 0.70
    dose = inhaled_micrograms(100.0, 60, "rest", "elderly")
    assert dose > 0


def test_school_advisory_severe_aqi_alert() -> None:
    """Verify severe smog triggers high severity school advisory."""
    adv = get_school_day_advisory(max_aqi=350, indian_category="Severe")
    assert adv["severity"] == "high"
    assert "SEVERE SMOG ALERT" in adv["actions"][0]


def test_exposure_vehicle_and_interpolation_calculation() -> None:
    """Verify vehicle exposure calculation and empty interpolation."""
    members = [FamilyMember(name="Adult", age_group=AgeGroup.adult, sensitive=False)]
    routine = Routine(
        activities=[
            Activity(
                label="Car commute",
                start_hour=8,
                duration_min=30,
                place=ActivityPlace.vehicle,
                mode=TravelMode.car,
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
    pm25 = [None] * 24
    pm25[0] = 50.0
    pm25[23] = 100.0
    res = simulate_exposure(pm25, [100.0] * 24, members, routine)
    assert res["total_before"] > 0

    # Test interpolate with all None
    vals, interp = interpolate_hourly([None, None])
    assert vals == [0.0, 0.0]
    assert interp == [True, True]


def test_persona_member_attribute_access() -> None:
    """Verify PersonaMember dictionary-like subscript and fallback retrieval."""
    from app.engine.domain_models import PersonaMember

    m = PersonaMember(name="Test", age_group="adult", sensitive=False)
    assert m["ageGroup"] == "adult"
    assert m["name"] == "Test"
    assert m.get("ageGroup") == "adult"
    assert m.get("missing", "default") == "default"
