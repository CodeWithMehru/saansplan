"""Bounded memory-safe TTL cache with LRU eviction and single-flight locking."""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class BoundedTTLCache(Generic[T]):
    """In-memory cache with fixed maximum item capacity and time-to-live expiration."""

    def __init__(self, max_size: int = 128, ttl_seconds: float = 300.0) -> None:
        """Initialize cache with capacity limit and TTL duration in seconds."""
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._store: OrderedDict[str, tuple[float, T]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._in_flight: dict[str, asyncio.Future[T]] = {}
        self._background_tasks: set[asyncio.Task[None]] = set()

    def get(self, key: str) -> T | None:
        """Retrieve value if present and not expired, refreshing LRU position."""
        if key not in self._store:
            return None
        created_at, value = self._store[key]
        if time.monotonic() - created_at > self.ttl_seconds:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return value

    def _evict_expired(self, now: float) -> None:
        """Evict all entries that exceeded time-to-live."""
        expired = [k for k, (t, _) in self._store.items() if now - t > self.ttl_seconds]
        for k in expired:
            del self._store[k]

    def _evict_over_capacity(self) -> None:
        """Evict oldest entries when storage size exceeds maximum capacity."""
        while len(self._store) > self.max_size:
            self._store.popitem(last=False)

    def set(self, key: str, value: T) -> None:
        """Store value, evicting expired or oldest items if capacity is exceeded."""
        now = time.monotonic()
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = (now, value)
        self._evict_expired(now)
        self._evict_over_capacity()

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()

    async def get_or_compute(self, key: str, compute_fn: Callable[[], Awaitable[T]]) -> T:
        """Return cached value or run compute_fn with single-flight deduplication."""
        val = self.get(key)
        if val is not None:
            return val

        async with self._lock:
            val = self.get(key)
            if val is not None:
                return val

            if key in self._in_flight:
                future = self._in_flight[key]
            else:
                loop = asyncio.get_running_loop()
                future = loop.create_future()
                self._in_flight[key] = future
                task = asyncio.create_task(self._execute_compute(key, compute_fn, future))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

        return await future

    async def _execute_compute(
        self, key: str, compute_fn: Callable[[], Awaitable[T]], future: asyncio.Future[T]
    ) -> None:
        """Run asynchronous computation function and resolve the waiting future."""
        try:
            res = await compute_fn()
            self.set(key, res)
            if not future.done():
                future.set_result(res)
        except Exception as exc:  # noqa: BLE001  # Safe future error propagation boundary
            if not future.done():
                future.set_exception(exc)
        finally:
            async with self._lock:
                self._in_flight.pop(key, None)
