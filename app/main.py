"""FastAPI application entry point, lifecycle, and security configuration."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.error_handlers import register_error_handlers
from app.core.limiting import limiter
from app.core.middleware import security_middleware
from app.core.settings import get_settings

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

app.middleware("http")(security_middleware)
app.include_router(api_router)
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


register_error_handlers(app)

__all__ = [
    "accessibility",
    "app",
    "favicon",
    "index",
    "lifespan",
    "security_txt",
]
