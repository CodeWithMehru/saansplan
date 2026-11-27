"""Unit tests for app.services.air_quality and Open-Meteo fetching."""

from __future__ import annotations

import httpx
import pytest

from app.engine.assistant_models import AirQualityData
from app.services import air_quality
from app.services.air_quality import fetch_air_quality


@pytest.mark.asyncio
async def test_fetch_air_quality_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify air quality parser handles mocked fetch."""
    mocked_data = AirQualityData(
        pm25=[120.0] * 120,
        aqi=[200.0] * 120,
        times=[f"2026-11-25T{h:02d}:00" for h in range(120)],
        wind_speed=[5.0] * 120,
        timezone="Asia/Kolkata",
        source="Open-Meteo",
    )

    async def _mock_fetch(*args: object, **kwargs: object) -> AirQualityData:
        return mocked_data

    monkeypatch.setattr("app.services.air_quality._execute_upstream_fetch", _mock_fetch)
    data = await fetch_air_quality(28.6139, 77.2090)
    assert len(data.pm25) == 120
    assert data.pm25[0] == 120.0


class _MockRawResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return {
            "timezone": "Asia/Kolkata",
            "hourly": {
                "pm2_5": [100.0, None, 150.0],
                "us_aqi": [200, None, 300],
                "time": ["00", "01", "02"],
            },
        }


@pytest.mark.asyncio
async def test_fetch_air_quality_raw_upstream_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify raw Open-Meteo response formatting and cache clearing."""
    air_quality.clear_air_quality_cache()

    class _MockClient:
        async def __aenter__(self) -> _MockClient:
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

        async def get(self, *args: object, **kwargs: object) -> _MockRawResponse:
            return _MockRawResponse()

    monkeypatch.setattr(httpx, "AsyncClient", lambda *args, **kwargs: _MockClient())
    result = await air_quality.fetch_air_quality(28.6, 77.2)
    assert result["timezone"] == "Asia/Kolkata"
    assert result["pm25"][1] is None
