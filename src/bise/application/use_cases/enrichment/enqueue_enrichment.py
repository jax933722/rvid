"""Use case: enqueue background enrichment for companies and/or a whole list."""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.enrichment_dto import EnqueueEnrichmentCommand, EnqueueResultDTO
from bise.application.errors import NotFoundError
from bise.application.mappers import enrichment_job_to_dto
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.enrichment_job import EnrichmentJob

logger = get_logger(__name__)


class EnqueueEnrichment:
    """Create PENDING enrichment jobs, skipping companies already queued/running."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, workspace_id: int, command: EnqueueEnrichmentCommand) -> EnqueueResultDTO:
        with self._uow as uow:
            company_ids = list(command.company_ids)
            if command.list_id is not None:
                if uow.company_lists.get(workspace_id, command.list_id) is None:
                    raise NotFoundError(f"List not found: {command.list_id}")
                members = uow.company_lists.list_members(command.list_id)
                company_ids.extend(c.id for c in members if c.id is not None)

            enqueued = []
            skipped = 0
            seen: set[int] = set()
            for company_id in company_ids:
                if company_id in seen:
                    continue
                seen.add(company_id)
                if uow.companies.get(company_id) is None:
                    skipped += 1
                    continue
                if uow.enrichment_jobs.has_active_for_company(company_id):
                    skipped += 1
                    continue
                job = uow.enrichment_jobs.add(EnrichmentJob(company_id=company_id))
                enqueued.append(job)
            uow.commit()

        logger.info("enrichment.enqueued", enqueued=len(enqueued), skipped=skipped)
        return EnqueueResultDTO(
            enqueued=len(enqueued),
            skipped=skipped,
            jobs=tuple(enrichment_job_to_dto(j) for j in enqueued),
        )
