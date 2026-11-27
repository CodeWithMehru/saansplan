"""Property tests for deterministic exposure calculations."""

from hypothesis import given, settings
from hypothesis import strategies as st

from app.engine.exposure import interpolate_hourly, simulate_exposure
from app.schemas.family import FamilyMember
from app.schemas.routine import Activity, HomeSetup, Routine


@given(st.lists(st.integers(min_value=0, max_value=500), min_size=24, max_size=24))
def test_inhaled_total_never_decreases_when_outdoor_pm25_rises(pm25_values: list[int]) -> None:
    member = FamilyMember(age_group="adult")
    home = HomeSetup(
        heating="none", cooking="lpg", windows="mostly_closed", purifier=False, has_chimney=False
    )
    routine = Routine(
        activities=[
            Activity(
                label="Walk",
                start_hour=18,
                duration_min=40,
                place="outdoor",
                mode="walk",
                intensity="moderate",
                member_refs=[0],
            )
        ],
        home=home,
    )
    low = simulate_exposure(
        [float(value) for value in pm25_values], [150.0] * 24, [member], routine
    )
    high = simulate_exposure(
        [float(value + 50) for value in pm25_values], [150.0] * 24, [member], routine
    )
    assert low["total_before"] <= high["total_before"]


@given(
    st.lists(st.one_of(st.none(), st.floats(min_value=0, max_value=500)), min_size=1, max_size=24)
)
@settings(max_examples=50)
def test_interpolation_stays_within_known_neighbour_bounds(values: list[float | None]) -> None:
    filled, flags = interpolate_hourly(values)
    assert len(filled) == len(values)
    assert len(flags) == len(values)
    assert all(value >= 0 for value in filled)


def test_exposure_vehicle_and_interpolation_calculation() -> None:
    """Verify vehicle exposure calculation and empty interpolation."""
    from app.engine.exposure import _fill_missing_value, _interpolate_between, simulate_exposure
    from app.schemas.family import AgeGroup, FamilyMember
    from app.schemas.routine import (
        Activity,
        ActivityPlace,
        HomeSetup,
        Intensity,
        Routine,
        TravelMode,
    )

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

    vals, interp = interpolate_hourly([None, None])
    assert vals == [0.0, 0.0]
    assert interp == [True, True]

    assert interpolate_hourly([]) == ([], [])
    assert _interpolate_between(1, 0, 2, [None, 50.0, 100.0]) == 0.0
    assert _fill_missing_value(1, [0], [None]) == 0.0
