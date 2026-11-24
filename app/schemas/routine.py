"""Daily activity, commute mode, and home setup schemas."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MIN_PRINTABLE_ASCII = 32


class ActivityPlace(str, Enum):
    """Micro-environment category where an activity takes place."""

    outdoor = "outdoor"
    indoor = "indoor"
    vehicle = "vehicle"


class TravelMode(str, Enum):
    """Transportation modality used during transit activities."""

    walk = "walk"
    cycle = "cycle"
    bike = "bike"
    car = "car"
    bus = "bus"
    metro = "metro"
    none = "none"


class Intensity(str, Enum):
    """Physical exertion intensity affecting minute ventilation rate."""

    rest = "rest"
    light = "light"
    moderate = "moderate"
    heavy = "heavy"


class Activity(BaseModel):
    """Structured discrete schedule block for family routine exposure tracking."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(max_length=60)
    start_hour: int = Field(ge=0, le=23)
    duration_min: int = Field(ge=1, le=720)
    place: ActivityPlace
    mode: TravelMode
    intensity: Intensity
    member_refs: list[int] = Field(min_length=1, max_length=12)

    @field_validator("label")
    @classmethod
    def no_control_chars(cls, value: str) -> str:
        """Reject unprintable ASCII control characters."""
        if any(ord(char) < MIN_PRINTABLE_ASCII for char in value):
            raise ValueError("Control characters are not allowed")
        return value.strip()


class HomeSetup(BaseModel):
    """Residential baseline factors dictating indoor infiltration and emission sources."""

    model_config = ConfigDict(extra="forbid")

    heating: Literal["none", "electric", "wood_coal", "gas", "other"]
    cooking: Literal["lpg", "induction", "wood_coal", "other"]
    windows: Literal["mostly_open", "mostly_closed"]
    purifier: bool
    has_chimney: bool


class Routine(BaseModel):
    """Full family daily schedule and residential characteristics."""

    model_config = ConfigDict(extra="forbid")

    activities: list[Activity] = Field(max_length=24)
    home: HomeSetup
    unclear: list[str] = Field(default_factory=list, max_length=12)
