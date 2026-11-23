"""Winter smog multi-day forecast engine."""

from typing import Any

from app.core.aqi import indian_aqi_category

DAYTIME_AIRING_START_HOUR = 11
DAYTIME_AIRING_END_HOUR = 15
STAGNATION_WIND_THRESHOLD_MPS = 2.0


def analyze_forecast(
    pm25_hourly: list[float | None],
    wind_speed_hourly: list[float | None] | None = None,
    forecast_days: int = 5,
) -> list[dict[str, Any]]:
    """Analyze multi-day hourly forecast for smog windows, airing times, and stagnation.

    Sources:
    - Open-Meteo Air Quality API (hourly PM2.5).
    - Central Pollution Control Board (CPCB) NAQI category breakpoints.
    - Atmospheric boundary layer mixing: midday solar heating increases ventilation.
    """
    days: list[dict[str, Any]] = []
    total_hours = len(pm25_hourly)
    hours_per_day = 24

    for day_idx in range(min(forecast_days, (total_hours + hours_per_day - 1) // hours_per_day)):
        start_hour = day_idx * hours_per_day
        end_hour = min(start_hour + hours_per_day, total_hours)
        day_pm25_raw = pm25_hourly[start_hour:end_hour]

        if not day_pm25_raw:
            continue

        day_pm25 = [val if val is not None else 0.0 for val in day_pm25_raw]
        day_winds = []
        if wind_speed_hourly and len(wind_speed_hourly) >= end_hour:
            day_winds = [
                w if w is not None else 3.0 for w in wind_speed_hourly[start_hour:end_hour]
            ]

        avg_pm25 = sum(day_pm25) / len(day_pm25)
        max_pm25 = max(day_pm25)
        min_pm25 = min(day_pm25)

        # Worst 2-hour window
        worst_start = 0
        worst_sum = -1.0
        for h in range(len(day_pm25) - 1):
            window_sum = day_pm25[h] + day_pm25[h + 1]
            if window_sum > worst_sum:
                worst_sum = window_sum
                worst_start = h

        # Best 2-hour outdoor window
        best_start = 0
        best_sum = float("inf")
        for h in range(len(day_pm25) - 1):
            window_sum = day_pm25[h] + day_pm25[h + 1]
            if window_sum < best_sum:
                best_sum = window_sum
                best_start = h

        # Safest airing window: lowest 1-hour window during daytime (11:00 to 15:00)
        daytime_hours = [
            h
            for h in range(len(day_pm25))
            if DAYTIME_AIRING_START_HOUR <= h <= DAYTIME_AIRING_END_HOUR
        ]
        if daytime_hours:
            safest_hour = min(daytime_hours, key=lambda h: day_pm25[h])
        else:
            safest_hour = min(range(len(day_pm25)), key=lambda h: day_pm25[h])

        category_label, category_slug, _, approx_aqi = indian_aqi_category(max_pm25)

        # Stagnation indicator: surface wind < 2.0 m/s (~7.2 km/h) indicates severe trapping
        avg_wind = (sum(day_winds) / len(day_winds)) if day_winds else 2.5
        is_stagnant = avg_wind < STAGNATION_WIND_THRESHOLD_MPS

        days.append(
            {
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
        )

    return days
