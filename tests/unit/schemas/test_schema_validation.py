from pydantic import ValidationError

from app.schemas.plan import PlanRequest
from app.schemas.routine import Routine


def test_extra_fields_rejected():
    try:
        Routine.model_validate(
            {
                "activities": [],
                "home": {
                    "heating": "none",
                    "cooking": "lpg",
                    "windows": "mostly_closed",
                    "purifier": False,
                    "has_chimney": False,
                },
                "extra": True,
            }
        )
    except ValidationError:
        return
    raise AssertionError("Extra field should be rejected")


def test_bad_enum_rejected():
    try:
        PlanRequest.model_validate(
            {"latitude": 28.6, "longitude": 77.2, "members": [{"age_group": "infant"}]}
        )
    except ValidationError:
        return
    raise AssertionError("Bad enum should be rejected")


def test_schema_control_characters() -> None:
    """Verify plan request and routine validation rejects unprintable control characters."""
    import pytest

    from app.schemas.family import AgeGroup, FamilyMember
    from app.schemas.plan import PlanRequest
    from app.schemas.routine import (
        Activity,
        ActivityPlace,
        Intensity,
        TravelMode,
    )

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
