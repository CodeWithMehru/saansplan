"""Backward-compatible re-export of rate limiter."""

from app.core.limiting import client_ip, limiter

__all__ = ["client_ip", "limiter"]
