"""Candidate swap generation and ranking."""

from copy import deepcopy

from app.config import TOP_SWAP_LIMIT
from app.engine.exposure import interpolate_hourly, simulate_exposure


def reduce_fraction(before: float, after: float) -> float:
    """Return percentage reduction for a pair of exposure estimates."""
    if before <= 0:
        return 0.0
    return round(max(0.0, (before - after) / before * 100.0), 1)


def generate_swaps(
    pm25_hourly: list[float | None],
    aqi_hourly: list[float | None],
    members: list[object],
    routine: object,
) -> list[dict]:
    """Generate and rank practical low-exposure, lower-emission swaps."""
    baseline = simulate_exposure(pm25_hourly, aqi_hourly, members, routine)
    pm25, _ = interpolate_hourly(pm25_hourly)
    candidates: list[dict] = []

    outdoor_activities = [
        activity for activity in routine.activities if activity.place == "outdoor"
    ]
    for activity in outdoor_activities:
        valid_hours = [hour for hour in range(24) if hour != activity.start_hour]
        cleaner = min(valid_hours, key=lambda hour: pm25[hour] if hour < len(pm25) else 0.0)
        changed = deepcopy(routine)
        target = next(item for item in changed.activities if item.label == activity.label)
        target.start_hour = cleaner
        reduced = simulate_exposure(pm25_hourly, aqi_hourly, members, changed)
        candidates.append(
            {
                "key": "shift_activity",
                "description_key": "swap_shift",
                "from_hour": activity.start_hour,
                "to_hour": cleaner,
                "exposure_before": baseline["total_before"],
                "exposure_after": reduced["total_before"],
                "percent_reduction": reduce_fraction(
                    baseline["total_before"], reduced["total_before"]
                ),
                "emissions_note": (
                    "Estimated: no added fuel use; walking or cycling may avoid vehicle emissions."
                ),
            }
        )

    close_changed = deepcopy(routine)
    close_changed.home.windows = "mostly_closed"
    closed = simulate_exposure(pm25_hourly, aqi_hourly, members, close_changed)
    candidates.append(
        {
            "key": "close_windows",
            "description_key": "swap_windows",
            "exposure_before": baseline["total_before"],
            "exposure_after": closed["total_before"],
            "percent_reduction": reduce_fraction(baseline["total_before"], closed["total_before"]),
            "emissions_note": (
                "Estimated: lower infiltration can reduce exposure; open windows "
                "for indoor safety ventilation when smoke is lower."
            ),
        }
    )

    purifier_changed = deepcopy(routine)
    purifier_changed.home.purifier = True
    purified = simulate_exposure(pm25_hourly, aqi_hourly, members, purifier_changed)
    candidates.append(
        {
            "key": "run_purifier",
            "description_key": "swap_purifier",
            "exposure_before": baseline["total_before"],
            "exposure_after": purified["total_before"],
            "percent_reduction": reduce_fraction(
                baseline["total_before"], purified["total_before"]
            ),
            "emissions_note": (
                "Estimated: electricity use varies; use a clean, correctly sized purifier."
            ),
        }
    )

    induction_changed = deepcopy(routine)
    induction_changed.home.cooking = "induction"
    induction = simulate_exposure(pm25_hourly, aqi_hourly, members, induction_changed)
    candidates.append(
        {
            "key": "cook_induction",
            "description_key": "swap_cooking",
            "exposure_before": baseline["total_before"],
            "exposure_after": induction["total_before"],
            "percent_reduction": reduce_fraction(
                baseline["total_before"], induction["total_before"]
            ),
            "emissions_note": (
                "Estimated: induction avoids direct biomass combustion, subject to local grid mix."
            ),
        }
    )

    candidates = [item for item in candidates if item["percent_reduction"] > 0]
    candidates.sort(key=lambda item: item["percent_reduction"], reverse=True)
    return candidates[:TOP_SWAP_LIMIT]
