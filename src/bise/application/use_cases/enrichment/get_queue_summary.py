"""Use case: summarize the enrichment queue for the monitor UI."""

from __future__ import annotations

from bise.application.dto.enrichment_dto import QueueSummaryDTO
from bise.application.mappers import enrichment_job_to_dto
from bise.application.ports.unit_of_work import UnitOfWork
from bise.shared.pagination import PageRequest


class GetQueueSummary:
    """Return queue counts by status plus the most recent jobs."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, recent: int = 20) -> QueueSummaryDTO:
        with self._uow as uow:
            counts = uow.enrichment_jobs.counts_by_status()
            page = uow.enrichment_jobs.list(PageRequest(page=1, page_size=recent))
        return QueueSummaryDTO(
            counts=counts,
            recent=tuple(enrichment_job_to_dto(j) for j in page.items),
        )
