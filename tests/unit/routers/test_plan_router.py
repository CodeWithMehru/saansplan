"""Unit tests for app.routers.plan router."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_plan_invalid_schema_rejected() -> None:
    """Missing required location fields must return 422."""
    response = client.post("/api/plan", json={"latitude": "invalid"})
    assert response.status_code == 422


def test_plan_content_type_enforcement() -> None:
    """Non-JSON content type must return 415 Unsupported Media Type."""
    response = client.post("/api/plan", content="not-json", headers={"content-type": "text/plain"})
    assert response.status_code == 415
