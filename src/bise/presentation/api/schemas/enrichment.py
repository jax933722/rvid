"""Request/response schemas for the enrichment queue API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from bise.application.dto.enrichment_dto import (
    EnqueueEnrichmentCommand,
    EnqueueResultDTO,
    EnrichmentJobDTO,
    QueueSummaryDTO,
)


class EnqueueRequest(BaseModel):
    """Request body for ``POST /enrichment/jobs``."""

    company_ids: list[int] = Field(default_factory=list)
    list_id: int | None = Field(default=None, description="Enqueue every company in this list")

    def to_command(self) -> EnqueueEnrichmentCommand:
        return EnqueueEnrichmentCommand(
            company_ids=tuple(self.company_ids), list_id=self.list_id
        )


class EnrichmentJobResponse(BaseModel):
    """An enrichment job's state."""

    id: int | None
    company_id: int
    status: str
    attempts: int
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: EnrichmentJobDTO) -> EnrichmentJobResponse:
        return cls(
            id=dto.id,
            company_id=dto.company_id,
            status=dto.status,
            attempts=dto.attempts,
            error=dto.error,
            started_at=dto.started_at,
            finished_at=dto.finished_at,
            created_at=dto.created_at,
        )


class EnqueueResultResponse(BaseModel):
    """How many jobs an enqueue request created vs. skipped."""

    enqueued: int
    skipped: int
    jobs: list[EnrichmentJobResponse]

    @classmethod
    def from_dto(cls, dto: EnqueueResultDTO) -> EnqueueResultResponse:
        return cls(
            enqueued=dto.enqueued,
            skipped=dto.skipped,
            jobs=[EnrichmentJobResponse.from_dto(j) for j in dto.jobs],
        )


class QueueSummaryResponse(BaseModel):
    """Queue counts by status plus the most recent jobs."""

    counts: dict[str, int]
    recent: list[EnrichmentJobResponse]

    @classmethod
    def from_dto(cls, dto: QueueSummaryDTO) -> QueueSummaryResponse:
        return cls(
            counts=dto.counts,
            recent=[EnrichmentJobResponse.from_dto(j) for j in dto.recent],
        )
