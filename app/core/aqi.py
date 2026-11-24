"""India PM2.5 National AQI category helpers."""

from app.core.constants import CPCB_PM25_BREAKPOINTS


def indian_aqi_category(pm25_ug_m3: float) -> tuple[str, str, int, int]:
    """Return CPCB category, slug, and approximate AQI band for an hourly PM2.5 value."""
    pm25 = max(0.0, float(round(pm25_ug_m3)))
    for pm_low, pm_high, aq_low, aq_high, label, slug in CPCB_PM25_BREAKPOINTS:
        if pm_low <= pm25 <= pm_high:
            if pm_high == pm_low:
                aq = aq_low
            else:
                aq = round(aq_low + (pm25 - pm_low) * (aq_high - aq_low) / (pm_high - pm_low))
            return label, slug, aq_low, aq
    return "Severe", "severe", 401, 500
