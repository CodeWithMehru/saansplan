"""Centralized, typed, frozen application settings loaded from environment."""

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Application runtime configuration and environment variables."""

    groq_api_key: str | None
    groq_model: str
    trust_proxy: bool
    environment: str
    cors_origins: tuple[str, ...]
    groq_endpoint: str
    air_quality_endpoint: str
    weather_endpoint: str
    geocoding_endpoint: str
    cache_ttl_seconds: int
    outbound_timeout_seconds: float
    outbound_retries: int
    rate_limit: str
    max_request_bytes: int


def load_settings() -> Settings:
    """Load settings from environment with verified defaults and validation."""
    cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:8000")
    cors_tuple = tuple(origin.strip() for origin in cors_raw.split(",") if origin.strip())

    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        trust_proxy=os.getenv("TRUST_PROXY", "false").lower() in ("true", "1", "yes"),
        environment=os.getenv("ENVIRONMENT", "production"),
        cors_origins=cors_tuple,
        groq_endpoint="https://api.groq.com/openai/v1/chat/completions",
        air_quality_endpoint="https://air-quality-api.open-meteo.com/v1/air-quality",
        weather_endpoint="https://api.open-meteo.com/v1/forecast",
        geocoding_endpoint="https://geocoding-api.open-meteo.com/v1/search",
        cache_ttl_seconds=30 * 60,
        outbound_timeout_seconds=10.0,
        outbound_retries=2,
        rate_limit="30/minute",
        max_request_bytes=64 * 1024,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton Settings instance."""
    return load_settings()
