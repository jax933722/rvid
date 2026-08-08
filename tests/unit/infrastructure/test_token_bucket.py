"""Unit tests for the in-memory token-bucket limiter."""

from __future__ import annotations

import pytest

from bise.infrastructure.ratelimit.token_bucket import InMemoryTokenBucketLimiter


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def test_allows_up_to_capacity_then_denies() -> None:
    clock = FakeClock()
    limiter = InMemoryTokenBucketLimiter(capacity=3, refill_per_second=1.0, clock=clock)

    decisions = [limiter.hit("a") for _ in range(3)]
    assert all(d.allowed for d in decisions)
    assert decisions[-1].remaining == 0

    denied = limiter.hit("a")
    assert not denied.allowed
    assert denied.remaining == 0
    assert denied.retry_after == pytest.approx(1.0)  # 1 token / 1 per sec


def test_refills_over_time() -> None:
    clock = FakeClock()
    limiter = InMemoryTokenBucketLimiter(capacity=1, refill_per_second=2.0, clock=clock)

    assert limiter.hit("a").allowed
    assert not limiter.hit("a").allowed
    clock.t += 0.5  # 0.5s * 2/s = 1 token
    assert limiter.hit("a").allowed


def test_identities_are_independent() -> None:
    clock = FakeClock()
    limiter = InMemoryTokenBucketLimiter(capacity=1, refill_per_second=1.0, clock=clock)
    assert limiter.hit("a").allowed
    assert limiter.hit("b").allowed  # separate bucket
    assert not limiter.hit("a").allowed


def test_capacity_is_not_exceeded_by_refill() -> None:
    clock = FakeClock()
    limiter = InMemoryTokenBucketLimiter(capacity=2, refill_per_second=1.0, clock=clock)
    clock.t += 100  # lots of idle time
    assert limiter.hit("a").allowed
    assert limiter.hit("a").allowed
    assert not limiter.hit("a").allowed  # capped at 2, not 100


def test_invalid_config_rejected() -> None:
    with pytest.raises(ValueError):
        InMemoryTokenBucketLimiter(capacity=0, refill_per_second=1.0)
    with pytest.raises(ValueError):
        InMemoryTokenBucketLimiter(capacity=1, refill_per_second=0.0)
