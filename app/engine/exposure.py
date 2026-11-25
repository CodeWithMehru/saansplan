"""Deterministic per-hour family exposure simulation."""

from __future__ import annotations

from collections.abc import Sequence

from app.config import BREATHING_FACTORS, MEMBER_SENSITIVITY, VEHICLE_FACTOR
from app.core.aqi import indian_aqi_category
from app.engine.domain_models import ExposureResult, HourlyExposureRow, MemberExposure
from app.engine.indoor import indoor_concentration
from app.models import Activity, FamilyMember, Routine


def _interpolate_between(
    index: int, left_idx: int, right_idx: int, values: list[float | None]
) -> float:
    """Linearly interpolate value between two known indices."""
    left_val = values[left_idx]
    right_val = values[right_idx]
    if left_val is None or right_val is None:
        return 0.0
    span = right_idx - left_idx
    frac = (index - left_idx) / span
    return float(left_val) + (float(right_val) - float(left_val)) * frac


def _nearest_known(index: int, known: list[int]) -> tuple[int | None, int | None]:
    """Find left and right known indices around a target index."""
    left = [i for i in known if i < index]
    right = [i for i in known if i > index]
    return (left[-1] if left else None), (right[0] if right else None)


def _fill_missing_value(index: int, known: list[int], values: list[float | None]) -> float:
    """Fill a missing point from adjacent known endpoints."""
    left_idx, right_idx = _nearest_known(index, known)
    if left_idx is not None and right_idx is not None:
        return _interpolate_between(index, left_idx, right_idx, values)
    edge_idx = left_idx if left_idx is not None else right_idx
    if edge_idx is not None:
        val = values[edge_idx]
        return float(val) if val is not None else 0.0
    return 0.0


def interpolate_hourly(values: list[float | None]) -> tuple[list[float], list[bool]]:
    """Fill missing hourly values linearly and return flags for interpolated hours."""
    if not values:
        return [], []

    known = [i for i, v in enumerate(values) if v is not None]
    if not known:
        return [0.0] * len(values), [True] * len(values)

    result: list[float] = []
    interpolated: list[bool] = []
    for i, v in enumerate(values):
        if v is not None:
            result.append(float(v))
            interpolated.append(False)
        else:
            result.append(_fill_missing_value(i, known, values))
            interpolated.append(True)

    return result, interpolated


def _is_active_during_hour(activity: Activity, hour: int) -> bool:
    """Check if activity spans across the designated 24h clock hour."""
    end_hour = activity.start_hour + max(1, (activity.duration_min + 59) // 60)
    return activity.start_hour <= hour < end_hour


def _activity_concentration(activity: Activity, outdoor: float, indoor: float) -> float:
    """Select exposure concentration by activity microenvironment."""
    if activity.place == "outdoor":
        return outdoor
    if activity.place == "vehicle":
        return outdoor * VEHICLE_FACTOR
    return indoor


def _calculate_member_activity_exposure(
    activity: Activity, member: FamilyMember, outdoor: float, indoor: float
) -> float:
    """Compute inhaled dose for an active routine activity block."""
    conc = _activity_concentration(activity, outdoor, indoor)
    active_minutes = min(60, activity.duration_min)
    rate = BREATHING_FACTORS[activity.intensity.value]
    sens = MEMBER_SENSITIVITY[member.age_group.value]
    multiplier = 1.25 if member.sensitive else 1.0
    return conc * active_minutes * rate * sens * multiplier


def _compute_member_exposure_for_hour(
    member: FamilyMember,
    member_idx: int,
    routine: Routine,
    hour: int,
    concs: tuple[float, float],
) -> float:
    """Compute total exposure for a single member during one hour."""
    outdoor, indoor = concs
    base_exposure = indoor * 24 * MEMBER_SENSITIVITY[member.age_group.value]
    activity_exposure = 0.0
    has_activity = False

    for act in routine.activities:
        if member_idx in act.member_refs and _is_active_during_hour(act, hour):
            activity_exposure = _calculate_member_activity_exposure(act, member, outdoor, indoor)
            has_activity = True

    return activity_exposure if has_activity else base_exposure


def _compute_hour_exposures(
    members: Sequence[FamilyMember],
    routine: Routine,
    hour: int,
    outdoor: float,
) -> tuple[float, list[float]]:
    """Compute exposures for all members across one single hour."""
    indoor = indoor_concentration(outdoor, routine.home)
    concs = (outdoor, indoor)
    member_hour_exps: list[float] = []
    total_hour_exp = 0.0
    for m_idx, member in enumerate(members):
        m_exp = _compute_member_exposure_for_hour(member, m_idx, routine, hour, concs)
        member_hour_exps.append(m_exp)
        total_hour_exp += m_exp
    return total_hour_exp, member_hour_exps


def _build_hourly_row(
    hour: int,
    outdoor: float,
    raw_aqi: float | None,
    exposure_this_hour: float,
    is_interpolated: bool,
) -> HourlyExposureRow:
    """Construct a standardized hourly evaluation entry."""
    aqi = float(raw_aqi) if raw_aqi is not None else 0.0
    pm25_val = max(0.0, outdoor)
    indian_cat, _, _, indian_aqi = indian_aqi_category(pm25_val)
    return HourlyExposureRow(
        hour=hour,
        pm25=round(pm25_val, 1),
        aqi=int(max(0.0, aqi)),
        exposure=round(exposure_this_hour, 2),
        interpolated=is_interpolated,
        indian_aqi=indian_aqi,
        indian_category=indian_cat,
    )


def _simulate_day_hours(
    pm25: list[float],
    interpolated: list[bool],
    aqi_hourly: list[float | None],
    members: Sequence[FamilyMember],
    routine: Routine,
) -> tuple[list[HourlyExposureRow], list[float]]:
    """Simulate exposures across all 24 hours of the day."""
    hourly_rows: list[HourlyExposureRow] = []
    member_totals = [0.0 for _ in members]

    for hour in range(24):
        outdoor = pm25[hour] if hour < len(pm25) else 0.0
        exp_hour, m_exps = _compute_hour_exposures(members, routine, hour, outdoor)
        for i, val in enumerate(m_exps):
            member_totals[i] += val

        raw_aqi = aqi_hourly[hour] if hour < len(aqi_hourly) else None
        is_interp = interpolated[hour] if hour < len(interpolated) else True
        hourly_rows.append(_build_hourly_row(hour, outdoor, raw_aqi, exp_hour, is_interp))

    return hourly_rows, member_totals


def simulate_exposure(
    pm25_hourly: list[float | None],
    aqi_hourly: list[float | None],
    members: Sequence[FamilyMember],
    routine: Routine,
) -> ExposureResult:
    """Return per-hour and per-member exposure totals without network or AI calls."""
    pm25, interpolated = interpolate_hourly(pm25_hourly)
    hourly_rows, member_totals = _simulate_day_hours(
        pm25, interpolated, aqi_hourly, members, routine
    )
    peak = max(hourly_rows, key=lambda row: row.exposure)
    highest_aqi = max(hourly_rows, key=lambda row: row.pm25)
    return ExposureResult(
        total_before=round(sum(member_totals), 2),
        members=[
            MemberExposure(name=m.name or f"Member {i + 1}", exposure=round(member_totals[i], 2))
            for i, m in enumerate(members)
        ],
        hourly=hourly_rows,
        peak_hour=peak.hour,
        peak_aqi=peak.aqi,
        highest_aqi_hour=highest_aqi.hour,
        highest_aqi=highest_aqi.indian_aqi,
        estimate_label="All values are estimates",
    )
