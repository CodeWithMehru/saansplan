"""Security and HTTP defense-in-depth automated tests."""

from datetime import UTC, datetime
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
            assert exp_date.timestamp() > datetime.now(UTC).timestamp()


def test_groq_api_key_never_leaked() -> None:
    """Verify GROQ_API_KEY value is never reflected in API outputs or headers."""
    dummy_key = "gsk_test_dummy_token_never_real_12345"
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


def test_rate_limit_retry_after_header() -> None:
    """Verify 429 response sets RFC 6585 Retry-After header."""
    from unittest.mock import MagicMock

    from slowapi.errors import RateLimitExceeded
    from starlette.requests import Request

    from app.core.error_handlers import rate_limit_handler

    req = Request({"type": "http", "method": "POST", "path": "/api/plan", "headers": []})
    mock_limit = MagicMock()
    mock_limit.error_message = "10 per minute"
    exc = RateLimitExceeded(mock_limit)
    import asyncio

    resp = asyncio.run(rate_limit_handler(req, exc))
    assert resp.status_code == 429
    assert resp.headers.get("Retry-After") == "60"


def test_redos_regex_timing_resilience() -> None:
    """Verify regex patterns execute in sub-millisecond time on pathological repetitive input."""
    import time

    from app.services.assistant_grounding import extract_hour, extract_room_size_sqft

    # 10,000 character repetition of potential backtracking triggers
    adversarial_text = "sqft " * 2000 + "99999" * 1000 + "shaam baje " * 1000
    t0 = time.perf_counter()
    _ = extract_room_size_sqft(adversarial_text)
    _ = extract_hour(adversarial_text)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert elapsed_ms < 50.0  # Must complete in under 50ms without catastrophic backtracking


def test_oversized_payload_rejected_with_413() -> None:
    """Verify requests exceeding MAX_REQUEST_BYTES are rejected with 413."""
    from app.core.constants import MAX_REQUEST_BYTES

    oversized = "x" * (MAX_REQUEST_BYTES + 500)
    resp = client.post(
        "/api/plan",
        content=oversized,
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 413
    assert "Request body is too large" in resp.json()["detail"]


def test_request_id_sanitization() -> None:
    """Ensure incoming X-Request-ID is validated and sanitized against injection."""
    # 1. Valid alphanumeric/allowed punctuation is preserved
    resp_valid = client.get("/health", headers={"X-Request-ID": "req-123_abc.xyz"})
    assert resp_valid.headers.get("X-Request-ID") == "req-123_abc.xyz"

    # 2. Invalid characters (spaces, semicolons, quotes) are reset to default
    resp_invalid_chars = client.get("/health", headers={"X-Request-ID": "bad id with spaces"})
    assert resp_invalid_chars.headers.get("X-Request-ID") == "local"

    resp_semi = client.get("/health", headers={"X-Request-ID": "bad;semi"})
    assert resp_semi.headers.get("X-Request-ID") == "local"

    # 3. Oversized (>64 chars) is rejected and reset to default
    resp_oversized = client.get("/health", headers={"X-Request-ID": "a" * 65})
    assert resp_oversized.headers.get("X-Request-ID") == "local"

    # 4. Missing header defaults to local
    resp_missing = client.get("/health")
    assert resp_missing.headers.get("X-Request-ID") == "local"


def test_invalid_content_length_rejected_with_400() -> None:
    """Verify non-numeric or negative Content-Length returns 400 Bad Request."""
    # 1. Non-numeric Content-Length
    resp_non_numeric = client.post(
        "/api/plan",
        content='{"routine": "test"}',
        headers={"Content-Type": "application/json", "Content-Length": "not-an-int"},
    )
    assert resp_non_numeric.status_code == 400
    assert resp_non_numeric.json()["detail"] == "Invalid Content-Length header"

    # 2. Negative Content-Length
    resp_negative = client.post(
        "/api/plan",
        content='{"routine": "test"}',
        headers={"Content-Type": "application/json", "Content-Length": "-42"},
    )
    assert resp_negative.status_code == 400
    assert resp_negative.json()["detail"] == "Invalid Content-Length header"
