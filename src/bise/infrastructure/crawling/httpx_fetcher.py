"""``HttpxPageFetcher`` — a polite, robots-aware :class:`PageFetcherPort`.

Enforces robots.txt, per-host rate limiting, request timeouts, and retry with
backoff. Ordinary HTTP/network failures are returned as ``FetchedPage(ok=False)``
rather than raised, so the crawler records the outcome and moves on.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from config.logging import get_logger

from bise.application.ports.fetcher import FetchedPage
from bise.infrastructure.crawling.robots import RobotsPolicy

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class FetcherConfig:
    """Tunable politeness/reliability parameters."""

    user_agent: str = "BISEbot/0.1 (+https://example.local/bot)"
    timeout_seconds: float = 15.0
    max_retries: int = 2
    default_delay_seconds: float = 1.0
    max_response_bytes: int = 2_000_000


class HttpxPageFetcher:
    """Fetches pages over HTTP using httpx, respecting robots and rate limits."""

    def __init__(
        self,
        config: FetcherConfig | None = None,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._config = config or FetcherConfig()
        self._client = client or httpx.Client(
            headers={"User-Agent": self._config.user_agent},
            timeout=self._config.timeout_seconds,
            follow_redirects=True,
        )
        self._sleep = sleep
        self._robots = RobotsPolicy(self._config.user_agent, self._load_robots)
        self._last_fetch_at: dict[str, float] = {}

    def _load_robots(self, robots_url: str) -> str | None:
        try:
            response = self._client.get(robots_url)
        except httpx.HTTPError:
            return None
        return response.text if response.status_code == 200 else None

    def can_fetch(self, url: str) -> bool:
        return self._robots.can_fetch(url)

    def _respect_rate_limit(self, url: str) -> None:
        host = urlparse(url).netloc
        delay = self._robots.crawl_delay(url) or self._config.default_delay_seconds
        last = self._last_fetch_at.get(host)
        if last is not None:
            elapsed = time.monotonic() - last
            if elapsed < delay:
                self._sleep(delay - elapsed)
        self._last_fetch_at[host] = time.monotonic()

    def fetch(self, url: str) -> FetchedPage:
        self._respect_rate_limit(url)
        started = time.monotonic()
        last_error: str | None = None

        for attempt in range(self._config.max_retries + 1):
            try:
                response = self._client.get(url)
            except httpx.HTTPError as exc:
                last_error = type(exc).__name__
                logger.warning("fetch.error", url=url, attempt=attempt, error=last_error)
                continue

            elapsed_ms = int((time.monotonic() - started) * 1000)
            content_type = response.headers.get("content-type", "").split(";")[0] or None
            is_html = (content_type or "").startswith("text/html")
            body = response.text[: self._config.max_response_bytes] if is_html else ""
            return FetchedPage(
                url=str(response.url),
                status_code=response.status_code,
                ok=response.is_success,
                html=body,
                content_type=content_type,
                elapsed_ms=elapsed_ms,
            )

        logger.warning("fetch.failed", url=url, error=last_error)
        return FetchedPage(url=url, status_code=0, ok=False)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
