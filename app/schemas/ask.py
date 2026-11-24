"""Request models for the grounded Q&A ask endpoint."""

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    """Payload for submitting an air quality question with location coordinates."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=300)
    latitude: float | None = Field(default=28.6139, ge=-90, le=90)
    longitude: float | None = Field(default=77.2090, ge=-180, le=180)
    city: str | None = Field(default="Delhi", max_length=100)
