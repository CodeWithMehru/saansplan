"""Shared SlowAPI rate limiter instance and client IP resolver."""

from fastapi import Request
from slowapi import Limiter

from app.core.settings import is_proxy_trusted


def client_ip(request: Request) -> str:
    """Return real client IP only when proxy trust is explicitly enabled."""
    if is_proxy_trusted():
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()[:45]
    if request.client:
        return request.client.host
    return "unknown"


limiter = Limiter(key_func=client_ip)
