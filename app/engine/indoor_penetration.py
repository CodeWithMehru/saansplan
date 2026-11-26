"""Indoor concentration calculations with documented infiltration and source physics."""

from app.config import (
    INDOOR_SOURCE_INCREMENTS,
    INFILTRATION_CLOSED,
    INFILTRATION_OPEN,
    PURIFIER_FACTOR,
)
from app.models import HomeSetup

COOKING_SOURCE_INCREMENTS: dict[str, float] = {
    "wood_coal": INDOOR_SOURCE_INCREMENTS["biomass"],
    "lpg": INDOOR_SOURCE_INCREMENTS["lpg_cooking"],
    "induction": INDOOR_SOURCE_INCREMENTS["induction"],
}


def indoor_concentration(outdoor_pm25: float, home: HomeSetup) -> float:
    """Estimate indoor PM2.5 from infiltration and home source increments."""
    infiltration = INFILTRATION_OPEN if home.windows == "mostly_open" else INFILTRATION_CLOSED
    if home.purifier:
        infiltration *= PURIFIER_FACTOR

    heating_source = INDOOR_SOURCE_INCREMENTS["wood_coal"] if home.heating == "wood_coal" else 0.0
    cooking_source = COOKING_SOURCE_INCREMENTS.get(home.cooking, 0.0)
    return max(0.0, outdoor_pm25 * infiltration + heating_source + cooking_source)
