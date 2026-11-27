"""Unit tests for app.core.cache module."""

from __future__ import annotations

import asyncio
import time

import pytest

from app.core.cache import BoundedTTLCache


def test_cache_set_get() -> None:
    """Verify basic set and get semantics."""
    cache: BoundedTTLCache[str] = BoundedTTLCache(max_size=3, ttl_seconds=10.0)
    cache.set("a", "1")
    assert cache.get("a") == "1"
    assert cache.get("nonexistent") is None


def test_cache_ttl_expiration() -> None:
    """Verify item expiration when TTL passes."""
    cache: BoundedTTLCache[str] = BoundedTTLCache(max_size=3, ttl_seconds=0.05)
    cache.set("k", "v")
    assert cache.get("k") == "v"
    time.sleep(0.06)
    assert cache.get("k") is None


def test_cache_lru_eviction() -> None:
    """Verify oldest items are evicted when capacity is reached."""
    cache: BoundedTTLCache[str] = BoundedTTLCache(max_size=2, ttl_seconds=100.0)
    cache.set("k1", "v1")
    cache.set("k2", "v2")
    cache.set("k3", "v3")  # should evict k1
    assert cache.get("k1") is None
    assert cache.get("k2") == "v2"
    assert cache.get("k3") == "v3"


def test_cache_clear() -> None:
    """Verify cache clear method empties the storage."""
    cache: BoundedTTLCache[str] = BoundedTTLCache(max_size=5, ttl_seconds=100.0)
    cache.set("x", "y")
    cache.clear()
    assert cache.get("x") is None


def test_bounded_ttl_cache_lru_and_expiry() -> None:
    """Verify bounded cache LRU ordering and subsequent access."""
    cache: BoundedTTLCache[int] = BoundedTTLCache(max_size=2, ttl_seconds=0.1)
    cache.set("a", 1)
    cache.set("b", 2)

    assert cache.get("a") == 1
    assert cache.get("b") == 2

    # Exceed capacity
    cache.set("c", 3)
    assert cache.get("c") == 3


@pytest.mark.asyncio
async def test_single_flight_deduplication() -> None:
    """Verify concurrent requests for the same key execute only once."""
    cache: BoundedTTLCache[str] = BoundedTTLCache(max_size=10, ttl_seconds=60.0)
    call_count = 0

    async def expensive_fetch() -> str:
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.05)
        return "result"

    # Launch 5 concurrent requests for same key
    tasks = [cache.get_or_compute("same_key", expensive_fetch) for _ in range(5)]
    results = await asyncio.gather(*tasks)

    assert all(r == "result" for r in results)
    assert call_count == 1  # only computed once
