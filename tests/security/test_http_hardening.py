"""Security and HTTP defense-in-depth automated tests."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_post_rejects_non_json_content_type() -> None:
    """Ensure POST endpoints reject non-application/json with 415 Unsupported Media Type."""
    # 1. Plain text payload
    resp_text = client.post(
        "/api/plan",
        content="hello world",
        headers={"Content-Type": "text/plain"},
    )
    assert resp_text.status_code == 415
    assert "Unsupported Media Type" in resp_text.json()["detail"]

    # 2. Form urlencoded payload
    resp_form = client.post(
        "/api/ask",
        content="question=hello",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp_form.status_code == 415
    assert "Unsupported Media Type" in resp_form.json()["detail"]


def test_defense_in_depth_security_headers() -> None:
    """Ensure all mandatory security and isolation headers are present on responses."""
    resp = client.get("/health")
    assert resp.status_code == 200

    # Isolation and CSP headers
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert resp.headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in resp.headers["Content-Security-Policy"]
    assert "script-src 'self'" in resp.headers["Content-Security-Policy"]
    assert "X-Request-ID" in resp.headers


def test_security_txt_rfc_9116_compliance() -> None:
    """Validate RFC 9116 security.txt existence, MIME type, and mandatory fields."""
    resp = client.get("/.well-known/security.txt")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers.get("content-type", "")

    body = resp.text
    assert "Contact:" in body
    assert "Expires:" in body

    # Verify expiration date is in the future
    for line in body.splitlines():
        if line.startswith("Expires:"):
            date_str = line.split(":", 1)[1].strip()
            # ISO 8601 parsing
            clean_date_str = date_str.replace("Z", "+00:00")
            exp_date = datetime.fromisoformat(clean_date_str)
            assert exp_date.timestamp() > datetime.now().timestamp()


def test_groq_api_key_never_leaked() -> None:
    """Verify GROQ_API_KEY value is never reflected in API outputs or headers."""
    dummy_key = "gsk_test_dummy_token_never_real_12345"  # noqa: S105 - Test fixture dummy token
    with (
        patch.dict("os.environ", {"GROQ_API_KEY": dummy_key}),
        patch("app.services.assistant.groq_chat", new_callable=AsyncMock) as mock_chat,
    ):
        mock_chat.return_value = "Verified answer."
        resp = client.post(
            "/api/ask",
            json={"question": "purifier size"},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        assert dummy_key not in resp.text
        for hval in resp.headers.values():
            assert dummy_key not in hval
