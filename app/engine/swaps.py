"""Candidate swap generation and ranking."""

from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy

from app.config import TOP_SWAP_LIMIT
from app.engine.domain_models import ExposureResult, SwapRecommendation
from app.engine.exposure import interpolate_hourly, simulate_exposure
from app.models import Activity, FamilyMember, Routine


def reduce_fraction(before: float, after: float) -> float:
    """Return percentage reduction for a pair of exposure estimates."""
    if before <= 0:
        return 0.0
    return round(max(0.0, (before - after) / before * 100.0), 1)


SimContext = tuple[list[float | None], list[float | None], Sequence[FamilyMember]]


def _find_cleanest_alternate_hour(current_hour: int, pm25: list[float]) -> int:
    """Identify the hour of the day with lowest PM2.5 excluding current hour."""
    cleanest_hour = 0
    lowest_pm = float("inf")
    for hour in range(24):
        if hour == current_hour:
            continue
        level = pm25[hour] if hour < len(pm25) else 0.0
        if level < lowest_pm:
            lowest_pm = level
            cleanest_hour = hour
    return cleanest_hour


def _shift_activity_start_hour(routine: Routine, label: str, new_hour: int) -> Routine:
    """Create routine copy with designated activity shifted to new start hour."""
    changed = deepcopy(routine)
    for act in changed.activities:
        if act.label == label:
            act.start_hour = new_hour
            break
    return changed


def _evaluate_outdoor_shift(
    activity: Activity,
    sim_ctx: SimContext,
    routine: Routine,
    baseline: ExposureResult,
    pm25: list[float],
) -> SwapRecommendation:
    """Evaluate shifting one outdoor activity to the lowest-pollution hour of the day."""
    pm25_hourly, aqi_hourly, members = sim_ctx
    cleaner = _find_cleanest_alternate_hour(activity.start_hour, pm25)
    changed = _shift_activity_start_hour(routine, activity.label, cleaner)
    reduced = simulate_exposure(pm25_hourly, aqi_hourly, members, changed)
    return SwapRecommendation(
        key="shift_activity",
        description_key="swap_shift",
        from_hour=activity.start_hour,
        to_hour=cleaner,
        exposure_before=baseline.total_before,
        exposure_after=reduced.total_before,
        percent_reduction=reduce_fraction(baseline.total_before, reduced.total_before),
        emissions_note=(
            "Estimated: no added fuel use; walking or cycling may avoid vehicle emissions."
        ),
    )


def _generate_outdoor_swaps(
    sim_ctx: SimContext,
    routine: Routine,
    baseline: ExposureResult,
    pm25: list[float],
) -> list[SwapRecommendation]:
    """Generate shift candidates for all outdoor activities."""
    outdoor_acts = [act for act in routine.activities if act.place == "outdoor"]
    return [_evaluate_outdoor_shift(act, sim_ctx, routine, baseline, pm25) for act in outdoor_acts]


def _generate_home_swaps(
    pm25_hourly: list[float | None],
    aqi_hourly: list[float | None],
    members: Sequence[FamilyMember],
    routine: Routine,
    baseline: ExposureResult,
) -> list[SwapRecommendation]:
    """Generate structural home intervention swaps (windows, purifier, cooking)."""
    swaps: list[SwapRecommendation] = []

    # Window closure
    close_changed = deepcopy(routine)
    close_changed.home.windows = "mostly_closed"
    closed = simulate_exposure(pm25_hourly, aqi_hourly, members, close_changed)
    swaps.append(
        SwapRecommendation(
            key="close_windows",
            description_key="swap_windows",
            exposure_before=baseline.total_before,
            exposure_after=closed.total_before,
            percent_reduction=reduce_fraction(baseline.total_before, closed.total_before),
            emissions_note=(
                "Estimated: lower infiltration can reduce exposure; open windows "
                "for indoor safety ventilation when smoke is lower."
            ),
        )
    )

    # Purifier activation
    purifier_changed = deepcopy(routine)
    purifier_changed.home.purifier = True
    purified = simulate_exposure(pm25_hourly, aqi_hourly, members, purifier_changed)
    swaps.append(
        SwapRecommendation(
            key="run_purifier",
            description_key="swap_purifier",
            exposure_before=baseline.total_before,
            exposure_after=purified.total_before,
            percent_reduction=reduce_fraction(baseline.total_before, purified.total_before),
            emissions_note=(
                "Estimated: electricity use varies; use a clean, correctly sized purifier."
            ),
        )
    )

    # Induction cooking
    induction_changed = deepcopy(routine)
    induction_changed.home.cooking = "induction"
    induction = simulate_exposure(pm25_hourly, aqi_hourly, members, induction_changed)
    swaps.append(
        SwapRecommendation(
            key="cook_induction",
            description_key="swap_cooking",
            exposure_before=baseline.total_before,
            exposure_after=induction.total_before,
            percent_reduction=reduce_fraction(baseline.total_before, induction.total_before),
            emissions_note=(
                "Estimated: induction avoids direct biomass combustion, subject to local grid mix."
            ),
        )
    )
    return swaps


def generate_swaps(
    pm25_hourly: list[float | None],
    aqi_hourly: list[float | None],
    members: Sequence[FamilyMember],
    routine: Routine,
) -> list[SwapRecommendation]:
    """Generate and rank practical low-exposure, lower-emission swaps."""
    baseline = simulate_exposure(pm25_hourly, aqi_hourly, members, routine)
    pm25, _ = interpolate_hourly(pm25_hourly)

    sim_ctx = (pm25_hourly, aqi_hourly, members)
    candidates = _generate_outdoor_swaps(sim_ctx, routine, baseline, pm25) + _generate_home_swaps(
        pm25_hourly, aqi_hourly, members, routine, baseline
    )

    positive_candidates = [item for item in candidates if item.percent_reduction > 0]
    positive_candidates.sort(key=lambda item: item.percent_reduction, reverse=True)
    return positive_candidates[:TOP_SWAP_LIMIT]
