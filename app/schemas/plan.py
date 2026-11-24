"""Request models for the main plan generation endpoint."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.family import FamilyMember
from app.schemas.routine import MIN_PRINTABLE_ASCII, Routine


class PlanRequest(BaseModel):
    """Payload for submitting location, family demographics, and optional routine."""

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
        """Reject unprintable ASCII control characters while preserving whitespace."""
        if value is None:
            return None
        if any(ord(char) < MIN_PRINTABLE_ASCII and char not in "\n\t" for char in value):
            raise ValueError("Control characters are not allowed")
        return value.strip()
