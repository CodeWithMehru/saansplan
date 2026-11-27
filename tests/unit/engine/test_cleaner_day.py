"""Unit tests for Your Cleaner Day 24-hour alternative routine generator."""

from app.engine.cleaner_day import generate_cleaner_day, is_fixed_commitment
from app.schemas.family import AgeGroup, FamilyMember
from app.schemas.routine import (
    Activity,
    ActivityPlace,
    HomeSetup,
    Intensity,
    Routine,
    TravelMode,
)


def test_fixed_commitment_detection():
    school_act = Activity(
        label="Morning school drop-off",
        start_hour=7,
        duration_min=30,
        place=ActivityPlace.outdoor,
        mode=TravelMode.walk,
        intensity=Intensity.light,
        member_refs=[0],
    )
    assert is_fixed_commitment(school_act) is True

    walk_act = Activity(
        label="Evening park walk",
        start_hour=18,
        duration_min=45,
        place=ActivityPlace.outdoor,
        mode=TravelMode.walk,
        intensity=Intensity.moderate,
        member_refs=[0],
    )
    assert is_fixed_commitment(walk_act) is False


def test_generate_cleaner_day_preserves_commitments_and_shifts_flexible():
    # PM2.5 is high in evening (18:00) and low at midday (13:00)
    pm25 = [200.0] * 24
    pm25[13] = 40.0  # clean midday
    pm25[18] = 250.0  # high evening

    members = [FamilyMember(name="Parent", age_group=AgeGroup.adult, sensitive=False)]
    routine = Routine(
        activities=[
            Activity(
                label="Evening leisure walk",
                start_hour=18,
                duration_min=60,
                place=ActivityPlace.outdoor,
                mode=TravelMode.walk,
                intensity=Intensity.moderate,
                member_refs=[0],
            ),
            Activity(
                label="Office work shift",
                start_hour=9,
                duration_min=480,
                place=ActivityPlace.indoor,
                mode=TravelMode.none,
                intensity=Intensity.rest,
                member_refs=[0],
            ),
        ],
        home=HomeSetup(
            heating="none",
            cooking="wood_coal",
            windows="mostly_open",
            purifier=False,
            has_chimney=False,
        ),
    )

    result = generate_cleaner_day(pm25, [150.0] * 24, members, routine)

    assert result["percent_reduction"] > 0
    assert result["inhaled_saved_ug"] > 0
    assert len(result["hourly_comparison"]) == 24
    assert result["routine"].home.windows == "mostly_closed"
    assert result["routine"].home.purifier is True
    assert result["routine"].home.cooking == "induction"

    # Verify flexible activity shifted to midday
    walk_opt = next(a for a in result["routine"].activities if a.label == "Evening leisure walk")
    assert 11 <= walk_opt.start_hour <= 15

    # Verify fixed commitment hour was preserved
    office_opt = next(a for a in result["routine"].activities if a.label == "Office work shift")
    assert office_opt.start_hour == 9
