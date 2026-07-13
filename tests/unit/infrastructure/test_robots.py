"""Unit tests for robots.txt compliance (fake loader, no network)."""

from __future__ import annotations

from bise.infrastructure.crawling.robots import RobotsPolicy

_ROBOTS = """
User-agent: *
Disallow: /private
Crawl-delay: 2
"""


def _policy(raw: str | None) -> RobotsPolicy:
    return RobotsPolicy("BISEbot", lambda _url: raw)


def test_allows_permitted_path() -> None:
    policy = _policy(_ROBOTS)
    assert policy.can_fetch("https://acme.com/about") is True


def test_disallows_blocked_path() -> None:
    policy = _policy(_ROBOTS)
    assert policy.can_fetch("https://acme.com/private/data") is False


def test_missing_robots_is_permissive() -> None:
    policy = _policy(None)
    assert policy.can_fetch("https://acme.com/anything") is True


def test_reads_crawl_delay() -> None:
    policy = _policy(_ROBOTS)
    assert policy.crawl_delay("https://acme.com/") == 2.0


def test_robots_is_cached_per_host() -> None:
    calls: list[str] = []

    def loader(url: str) -> str:
        calls.append(url)
        return _ROBOTS

    policy = RobotsPolicy("BISEbot", loader)
    policy.can_fetch("https://acme.com/a")
    policy.can_fetch("https://acme.com/b")
    assert calls == ["https://acme.com/robots.txt"]
