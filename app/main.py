"""FastAPI application entry point, lifecycle, and security configuration."""

import hashlib
import os
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app.config import MAX_REQUEST_BYTES
from app.limiting import limiter
from app.routers import ask, geocode, health, plan

load_dotenv()

ENV = os.getenv("ENVIRONMENT", "production")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage application lifespan: shared HTTP client, cache setup, and graceful cleanup."""
    app.state.http_client = httpx.AsyncClient(
        timeout=10.0,
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
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:8000").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def security_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Apply strict body size limits, strict CSP, and defense-in-depth headers."""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Request body is too large"})

    try:
        response = await call_next(request)
    except Exception:
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    # Strict Content Security Policy with no unsafe-inline or unsafe-eval
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

    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
        # Generate weak ETag for static assets if body is available
        if hasattr(response, "body") and response.body:
            etag = f'W/"{hashlib.md5(response.body, usedforsecurity=False).hexdigest()[:16]}"'
            response.headers["ETag"] = etag
    else:
        response.headers["Cache-Control"] = "no-store"

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
