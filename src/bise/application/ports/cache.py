"""Cache port — the swap seam for response/read caching.

An in-memory TTL cache implements this now (local-first, single process); a
Redis-backed cache can implement the same interface for a shared, multi-process
cache without touching call sites.
"""

from __future__ import annotations

from typing import Protocol


class CachePort(Protocol):
    """A simple string-keyed byte cache with per-entry TTL."""

    def get(self, key: str) -> bytes | None:
        """Return the cached bytes for ``key``, or ``None`` if absent/expired."""
        ...

    def set(self, key: str, value: bytes, ttl_seconds: float) -> None:
        """Store ``value`` under ``key`` for ``ttl_seconds`` seconds."""
        ...

    def clear(self) -> None:
        """Drop every entry (used to invalidate after writes)."""
        ...
