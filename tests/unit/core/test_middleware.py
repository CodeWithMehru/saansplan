"""Unit tests for app.core.middleware module."""

from __future__ import annotations

import pytest
from fastapi import Request, Response

from app.core.constants import MAX_REQUEST_BYTES
from app.core.middleware import (
    _apply_cache_headers,
    _apply_security_headers,
    _validate_request_limits,
    security_middleware,
)


def test_validate_request_limits_oversized_payload() -> None:
    """Request exceeding MAX_REQUEST_BYTES must return 413 Payload Too Large."""
    headers = [(b"content-length", str(MAX_REQUEST_BYTES + 500).encode())]
    scope = {"type": "http", "method": "POST", "path": "/api/plan", "headers": headers}
    request = Request(scope)
    res = _validate_request_limits(request)
    assert res is not None
    assert res.status_code == 413


def test_validate_request_limits_invalid_content_type() -> None:
    """POST to /api/ with non-JSON content-type must return 415 Unsupported Media Type."""
    headers = [
        (b"content-length", b"100"),
        (b"content-type", b"text/plain"),
    ]
    scope = {"type": "http", "method": "POST", "path": "/api/plan", "headers": headers}
    request = Request(scope)
    res = _validate_request_limits(request)
    assert res is not None
    assert res.status_code == 415


def test_validate_request_limits_valid_json() -> None:
    """Valid JSON request passes without rejection."""
    headers = [
        (b"content-length", b"100"),
        (b"content-type", b"application/json"),
    ]
    scope = {"type": "http", "method": "POST", "path": "/api/plan", "headers": headers}
    request = Request(scope)
    assert _validate_request_limits(request) is None


def test_apply_security_headers() -> None:
    """Response receives complete suite of security headers."""
    scope = {"type": "http", "headers": [(b"x-request-id", b"test-req-123")]}
    request = Request(scope)
    response = Response(content="ok")
    _apply_security_headers(response, request)
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Request-ID"] == "test-req-123"


def test_apply_security_headers_sanitizes_crlf_and_invalid_request_id() -> None:
    """Ensure invalid, CRLF injection, or oversized X-Request-ID defaults to local."""
    # CRLF injection in raw ASGI header
    req_crlf = Request({"type": "http", "headers": [(b"x-request-id", b"bad\r\ninjection")]})
    resp_crlf = Response(content="ok")
    _apply_security_headers(resp_crlf, req_crlf)
    assert resp_crlf.headers["X-Request-ID"] == "local"

    # Non-ASCII raw bytes
    req_unicode = Request({"type": "http", "headers": [(b"x-request-id", b"req-\xf0\x9f\x94\xa5")]})
    resp_unicode = Response(content="ok")
    _apply_security_headers(resp_unicode, req_unicode)
    assert resp_unicode.headers["X-Request-ID"] == "local"

    # Oversized > 64 chars
    req_long = Request({"type": "http", "headers": [(b"x-request-id", b"a" * 65)]})
    resp_long = Response(content="ok")
    _apply_security_headers(resp_long, req_long)
    assert resp_long.headers["X-Request-ID"] == "local"


def test_apply_cache_headers_static_and_dynamic() -> None:
    """Static assets get public cache headers and dynamic routes get no-store."""
    static_resp = Response(content=b"test-asset")
    _apply_cache_headers(static_resp, "/static/bundle.js")
    assert "public" in static_resp.headers["Cache-Control"]
    assert "ETag" in static_resp.headers

    dynamic_resp = Response(content=b"api-data")
    _apply_cache_headers(dynamic_resp, "/api/plan")
    assert dynamic_resp.headers["Cache-Control"] == "no-store"


@pytest.mark.asyncio
async def test_security_middleware_unhandled_exception_returns_500() -> None:
    """Unhandled exception in downstream pipeline returns clean 500 JSON boundary."""
    headers = [(b"content-type", b"application/json")]
    scope = {"type": "http", "method": "POST", "path": "/api/plan", "headers": headers}
    request = Request(scope)

    async def faulty_next(_req: Request) -> Response:
        raise RuntimeError("Crash inside handler")

    response = await security_middleware(request, faulty_next)
    assert response.status_code == 500
