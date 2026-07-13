"""``CrawledPage`` entity and ``PageType`` — a downloaded page record."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class PageType(StrEnum):
    """Classification of a crawled page by its role on the website."""

    HOME = "home"
    ABOUT = "about"
    CONTACT = "contact"
    BLOG = "blog"
    CAREERS = "careers"
    PRIVACY = "privacy"
    TERMS = "terms"
    OTHER = "other"


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class CrawledPage:
    """A single page fetched during a crawl job."""

    url: str
    page_type: PageType
    http_status: int
    content_hash: str
    content_type: str | None = None
    title: str | None = None
    crawl_job_id: int | None = None
    domain_id: int | None = None
    id: int | None = field(default=None)
    fetched_at: datetime = field(default_factory=_utcnow)
