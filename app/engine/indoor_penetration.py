"""Indoor concentration calculations with documented infiltration and source physics."""

from app.config import (
    INDOOR_SOURCE_INCREMENTS,
    INFILTRATION_CLOSED,
    INFILTRATION_OPEN,
    PURIFIER_FACTOR,
)
from app.models import HomeSetup


def indoor_concentration(outdoor_pm25: float, home: HomeSetup) -> float:
    """Estimate indoor PM2.5 from infiltration and home source increments."""
    infiltration = INFILTRATION_OPEN if home.windows == "mostly_open" else INFILTRATION_CLOSED
    if home.purifier:
        infiltration *= PURIFIER_FACTOR

    source = 0.0
    if home.heating == "wood_coal":
        source += INDOOR_SOURCE_INCREMENTS["wood_coal"]
    if home.cooking == "wood_coal":
        source += INDOOR_SOURCE_INCREMENTS["biomass"]
    elif home.cooking == "lpg":
        source += INDOOR_SOURCE_INCREMENTS["lpg_cooking"]
    elif home.cooking == "induction":
        source += INDOOR_SOURCE_INCREMENTS["induction"]
    return max(0.0, outdoor_pm25 * infiltration + source)
