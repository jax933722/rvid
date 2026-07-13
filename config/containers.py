"""Composition root — the single place that wires concrete infrastructure.

Everything else depends on abstractions; only this module (and it alone) knows
the concrete engine, session factory, and repository implementations. It builds
fully-wired use cases for the presentation layer to consume.
"""

from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from bise.application.ports.fetcher import PageFetcherPort
from bise.application.ports.html_parser import HtmlParserPort
from bise.application.ports.technology_detector import TechnologyDetectorPort
from bise.application.use_cases.companies.create_company import CreateCompany
from bise.application.use_cases.companies.get_company import GetCompany
from bise.application.use_cases.companies.list_companies import ListCompanies
from bise.application.use_cases.crawling.get_crawl_job import GetCrawlJob
from bise.application.use_cases.crawling.list_crawl_jobs import ListCrawlJobs
from bise.application.use_cases.crawling.request_crawl import RequestCrawl
from bise.application.use_cases.enrichment.detect_technologies import DetectTechnologies
from bise.application.use_cases.enrichment.list_company_technologies import ListCompanyTechnologies
from bise.application.use_cases.enrichment.list_technologies import ListTechnologies
from bise.crawlers.website_crawler import WebsiteCrawler
from bise.infrastructure.analyzers.tech_fingerprint import RuleBasedTechnologyDetector
from bise.infrastructure.crawling.html_parser import BeautifulSoupHtmlParser
from bise.infrastructure.crawling.httpx_fetcher import FetcherConfig, HttpxPageFetcher
from bise.infrastructure.db.engine import create_db_engine, create_session_factory
from bise.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
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

    def website_crawler(self) -> WebsiteCrawler:
        return WebsiteCrawler(
            uow_factory=self.unit_of_work,
            fetcher=self.page_fetcher(),
            parser=self.html_parser(),
        )
