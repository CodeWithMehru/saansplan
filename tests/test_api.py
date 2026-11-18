from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_security_headers():
    response = client.get("/")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors" in response.headers["content-security-policy"]


def test_reject_bad_enum():
    response = client.post(
        "/api/plan",
        json={"latitude": 28.6, "longitude": 77.2, "members": [{"age_group": "infant"}]},
    )
    assert 400 <= response.status_code < 500


def test_reject_oversized_body():
    response = client.post(
        "/api/plan", content=b"x" * 70000, headers={"content-type": "application/json"}
    )
    assert response.status_code == 413
