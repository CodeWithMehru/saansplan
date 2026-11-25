"""FastAPI application entry point, lifecycle, and security configuration."""

import hashlib
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from app.config import MAX_REQUEST_BYTES
from app.core.limiting import limiter
from app.core.settings import get_settings
from app.routers import ask, geocode, health, plan

_settings = get_settings()
ENV = _settings.environment


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage application lifespan: shared HTTP client, cache setup, and graceful cleanup."""
    app.state.http_client = httpx.AsyncClient(
        timeout=_settings.outbound_timeout_seconds,
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
    )
    yield
    await app.state.http_client.aclose()


# In production, disable openapi and docs
docs_url = None if ENV == "production" else "/docs"
redoc_url = None if ENV == "production" else "/redoc"
openapi_url = None if ENV == "production" else "/openapi.json"

app = FastAPI(
    title="SaansPlan",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
    lifespan=lifespan,
)
app.state.limiter = limiter

# GZip compression for payloads over 1000 bytes
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(_settings.cors_origins),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


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


@app.middleware("http")
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


app.include_router(health.router, tags=["health"])
app.include_router(plan.router, tags=["plan"])
app.include_router(geocode.router, tags=["geocode"])
app.include_router(ask.router, tags=["ask"])
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def index() -> FileResponse:
    """Serve the lightweight application shell."""
    return FileResponse("app/static/index.html")


@app.get("/accessibility", include_in_schema=False)
async def accessibility() -> FileResponse:
    """Serve the WCAG 2.2 AA accessibility statement."""
    return FileResponse("app/static/accessibility.html")


@app.get("/.well-known/security.txt", include_in_schema=False)
async def security_txt() -> FileResponse:
    """Serve RFC 9116 security contact information."""
    return FileResponse("app/static/.well-known/security.txt", media_type="text/plain")


@app.get("/favicon.ico")
async def favicon() -> Response:
    """Serve a tiny inline SVG favicon."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<rect width="32" height="32" rx="8" fill="#146b43"/>'
        '<text x="16" y="23" text-anchor="middle" font-size="22" fill="#fff" '
        'font-family="sans-serif">S</text></svg>'
    )
    return Response(content=svg, media_type="image/svg+xml")


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return 429 response with RFC 6585 Retry-After header."""
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
        headers={"Retry-After": "60"},
    )


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception) -> JSONResponse:
    """Return a clean JSON error response for unknown API routes."""
    return JSONResponse(status_code=404, content={"detail": "Not found"})


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
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
