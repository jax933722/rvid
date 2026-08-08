"""Rate limiter port — the swap seam for request throttling.

An in-memory token-bucket implements this now (local-first, no dependencies); a
Redis-backed limiter can implement the same interface for multi-process
deployments without touching the middleware.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    """The outcome of accounting for a single request against an identity."""

    allowed: bool
    limit: int
    remaining: int
    retry_after: float  # seconds until the next token is available (0 when allowed)


class RateLimiterPort(Protocol):
    """Accounts for one request by an identity and decides whether to allow it."""

    def hit(self, identity: str) -> RateLimitDecision:
        """Consume one unit for ``identity`` and return the decision."""
        ...
