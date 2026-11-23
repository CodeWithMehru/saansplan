"""Open-Meteo air-quality and atmospheric dispersion fetcher with TTL cache and single-flight."""

import asyncio
from typing import Any

import httpx

from app.config import (
    AIR_QUALITY_ENDPOINT,
    CACHE_TTL_SECONDS,
    OUTBOUND_RETRIES,
    OUTBOUND_TIMEOUT_SECONDS,
)
from app.core.cache import BoundedTTLCache
from app.core.constants import DEFAULT_FORECAST_DAYS, HOURS_IN_DAY, HTTP_STATUS_OK

# Strict egress allowlist for outbound requests
ALLOWED_EGRESS_HOSTS = {
    "air-quality-api.open-meteo.com",
    "api.open-meteo.com",
    "geocoding-api.open-meteo.com",
    "api.groq.com",
}

_AQ_CACHE = BoundedTTLCache(max_size=64, ttl_seconds=CACHE_TTL_SECONDS)
WEATHER_ENDPOINT = "https://api.open-meteo.com/v1/forecast"


def cache_key(latitude: float, longitude: float, days: int = DEFAULT_FORECAST_DAYS) -> str:
    """Create a 0.1-degree cache key for spatial weather data reuse."""
    return f"{round(latitude, 1):.1f},{round(longitude, 1):.1f}:{days}"


async def fetch_air_quality(
    latitude: float,
    longitude: float,
    forecast_days: int = DEFAULT_FORECAST_DAYS,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Fetch multi-day hourly PM2.5, AQI, and atmospheric wind speed data from Open-Meteo."""
    key = cache_key(latitude, longitude, forecast_days)

    async def _fetch() -> dict[str, Any]:
        params: dict[str, str | int | float] = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "hourly": "pm2_5,us_aqi",
            "forecast_days": forecast_days,
            "timezone": "auto",
        }
        weather_params: dict[str, str | int | float] = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "hourly": "wind_speed_10m",
            "forecast_days": forecast_days,
            "timezone": "auto",
        }

        async def fetch_with_client(c: httpx.AsyncClient) -> dict[str, Any]:
            last_error: Exception | None = None
            total_expected_hours = forecast_days * HOURS_IN_DAY
            for attempt in range(OUTBOUND_RETRIES + 1):
                try:
                    aq_task = c.get(AIR_QUALITY_ENDPOINT, params=params)
                    w_task = c.get(WEATHER_ENDPOINT, params=weather_params)
                    aq_resp, w_resp = await asyncio.gather(aq_task, w_task, return_exceptions=True)

                    if isinstance(aq_resp, BaseException):
                        raise aq_resp

                    aq_resp.raise_for_status()
                    payload = aq_resp.json()
                    hourly = payload.get("hourly", {})
                    pm25 = hourly.get("pm2_5", [None] * total_expected_hours)
                    aqi = hourly.get("us_aqi", [None] * total_expected_hours)
                    times = hourly.get("time", [])

                    wind_speeds = None
                    if isinstance(w_resp, httpx.Response) and w_resp.status_code == HTTP_STATUS_OK:
                        w_hourly = w_resp.json().get("hourly", {})
                        wind_speeds = w_hourly.get("wind_speed_10m")

                    return {
                        "pm25": pm25,
                        "aqi": aqi,
                        "times": times,
                        "wind_speed": wind_speeds,
                        "timezone": payload.get("timezone", "Asia/Kolkata"),
                        "source": "Open-Meteo Air Quality & Weather API (CAMS Ensemble)",
                    }
                except Exception as error:
                    last_error = error
                    if attempt < OUTBOUND_RETRIES:
                        await asyncio.sleep(0.2 * (2**attempt))
            raise RuntimeError("Air-quality service unavailable") from last_error

        if client is not None:
            return await fetch_with_client(client)
        async with httpx.AsyncClient(timeout=OUTBOUND_TIMEOUT_SECONDS) as new_client:
            return await fetch_with_client(new_client)

    return await _AQ_CACHE.get_or_compute(key, _fetch)


def clear_air_quality_cache() -> None:
    """Clear cached responses; useful for tests and operator refresh."""
    _AQ_CACHE.clear()
