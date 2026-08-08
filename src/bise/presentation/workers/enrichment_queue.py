"""Background worker: drain the enrichment job queue.

Picks the oldest PENDING job, marks it RUNNING, runs the full enrichment
pipeline for that company, then records COMPLETED or FAILED. A single failing
company never stops the queue — its job is marked FAILED and the loop moves on.

This is the piece that lets a whole discovered/list set enrich without blocking
the request that scheduled it. It can run inside an API "drain" call (bounded by
``max_jobs``) or as a long-lived process (see ``scripts/enrichment_worker.py``).
"""

from __future__ import annotations

from collections.abc import Callable

from config.containers import Container
from config.logging import get_logger

from bise.presentation.workers.enrich import enrich_company

logger = get_logger(__name__)

EnrichFn = Callable[[Container, int], None]


def process_enrichment_jobs(
    container: Container,
    max_jobs: int | None = None,
    enrich: EnrichFn = enrich_company,
) -> int:
    """Process pending jobs until the queue is empty or ``max_jobs`` is reached.

    Returns the number of jobs processed (completed or failed).
    """
    processed = 0
    while max_jobs is None or processed < max_jobs:
        # Claim the next job in its own transaction so its RUNNING state is
        # visible before the (potentially slow) enrichment begins.
        with container.unit_of_work() as uow:
            job = uow.enrichment_jobs.next_pending()
            if job is None:
                break
            job.start()
            uow.enrichment_jobs.update(job)
            uow.commit()

        assert job.id is not None
        try:
            enrich(container, job.company_id)
            _finish(container, job.id, error=None)
        except Exception as exc:  # noqa: BLE001 - isolate one company's failure
            logger.warning("enrichment.job_failed", job_id=job.id, error=str(exc))
            _finish(container, job.id, error=str(exc))
        processed += 1

    logger.info("enrichment.drain_completed", processed=processed)
    return processed


def _finish(container: Container, job_id: int, error: str | None) -> None:
    """Mark a running job COMPLETED or FAILED in its own transaction."""
    with container.unit_of_work() as uow:
        job = uow.enrichment_jobs.get(job_id)
        if job is None:
            return
        if error is None:
            job.complete()
        else:
            job.fail(error)
        uow.enrichment_jobs.update(job)
        uow.commit()
