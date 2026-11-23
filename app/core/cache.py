"""Bounded memory-safe TTL cache with LRU eviction and single-flight locking."""

import asyncio
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

T = TypeVar("T")


class BoundedTTLCache:
    """In-memory cache with fixed maximum item capacity and time-to-live expiration."""

    def __init__(self, max_size: int = 128, ttl_seconds: float = 300.0) -> None:
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._in_flight: dict[str, asyncio.Future[Any]] = {}

    def get(self, key: str) -> Any | None:
        """Retrieve value if present and not expired, refreshing LRU position."""
        if key not in self._store:
            return None
        created_at, value = self._store[key]
        if time.monotonic() - created_at > self.ttl_seconds:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: Any) -> None:
        """Store value, evicting expired or oldest items if capacity is exceeded."""
        now = time.monotonic()
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = (now, value)

        # Evict expired items first
        keys_to_remove = [k for k, (t, _) in self._store.items() if now - t > self.ttl_seconds]
        for k in keys_to_remove:
            del self._store[k]

        # Evict oldest if still over capacity
        while len(self._store) > self.max_size:
            self._store.popitem(last=False)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()

    async def get_or_compute(self, key: str, compute_fn: Callable[[], Awaitable[T]]) -> T:
        """Return cached value or run compute_fn with single-flight deduplication."""
        val = self.get(key)
        if val is not None:
            return val  # type: ignore[no-any-return]

        async with self._lock:
            val = self.get(key)
            if val is not None:
                return val  # type: ignore[no-any-return]

            if key in self._in_flight:
                future = self._in_flight[key]
            else:
                loop = asyncio.get_running_loop()
                future = loop.create_future()
                self._in_flight[key] = future
                asyncio.create_task(self._execute_compute(key, compute_fn, future))

        result = await future
        return result  # type: ignore[no-any-return]

    async def _execute_compute(
        self, key: str, compute_fn: Callable[[], Awaitable[T]], future: asyncio.Future[Any]
    ) -> None:
        try:
            res = await compute_fn()
            self.set(key, res)
            if not future.done():
                future.set_result(res)
        except Exception as exc:
            if not future.done():
                future.set_exception(exc)
        finally:
            async with self._lock:
                self._in_flight.pop(key, None)
