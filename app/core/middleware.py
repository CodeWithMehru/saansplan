"""Security, caching, and payload size inspection middleware."""

from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from app.config import MAX_REQUEST_BYTES


def _validate_request_limits(request: Request) -> JSONResponse | None:
    """Validate request size and Content-Type."""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Request body is too large"})

    if request.method == "POST" and request.url.path.startswith("/api/"):
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type.lower():
            return JSONResponse(
                status_code=415,
                content={"detail": "Unsupported Media Type: expected application/json"},
            )
    return None


def _apply_security_headers(response: Response, request: Request) -> None:
    """Apply strict security and tracking headers to response."""
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["X-Request-ID"] = request.headers.get("x-request-id", "local")


def _apply_cache_headers(response: Response, path: str) -> None:
    """Apply caching policy and weak ETags for static assets."""
    if path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
        if hasattr(response, "body") and response.body:
            etag = f'W/"{hashlib.md5(response.body, usedforsecurity=False).hexdigest()[:16]}"'
            response.headers["ETag"] = etag
    else:
        response.headers["Cache-Control"] = "no-store"


async def security_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Apply strict body size limits, strict CSP, and defense-in-depth headers."""
    rejection = _validate_request_limits(request)
    if rejection is not None:
        return rejection

    try:
        response = await call_next(request)
    except Exception:  # noqa: BLE001  # Top-level ASGI error boundary
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    _apply_security_headers(response, request)
    _apply_cache_headers(response, request.url.path)
    return response


__all__ = [
    "security_middleware",
]
