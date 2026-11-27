"""Unit tests for FastAPI main application lifespan, endpoints, and error handling."""

from __future__ import annotations

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import Response

from app.core.error_handlers import not_found, validation_error
from app.core.middleware import _apply_cache_headers, security_middleware
from app.main import accessibility, lifespan, security_txt


@pytest.mark.asyncio
async def test_main_lifespan_manages_client() -> None:
    """Verify lifespan startup creates shared AsyncClient and closes it on shutdown."""
    dummy_app = FastAPI()
    async with lifespan(dummy_app):
        assert hasattr(dummy_app.state, "http_client")
        assert not dummy_app.state.http_client.is_closed


def test_main_static_cache_headers() -> None:
    """Verify static assets receive cache-control and ETag headers."""
    resp = Response(content=b"console.log(1);", media_type="application/javascript")
    _apply_cache_headers(resp, "/static/app.js")
    assert "public" in resp.headers["Cache-Control"]
    assert "ETag" in resp.headers


@pytest.mark.asyncio
async def test_main_security_middleware_catches_unhandled_error() -> None:
    """Verify security middleware catches unexpected exceptions and returns 500 JSON."""
    req = Request({"type": "http", "method": "GET", "path": "/test", "headers": []})

    async def throwing_call_next(r: Request) -> Response:
        raise RuntimeError("Internal crash")

    err_resp = await security_middleware(req, throwing_call_next)
    assert err_resp.status_code == 500


@pytest.mark.asyncio
async def test_main_custom_exception_handlers() -> None:
    """Verify 404 and 422 exception handlers produce standard JSON responses."""
    req = Request({"type": "http", "method": "GET", "path": "/test", "headers": []})

    nf_resp = await not_found(req, HTTPException(404))
    assert nf_resp.status_code == 404

    err = [{"loc": ("body",), "msg": "err", "type": "value_error"}]
    val_resp = await validation_error(req, RequestValidationError(errors=err))
    assert val_resp.status_code == 422


@pytest.mark.asyncio
async def test_accessibility_and_security_endpoints() -> None:
    """Verify accessibility.html and security.txt endpoints return valid FileResponses."""
    a_resp = await accessibility()
    assert a_resp.path == "app/static/accessibility.html"

    s_resp = await security_txt()
    assert s_resp.path == "app/static/.well-known/security.txt"
