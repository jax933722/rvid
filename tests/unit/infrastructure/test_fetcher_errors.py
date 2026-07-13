"""Error-handling edge cases for HttpxPageFetcher (all offline via MockTransport)."""

from __future__ import annotations

import httpx
import pytest

from bise.infrastructure.crawling.httpx_fetcher import FetcherConfig, HttpxPageFetcher

_HTML = "<html><head><title>ok</title></head><body>x</body></html>"


def _fetcher(handler: httpx.MockTransport) -> HttpxPageFetcher:
    client = httpx.Client(transport=handler, follow_redirects=True)
    return HttpxPageFetcher(
        FetcherConfig(default_delay_seconds=0.0, max_retries=2),
        client=client,
        sleep=lambda _s: None,
    )


@pytest.mark.parametrize("status", [429, 500, 503, 403])
def test_http_error_statuses_return_not_ok(status: int) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(status, text="err")

    page = _fetcher(httpx.MockTransport(handler)).fetch("https://x.com/page")
    assert page.ok is False
    assert page.status_code == status


def test_network_error_is_swallowed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        raise httpx.ConnectError("dns failure")

    page = _fetcher(httpx.MockTransport(handler)).fetch("https://x.com/page")
    assert page.ok is False
    assert page.status_code == 0  # network failure sentinel


def test_redirect_is_followed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        if request.url.path == "/old":
            return httpx.Response(301, headers={"location": "https://x.com/new"})
        return httpx.Response(200, text=_HTML, headers={"content-type": "text/html"})

    page = _fetcher(httpx.MockTransport(handler)).fetch("https://x.com/old")
    assert page.ok is True
    assert page.url.endswith("/new")


def test_non_html_content_type_has_empty_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(200, content=b"%PDF-1.4", headers={"content-type": "application/pdf"})

    page = _fetcher(httpx.MockTransport(handler)).fetch("https://x.com/file.pdf")
    assert page.ok is True
    assert page.is_html is False
    assert page.html == ""
