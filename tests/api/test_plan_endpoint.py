"""Contract and integration tests for /api/plan endpoint."""

from fastapi.testclient import TestClient

from app.main import app
from app.routers import plan

client = TestClient(app)


def test_plan_returns_422_when_age_group_is_unknown():
    payload = {
        "latitude": 28.6139,
        "longitude": 77.209,
        "members": [{"name": "Child", "age_group": "teenager_unknown", "sensitive": False}],
        "language": "en",
    }
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_plan_returns_422_when_latitude_out_of_bounds():
    payload = {
        "latitude": 95.0,  # invalid latitude > 90
        "longitude": 77.209,
        "members": [{"age_group": "adult", "sensitive": False}],
    }
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 422


def test_form_only_plan_mocked(monkeypatch):
    async def mock_air_quality(latitude, longitude, forecast_days=5, client=None):
        return {
            "pm25": [100.0] * 120,
            "aqi": [150.0] * 120,
            "wind_speed": [2.5] * 120,
            "timezone": "Asia/Kolkata",
            "source": "Open-Meteo test",
        }

    async def mock_explanation(*args, **kwargs):
        return {"explanation": "AI explanation unavailable", "ai_available": False}

    monkeypatch.setattr(plan, "fetch_air_quality", mock_air_quality)
    monkeypatch.setattr(plan, "explain_with_fallback", mock_explanation)

    payload = {
        "latitude": 28.6139,
        "longitude": 77.209,
        "members": [{"name": "Child", "age_group": "child", "sensitive": False}],
        "routine": {
            "activities": [
                {
                    "label": "Park walk",
                    "start_hour": 18,
                    "duration_min": 40,
                    "place": "outdoor",
                    "mode": "walk",
                    "intensity": "moderate",
                    "member_refs": [0],
                }
            ],
            "home": {
                "heating": "wood_coal",
                "cooking": "lpg",
                "windows": "mostly_closed",
                "purifier": False,
                "has_chimney": False,
            },
            "unclear": [],
        },
        "language": "hinglish",
    }
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert len(body["hourly"]) == 24
    assert body["top_swaps"]
    assert "forecast" in body
    assert len(body["forecast"]) == 5
    assert "cleaner_day" in body
    assert "emissions" in body
    assert "indoor_module" in body
    assert "personas" in body
    assert "community" in body
    assert body["explanation"]["ai_available"] is False


def test_free_text_plan_falls_back_without_key(monkeypatch):
    async def mock_air_quality(latitude, longitude, forecast_days=5, client=None):
        return {
            "pm25": [100.0] * 120,
            "aqi": [150.0] * 120,
            "wind_speed": [2.5] * 120,
            "timezone": "Asia/Kolkata",
            "source": "Open-Meteo test",
        }

    async def mock_parse(text):
        raise RuntimeError("Groq unavailable")

    async def mock_explanation(*args, **kwargs):
        return {"explanation": "AI explanation unavailable", "ai_available": False}

    monkeypatch.setattr(plan, "fetch_air_quality", mock_air_quality)
    monkeypatch.setattr(plan, "explain_with_fallback", mock_explanation)
    payload = {
        "latitude": 28.6139,
        "longitude": 77.209,
        "members": [{"age_group": "adult", "sensitive": False}],
        "routine_text": "Subah 7 baje bacche ko school chhodta hoon bike pe.",
        "language": "en",
    }
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 200
    assert response.json()["explanation"]["ai_available"] is False
