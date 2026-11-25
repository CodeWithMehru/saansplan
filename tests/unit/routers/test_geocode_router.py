"""Unit tests for app.routers.geocode router."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

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
