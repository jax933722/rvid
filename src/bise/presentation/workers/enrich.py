"""On-demand enrichment: crawl a company's site and run the full analysis.

Runs the whole pipeline synchronously for a single company — crawl → detect
technologies → detect marketing → SEO scan → rebuild search index — so a
user-triggered "Enrich" makes the company fully searchable in one step.

This performs live network I/O (the crawl), so it is meant for on-demand,
single-company use, not bulk processing.
"""

from __future__ import annotations

from config.containers import Container
from config.logging import get_logger

from bise.application.dto.crawl_dto import RequestCrawlCommand
from bise.application.errors import NotFoundError

logger = get_logger(__name__)


def enrich_company(container: Container, company_id: int) -> None:
    """Crawl and fully enrich one company, then index it for search."""
    with container.unit_of_work() as uow:
        company = uow.companies.get(company_id)
        if company is None:
            raise NotFoundError(f"Company not found: {company_id}")
        primary = company.primary_domain
        hostname = primary.hostname if primary else None

    if hostname is not None:
        job = container.request_crawl().execute(RequestCrawlCommand(hostname=hostname))
        if job.id is not None:
            container.website_crawler().run(job.id)

    container.detect_technologies().execute(company_id)
    container.detect_marketing().execute(company_id)
    container.extract_people().execute(company_id)
    try:
        container.run_seo_scan().execute(company_id)
    except NotFoundError:
        # No crawled pages to analyze (e.g. the site was unreachable) — skip SEO.
        logger.info("enrich.seo_skipped", company_id=company_id)
    container.rebuild_search_document().execute(company_id)
    logger.info("enrich.completed", company_id=company_id)
