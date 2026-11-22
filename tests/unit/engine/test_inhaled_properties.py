"""Property tests for physical-unit inhalation estimates."""

from hypothesis import given
from hypothesis import strategies as st

from app.engine.inhaled import inhaled_micrograms, uncertainty_band


@given(
    low=st.floats(min_value=0, max_value=500),
    high=st.floats(min_value=0, max_value=500),
)
def test_total_inhaled_never_decreases_when_outdoor_pm25_rises(low: float, high: float) -> None:
    low_intake = inhaled_micrograms(min(low, high), 30, "moderate", "adult")
    high_intake = inhaled_micrograms(max(low, high), 30, "moderate", "adult")
    assert low_intake <= high_intake


@given(
    concentration=st.floats(min_value=0, max_value=1000),
    minutes=st.integers(min_value=1, max_value=720),
)
def test_uncertainty_band_contains_estimate(concentration: float, minutes: int) -> None:
    estimate = inhaled_micrograms(concentration, minutes, "light", "adult")
    low, high = uncertainty_band(estimate)
    if estimate == 0:
        assert low == high == 0
        return
    assert low <= estimate <= high
