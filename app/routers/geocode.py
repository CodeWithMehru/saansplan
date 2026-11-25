"""Validated city search proxy for Open-Meteo geocoding."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.config import OUTBOUND_RETRIES, OUTBOUND_TIMEOUT_SECONDS, RATE_LIMIT
from app.core.settings import Settings, get_settings
from app.limiting import limiter

router = APIRouter()


def _filter_safe_geocode_results(results: list[dict[str, Any]]) -> list[dict[str, str | float]]:
    """Filter raw geocoding payloads to validated safe coordinates."""
    safe: list[dict[str, str | float]] = []
    for result in results:
        lat = result.get("latitude")
        lon = result.get("longitude")
        if not isinstance(lat, int | float) or not isinstance(lon, int | float):
            continue
        safe.append(
            {
                "name": str(result.get("name", ""))[:80],
                "latitude": float(lat),
                "longitude": float(lon),
                "country": str(result.get("country", ""))[:80],
                "admin1": str(result.get("admin1", ""))[:80],
            }
        )
    return safe


async def _fetch_geocode_with_retry(
    params: dict[str, str | int], endpoint: str
) -> list[dict[str, str | float]]:
    """Execute outbound geocoding request with backoff retry."""
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=OUTBOUND_TIMEOUT_SECONDS) as client:
        for attempt in range(OUTBOUND_RETRIES + 1):
            try:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                payload = response.json()
                results = payload.get("results", [])
                return _filter_safe_geocode_results(results) if results else []
            except Exception as error:  # noqa: BLE001  # Safe retry boundary
                last_error = error
                if attempt < OUTBOUND_RETRIES:
                    await asyncio.sleep(0.25 * (2**attempt))
    msg = "City search is unavailable"
    raise HTTPException(status_code=502, detail=msg) from last_error


@router.get("/api/geocode")
@limiter.limit(RATE_LIMIT)
async def geocode(
    request: Request,
    name: str = Query(min_length=2, max_length=80),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Search a city and return only safe display coordinates."""
    endpoint = getattr(settings, "geocoding_endpoint", None) or get_settings().geocoding_endpoint
    params: dict[str, str | int] = {
        "name": name.strip(),
        "count": 5,
        "language": "en",
        "format": "json",
    }
    safe = await _fetch_geocode_with_retry(params, endpoint)
    return {"results": safe}
