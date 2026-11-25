"""Unit tests for app.services.air_quality and Open-Meteo fetching."""

from __future__ import annotations

import pytest

from app.engine.domain_models import AirQualityData
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
