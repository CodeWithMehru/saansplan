"""Unit tests for app.core.limiting module."""

from __future__ import annotations

import pytest
from starlette.datastructures import Headers

from app.core.limiting import client_ip


class DummyRequest:
    """Minimal mock request object for testing client IP resolution."""

    def __init__(self, headers: dict[str, str], client_host: str = "127.0.0.1") -> None:
        self.headers = Headers(headers)
        self.client = type("Client", (), {"host": client_host})()


def test_client_ip_direct_without_proxy() -> None:
    """When proxy is untrusted, client.host must be used."""
    req = DummyRequest(headers={"x-forwarded-for": "1.2.3.4"}, client_host="192.168.1.1")
    ip = client_ip(req)  # type: ignore[arg-type]
    assert ip == "192.168.1.1"


def test_client_ip_with_trusted_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    """When proxy is trusted, leftmost x-forwarded-for IP should be resolved."""
    monkeypatch.setenv("TRUST_PROXY", "true")
    req = DummyRequest(
        headers={"x-forwarded-for": "203.0.113.195, 70.41.3.18"}, client_host="10.0.0.1"
    )
    ip = client_ip(req)  # type: ignore[arg-type]
    assert ip == "203.0.113.195"


def test_client_ip_empty_forwarded_with_trusted_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    """When proxy is trusted but no forwarded headers exist, fall back to client.host."""
    monkeypatch.setenv("TRUST_PROXY", "1")
    req = DummyRequest(headers={}, client_host="10.0.0.1")
    ip = client_ip(req)  # type: ignore[arg-type]
    assert ip == "10.0.0.1"
