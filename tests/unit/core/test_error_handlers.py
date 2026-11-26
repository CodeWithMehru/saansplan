"""Unit tests for app.core.error_handlers module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

from app.core.error_handlers import (
    not_found,
    rate_limit_handler,
    register_error_handlers,
    validation_error,
)


@pytest.mark.asyncio
async def test_rate_limit_handler_returns_429() -> None:
    """Rate limit exceeded returns 429 with Retry-After header."""
    scope = {"type": "http"}
    request = Request(scope)
    mock_limit = MagicMock()
    mock_limit.error_message = "10 per minute"
    exc = RateLimitExceeded(mock_limit)
    response = await rate_limit_handler(request, exc)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"


@pytest.mark.asyncio
async def test_not_found_returns_404() -> None:
    """404 handler returns clean JSON not found envelope."""
    scope = {"type": "http"}
    request = Request(scope)
    response = await not_found(request, Exception("Not Found"))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_validation_error_returns_stable_envelope() -> None:
    """Validation error handler formats standard VALIDATION_ERROR envelope."""
    headers = [(b"x-request-id", b"trace-999")]
    scope = {"type": "http", "headers": headers}
    request = Request(scope)
    exc = RequestValidationError([])
    response = await validation_error(request, exc)
    assert response.status_code == 422


def test_register_error_handlers_integration() -> None:
    """Registering handlers on fresh FastAPI app hooks exception handling."""
    test_app = FastAPI()
    register_error_handlers(test_app)
    client = TestClient(test_app)
    resp = client.get("/non-existent-route-404")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Not found"}
