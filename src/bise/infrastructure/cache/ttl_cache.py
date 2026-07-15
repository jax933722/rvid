"""In-memory TTL cache (thread-safe, local-first) implementing ``CachePort``.

Entries expire lazily on read and are also pruned opportunistically on write, so
a burst of distinct keys can't grow the map without bound. State lives
in-process; a Redis cache can replace it behind the port for a shared cache.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable


class InMemoryTTLCache:
    """A dict-backed cache with per-entry expiry."""

    def __init__(self, *, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        # key -> (value, expires_at)
        self._entries: dict[str, tuple[bytes, float]] = {}

    def get(self, key: str) -> bytes | None:
        now = self._clock()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if expires_at <= now:
                del self._entries[key]
                return None
            return value

    def set(self, key: str, value: bytes, ttl_seconds: float) -> None:
        now = self._clock()
        with self._lock:
            # Opportunistically drop expired entries to bound memory.
            if len(self._entries) > 256:
                self._entries = {
                    k: v for k, v in self._entries.items() if v[1] > now
                }
            self._entries[key] = (value, now + ttl_seconds)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
