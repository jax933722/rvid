"""``WebsiteDomain`` entity — a hostname belonging to a company.

Named ``WebsiteDomain`` (not ``Domain``) to avoid confusion with the DDD term
"domain layer". It is an entity: it has identity (``id`` once persisted) and a
lifecycle (its crawl status changes over time).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from bise.domain.errors import InvalidValueError


class CrawlStatus(StrEnum):
    """Lifecycle of a domain's crawl state."""

    PENDING = "pending"
    CRAWLING = "crawling"
    CRAWLED = "crawled"
    FAILED = "failed"


def _normalize_hostname(hostname: str) -> str:
    host = hostname.strip().lower()
    if not host or "." not in host or "/" in host or " " in host:
        raise InvalidValueError(f"Invalid hostname: {hostname!r}")
    return host[4:] if host.startswith("www.") else host


@dataclass(slots=True)
class WebsiteDomain:
    """A company website hostname (e.g. ``acme.com``)."""

    hostname: str
    is_primary: bool = False
    crawl_status: CrawlStatus = CrawlStatus.PENDING
    id: int | None = field(default=None)

    def __post_init__(self) -> None:
        self.hostname = _normalize_hostname(self.hostname)

    def mark_crawled(self) -> None:
        """Transition this domain to the CRAWLED state."""
        self.crawl_status = CrawlStatus.CRAWLED

    def mark_failed(self) -> None:
        """Transition this domain to the FAILED state."""
        self.crawl_status = CrawlStatus.FAILED
