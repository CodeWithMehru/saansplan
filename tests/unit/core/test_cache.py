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


@pytest.mark.asyncio
async def test_cache_hits_and_cancelled_futures() -> None:
    """Verify BoundedTTLCache fast-path hits and completed future handling."""
    from unittest.mock import AsyncMock

    cache: BoundedTTLCache[str] = BoundedTTLCache(max_size=5, ttl_seconds=60.0)
    cache.set("preloaded", "val")

    # Hit before lock
    res1 = await cache.get_or_compute("preloaded", AsyncMock())
    assert res1 == "val"

    # Future already done in _execute_compute
    loop = asyncio.get_running_loop()
    f1: asyncio.Future[str] = loop.create_future()
    f1.set_result("cancelled_or_early")
    await cache._execute_compute("k_done", AsyncMock(return_value="late"), f1)

    f2: asyncio.Future[str] = loop.create_future()
    f2.set_result("early_done")

    async def fail() -> str:
        raise RuntimeError("fail")

    await cache._execute_compute("k_fail", fail, f2)


def test_cache_expiration_and_overwriting() -> None:
    """Verify BoundedTTLCache expiration on get, key overwrite, and eviction on set."""
    cache = BoundedTTLCache[str](max_size=3, ttl_seconds=0.05)
    cache.set("k1", "v1")
    cache.set("k1", "v1_new")  # overwrite key
    assert cache.get("k1") == "v1_new"

    time.sleep(0.06)
    assert cache.get("k1") is None  # expired during get()

    # Eviction of expired items during set()
    cache.set("k2", "v2")
    time.sleep(0.06)
    cache.set("k3", "v3")  # cleans up k2
    assert cache.get("k2") is None
    assert cache.get("k3") == "v3"


@pytest.mark.asyncio
async def test_cache_get_or_compute_exceptions_and_double_check() -> None:
    """Verify cache exception propagation and double-check locking recovery."""
    cache = BoundedTTLCache[str](max_size=5, ttl_seconds=60.0)

    async def failing_compute() -> str:
        raise ValueError("Computation failed")

    with pytest.raises(ValueError, match="Computation failed"):
        await cache.get_or_compute("err_key", failing_compute)

    async def successful_compute() -> str:
        return "success"

    res = await cache.get_or_compute("err_key", successful_compute)
    assert res == "success"
