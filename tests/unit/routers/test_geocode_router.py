"""Unit tests for app.routers.geocode router."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_geocode_short_query_returns_422() -> None:
    """City query under 2 characters must fail validation with 422."""
    response = client.get("/api/geocode?name=a")
    assert response.status_code == 422


def test_geocode_valid_query_mocked() -> None:
    """Mock geocode upstream service and verify structured response."""
    sample_results = [
        {
            "name": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "country": "India",
            "admin1": "Delhi",
        }
    ]
    with patch(
        "app.routers.geocode._fetch_geocode_with_retry", new=AsyncMock(return_value=sample_results)
    ):
        response = client.get("/api/geocode?name=Delhi")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1
        assert data["results"][0]["name"] == "Delhi"


@pytest.mark.asyncio
async def test_geocode_missing_coordinates_and_error() -> None:
    """Verify geocode handling of malformed records and upstream failure."""
    import httpx
    import pytest
    from fastapi import HTTPException
    from starlette.requests import Request

    from app.routers.geocode import geocode

    req = Request({"type": "http", "method": "GET", "path": "/api/geocode", "headers": []})
    mock_payload = {
        "results": [
            {"name": "NoLat", "longitude": 77.0},
            {"name": "NoLon", "latitude": 28.0},
            {"name": "Valid", "latitude": 28.6, "longitude": 77.2, "country": "India"},
        ]
    }
    mock_resp = httpx.Response(200, json=mock_payload, request=httpx.Request("GET", "http://test"))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await geocode(req, name="Delhi")
        assert len(result["results"]) == 1
        assert result["results"][0]["name"] == "Valid"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=httpx.Request("GET", "http://test"),
            response=httpx.Response(500, request=httpx.Request("GET", "http://test")),
        )
        with pytest.raises(HTTPException) as exc_info:
            await geocode(req, name="FailCity")
        assert exc_info.value.status_code == 502
