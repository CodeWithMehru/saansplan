"""Standard application exception handlers."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded


async def rate_limit_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Return 429 response with RFC 6585 Retry-After header."""
    detail = getattr(exc, "detail", str(exc))
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {detail}"},
        headers={"Retry-After": "60"},
    )


async def not_found(_request: Request, _exc: Exception) -> JSONResponse:
    """Return a clean JSON error response for unknown API routes."""
    return JSONResponse(status_code=404, content={"detail": "Not found"})


async def validation_error(request: Request, _exc: Exception) -> JSONResponse:
    """Return a stable validation envelope without exposing internals."""
    request_id = request.headers.get("x-request-id", "local")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Check the submitted fields",
                "request_id": request_id,
            }
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers on the FastAPI instance."""
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_exception_handler(404, not_found)
    app.add_exception_handler(RequestValidationError, validation_error)


__all__ = [
    "not_found",
    "rate_limit_handler",
    "register_error_handlers",
    "validation_error",
]
