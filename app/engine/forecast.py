"""Winter smog multi-day forecast engine."""

from typing import Any

from app.core.aqi import indian_aqi_category

DAYTIME_AIRING_START_HOUR = 11
DAYTIME_AIRING_END_HOUR = 15
STAGNATION_WIND_THRESHOLD_MPS = 2.0
HOURS_PER_DAY = 24


def _find_extrema_windows(day_pm25: list[float]) -> tuple[int, int]:
    """Identify starting hours for the worst and best 2-hour exposure windows."""
    worst_start = 0
    worst_sum = -1.0
    best_start = 0
    best_sum = float("inf")

    for h in range(len(day_pm25) - 1):
        window_sum = day_pm25[h] + day_pm25[h + 1]
        if window_sum > worst_sum:
            worst_sum = window_sum
            worst_start = h
        if window_sum < best_sum:
            best_sum = window_sum
            best_start = h

    return worst_start, best_start


def _find_safest_airing_hour(day_pm25: list[float]) -> int:
    """Find the lowest PM2.5 hour during midday boundary layer ventilation (11:00-15:00)."""
    daytime_hours = [
        h for h in range(len(day_pm25)) if DAYTIME_AIRING_START_HOUR <= h <= DAYTIME_AIRING_END_HOUR
    ]
    if daytime_hours:
        return min(daytime_hours, key=lambda h: day_pm25[h])
    return min(range(len(day_pm25)), key=lambda h: day_pm25[h])


def _calculate_stagnation(day_winds: list[float]) -> tuple[bool, float]:
    """Assess whether surface winds fall below the 2.0 m/s stagnation inversion threshold."""
    avg_wind = (sum(day_winds) / len(day_winds)) if day_winds else 2.5
    is_stagnant = avg_wind < STAGNATION_WIND_THRESHOLD_MPS
    return is_stagnant, avg_wind


def _analyze_single_day(
    day_idx: int, day_pm25: list[float], day_winds: list[float]
) -> dict[str, Any]:
    """Evaluate smog patterns, ventilation windows, and severity for a single day."""
    avg_pm25 = sum(day_pm25) / len(day_pm25)
    max_pm25 = max(day_pm25)
    min_pm25 = min(day_pm25)

    worst_start, best_start = _find_extrema_windows(day_pm25)
    safest_hour = _find_safest_airing_hour(day_pm25)
    is_stagnant, avg_wind = _calculate_stagnation(day_winds)
    category_label, category_slug, _, approx_aqi = indian_aqi_category(max_pm25)

    return {
        "day_index": day_idx,
        "avg_pm25": round(avg_pm25, 1),
        "max_pm25": round(max_pm25, 1),
        "min_pm25": round(min_pm25, 1),
        "peak_aqi": approx_aqi,
        "indian_category": category_label,
        "category_slug": category_slug,
        "is_severe": category_slug in ("severe", "very-poor"),
        "worst_window": {"start_hour": worst_start, "end_hour": worst_start + 2},
        "best_window": {"start_hour": best_start, "end_hour": best_start + 2},
        "safest_airing_hour": safest_hour,
        "is_stagnant": is_stagnant,
        "avg_wind_speed_mps": round(avg_wind, 1),
    }


def _extract_day_data(
    day_idx: int,
    pm25_hourly: list[float | None],
    wind_speed_hourly: list[float | None] | None,
) -> tuple[list[float], list[float]] | None:
    """Extract PM2.5 and wind values for a 24-hour day slice."""
    start = day_idx * HOURS_PER_DAY
    end = min(start + HOURS_PER_DAY, len(pm25_hourly))
    raw_pm25 = pm25_hourly[start:end]
    if not raw_pm25:
        return None
    day_pm25 = [v if v is not None else 0.0 for v in raw_pm25]
    day_winds = []
    if wind_speed_hourly and len(wind_speed_hourly) >= end:
        day_winds = [w if w is not None else 3.0 for w in wind_speed_hourly[start:end]]
    return day_pm25, day_winds


def analyze_forecast(
    pm25_hourly: list[float | None],
    wind_speed_hourly: list[float | None] | None = None,
    forecast_days: int = 5,
) -> list[dict[str, Any]]:
    """Analyze multi-day hourly forecast for smog windows, airing times, and stagnation."""
    days: list[dict[str, Any]] = []
    total_hours = len(pm25_hourly)
    max_days = min(forecast_days, (total_hours + HOURS_PER_DAY - 1) // HOURS_PER_DAY)

    for day_idx in range(max_days):
        day_data = _extract_day_data(day_idx, pm25_hourly, wind_speed_hourly)
        if day_data is None:
            continue
        day_pm25, day_winds = day_data
        days.append(_analyze_single_day(day_idx, day_pm25, day_winds))

    return days
