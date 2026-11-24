"""Characterization snapshot tests ensuring zero regression across refactors."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    Activity,
    ActivityPlace,
    HomeSetup,
    Intensity,
    Routine,
    TravelMode,
)
from app.routers import plan

client = TestClient(app)
SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "snapshots"

FIXED_AIR_DATA: dict[str, Any] = {
    "pm25": [120.0 + (i % 6) * 15 for i in range(120)],
    "aqi": [180.0 + (i % 6) * 10 for i in range(120)],
    "wind_speed": [2.5] * 120,
    "timezone": "Asia/Kolkata",
    "source": "Open-Meteo Air Quality & Weather API (CAMS Ensemble)",
}


@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock Open-Meteo and Groq upstreams with fixed deterministic responses."""

    async def mock_fetch_aq(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return FIXED_AIR_DATA

    async def mock_parse_routine(text: str) -> Routine:
        return Routine(
            activities=[
                Activity(
                    label="School drop",
                    start_hour=7,
                    duration_min=30,
                    place=ActivityPlace.outdoor,
                    mode=TravelMode.walk,
                    intensity=Intensity.light,
                    member_refs=[0, 1],
                ),
                Activity(
                    label="Metro commute",
                    start_hour=9,
                    duration_min=45,
                    place=ActivityPlace.vehicle,
                    mode=TravelMode.metro,
                    intensity=Intensity.light,
                    member_refs=[0],
                ),
                Activity(
                    label="Park walk",
                    start_hour=18,
                    duration_min=60,
                    place=ActivityPlace.outdoor,
                    mode=TravelMode.walk,
                    intensity=Intensity.moderate,
                    member_refs=[0],
                ),
            ],
            home=HomeSetup(
                heating="none",
                cooking="lpg",
                windows="mostly_closed",
                purifier=False,
                has_chimney=False,
            ),
            unclear=[],
        )

    async def mock_explain(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "explanation": "At 6 pm AQI is 190, could reduce about 29% (estimate).",
            "ai_available": True,
        }

    monkeypatch.setattr(plan, "fetch_air_quality", mock_fetch_aq)
    monkeypatch.setattr(plan, "parse_routine", mock_parse_routine)
    monkeypatch.setattr(plan, "explain_with_fallback", mock_explain)

    from app.routers import ask

    async def mock_groq_chat(system: str, user: str, temperature: float, **kwargs: Any) -> str:
        try:
            data = json.loads(user)
            facts = data.get("deterministic_engine_facts", {})
            if "purifier_sizing" in facts:
                cfm = facts["purifier_sizing"]["recommended_smoke_cadr_cfm"]
                ans = (
                    "For this room size, the AHAM 2/3 guideline recommends a "
                    f"Smoke CADR of about {cfm} CFM [purifier-sizing]."
                )
                return json.dumps(
                    {
                        "answer": ans,
                        "kb_ids": ["purifier-sizing"],
                    }
                )
        except Exception:
            cpcb_ans = (
                "Refer to CPCB guidelines for air-quality precautions [cpcb-aqi-breakpoints]."
            )
            return json.dumps(
                {
                    "answer": cpcb_ans,
                    "kb_ids": ["cpcb-aqi-breakpoints"],
                }
            )
        cpcb_ans = "Refer to CPCB guidelines for air-quality precautions [cpcb-aqi-breakpoints]."
        return json.dumps(
            {
                "answer": cpcb_ans,
                "kb_ids": ["cpcb-aqi-breakpoints"],
            }
        )

    monkeypatch.setattr(ask, "groq_chat", mock_groq_chat)
    monkeypatch.setattr(ask, "fetch_air_quality", mock_fetch_aq)


def assert_or_record_snapshot(snapshot_name: str, actual_data: Any) -> None:
    """Compare normalized data with golden snapshot file, recording if absent."""
    snapshot_path = SNAPSHOT_DIR / f"{snapshot_name}.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    if not snapshot_path.exists():
        snapshot_path.write_text(json.dumps(actual_data, indent=2, sort_keys=True))
    expected = json.loads(snapshot_path.read_text())
    assert actual_data == expected


def test_characterization_plan_structured() -> None:
    payload = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "city": "Delhi",
        "members": [
            {"name": "Parent", "age_group": "adult", "sensitive": False},
            {"name": "Child", "age_group": "child", "sensitive": True},
        ],
        "routine": {
            "activities": [
                {
                    "label": "Morning Metro Commute",
                    "start_hour": 8,
                    "duration_min": 60,
                    "place": "vehicle",
                    "mode": "metro",
                    "intensity": "light",
                    "member_refs": [0],
                },
                {
                    "label": "Evening Park Walk",
                    "start_hour": 18,
                    "duration_min": 45,
                    "place": "outdoor",
                    "mode": "walk",
                    "intensity": "moderate",
                    "member_refs": [0, 1],
                },
            ],
            "home": {
                "heating": "none",
                "cooking": "lpg",
                "windows": "mostly_closed",
                "purifier": False,
                "has_chimney": False,
            },
        },
        "language": "en",
    }
    resp = client.post("/api/plan", json=payload)
    assert resp.status_code == 200
    assert_or_record_snapshot("plan_structured", resp.json())


def test_characterization_plan_hinglish_text() -> None:
    payload = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "city": "Delhi",
        "members": [
            {"name": "Parent", "age_group": "adult", "sensitive": False},
            {"name": "Child", "age_group": "child", "sensitive": True},
        ],
        "routine_text": (
            "Subah 7:30 bache ko school drop karte hain, 9 baje metro se office, "
            "shaam 6 baje park walk."
        ),
        "language": "hinglish",
    }
    resp = client.post("/api/plan", json=payload)
    assert resp.status_code == 200
    assert_or_record_snapshot("plan_hinglish", resp.json())


def test_characterization_ask_normal() -> None:
    resp = client.post(
        "/api/ask",
        json={"question": "What CADR is recommended for a 150 sq ft bedroom?"},
    )
    assert resp.status_code == 200
    assert_or_record_snapshot("ask_normal", resp.json())


def test_characterization_ask_symptom() -> None:
    question = (
        "I have chest tightness and severe shortness of breath from smog, "
        "what medicine should I take?"
    )
    resp = client.post(
        "/api/ask",
        json={"question": question},
    )
    assert resp.status_code == 200
    assert_or_record_snapshot("ask_symptom", resp.json())


def test_characterization_ask_purifier_sizing() -> None:
    resp = client.post(
        "/api/ask",
        json={"question": "Recommend air purifier for 200 sq ft room."},
    )
    assert resp.status_code == 200
    assert_or_record_snapshot("ask_purifier", resp.json())


def test_characterization_geocode(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, Any]:
            return {
                "results": [
                    {
                        "name": "Delhi",
                        "latitude": 28.65195,
                        "longitude": 77.23149,
                        "country": "India",
                    }
                ]
            }

    async def mock_get(*args: Any, **kwargs: Any) -> MockResponse:
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    resp = client.get("/api/geocode?name=Delhi")
    assert resp.status_code == 200
    assert_or_record_snapshot("geocode_delhi", resp.json())


def test_characterization_openapi_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import main

    monkeypatch.setattr(main, "ENV", "development")
    dev_app = main.app
    # Re-evaluate openapi_url in development mode
    schema = dev_app.openapi()
    assert schema["info"]["title"] == "SaansPlan"
    assert "/api/plan" in schema["paths"]
    assert "/api/ask" in schema["paths"]
    assert "/api/geocode" in schema["paths"]
    assert "/health" in schema["paths"]
    assert_or_record_snapshot("openapi_dev", schema)
