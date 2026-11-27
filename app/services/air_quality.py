"""Open-Meteo air-quality and atmospheric dispersion fetcher with TTL cache and single-flight."""

import asyncio
from typing import Any

import httpx

from app.core.cache import BoundedTTLCache
from app.core.constants import (
    CACHE_TTL_SECONDS,
    DEFAULT_FORECAST_DAYS,
    HOURS_IN_DAY,
    HTTP_STATUS_OK,
    OUTBOUND_RETRIES,
    OUTBOUND_TIMEOUT_SECONDS,
)
from app.core.settings import get_settings
from app.engine.domain_models import AirQualityData

# Strict egress allowlist for outbound requests
ALLOWED_EGRESS_HOSTS = {
    "air-quality-api.open-meteo.com",
    "api.open-meteo.com",
    "geocoding-api.open-meteo.com",
    "api.groq.com",
}

_AQ_CACHE: BoundedTTLCache[AirQualityData] = BoundedTTLCache(
    max_size=64, ttl_seconds=CACHE_TTL_SECONDS
)
WEATHER_ENDPOINT = "https://api.open-meteo.com/v1/forecast"


def cache_key(latitude: float, longitude: float, days: int = DEFAULT_FORECAST_DAYS) -> str:
    """Create a 0.1-degree cache key for spatial weather data reuse."""
    return f"{round(latitude, 1):.1f},{round(longitude, 1):.1f}:{days}"


def _build_request_params(
    latitude: float, longitude: float, forecast_days: int
) -> tuple[dict[str, str | int | float], dict[str, str | int | float]]:
    """Build query params for air quality and wind speed requests."""
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
    return params, weather_params


def _parse_air_quality_payload(
    payload: dict[str, Any],
    w_resp: Any,
    forecast_days: int,
) -> AirQualityData:
    """Parse air quality and optional wind speed API responses."""
    total_expected_hours = forecast_days * HOURS_IN_DAY
    hourly = payload.get("hourly", {})
    pm25 = hourly.get("pm2_5", [None] * total_expected_hours)
    aqi = hourly.get("us_aqi", [None] * total_expected_hours)
    times = hourly.get("time", [])

    wind_speeds = None
    if isinstance(w_resp, httpx.Response) and w_resp.status_code == HTTP_STATUS_OK:
        w_hourly = w_resp.json().get("hourly", {})
        wind_speeds = w_hourly.get("wind_speed_10m")

    return AirQualityData(
        pm25=pm25,
        aqi=aqi,
        times=times,
        wind_speed=wind_speeds,
        timezone=payload.get("timezone", "Asia/Kolkata"),
        source="Open-Meteo Air Quality & Weather API (CAMS Ensemble)",
    )


async def _fetch_with_client(
    c: httpx.AsyncClient,
    params: dict[str, str | int | float],
    weather_params: dict[str, str | int | float],
    forecast_days: int,
) -> AirQualityData:
    """Perform HTTP calls with exponential backoff retries."""
    last_error: Exception | None = None
    for attempt in range(OUTBOUND_RETRIES + 1):
        try:
            aq_task = c.get(get_settings().air_quality_endpoint, params=params)
            w_task = c.get(WEATHER_ENDPOINT, params=weather_params)
            aq_resp, w_resp = await asyncio.gather(aq_task, w_task, return_exceptions=True)

            if isinstance(aq_resp, BaseException):
                raise aq_resp

            aq_resp.raise_for_status()
            return _parse_air_quality_payload(aq_resp.json(), w_resp, forecast_days)
        except Exception as error:  # noqa: BLE001  # Safe retry boundary
            last_error = error
            if attempt < OUTBOUND_RETRIES:
                await asyncio.sleep(0.2 * (2**attempt))
    raise RuntimeError("Air-quality service unavailable") from last_error


async def _execute_upstream_fetch(
    latitude: float,
    longitude: float,
    forecast_days: int,
    client: httpx.AsyncClient | None,
) -> AirQualityData:
    """Dispatch upstream request using existing or newly created AsyncClient."""
    params, weather_params = _build_request_params(latitude, longitude, forecast_days)
    if client is not None:
        return await _fetch_with_client(client, params, weather_params, forecast_days)
    async with httpx.AsyncClient(timeout=OUTBOUND_TIMEOUT_SECONDS) as new_client:
        return await _fetch_with_client(new_client, params, weather_params, forecast_days)


async def fetch_air_quality(
    latitude: float,
    longitude: float,
    forecast_days: int = DEFAULT_FORECAST_DAYS,
    client: httpx.AsyncClient | None = None,
) -> AirQualityData:
    """Fetch multi-day hourly PM2.5, AQI, and atmospheric wind speed data from Open-Meteo."""
    key = cache_key(latitude, longitude, forecast_days)
    return await _AQ_CACHE.get_or_compute(
        key,
        lambda: _execute_upstream_fetch(latitude, longitude, forecast_days, client),
    )


def clear_air_quality_cache() -> None:
    """Clear cached responses; useful for tests and operator refresh."""
    _AQ_CACHE.clear()
