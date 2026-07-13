"""In-memory fake of :class:`PageFetcherPort` for deterministic crawler tests."""

from __future__ import annotations

from collections.abc import Iterable

from bise.application.ports.fetcher import FetchedPage


class FakePageFetcher:
    """Serves preconfigured pages; records what was fetched; no network."""

    def __init__(
        self,
        pages: dict[str, FetchedPage],
        disallowed: Iterable[str] = (),
    ) -> None:
        self._pages = pages
        self._disallowed = set(disallowed)
        self.fetched: list[str] = []

    def can_fetch(self, url: str) -> bool:
        return url not in self._disallowed

    def fetch(self, url: str) -> FetchedPage:
        self.fetched.append(url)
        return self._pages.get(url, FetchedPage(url=url, status_code=404, ok=False))
