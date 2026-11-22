"""Deterministic per-hour family exposure simulation."""

from collections.abc import Sequence
from typing import Any

from app.config import BREATHING_FACTORS, MEMBER_SENSITIVITY, VEHICLE_FACTOR
from app.engine.indoor import indoor_concentration
from app.models import FamilyMember, Routine


def interpolate_hourly(values: list[float | None]) -> tuple[list[float], list[bool]]:
    """Fill missing hourly values linearly and return flags for interpolated hours."""
    result = [float(value) if value is not None else 0.0 for value in values]
    interpolated = [value is None for value in values]
    if not values:
        return result, interpolated

    known = [index for index, value in enumerate(values) if value is not None]
    if not known:
        return [0.0] * len(values), [True] * len(values)

    for index in range(len(result)):
        if values[index] is not None:
            continue
        left = [item for item in known if item < index]
        right = [item for item in known if item > index]
        if left and right:
            left_index, right_index = left[-1], right[0]
            span = right_index - left_index
            left_value_raw = values[left_index]
            right_value_raw = values[right_index]
            if left_value_raw is None or right_value_raw is None:
                continue
            left_value = float(left_value_raw)
            right_value = float(right_value_raw)
            result[index] = left_value + (right_value - left_value) * ((index - left_index) / span)
        elif left:
            raw = values[left[-1]]
            if raw is not None:
                result[index] = float(raw)
        elif right:
            raw = values[right[0]]
            if raw is not None:
                result[index] = float(raw)
    return result, interpolated


def simulate_exposure(
    pm25_hourly: list[float | None],
    aqi_hourly: list[float | None],
    members: Sequence[FamilyMember],
    routine: Routine,
) -> dict[str, Any]:
    """Return per-hour and per-member exposure totals without network or AI calls."""
    pm25, interpolated = interpolate_hourly(pm25_hourly)
    hourly_rows: list[dict[str, Any]] = []
    member_totals = [0.0 for _ in members]

    for hour in range(24):
        outdoor = pm25[hour] if hour < len(pm25) else 0.0
        indoor = indoor_concentration(outdoor, routine.home)
        raw_aqi = aqi_hourly[hour] if hour < len(aqi_hourly) else None
        aqi = float(raw_aqi) if raw_aqi is not None else 0.0
        exposure_this_hour = 0.0

        for member_index, member in enumerate(members):
            member_exposure = indoor * 24 * MEMBER_SENSITIVITY[member.age_group.value]
            for activity in routine.activities:
                if member_index not in activity.member_refs:
                    continue
                if (
                    activity.start_hour
                    <= hour
                    < activity.start_hour + max(1, (activity.duration_min + 59) // 60)
                ):
                    if activity.place == "outdoor":
                        concentration = outdoor
                    elif activity.place == "vehicle":
                        concentration = outdoor * VEHICLE_FACTOR
                    else:
                        concentration = indoor
                    active_minutes = min(60, activity.duration_min)
                    member_exposure = (
                        concentration
                        * active_minutes
                        * BREATHING_FACTORS[activity.intensity.value]
                        * MEMBER_SENSITIVITY[member.age_group.value]
                        * (1.0 + (0.25 if member.sensitive else 0.0))
                    )
            member_totals[member_index] += member_exposure
            exposure_this_hour += member_exposure

        hourly_rows.append(
            {
                "hour": hour,
                "pm25": round(max(0.0, pm25[hour] if hour < len(pm25) else 0.0), 1),
                "aqi": int(max(0.0, aqi)),
                "exposure": round(exposure_this_hour, 2),
                "interpolated": interpolated[hour] if hour < len(interpolated) else True,
            }
        )

    total = round(sum(member_totals), 2)
    peak = max(hourly_rows, key=lambda row: row["exposure"])
    return {
        "total_before": total,
        "members": [
            {"name": member.name, "exposure": round(member_totals[index], 2)}
            for index, member in enumerate(members)
        ],
        "hourly": hourly_rows,
        "peak_hour": peak["hour"],
        "peak_aqi": peak["aqi"],
        "estimate_label": "All values are estimates",
    }
