"""Crawl worker entrypoint.

Processes PENDING crawl jobs by running the Website Crawler. This is the seam a
real queue/scheduler replaces in a later phase; today it is driven on demand
(CLI or a test). Because jobs are claimed from the database, running multiple
workers is safe once queue-level locking is added.
"""

from __future__ import annotations

from config.containers import Container
from config.logging import get_logger

from bise.domain.entities.crawl_job import CrawlJobStatus
from bise.shared.pagination import PageRequest

logger = get_logger(__name__)


def process_pending_jobs(container: Container, limit: int = 50) -> int:
    """Run the Website Crawler for up to ``limit`` pending jobs.

    Returns the number of jobs processed.
    """
    with container.unit_of_work() as uow:
        pending = uow.crawl_jobs.list(PageRequest(page=1, page_size=limit), CrawlJobStatus.PENDING)
        job_ids = [job.id for job in pending.items if job.id is not None]

    crawler = container.website_crawler()
    for job_id in job_ids:
        crawler.run(job_id)

    logger.info("crawl_worker.batch_done", processed=len(job_ids))
    return len(job_ids)
