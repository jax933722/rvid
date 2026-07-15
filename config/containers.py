"""Composition root — the single place that wires concrete infrastructure.

Everything else depends on abstractions; only this module (and it alone) knows
the concrete engine, session factory, and repository implementations. It builds
fully-wired use cases for the presentation layer to consume.
"""

from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from bise.application.dto.export_dto import ExportFormat
from bise.application.ports.discovery import DiscoverySourcePort
from bise.application.ports.exporter import ExporterPort
from bise.application.ports.fetcher import PageFetcherPort
from bise.application.ports.html_parser import HtmlParserPort
from bise.application.ports.marketing_detector import MarketingDetectorPort
from bise.application.ports.page_speed import PageSpeedPort
from bise.application.ports.rate_limiter import RateLimiterPort
from bise.application.ports.search import SearchIndexPort
from bise.application.ports.seo_analyzer import SeoAnalyzerPort
from bise.application.ports.technology_detector import TechnologyDetectorPort
from bise.application.use_cases.auth.api_keys import CreateApiKey, ListApiKeys, RevokeApiKey
from bise.application.use_cases.auth.authenticate import AuthenticateApiKey
from bise.application.use_cases.auth.workspaces import (
    CreateWorkspace,
    GetOrCreateDefaultWorkspace,
)
from bise.application.use_cases.companies.create_company import CreateCompany
from bise.application.use_cases.companies.get_company import GetCompany
from bise.application.use_cases.companies.list_companies import ListCompanies
from bise.application.use_cases.crawling.get_crawl_job import GetCrawlJob
from bise.application.use_cases.crawling.list_crawl_jobs import ListCrawlJobs
from bise.application.use_cases.crawling.request_crawl import RequestCrawl
from bise.application.use_cases.discovery.discover_businesses import DiscoverBusinesses
from bise.application.use_cases.enrichment.detect_marketing import DetectMarketing
from bise.application.use_cases.enrichment.detect_technologies import DetectTechnologies
from bise.application.use_cases.enrichment.enqueue_enrichment import EnqueueEnrichment
from bise.application.use_cases.enrichment.get_company_seo import GetCompanySeo
from bise.application.use_cases.enrichment.get_queue_summary import GetQueueSummary
from bise.application.use_cases.enrichment.list_company_marketing import ListCompanyMarketing
from bise.application.use_cases.enrichment.list_company_technologies import ListCompanyTechnologies
from bise.application.use_cases.enrichment.list_technologies import ListTechnologies
from bise.application.use_cases.enrichment.run_seo_scan import RunSeoScan
from bise.application.use_cases.export.export_list import ExportListMembers
from bise.application.use_cases.export.export_search import ExportSearchResults
from bise.application.use_cases.search.rebuild_search_document import RebuildSearchDocument
from bise.application.use_cases.search.search_companies import SearchCompanies
from bise.application.use_cases.workspace.lists import (
    AddCompanyToList,
    CreateCompanyList,
    DeleteCompanyList,
    ListCompanyLists,
    ListListMembers,
    RemoveCompanyFromList,
)
from bise.application.use_cases.workspace.saved_searches import (
    DeleteSavedSearch,
    ListSavedSearches,
    SaveSearch,
)
from bise.application.use_cases.workspace.tags import (
    AddCompanyTag,
    ListCompanyTags,
    RemoveCompanyTag,
)
from bise.crawlers.website_crawler import WebsiteCrawler
from bise.infrastructure.analyzers.marketing_fingerprint import RuleBasedMarketingDetector
from bise.infrastructure.analyzers.seo_analyzer import BeautifulSoupSeoAnalyzer
from bise.infrastructure.analyzers.tech_fingerprint import RuleBasedTechnologyDetector
from bise.infrastructure.crawling.html_parser import BeautifulSoupHtmlParser
from bise.infrastructure.crawling.httpx_fetcher import FetcherConfig, HttpxPageFetcher
from bise.infrastructure.db.engine import create_db_engine, create_session_factory
from bise.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from bise.infrastructure.discovery.overpass_source import OverpassDiscoverySource
from bise.infrastructure.export.exporters import build_exporter
from bise.infrastructure.pagespeed.null_provider import NullPageSpeedProvider
from bise.infrastructure.ratelimit.token_bucket import InMemoryTokenBucketLimiter
from bise.infrastructure.search.sql_search_adapter import SqlSearchAdapter
from config.settings import Settings, get_settings


class Container:
    """Owns process-wide singletons and builds use cases on demand."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings: Settings = settings or get_settings()
        self.engine: Engine = create_db_engine(self.settings)
        self.session_factory: sessionmaker[Session] = create_session_factory(self.engine)
        self._fetcher: PageFetcherPort | None = None
        self._html_parser: HtmlParserPort | None = None
        self._tech_detector: TechnologyDetectorPort | None = None
        self._seo_analyzer: SeoAnalyzerPort | None = None
        self._page_speed: PageSpeedPort | None = None
        self._search_index: SearchIndexPort | None = None
        self._marketing_detector: MarketingDetectorPort | None = None
        self._discovery_source: DiscoverySourcePort | None = None
        self._default_workspace_id: int | None = None
        self._rate_limiter: RateLimiterPort | None = None

    def unit_of_work(self) -> SqlAlchemyUnitOfWork:
        """Create a fresh Unit of Work (one transactional scope per use case call)."""
        return SqlAlchemyUnitOfWork(self.session_factory)

    # --- Shared adapters (built lazily; only the crawler process needs them) ---
    def page_fetcher(self) -> PageFetcherPort:
        if self._fetcher is None:
            self._fetcher = HttpxPageFetcher(
                FetcherConfig(user_agent=f"BISEbot/{self.settings.env}")
            )
        return self._fetcher

    def html_parser(self) -> HtmlParserPort:
        if self._html_parser is None:
            self._html_parser = BeautifulSoupHtmlParser()
        return self._html_parser

    def technology_detector(self) -> TechnologyDetectorPort:
        if self._tech_detector is None:
            self._tech_detector = RuleBasedTechnologyDetector()
        return self._tech_detector

    def marketing_detector(self) -> MarketingDetectorPort:
        if self._marketing_detector is None:
            self._marketing_detector = RuleBasedMarketingDetector()
        return self._marketing_detector

    def discovery_source(self) -> DiscoverySourcePort:
        if self._discovery_source is None:
            self._discovery_source = OverpassDiscoverySource()
        return self._discovery_source

    def seo_analyzer(self) -> SeoAnalyzerPort:
        if self._seo_analyzer is None:
            self._seo_analyzer = BeautifulSoupSeoAnalyzer()
        return self._seo_analyzer

    def page_speed(self) -> PageSpeedPort:
        if self._page_speed is None:
            self._page_speed = NullPageSpeedProvider()
        return self._page_speed

    def search_index(self) -> SearchIndexPort:
        if self._search_index is None:
            self._search_index = SqlSearchAdapter(self.session_factory)
        return self._search_index

    def rate_limiter(self) -> RateLimiterPort:
        if self._rate_limiter is None:
            self._rate_limiter = InMemoryTokenBucketLimiter(
                capacity=self.settings.rate_limit_burst,
                refill_per_second=self.settings.rate_limit_per_minute / 60.0,
            )
        return self._rate_limiter

    # --- Use case factories (a new UoW per call keeps sessions request-scoped) ---
    def create_company(self) -> CreateCompany:
        return CreateCompany(self.unit_of_work())

    def get_company(self) -> GetCompany:
        return GetCompany(self.unit_of_work())

    def list_companies(self) -> ListCompanies:
        return ListCompanies(self.unit_of_work())

    def request_crawl(self) -> RequestCrawl:
        return RequestCrawl(self.unit_of_work())

    def list_crawl_jobs(self) -> ListCrawlJobs:
        return ListCrawlJobs(self.unit_of_work())

    def get_crawl_job(self) -> GetCrawlJob:
        return GetCrawlJob(self.unit_of_work())

    def detect_technologies(self) -> DetectTechnologies:
        return DetectTechnologies(self.unit_of_work(), self.technology_detector())

    def list_company_technologies(self) -> ListCompanyTechnologies:
        return ListCompanyTechnologies(self.unit_of_work())

    def list_technologies(self) -> ListTechnologies:
        return ListTechnologies(self.unit_of_work())

    def detect_marketing(self) -> DetectMarketing:
        return DetectMarketing(self.unit_of_work(), self.marketing_detector())

    def list_company_marketing(self) -> ListCompanyMarketing:
        return ListCompanyMarketing(self.unit_of_work())

    def discover_businesses(self) -> DiscoverBusinesses:
        return DiscoverBusinesses(self.unit_of_work(), self.discovery_source())

    def run_seo_scan(self) -> RunSeoScan:
        return RunSeoScan(self.unit_of_work(), self.seo_analyzer(), self.page_speed())

    def get_company_seo(self) -> GetCompanySeo:
        return GetCompanySeo(self.unit_of_work())

    def search_companies(self) -> SearchCompanies:
        return SearchCompanies(self.search_index())

    def rebuild_search_document(self) -> RebuildSearchDocument:
        return RebuildSearchDocument(self.unit_of_work(), self.search_index())

    def website_crawler(self) -> WebsiteCrawler:
        return WebsiteCrawler(
            uow_factory=self.unit_of_work,
            fetcher=self.page_fetcher(),
            parser=self.html_parser(),
        )

    # --- Workspace: saved searches, lists, tags ---
    def save_search(self) -> SaveSearch:
        return SaveSearch(self.unit_of_work())

    def list_saved_searches(self) -> ListSavedSearches:
        return ListSavedSearches(self.unit_of_work())

    def delete_saved_search(self) -> DeleteSavedSearch:
        return DeleteSavedSearch(self.unit_of_work())

    def create_company_list(self) -> CreateCompanyList:
        return CreateCompanyList(self.unit_of_work())

    def list_company_lists(self) -> ListCompanyLists:
        return ListCompanyLists(self.unit_of_work())

    def delete_company_list(self) -> DeleteCompanyList:
        return DeleteCompanyList(self.unit_of_work())

    def add_company_to_list(self) -> AddCompanyToList:
        return AddCompanyToList(self.unit_of_work())

    def remove_company_from_list(self) -> RemoveCompanyFromList:
        return RemoveCompanyFromList(self.unit_of_work())

    def list_list_members(self) -> ListListMembers:
        return ListListMembers(self.unit_of_work())

    def add_company_tag(self) -> AddCompanyTag:
        return AddCompanyTag(self.unit_of_work())

    def remove_company_tag(self) -> RemoveCompanyTag:
        return RemoveCompanyTag(self.unit_of_work())

    def list_company_tags(self) -> ListCompanyTags:
        return ListCompanyTags(self.unit_of_work())

    # --- Export ---
    def exporter(self, fmt: ExportFormat) -> ExporterPort:
        return build_exporter(fmt)

    def export_search_results(self, fmt: ExportFormat) -> ExportSearchResults:
        return ExportSearchResults(self.search_index(), self.exporter(fmt))

    def export_list_members(self, fmt: ExportFormat) -> ExportListMembers:
        return ExportListMembers(self.unit_of_work(), self.exporter(fmt))

    # --- Auth / workspaces / API keys ---
    def create_workspace(self) -> CreateWorkspace:
        return CreateWorkspace(self.unit_of_work())

    def get_or_create_default_workspace(self) -> GetOrCreateDefaultWorkspace:
        return GetOrCreateDefaultWorkspace(self.unit_of_work())

    def create_api_key(self) -> CreateApiKey:
        return CreateApiKey(self.unit_of_work())

    def list_api_keys(self) -> ListApiKeys:
        return ListApiKeys(self.unit_of_work())

    def revoke_api_key(self) -> RevokeApiKey:
        return RevokeApiKey(self.unit_of_work())

    def authenticate_api_key(self) -> AuthenticateApiKey:
        return AuthenticateApiKey(self.unit_of_work())

    def default_workspace_id(self) -> int:
        """The default workspace id, created on first use and memoized."""
        if self._default_workspace_id is None:
            dto = self.get_or_create_default_workspace().execute(
                self.settings.default_workspace_slug
            )
            assert dto.id is not None
            self._default_workspace_id = dto.id
        return self._default_workspace_id

    # --- Enrichment queue ---
    def enqueue_enrichment(self) -> EnqueueEnrichment:
        return EnqueueEnrichment(self.unit_of_work())

    def get_queue_summary(self) -> GetQueueSummary:
        return GetQueueSummary(self.unit_of_work())
