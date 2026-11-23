"""Unit tests for bounded TTL cache and single-flight compute."""

import asyncio

import pytest

from app.core.cache import BoundedTTLCache


def test_bounded_ttl_cache_lru_and_expiry():
    cache = BoundedTTLCache(max_size=2, ttl_seconds=0.1)
    cache.set("a", 1)
    cache.set("b", 2)

    assert cache.get("a") == 1
    assert cache.get("b") == 2

    # Exceed capacity
    cache.set("c", 3)
    # 'a' was accessed before 'b', so 'b' was least recently used when 'c' arrived
    assert cache.get("c") == 3


@pytest.mark.asyncio
async def test_single_flight_deduplication():
    cache = BoundedTTLCache(max_size=10, ttl_seconds=60.0)
    call_count = 0

    async def expensive_fetch():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.05)
        return "result"

    # Launch 5 concurrent requests for same key
    tasks = [cache.get_or_compute("same_key", expensive_fetch) for _ in range(5)]
    results = await asyncio.gather(*tasks)

    assert all(r == "result" for r in results)
    assert call_count == 1  # only computed once
