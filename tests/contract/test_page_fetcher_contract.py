"""Shared contract suite for PageFetcherPort implementations.

Both the real httpx fetcher (driven by a MockTransport, so no live network) and
the in-memory fake must honor the same behavioral contract.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
import pytest

from bise.application.ports.fetcher import FetchedPage, PageFetcherPort
from bise.infrastructure.crawling.httpx_fetcher import FetcherConfig, HttpxPageFetcher
from tests.fakes.fetcher import FakePageFetcher

GOOD_URL = "https://acme.com/about"
BAD_URL = "https://acme.com/missing"
BLOCKED_URL = "https://acme.com/secret"
_HTML = "<html><head><title>Acme</title></head><body>hi</body></html>"


@dataclass
class FetcherHarness:
    fetcher: PageFetcherPort


def _httpx_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/robots.txt":
        return httpx.Response(200, text="User-agent: *\nDisallow: /secret\n")
    if request.url.path == "/missing":
        return httpx.Response(404, text="nope")
    return httpx.Response(200, text=_HTML, headers={"content-type": "text/html"})


@pytest.fixture(params=["httpx", "fake"])
def harness(request: pytest.FixtureRequest) -> FetcherHarness:
    if request.param == "httpx":
        client = httpx.Client(transport=httpx.MockTransport(_httpx_handler))
        fetcher: PageFetcherPort = HttpxPageFetcher(
            FetcherConfig(default_delay_seconds=0.0), client=client, sleep=lambda _s: None
        )
        return FetcherHarness(fetcher=fetcher)

    pages = {
        GOOD_URL: FetchedPage(
            url=GOOD_URL, status_code=200, ok=True, html=_HTML, content_type="text/html"
        )
    }
    return FetcherHarness(fetcher=FakePageFetcher(pages, disallowed=[BLOCKED_URL]))


def test_fetch_returns_fetchedpage(harness: FetcherHarness) -> None:
    page = harness.fetcher.fetch(GOOD_URL)
    assert isinstance(page, FetchedPage)
    assert page.ok is True
    assert page.status_code == 200
    assert page.is_html is True


def test_fetch_does_not_raise_on_failure(harness: FetcherHarness) -> None:
    # A missing/unknown URL must return a non-ok result, never raise.
    page = harness.fetcher.fetch(BAD_URL)
    assert page.ok is False


def test_can_fetch_returns_bool(harness: FetcherHarness) -> None:
    assert isinstance(harness.fetcher.can_fetch(GOOD_URL), bool)


def test_robots_disallow_is_respected(harness: FetcherHarness) -> None:
    assert harness.fetcher.can_fetch(BLOCKED_URL) is False
