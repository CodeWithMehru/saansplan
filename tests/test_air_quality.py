import pytest

from app.services import air_quality


class MockResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "timezone": "Asia/Kolkata",
            "hourly": {
                "pm2_5": [100.0, None, 150.0],
                "us_aqi": [200, None, 300],
                "time": ["00", "01", "02"],
            },
        }


@pytest.mark.asyncio
async def test_air_quality_fetch(monkeypatch):
    pytest.importorskip("pytest_asyncio")
    air_quality.clear_air_quality_cache()

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, *args, **kwargs):
            return MockResponse()

    monkeypatch.setattr(air_quality.httpx, "AsyncClient", lambda timeout: MockClient())
    result = await air_quality.fetch_air_quality(28.6, 77.2)
    assert result["timezone"] == "Asia/Kolkata"
    assert result["pm25"][1] is None
