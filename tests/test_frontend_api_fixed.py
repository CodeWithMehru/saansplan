from fastapi.testclient import TestClient

from app.main import app
from app.routers import plan

client = TestClient(app)


def test_form_only_plan_mocked(monkeypatch):
    async def mock_air_quality(latitude, longitude):
        return {
            "pm25": [100.0] * 24,
            "aqi": [150.0] * 24,
            "timezone": "Asia/Kolkata",
            "source": "Open-Meteo test",
        }

    monkeypatch.setattr(plan, "fetch_air_quality", mock_air_quality)
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
    assert body["explanation"]["ai_available"] is False


def test_free_text_plan_falls_back_without_key(monkeypatch):
    async def mock_air_quality(latitude, longitude):
        return {
            "pm25": [100.0] * 24,
            "aqi": [150.0] * 24,
            "timezone": "Asia/Kolkata",
            "source": "Open-Meteo test",
        }

    async def mock_parse(text):
        raise RuntimeError("Groq unavailable")

    monkeypatch.setattr(plan, "fetch_air_quality", mock_air_quality)
    monkeypatch.setattr(plan, "parse_routine", mock_parse)
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
