"""API contract conformance tests for all public endpoints."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import plan

client = TestClient(app)


def test_health_contract() -> None:
    """Validate /health response contract schema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert data.get("status") == "ok"
    assert data.get("service") == "SaansPlan"


def test_geocode_contract() -> None:
    """Validate /api/geocode response schema with mocked upstream."""
    mock_payload = {
        "results": [
            {
                "name": "New Delhi",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "country": "India",
                "admin1": "Delhi",
            }
        ]
    }
    mock_resp = httpx.Response(200, json=mock_payload, request=httpx.Request("GET", "http://test"))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        response = client.get("/api/geocode?name=Delhi")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 1
        res = data["results"][0]
        assert isinstance(res["name"], str)
        assert isinstance(res["latitude"], float)
        assert isinstance(res["longitude"], float)


def test_ask_contract() -> None:
    """Validate /api/ask response contract schema."""
    response = client.post("/api/ask", json={"question": "What is PM2.5?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert isinstance(data["answer"], str)
    assert "kb_ids" in data
    assert isinstance(data["kb_ids"], list)
    assert "safety_redirect" in data
    assert isinstance(data["safety_redirect"], bool)


def test_plan_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate /api/plan full response envelope schema."""

    async def mock_air_quality(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "pm25": [80.0] * 120,
            "aqi": [160.0] * 120,
            "wind_speed": [2.0] * 120,
            "timezone": "Asia/Kolkata",
            "source": "Open-Meteo test",
        }

    async def mock_explanation(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"explanation": "Keep windows closed during smog peaks.", "ai_available": True}

    monkeypatch.setattr(plan, "fetch_air_quality", mock_air_quality)
    monkeypatch.setattr(plan, "explain_with_fallback", mock_explanation)

    payload = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "city": "Delhi",
        "members": [{"name": "Arun", "age_group": "adult", "sensitive": False}],
        "language": "en",
    }
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Required top-level fields
    expected_top_keys = {
        "location",
        "exposure",
        "cleaner_day",
        "top_swaps",
        "emissions",
        "forecast",
        "indoor_module",
        "community",
        "explanation",
        "estimate_label",
    }
    for key in expected_top_keys:
        assert key in data, f"Missing key in /api/plan contract: {key}"

    # Verify exposure structure
    exp = data["exposure"]
    assert "total_before" in exp
    assert "peak_hour" in exp
    assert "highest_aqi" in exp
    assert "hourly" in exp
    assert len(exp["hourly"]) == 24

    # Verify cleaner_day structure
    cd = data["cleaner_day"]
    assert "percent_reduction" in cd
    assert "inhaled_saved_ug" in cd
    assert "hourly_comparison" in cd

    # Verify emissions structure
    em = data["emissions"]
    assert "current" in em
    assert "all_alternatives" in em

    # Verify forecast structure
    assert isinstance(data["forecast"], list)
    assert len(data["forecast"]) > 0

    # Verify explanation structure
    assert isinstance(data["explanation"], dict)
    assert "explanation" in data["explanation"]
    assert "ai_available" in data["explanation"]
    assert isinstance(data["explanation"]["ai_available"], bool)
