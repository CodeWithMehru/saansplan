"""Unit tests for app.routers.ask router."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ask_empty_question_rejected() -> None:
    """Empty question string should fail schema validation."""
    response = client.post("/api/ask", json={"question": ""})
    assert response.status_code == 422


def test_ask_valid_symptom_triage() -> None:
    """Symptom question receives immediate clinical triage response."""
    response = client.post(
        "/api/ask", json={"question": "I have shortness of breath and chest tightness"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "doctor" in data["answer"].lower() or "medical" in data["answer"].lower()
    assert data.get("safety_redirect") is True
