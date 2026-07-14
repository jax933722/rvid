"""Repository ports (interfaces) owned by the application layer.

Concrete implementations live in ``infrastructure/db/repositories``. Business
logic depends only on these abstractions (Dependency Inversion), which is what
makes persistence swappable and use cases unit-testable with in-memory fakes.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from bise.domain.entities.company import Company
from bise.domain.entities.company_list import CompanyList
from bise.domain.entities.company_tag import CompanyTag
from bise.domain.entities.crawl_job import CrawlJob, CrawlJobStatus
from bise.domain.entities.crawled_page import CrawledPage
from bise.domain.entities.marketing_signal import MarketingSignal
from bise.domain.entities.saved_search import SavedSearch
from bise.domain.entities.seo_profile import SeoProfile
from bise.domain.entities.technology import CompanyTechnology, Technology
from bise.domain.entities.website_domain import CrawlStatus
from bise.shared.pagination import Page, PageRequest


class CompanyRepository(Protocol):
    """Persistence operations for the :class:`Company` aggregate."""

    def add(self, company: Company) -> Company:
        """Persist a new company and return it with its assigned id."""
        ...

    def get(self, company_id: int) -> Company | None:
        """Return the company with the given id, or ``None`` if absent."""
        ...

    def find_by_hostname(self, hostname: str) -> Company | None:
        """Return the company owning the given domain hostname, if any."""
        ...

    def list(self, page: PageRequest) -> Page[Company]:
        """Return a page of companies ordered by creation time (newest first)."""
        ...

    def mark_domain_crawl_status(self, domain_id: int, status: CrawlStatus) -> None:
        """Update the crawl status of a single owned domain."""
        ...


class CrawlJobRepository(Protocol):
    """Persistence operations for :class:`CrawlJob`."""

    def add(self, job: CrawlJob) -> CrawlJob:
        """Persist a new crawl job and return it with its assigned id."""
        ...

    def get(self, job_id: int) -> CrawlJob | None:
        """Return the crawl job with the given id, or ``None`` if absent."""
        ...

    def update(self, job: CrawlJob) -> None:
        """Persist state changes to an existing crawl job."""
        ...

    def list(self, page: PageRequest, status: CrawlJobStatus | None = None) -> Page[CrawlJob]:
        """Return a page of crawl jobs, optionally filtered by status."""
        ...


class CrawledPageRepository(Protocol):
    """Persistence operations for :class:`CrawledPage`."""

    def add(self, page: CrawledPage) -> CrawledPage:
        """Persist a crawled page record and return it with its assigned id."""
        ...

    def list_for_job(self, crawl_job_id: int) -> list[CrawledPage]:
        """Return all pages recorded for a crawl job."""
        ...

    def list_for_domain(self, domain_id: int) -> list[CrawledPage]:
        """Return all pages recorded for a domain (used by enrichment analyzers)."""
        ...


class TechnologyRepository(Protocol):
    """Persistence for canonical :class:`Technology` reference data."""

    def get_or_create(self, name: str, category: str, vendor: str | None = None) -> Technology:
        """Return the technology with this name, creating it (and category) if new."""
        ...

    def list(self, page: PageRequest) -> Page[Technology]:
        """Return a page of known technologies ordered by name."""
        ...


class CompanyTechnologyRepository(Protocol):
    """Persistence for company↔technology detections."""

    def replace_for_company(self, company_id: int, detections: list[CompanyTechnology]) -> None:
        """Replace all detections for a company (idempotent re-detection)."""
        ...

    def list_for_company(self, company_id: int) -> list[CompanyTechnology]:
        """Return all technologies detected for a company (with technology loaded)."""
        ...


class MarketingSignalRepository(Protocol):
    """Persistence for company marketing detections."""

    def replace_for_company(self, company_id: int, signals: list[MarketingSignal]) -> None:
        """Replace all marketing signals for a company (idempotent re-detection)."""
        ...

    def list_for_company(self, company_id: int) -> list[MarketingSignal]:
        """Return all marketing tools detected for a company."""
        ...


class SeoProfileRepository(Protocol):
    """Persistence for a company's SEO profile (one current profile per company)."""

    def upsert(self, profile: SeoProfile) -> SeoProfile:
        """Insert or replace the company's SEO profile."""
        ...

    def get_for_company(self, company_id: int) -> SeoProfile | None:
        """Return the company's current SEO profile, if scanned."""
        ...


class SavedSearchRepository(Protocol):
    """Persistence for named Prospector searches."""

    def add(self, search: SavedSearch) -> SavedSearch:
        """Persist a new saved search and return it with its assigned id."""
        ...

    def get(self, search_id: int) -> SavedSearch | None:
        """Return the saved search with the given id, or ``None`` if absent."""
        ...

    def list(self) -> Sequence[SavedSearch]:
        """Return all saved searches, newest first."""
        ...

    def delete(self, search_id: int) -> bool:
        """Delete a saved search; return ``True`` if a row was removed."""
        ...


class CompanyListRepository(Protocol):
    """Persistence for company lists (also used for bookmarking)."""

    def add(self, company_list: CompanyList) -> CompanyList:
        """Persist a new list and return it with its assigned id."""
        ...

    def get(self, list_id: int) -> CompanyList | None:
        """Return the list with the given id (with ``member_count`` filled), or ``None``."""
        ...

    def list(self) -> Sequence[CompanyList]:
        """Return all lists (with ``member_count`` filled), newest first."""
        ...

    def delete(self, list_id: int) -> bool:
        """Delete a list and its memberships; return ``True`` if a row was removed."""
        ...

    def add_company(self, list_id: int, company_id: int) -> bool:
        """Add a company to a list; ``True`` if newly added, ``False`` if already present."""
        ...

    def remove_company(self, list_id: int, company_id: int) -> bool:
        """Remove a company from a list; return ``True`` if a membership was removed."""
        ...

    def list_members(self, list_id: int) -> Sequence[Company]:
        """Return the companies in a list, newest membership first."""
        ...


class CompanyTagRepository(Protocol):
    """Persistence for company tags (normalized labels)."""

    def add(self, tag: CompanyTag) -> CompanyTag:
        """Add a tag to a company (idempotent); return the stored tag."""
        ...

    def remove(self, company_id: int, label: str) -> bool:
        """Remove a tag from a company; return ``True`` if a row was removed."""
        ...

    def list_for_company(self, company_id: int) -> Sequence[CompanyTag]:
        """Return all tags on a company, ordered by label."""
        ...
