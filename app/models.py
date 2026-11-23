"""Pydantic request and strict response models."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgeGroup(str, Enum):
    child = "child"
    adult = "adult"
    elderly = "elderly"


class FamilyMember(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=40)
    age_group: AgeGroup
    sensitive: bool = False


class ActivityPlace(str, Enum):
    outdoor = "outdoor"
    indoor = "indoor"
    vehicle = "vehicle"


class TravelMode(str, Enum):
    walk = "walk"
    cycle = "cycle"
    bike = "bike"
    car = "car"
    bus = "bus"
    metro = "metro"
    none = "none"


class Intensity(str, Enum):
    rest = "rest"
    light = "light"
    moderate = "moderate"
    heavy = "heavy"


class Activity(BaseModel):
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
        if any(ord(char) < 32 for char in value):
            raise ValueError("Control characters are not allowed")
        return value.strip()


class HomeSetup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heating: Literal["none", "electric", "wood_coal", "gas", "other"]
    cooking: Literal["lpg", "induction", "wood_coal", "other"]
    windows: Literal["mostly_open", "mostly_closed"]
    purifier: bool
    has_chimney: bool


class Routine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activities: list[Activity] = Field(max_length=24)
    home: HomeSetup
    unclear: list[str] = Field(default_factory=list, max_length=12)


class PlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    city: str | None = Field(default=None, max_length=80)
    members: list[FamilyMember] = Field(min_length=1, max_length=12)
    routine_text: str = Field(default="", max_length=1000)
    routine: Routine | None = None
    language: Literal["en", "hinglish", "hi"] = "hinglish"

    @field_validator("routine_text", "city")
    @classmethod
    def strip_control_characters(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if any(ord(char) < 32 and char not in "\n\t" for char in value):
            raise ValueError("Control characters are not allowed")
        return value.strip()


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=300)
    latitude: float | None = Field(default=28.6139, ge=-90, le=90)
    longitude: float | None = Field(default=77.2090, ge=-180, le=180)
    city: str | None = Field(default="Delhi", max_length=100)
