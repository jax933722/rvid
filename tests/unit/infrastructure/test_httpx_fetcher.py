"""Unit tests for HttpxPageFetcher using httpx.MockTransport (no real network)."""

from __future__ import annotations

import httpx

from bise.infrastructure.crawling.httpx_fetcher import FetcherConfig, HttpxPageFetcher

_ROBOTS = "User-agent: *\nDisallow: /secret\n"
_HTML = "<html><head><title>Acme</title></head><body>hi</body></html>"


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/robots.txt":
        return httpx.Response(200, text=_ROBOTS)
    if request.url.path == "/secret":
        return httpx.Response(200, text=_HTML, headers={"content-type": "text/html"})
    if request.url.path == "/missing":
        return httpx.Response(404, text="nope")
    return httpx.Response(200, text=_HTML, headers={"content-type": "text/html; charset=utf-8"})


def _fetcher() -> HttpxPageFetcher:
    client = httpx.Client(transport=httpx.MockTransport(_handler))
    return HttpxPageFetcher(
        FetcherConfig(default_delay_seconds=0.0),
        client=client,
        sleep=lambda _s: None,
    )


def test_fetch_returns_html_page() -> None:
    page = _fetcher().fetch("https://acme.com/about")
    assert page.ok is True
    assert page.status_code == 200
    assert page.is_html is True
    assert "Acme" in page.html


def test_http_404_is_not_ok_but_not_raised() -> None:
    page = _fetcher().fetch("https://acme.com/missing")
    assert page.ok is False
    assert page.status_code == 404


def test_can_fetch_respects_robots() -> None:
    fetcher = _fetcher()
    assert fetcher.can_fetch("https://acme.com/allowed") is True
    assert fetcher.can_fetch("https://acme.com/secret") is False
