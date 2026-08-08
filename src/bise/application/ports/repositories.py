"""Repository ports (interfaces) owned by the application layer.

Concrete implementations live in ``infrastructure/db/repositories``. Business
logic depends only on these abstractions (Dependency Inversion), which is what
makes persistence swappable and use cases unit-testable with in-memory fakes.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from bise.domain.entities.api_key import ApiKey
from bise.domain.entities.company import Company
from bise.domain.entities.company_list import CompanyList
from bise.domain.entities.company_tag import CompanyTag
from bise.domain.entities.crawl_job import CrawlJob, CrawlJobStatus
from bise.domain.entities.crawled_page import CrawledPage
from bise.domain.entities.enrichment_job import EnrichmentJob, EnrichmentJobStatus
from bise.domain.entities.lead import Lead
from bise.domain.entities.lead_campaign import LeadCampaign
from bise.domain.entities.marketing_signal import MarketingSignal
from bise.domain.entities.person import Person
from bise.domain.entities.saved_search import SavedSearch
from bise.domain.entities.seo_profile import SeoProfile
from bise.domain.entities.technology import CompanyTechnology, Technology
from bise.domain.entities.website_domain import CrawlStatus
from bise.domain.entities.workspace import Workspace
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
    """Persistence for named Prospector searches (scoped to a workspace)."""

    def add(self, search: SavedSearch) -> SavedSearch:
        """Persist a new saved search (``search.workspace_id`` must be set)."""
        ...

    def get(self, workspace_id: int, search_id: int) -> SavedSearch | None:
        """Return the workspace's saved search with the given id, or ``None``."""
        ...

    def list(self, workspace_id: int) -> Sequence[SavedSearch]:
        """Return the workspace's saved searches, newest first."""
        ...

    def delete(self, workspace_id: int, search_id: int) -> bool:
        """Delete a workspace's saved search; return ``True`` if a row was removed."""
        ...


class CompanyListRepository(Protocol):
    """Persistence for company lists (scoped to a workspace; also bookmarking)."""

    def add(self, company_list: CompanyList) -> CompanyList:
        """Persist a new list (``company_list.workspace_id`` must be set)."""
        ...

    def get(self, workspace_id: int, list_id: int) -> CompanyList | None:
        """Return the workspace's list (with ``member_count`` filled), or ``None``."""
        ...

    def list(self, workspace_id: int) -> Sequence[CompanyList]:
        """Return the workspace's lists (with ``member_count`` filled), newest first."""
        ...

    def delete(self, workspace_id: int, list_id: int) -> bool:
        """Delete a workspace's list and its memberships; ``True`` if removed."""
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


class LeadCampaignRepository(Protocol):
    """Persistence for recurring lead-generation campaigns."""

    def add(self, campaign: LeadCampaign) -> LeadCampaign:
        """Persist a new campaign and return it with its assigned id."""
        ...

    def get(self, campaign_id: int) -> LeadCampaign | None:
        """Return the campaign with the given id, or ``None``."""
        ...

    def update(self, campaign: LeadCampaign) -> None:
        """Persist changes (cursor, last_run_at, active flag, …)."""
        ...

    def list(self) -> Sequence[LeadCampaign]:
        """Return all campaigns, newest first."""
        ...

    def list_due(self, now: datetime) -> Sequence[LeadCampaign]:
        """Return active campaigns whose interval has elapsed."""
        ...

    def delete(self, campaign_id: int) -> bool:
        """Delete a campaign and its leads; ``True`` if a row was removed."""
        ...


class LeadRepository(Protocol):
    """Persistence for leads (campaign↔company) with dedup + inbox reads."""

    def exists(self, campaign_id: int, company_id: int) -> bool:
        """Whether this company is already a lead for this campaign (dedup guard)."""
        ...

    def add(self, lead: Lead) -> Lead:
        """Persist a new lead and return it with its assigned id."""
        ...

    def count_for_campaign(self, campaign_id: int) -> int:
        """Total leads accumulated by a campaign."""
        ...

    def list_recent(
        self, limit: int, campaign_id: int | None = None
    ) -> Sequence[tuple[Lead, Company]]:
        """Return recent leads with their company, newest first (the inbox)."""
        ...


class PersonRepository(Protocol):
    """Persistence for people extracted from a company's website (shared data)."""

    def replace_for_company(self, company_id: int, people: list[Person]) -> None:
        """Replace all people for a company (idempotent re-extraction)."""
        ...

    def list_for_company(self, company_id: int) -> Sequence[Person]:
        """Return the company's people, seniority first then name."""
        ...


class WorkspaceRepository(Protocol):
    """Persistence for :class:`Workspace` (tenants)."""

    def add(self, workspace: Workspace) -> Workspace:
        """Persist a new workspace and return it with its assigned id."""
        ...

    def get(self, workspace_id: int) -> Workspace | None:
        """Return the workspace with the given id, or ``None``."""
        ...

    def get_by_slug(self, slug: str) -> Workspace | None:
        """Return the workspace with the given slug, or ``None``."""
        ...

    def list(self) -> Sequence[Workspace]:
        """Return all workspaces, oldest first."""
        ...


class ApiKeyRepository(Protocol):
    """Persistence + lookup for :class:`ApiKey` credentials."""

    def add(self, api_key: ApiKey) -> ApiKey:
        """Persist a new API key (already hashed) and return it with its id."""
        ...

    def get_active_by_hash(self, key_hash: str) -> ApiKey | None:
        """Return the non-revoked key matching this hash, or ``None`` (auth lookup)."""
        ...

    def list_for_workspace(self, workspace_id: int) -> Sequence[ApiKey]:
        """Return the workspace's keys, newest first."""
        ...

    def revoke(self, workspace_id: int, key_id: int) -> bool:
        """Revoke a workspace's key; return ``True`` if a key was revoked."""
        ...

    def touch_last_used(self, key_id: int) -> None:
        """Record that a key was just used to authenticate."""
        ...


class EnrichmentJobRepository(Protocol):
    """Persistence + queue operations for :class:`EnrichmentJob`."""

    def add(self, job: EnrichmentJob) -> EnrichmentJob:
        """Persist a new enrichment job and return it with its assigned id."""
        ...

    def get(self, job_id: int) -> EnrichmentJob | None:
        """Return the job with the given id, or ``None`` if absent."""
        ...

    def update(self, job: EnrichmentJob) -> None:
        """Persist state changes to an existing job."""
        ...

    def next_pending(self) -> EnrichmentJob | None:
        """Return the oldest PENDING job, or ``None`` if the queue is empty."""
        ...

    def has_active_for_company(self, company_id: int) -> bool:
        """Whether the company already has a PENDING or RUNNING job (dedupe guard)."""
        ...

    def list(
        self, page: PageRequest, status: EnrichmentJobStatus | None = None
    ) -> Page[EnrichmentJob]:
        """Return a page of jobs, newest first, optionally filtered by status."""
        ...

    def counts_by_status(self) -> dict[str, int]:
        """Return a mapping of status -> job count across the whole queue."""
        ...


class CompanyTagRepository(Protocol):
    """Persistence for company tags (normalized labels, scoped to a workspace)."""

    def add(self, tag: CompanyTag) -> CompanyTag:
        """Add a tag (idempotent within the workspace); return the stored tag."""
        ...

    def remove(self, workspace_id: int, company_id: int, label: str) -> bool:
        """Remove a workspace's tag from a company; ``True`` if a row was removed."""
        ...

    def list_for_company(self, workspace_id: int, company_id: int) -> Sequence[CompanyTag]:
        """Return the workspace's tags on a company, ordered by label."""
        ...
