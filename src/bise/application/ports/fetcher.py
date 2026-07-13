"""Page fetching port — the boundary between crawl logic and the network.

The crawler depends only on this interface, so it can be driven by a real HTTP
client in production and a deterministic fake in tests (no live internet in CI).
Robots and rate-limiting are the fetcher's responsibility, hidden behind it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class FetchedPage:
    """The outcome of fetching a single URL."""

    url: str
    status_code: int
    ok: bool
    html: str = ""
    content_type: str | None = None
    elapsed_ms: int = 0

    @property
    def is_html(self) -> bool:
        """True when the response looks like an HTML document."""
        return self.ok and (self.content_type or "").lower().startswith("text/html")


class PageFetcherPort(Protocol):
    """Fetches web pages politely (robots-aware, rate-limited)."""

    def can_fetch(self, url: str) -> bool:
        """Return True if robots.txt permits fetching this URL."""
        ...

    def fetch(self, url: str) -> FetchedPage:
        """Fetch a URL, returning a result even for HTTP/network errors.

        Implementations must not raise for ordinary HTTP failures (4xx/5xx) or
        network errors — they return ``FetchedPage(ok=False, ...)`` instead, so
        the crawler can record the outcome and continue.
        """
        ...
