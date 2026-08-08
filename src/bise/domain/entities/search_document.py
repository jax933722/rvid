"""``SearchDocument`` — the denormalized read projection of a company.

This is the one intentionally denormalized record in the system: the pipeline
rebuilds it from normalized truth (company, technologies, SEO, crawled pages) so
the write side stays 3NF while the read/search side is a single fast lookup.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class SearchDocument:
    """A searchable, filterable summary of one company."""

    company_id: int
    display_name: str
    primary_domain: str | None = None
    industry: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    size_bucket: str | None = None
    founded_year: int | None = None
    employee_count: int | None = None
    seo_score: float | None = None
    seo_grade: str | None = None
    technologies: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    has_ssl: bool = False
    has_contact_page: bool = False
    has_careers_page: bool = False
    has_blog: bool = False
    has_privacy: bool = False
    has_terms: bool = False
    text_blob: str = ""
    indexed_at: datetime = field(default_factory=_utcnow)
