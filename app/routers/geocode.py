"""Validated city search proxy for Open-Meteo geocoding."""

import asyncio

import httpx
from fastapi import APIRouter, HTTPException, Query, Request

from app.config import OUTBOUND_RETRIES, OUTBOUND_TIMEOUT_SECONDS, RATE_LIMIT
from app.limiting import limiter

router = APIRouter()


@router.get("/api/geocode")
@limiter.limit(RATE_LIMIT)
async def geocode(request: Request, name: str = Query(min_length=2, max_length=80)) -> dict:
    """Search a city and return only safe display coordinates."""
    params = {"name": name.strip(), "count": 5, "language": "en", "format": "json"}
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=OUTBOUND_TIMEOUT_SECONDS) as client:
        for attempt in range(OUTBOUND_RETRIES + 1):
            try:
                response = await client.get(
                    "https://geocoding-api.open-meteo.com/v1/search", params=params
                )
                response.raise_for_status()
                payload = response.json()
                results = payload.get("results", [])
                if not results:
                    return {"results": []}
                safe = []
                for result in results:
                    if not isinstance(result.get("latitude"), int | float):
                        continue
                    if not isinstance(result.get("longitude"), int | float):
                        continue
                    safe.append(
                        {
                            "name": str(result.get("name", ""))[:80],
                            "latitude": float(result["latitude"]),
                            "longitude": float(result["longitude"]),
                            "country": str(result.get("country", ""))[:80],
                            "admin1": str(result.get("admin1", ""))[:80],
                        }
                    )
                return {"results": safe}
            except Exception as error:
                last_error = error
                if attempt < OUTBOUND_RETRIES:
                    await asyncio.sleep(0.25 * (2**attempt))
    raise HTTPException(status_code=502, detail="City search is unavailable") from last_error
