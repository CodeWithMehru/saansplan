"""Open-Meteo air-quality fetcher with TTL cache and retries."""

import asyncio
import time
from typing import Any

import httpx

from app.config import (
    AIR_QUALITY_ENDPOINT,
    CACHE_TTL_SECONDS,
    OUTBOUND_RETRIES,
    OUTBOUND_TIMEOUT_SECONDS,
)

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def cache_key(latitude: float, longitude: float) -> str:
    """Create a 0.1-degree cache key for weather data reuse."""
    return f"{round(latitude, 1):.1f},{round(longitude, 1):.1f}"


async def fetch_air_quality(latitude: float, longitude: float) -> dict[str, Any]:
    """Fetch one day of hourly PM2.5 and US AQI data from Open-Meteo."""
    key = cache_key(latitude, longitude)
    cached = _CACHE.get(key)
    if cached and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    params = {
        "latitude": round(latitude, 4),
        "longitude": round(longitude, 4),
        "hourly": "pm2_5,us_aqi",
        "forecast_days": 1,
        "timezone": "auto",
    }
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=OUTBOUND_TIMEOUT_SECONDS) as client:
        for attempt in range(OUTBOUND_RETRIES + 1):
            try:
                response = await client.get(AIR_QUALITY_ENDPOINT, params=params)
                response.raise_for_status()
                payload = response.json()
                hourly = payload.get("hourly", {})
                pm25 = hourly.get("pm2_5", [None] * 24)
                aqi = hourly.get("us_aqi", [None] * 24)
                times = hourly.get("time", [])
                result = {
                    "pm25": pm25,
                    "aqi": aqi,
                    "times": times,
                    "timezone": payload.get("timezone", "local time"),
                    "source": "Open-Meteo Air Quality API",
                }
                _CACHE[key] = (time.monotonic(), result)
                return result
            except Exception as error:
                last_error = error
                if attempt < OUTBOUND_RETRIES:
                    await asyncio.sleep(0.25 * (2**attempt))
    raise RuntimeError("Air-quality service unavailable") from last_error


def clear_air_quality_cache() -> None:
    """Clear cached responses; useful for tests and operator refresh."""
    _CACHE.clear()
