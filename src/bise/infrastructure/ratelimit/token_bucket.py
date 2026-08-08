"""In-memory token-bucket rate limiter (thread-safe, local-first).

Each identity gets a bucket that refills continuously at ``refill_per_second``
up to ``capacity`` tokens. A request consumes one token; when the bucket is
empty the request is denied and ``retry_after`` says how long until the next
token. State lives in-process, so this is ideal for a single API process; a
Redis-backed limiter can replace it behind :class:`RateLimiterPort` for a
multi-process deployment.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

from bise.application.ports.rate_limiter import RateLimitDecision


class InMemoryTokenBucketLimiter:
    """A process-local token-bucket implementation of ``RateLimiterPort``."""

    def __init__(
        self,
        capacity: int,
        refill_per_second: float,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        if refill_per_second <= 0:
            raise ValueError("refill_per_second must be > 0")
        self._capacity = capacity
        self._refill = refill_per_second
        self._clock = clock
        self._lock = threading.Lock()
        # identity -> (tokens, last_refill_ts)
        self._buckets: dict[str, tuple[float, float]] = {}

    def hit(self, identity: str) -> RateLimitDecision:
        now = self._clock()
        with self._lock:
            tokens, last = self._buckets.get(identity, (float(self._capacity), now))
            tokens = min(self._capacity, tokens + (now - last) * self._refill)

            if tokens >= 1.0:
                tokens -= 1.0
                self._buckets[identity] = (tokens, now)
                return RateLimitDecision(
                    allowed=True,
                    limit=self._capacity,
                    remaining=int(tokens),
                    retry_after=0.0,
                )

            self._buckets[identity] = (tokens, now)
            return RateLimitDecision(
                allowed=False,
                limit=self._capacity,
                remaining=0,
                retry_after=(1.0 - tokens) / self._refill,
            )
