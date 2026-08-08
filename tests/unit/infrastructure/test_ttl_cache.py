"""Unit tests for the in-memory TTL cache."""

from __future__ import annotations

from bise.infrastructure.cache.ttl_cache import InMemoryTTLCache


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def test_get_returns_stored_value() -> None:
    cache = InMemoryTTLCache()
    cache.set("k", b"v", ttl_seconds=10)
    assert cache.get("k") == b"v"


def test_missing_key_returns_none() -> None:
    assert InMemoryTTLCache().get("nope") is None


def test_entry_expires_after_ttl() -> None:
    clock = FakeClock()
    cache = InMemoryTTLCache(clock=clock)
    cache.set("k", b"v", ttl_seconds=5)
    clock.t = 4.9
    assert cache.get("k") == b"v"
    clock.t = 5.0
    assert cache.get("k") is None  # expired at exactly ttl


def test_clear_drops_all_entries() -> None:
    cache = InMemoryTTLCache()
    cache.set("a", b"1", ttl_seconds=10)
    cache.set("b", b"2", ttl_seconds=10)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None


def test_set_overwrites_and_refreshes_ttl() -> None:
    clock = FakeClock()
    cache = InMemoryTTLCache(clock=clock)
    cache.set("k", b"old", ttl_seconds=5)
    clock.t = 3
    cache.set("k", b"new", ttl_seconds=5)
    clock.t = 7  # would have expired the first entry, but ttl was refreshed
    assert cache.get("k") == b"new"
