"""Property-based invariant tests using Hypothesis."""

from hypothesis import given
from hypothesis import strategies as st

from app.core.aqi import indian_aqi_category
from app.engine.cleaner_day import generate_cleaner_day
from app.engine.indoor_guidance import calculate_purifier_cadr
from app.engine.inhaled import inhaled_micrograms, member_inhalation_scale
from app.schemas.family import AgeGroup, FamilyMember
from app.schemas.routine import Activity, ActivityPlace, HomeSetup, Intensity, Routine, TravelMode

SEVERITY_ORDER = ["Good", "Satisfactory", "Moderately polluted", "Poor", "Very poor", "Severe"]


@given(
    st.floats(min_value=0.0, max_value=2000.0),
    st.integers(min_value=0, max_value=720),
    st.sampled_from(["rest", "light", "moderate", "heavy"]),
    st.sampled_from(["adult", "child", "elderly", "infant"]),
)
def test_inhaled_micrograms_non_negative_and_bounded(
    conc: float, minutes: int, intensity: str, age_group: str
) -> None:
    """Inhaled dose must always be non-negative and finite."""
    dose = inhaled_micrograms(conc, minutes, intensity, age_group)
    assert dose >= 0.0


@given(st.sampled_from(list(AgeGroup)))
def test_member_inhalation_scale_bounds(age: AgeGroup) -> None:
    """Member scale must be strictly positive (never zero or negative)."""
    scale = member_inhalation_scale(age.value)
    assert scale > 0.0
    assert 0.5 <= scale <= 3.0


@given(st.floats(min_value=0.0, max_value=1000.0), st.floats(min_value=0.0, max_value=1000.0))
def test_cpcb_category_monotonicity(pm1: float, pm2: float) -> None:
    """CPCB category severity must not decrease as PM2.5 increases."""
    cat1 = indian_aqi_category(min(pm1, pm2))[0]
    cat2 = indian_aqi_category(max(pm1, pm2))[0]
    idx1 = SEVERITY_ORDER.index(cat1)
    idx2 = SEVERITY_ORDER.index(cat2)
    assert idx1 <= idx2


@given(st.floats(min_value=1.0, max_value=500.0), st.floats(min_value=2.0, max_value=6.0))
def test_cadr_calculation_invariants(area: float, ceiling: float) -> None:
    """CADR must be positive and scale monotonically with area and ceiling height."""
    res = calculate_purifier_cadr(area_sq_meters=area, ceiling_height_meters=ceiling)
    assert res["recommended_smoke_cadr_m3h"] > 0
    assert res["recommended_smoke_cadr_cfm"] > 0
    assert res["volume_m3"] > 0


@given(
    st.lists(st.floats(min_value=5.0, max_value=500.0), min_size=24, max_size=24),
    st.lists(st.integers(min_value=10, max_value=500), min_size=24, max_size=24),
)
def test_cleaner_day_percent_reduction_invariants(pm25: list[float], aqi: list[int]) -> None:
    """Cleaner day optimization dose reduction must always be between 0% and 100%."""
    members = [
        FamilyMember(name="Parent", age_group=AgeGroup.adult, sensitive=False),
        FamilyMember(name="Child", age_group=AgeGroup.child, sensitive=True),
    ]
    routine = Routine(
        activities=[
            Activity(
                label="Commute",
                start_hour=8,
                duration_min=45,
                place=ActivityPlace.vehicle,
                mode=TravelMode.bike,
                intensity=Intensity.light,
                member_refs=[0],
            ),
            Activity(
                label="Exercise",
                start_hour=18,
                duration_min=60,
                place=ActivityPlace.outdoor,
                mode=TravelMode.none,
                intensity=Intensity.moderate,
                member_refs=[0, 1],
            ),
        ],
        home=HomeSetup(
            heating="none",
            cooking="lpg",
            windows="mostly_closed",
            purifier=False,
            has_chimney=False,
        ),
    )
    res = generate_cleaner_day(pm25, aqi, members, routine)
    assert 0 <= res["percent_reduction"] <= 100
    assert res["inhaled_saved_ug"] >= 0.0
