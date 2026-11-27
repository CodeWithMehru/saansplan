"""Security, caching, and payload size inspection middleware."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.types import Message

from app.core.constants import MAX_REQUEST_BYTES

REQUEST_ID_REGEX = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class _BodySizeExceededError(Exception):
    """Internal exception raised when streaming request body exceeds MAX_REQUEST_BYTES."""


def _check_content_length(request: Request) -> JSONResponse | None:
    """Validate request size against MAX_REQUEST_BYTES."""
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            length = int(content_length)
        except (ValueError, TypeError):
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid Content-Length header"},
            )
        if length < 0:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid Content-Length header"},
            )
        if length > MAX_REQUEST_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body is too large"},
            )
    return None


def _check_api_content_type(request: Request) -> JSONResponse | None:
    """Enforce application/json media type on API POST endpoints."""
    if request.method == "POST" and request.url.path.startswith("/api/"):
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type.lower():
            return JSONResponse(
                status_code=415,
                content={"detail": "Unsupported Media Type: expected application/json"},
            )
    return None


def _validate_request_limits(request: Request) -> JSONResponse | None:
    """Validate request size and Content-Type."""
    return _check_content_length(request) or _check_api_content_type(request)


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
    raw_req_id = request.headers.get("x-request-id", "")
    req_id = raw_req_id if REQUEST_ID_REGEX.match(raw_req_id) else "local"
    response.headers["X-Request-ID"] = req_id


def _apply_cache_headers(response: Response, path: str) -> None:
    """Apply caching policy and weak ETags for static assets."""
    if path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
        if hasattr(response, "body") and response.body:
            etag = f'W/"{hashlib.md5(response.body, usedforsecurity=False).hexdigest()[:16]}"'
            response.headers["ETag"] = etag
    else:
        response.headers["Cache-Control"] = "no-store"


def _wrap_streaming_body_limiter(request: Request) -> None:
    """Wrap ASGI receive to enforce MAX_REQUEST_BYTES on streaming or chunked payloads."""
    content_length = request.headers.get("content-length")
    if content_length is not None:
        return
    bytes_received = 0
    orig_receive = request.receive

    async def limited_receive() -> Message:
        """Receive message chunks and abort with 413 if payload size exceeds budget."""
        nonlocal bytes_received
        msg = await orig_receive()
        if msg.get("type") == "http.request":
            body = msg.get("body", b"")
            if isinstance(body, bytes):
                bytes_received += len(body)
                if bytes_received > MAX_REQUEST_BYTES:
                    raise _BodySizeExceededError
        return msg

    request._receive = limited_receive


async def security_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Apply strict body size limits, strict CSP, and defense-in-depth headers."""
    rejection = _validate_request_limits(request)
    if rejection is not None:
        return rejection

    _wrap_streaming_body_limiter(request)

    try:
        response = await call_next(request)
    except _BodySizeExceededError:
        return JSONResponse(status_code=413, content={"detail": "Request body is too large"})
    except Exception:  # noqa: BLE001  # Top-level ASGI error boundary
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    _apply_security_headers(response, request)
    _apply_cache_headers(response, request.url.path)
    return response


__all__ = [
    "security_middleware",
]
