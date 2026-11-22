"""Physical-unit PM2.5 inhaled-intake estimates."""

from app.core.constants import CHILD_INHALATION_SCALE, ELDERLY_INHALATION_SCALE, VENTILATION_L_MIN


def member_inhalation_scale(age_group: str) -> float:
    """Return a conservative planning ventilation scale for a member age group."""
    if age_group == "child":
        return CHILD_INHALATION_SCALE
    if age_group == "elderly":
        return ELDERLY_INHALATION_SCALE
    return 1.0


def inhaled_micrograms(
    concentration_ug_m3: float, minutes: int, intensity: str, age_group: str
) -> float:
    """Estimate inhaled PM2.5 in micrograms using concentration and ventilation rate."""
    litres_per_minute = VENTILATION_L_MIN.get(intensity, VENTILATION_L_MIN["rest"])
    cubic_metres = litres_per_minute * minutes * member_inhalation_scale(age_group) / 1000.0
    return max(0.0, concentration_ug_m3 * cubic_metres)


def uncertainty_band(value_ug: float) -> tuple[float, float]:
    """Return a clearly labelled planning range of roughly ±25% around an estimate."""
    estimate = max(0.0, value_ug)
    return round(estimate * 0.75, 2), round(estimate * 1.25, 2)
