"""Website Crawler — the crawl engine (worker-side orchestration).

Given a crawl job, it fetches the homepage and a bounded set of key pages
(about, contact, blog, careers, privacy, terms), classifies and stores each,
then updates the job and domain state. It depends only on ports (fetcher,
parser) and repositories, so it is fully testable with fakes.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from urllib.parse import urlparse

from config.logging import get_logger

from bise.application.ports.fetcher import FetchedPage, PageFetcherPort
from bise.application.ports.html_parser import HtmlParserPort
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.crawl_job import CrawlJob
from bise.domain.entities.crawled_page import CrawledPage, PageType
from bise.domain.entities.website_domain import CrawlStatus
from bise.domain.services.page_classifier import classify_page_type

logger = get_logger(__name__)

# Page types worth following beyond the homepage.
_TARGET_TYPES = (
    PageType.ABOUT,
    PageType.CONTACT,
    PageType.BLOG,
    PageType.CAREERS,
    PageType.PRIVACY,
    PageType.TERMS,
)


def _host(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()


class WebsiteCrawler:
    """Fetches and records the important pages of a single website."""

    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        fetcher: PageFetcherPort,
        parser: HtmlParserPort,
        max_pages: int = 8,
    ) -> None:
        self._uow_factory = uow_factory
        self._fetcher = fetcher
        self._parser = parser
        self._max_pages = max_pages

    def run(self, job_id: int) -> None:
        """Execute the crawl for the given job id, updating its state."""
        job = self._start(job_id)
        if job is None:
            return
        try:
            pages = self._crawl(job)
            self._finish(job, pages)
            logger.info("crawl.completed", job_id=job.id, pages=len(pages))
        except Exception as exc:  # noqa: BLE001 - worker must not crash the pool
            self._mark_failed(job, exc)
            logger.warning("crawl.failed", job_id=job.id, error=str(exc))

    # --- steps -------------------------------------------------------------
    def _start(self, job_id: int) -> CrawlJob | None:
        with self._uow_factory() as uow:
            job = uow.crawl_jobs.get(job_id)
            if job is None:
                logger.warning("crawl.job_missing", job_id=job_id)
                return None
            job.start()
            uow.crawl_jobs.update(job)
            uow.companies.mark_domain_crawl_status(job.domain_id, CrawlStatus.CRAWLING)
            uow.commit()
            return job

    def _crawl(self, job: CrawlJob) -> list[CrawledPage]:
        base_url = f"https://{job.hostname}/"
        pages: list[CrawledPage] = []

        home = self._fetch(base_url, PageType.HOME, job)
        if home is not None:
            pages.append(home.page)

        candidates = self._select_candidates(home.fetched.html if home else "", job.hostname)
        for url, page_type in candidates:
            if len(pages) >= self._max_pages:
                break
            result = self._fetch(url, page_type, job)
            if result is not None:
                pages.append(result.page)
        return pages

    def _finish(self, job: CrawlJob, pages: list[CrawledPage]) -> None:
        with self._uow_factory() as uow:
            for page in pages:
                uow.crawled_pages.add(page)
            job.complete(len(pages))
            uow.crawl_jobs.update(job)
            uow.companies.mark_domain_crawl_status(job.domain_id, CrawlStatus.CRAWLED)
            uow.commit()

    def _mark_failed(self, job: CrawlJob, exc: Exception) -> None:
        with self._uow_factory() as uow:
            job.fail(f"{type(exc).__name__}: {exc}")
            uow.crawl_jobs.update(job)
            uow.companies.mark_domain_crawl_status(job.domain_id, CrawlStatus.FAILED)
            uow.commit()

    # --- helpers -----------------------------------------------------------
    def _fetch(self, url: str, page_type: PageType, job: CrawlJob) -> _FetchResult | None:
        if not self._fetcher.can_fetch(url):
            logger.info("crawl.robots_skip", url=url)
            return None
        fetched = self._fetcher.fetch(url)
        title = self._parser.extract_title(fetched.html) if fetched.is_html else None
        page = CrawledPage(
            crawl_job_id=job.id,
            domain_id=job.domain_id,
            url=fetched.url,
            page_type=page_type,
            http_status=fetched.status_code,
            content_type=fetched.content_type,
            title=title,
            content_hash=_content_hash(fetched.html),
        )
        return _FetchResult(fetched=fetched, page=page)

    def _select_candidates(self, home_html: str, hostname: str) -> list[tuple[str, PageType]]:
        if not home_html:
            return []
        chosen: dict[PageType, str] = {}
        for link in self._parser.extract_links(home_html, f"https://{hostname}/"):
            if _host(link) != hostname:
                continue
            page_type = classify_page_type(link)
            if page_type in _TARGET_TYPES and page_type not in chosen:
                chosen[page_type] = link
        return [(url, page_type) for page_type, url in chosen.items()]


class _FetchResult:
    """Internal pairing of a fetch outcome and its page record."""

    __slots__ = ("fetched", "page")

    def __init__(self, fetched: FetchedPage, page: CrawledPage) -> None:
        self.fetched = fetched
        self.page = page
