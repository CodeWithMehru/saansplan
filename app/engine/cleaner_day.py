"""Your Cleaner Day: Full alternative daily routine generator."""

from __future__ import annotations

from copy import deepcopy

from app.core.aqi import indian_aqi_category
from app.core.constants import HOURS_IN_DAY
from app.engine.domain_models import CleanerDayHourlyRow, CleanerDayResult, ExposureResult
from app.engine.exposure import interpolate_hourly, simulate_exposure
from app.engine.inhaled import inhaled_micrograms, uncertainty_band
from app.models import Activity, FamilyMember, Routine


def is_fixed_commitment(activity: Activity) -> bool:
    """Check if an activity has rigid timing (work, school, hospital)."""
    text = activity.label.lower()
    fixed_keywords = ("school", "office", "work", "class", "duty", "shift", "exam", "doctor")
    return any(keyword in text for keyword in fixed_keywords)


def _optimize_activities(
    routine: Routine, pm25: list[float], cleanest_hour: int
) -> list[dict[str, str | int | float]]:
    """Shift flexible outdoor activities to cleaner daytime hours."""
    changes: list[dict[str, str | int | float]] = []
    for act in routine.activities:
        if act.place == "outdoor" and not is_fixed_commitment(act):
            orig_h = act.start_hour
            if pm25[orig_h] > pm25[cleanest_hour] * 1.15:
                act.start_hour = cleanest_hour
                reduction = round((pm25[orig_h] - pm25[cleanest_hour]) / pm25[orig_h] * 100, 1)
                changes.append(
                    {
                        "activity": act.label,
                        "from_hour": orig_h,
                        "to_hour": cleanest_hour,
                        "reason_key": "shifted_to_cleaner_afternoon",
                        "reason": (
                            f"Shifted {act.label} from {orig_h}:00 to {cleanest_hour}:00 "
                            f"lowering outdoor PM2.5 by ~{reduction}%."
                        ),
                    }
                )
    return changes


def _optimize_home(routine: Routine) -> list[dict[str, str | int | float]]:
    """Apply indoor interventions (window closure, purifier, induction)."""
    changes: list[dict[str, str | int | float]] = []
    if routine.home.windows == "mostly_open":
        routine.home.windows = "mostly_closed"
        changes.append(
            {
                "activity": "Windows",
                "reason_key": "windows_closed_smog",
                "reason": "Keep windows closed during winter smog; open briefly at midday.",
            }
        )

    if not routine.home.purifier:
        routine.home.purifier = True
        changes.append(
            {
                "activity": "Purifier",
                "reason_key": "purifier_activated",
                "reason": "Activate indoor HEPA or supplemental filtration in living areas.",
            }
        )

    if routine.home.cooking in ("wood_coal", "other"):
        routine.home.cooking = "induction"
        changes.append(
            {
                "activity": "Cooking",
                "reason_key": "switched_to_induction",
                "reason": "Replaced smoky solid fuel with clean induction to eliminate smoke.",
            }
        )
    return changes


def _activity_dose_for_members(act: Activity, conc: float, members: list[FamilyMember]) -> float:
    """Calculate cumulative inhaled dose for all referenced family members."""
    dose = 0.0
    for m_idx in act.member_refs:
        if m_idx < len(members):
            m = members[m_idx]
            dose += inhaled_micrograms(
                conc, act.duration_min, act.intensity.value, m.age_group.value
            )
    return dose


def _compute_inhaled_dose(
    routine: Routine, members: list[FamilyMember], pm25: list[float]
) -> float:
    """Compute estimated total inhaled PM2.5 dose in micrograms for all activities."""
    total_ug = 0.0
    for act in routine.activities:
        penetration = 0.25 if routine.home.purifier else 0.5
        act_pm25 = pm25[act.start_hour]
        conc = act_pm25 if act.place == "outdoor" else act_pm25 * penetration
        total_ug += _activity_dose_for_members(act, conc, members)
    return total_ug


def _build_hourly_comparison(
    pm25: list[float], baseline: ExposureResult, optimized: ExposureResult
) -> list[CleanerDayHourlyRow]:
    """Build side-by-side hourly comparison rows."""
    comparison: list[CleanerDayHourlyRow] = []
    for h in range(HOURS_IN_DAY):
        b_exp = baseline.hourly[h].exposure
        o_exp = optimized.hourly[h].exposure
        cat_label, cat_slug, _, aqi = indian_aqi_category(pm25[h])
        comparison.append(
            CleanerDayHourlyRow(
                hour=h,
                pm25=pm25[h],
                aqi=aqi,
                category=cat_label,
                category_slug=cat_slug,
                exposure_before=b_exp,
                exposure_after=o_exp,
                difference=round(b_exp - o_exp, 2),
            )
        )
    return comparison


def generate_cleaner_day(
    pm25_hourly: list[float | None],
    aqi_hourly: list[float | None],
    members: list[FamilyMember],
    routine: Routine,
) -> CleanerDayResult:
    """Generate an optimized 24-hour routine shifting flexible activities to cleaner hours."""
    pm25, _ = interpolate_hourly(pm25_hourly)
    baseline = simulate_exposure(pm25_hourly, aqi_hourly, members, routine)

    cleanest_h = min(range(11, 16), key=lambda h: pm25[h] if h < len(pm25) else 999.0)
    opt_routine = deepcopy(routine)

    changes = _optimize_activities(opt_routine, pm25, cleanest_h)
    changes.extend(_optimize_home(opt_routine))

    optimized = simulate_exposure(pm25_hourly, aqi_hourly, members, opt_routine)

    base_dose = _compute_inhaled_dose(routine, members, pm25)
    opt_dose = _compute_inhaled_dose(opt_routine, members, pm25)

    base_total = baseline.total_before
    opt_total = optimized.total_before
    reduction_pct = round((base_total - opt_total) / base_total * 100, 1) if base_total > 0 else 0.0

    inhaled_saved = max(0.0, base_dose - opt_dose)
    low_ug, high_ug = uncertainty_band(inhaled_saved)

    hourly_comparison = _build_hourly_comparison(pm25, baseline, optimized)

    return CleanerDayResult(
        changes=changes,
        total_exposure_before=base_total,
        total_exposure_after=opt_total,
        percent_reduction=reduction_pct,
        inhaled_saved_ug=round(inhaled_saved, 1),
        inhaled_saved_range_ug=(round(low_ug, 1), round(high_ug, 1)),
        hourly_comparison=hourly_comparison,
        routine=opt_routine,
    )
