"""Enrichment queue API — enqueue background enrichment and drain the queue."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from bise.application.use_cases.enrichment.enqueue_enrichment import EnqueueEnrichment
from bise.application.use_cases.enrichment.get_queue_summary import GetQueueSummary
from bise.presentation.api.dependencies import (
    ContainerDep,
    WorkspaceDep,
    get_enqueue_enrichment,
    get_queue_summary,
)
from bise.presentation.api.schemas.enrichment import (
    EnqueueRequest,
    EnqueueResultResponse,
    QueueSummaryResponse,
)
from bise.presentation.workers.enrichment_queue import process_enrichment_jobs

router = APIRouter(tags=["enrichment"])


@router.post(
    "/enrichment/jobs",
    response_model=EnqueueResultResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue background enrichment for companies and/or a list",
)
async def enqueue(
    body: EnqueueRequest,
    workspace_id: WorkspaceDep,
    use_case: Annotated[EnqueueEnrichment, Depends(get_enqueue_enrichment)],
) -> EnqueueResultResponse:
    """Create PENDING jobs; companies already queued or running are skipped."""
    return EnqueueResultResponse.from_dto(use_case.execute(workspace_id, body.to_command()))


@router.get(
    "/enrichment/queue",
    response_model=QueueSummaryResponse,
    summary="Queue status: counts by status + recent jobs",
)
async def queue_status(
    use_case: Annotated[GetQueueSummary, Depends(get_queue_summary)],
) -> QueueSummaryResponse:
    return QueueSummaryResponse.from_dto(use_case.execute())


@router.post(
    "/enrichment/run",
    summary="Drain pending jobs now (bounded)",
)
async def run_queue(
    container: ContainerDep,
    max_jobs: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict[str, int]:
    """Process up to ``max_jobs`` pending jobs synchronously and report the count.

    For hands-off processing, run ``scripts/enrichment_worker.py`` as a separate
    process against the same database instead.
    """
    processed = process_enrichment_jobs(container, max_jobs=max_jobs)
    if processed:
        container.search_cache().clear()  # enriched companies changed the index
    return {"processed": processed}
