"""Family member definitions, age groupings, and sensitivity flags."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AgeGroup(str, Enum):
    """Vulnerability age bracket for breathing rate scaling and AQI susceptibility."""

    child = "child"
    adult = "adult"
    elderly = "elderly"


class FamilyMember(BaseModel):
    """Individual family member profile with physiological sensitivity."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=40)
    age_group: AgeGroup
    sensitive: bool = False
