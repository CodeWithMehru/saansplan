import pytest

from app.models import Activity, AgeGroup, FamilyMember, HomeSetup, Routine


@pytest.fixture
def members():
    return [
        FamilyMember(name="Child", age_group=AgeGroup.child),
        FamilyMember(name="Adult", age_group=AgeGroup.adult),
    ]


@pytest.fixture
def routine():
    return Routine(
        activities=[
            Activity(
                label="Park walk",
                start_hour=18,
                duration_min=40,
                place="outdoor",
                mode="walk",
                intensity="moderate",
                member_refs=[0],
            )
        ],
        home=HomeSetup(
            heating="wood_coal",
            cooking="lpg",
            windows="mostly_closed",
            purifier=False,
            has_chimney=False,
        ),
    )
