"""Proxy-aware client IP tests."""

from fastapi import Request

from app.limiting import client_ip


def test_forwarded_ip_is_ignored_when_proxy_trust_is_disabled(monkeypatch) -> None:
    monkeypatch.setenv("TRUST_PROXY", "false")
    scope = {
        "type": "http",
        "client": ("10.0.0.8", 1234),
        "headers": [(b"x-forwarded-for", b"203.0.113.9")],
        "server": ("test", 80),
        "scheme": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "root_path": "",
    }
    assert client_ip(Request(scope)) == "10.0.0.8"


def test_forwarded_ip_is_used_when_proxy_trust_is_enabled(monkeypatch) -> None:
    monkeypatch.setenv("TRUST_PROXY", "true")
    scope = {
        "type": "http",
        "client": ("10.0.0.8", 1234),
        "headers": [(b"x-forwarded-for", b"203.0.113.9, 10.0.0.8")],
        "server": ("test", 80),
        "scheme": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "root_path": "",
    }
    assert client_ip(Request(scope)) == "203.0.113.9"
