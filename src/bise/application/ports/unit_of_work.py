"""Unit of Work port — a transaction boundary abstraction.

Use cases open a UoW, perform repository operations, then commit or roll back
atomically. The concrete implementation (SQLAlchemy) lives in infrastructure.
"""

from __future__ import annotations

from types import TracebackType
from typing import Protocol

from bise.application.ports.repositories import (
    ApiKeyRepository,
    CompanyListRepository,
    CompanyRepository,
    CompanyTagRepository,
    CompanyTechnologyRepository,
    CrawledPageRepository,
    CrawlJobRepository,
    EnrichmentJobRepository,
    MarketingSignalRepository,
    PersonRepository,
    SavedSearchRepository,
    SeoProfileRepository,
    TechnologyRepository,
    WorkspaceRepository,
)


class UnitOfWork(Protocol):
    """A transactional scope exposing the repositories it coordinates."""

    companies: CompanyRepository
    crawl_jobs: CrawlJobRepository
    crawled_pages: CrawledPageRepository
    technologies: TechnologyRepository
    company_technologies: CompanyTechnologyRepository
    seo_profiles: SeoProfileRepository
    marketing_signals: MarketingSignalRepository
    people: PersonRepository
    saved_searches: SavedSearchRepository
    company_lists: CompanyListRepository
    company_tags: CompanyTagRepository
    enrichment_jobs: EnrichmentJobRepository
    workspaces: WorkspaceRepository
    api_keys: ApiKeyRepository

    def __enter__(self) -> UnitOfWork: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None:
        """Persist all changes made within this scope."""
        ...

    def rollback(self) -> None:
        """Discard all changes made within this scope."""
        ...
